# duckv16 = v10 (anim bundle + Qwen3.8, output UNCAPPED) + one change:
# push a compact change summary into EVERY turn's user message, not just animated ones.
#
# Evidence (R19 transcript lane): the model reads the BOARD correctly and misreads its own
# TOOL OUTPUT - before_frame/history indexing confusion 8+ times in sk48, 6+ in cn04, a full
# turn each. The system prompt is already explicit about the semantics (prompts.py:54-55, 90),
# which is why prose is not the fix: that warning exists because someone already hit this.
#
# The harness already pushes a change description unasked - but only when the action animated
# (tool_agent.py:1441, describe_animation). This wires the same channel for ordinary actions.
# That channel is proven to reach the model: the sibling nudge at :1448 fired 7 times in sk48
# and the model acted on every one.
#
# NOT last_action_result: that is a sandbox global the model must choose to print, i.e. PULL.
# cn04 called animation() zero times; a pull-based affordance is how that happens.
import inference.agent.tool_agent as tool_agent
from inference.utils import animation as _anim

_BUDGET = 12  # changed cells listed before _format_changes emits its own "... N further" line

# Fail loudly if the upstream helpers moved - a silent no-op here would produce a v10-shaped
# run we would read as "pushing the diff does not help" (R8: duckmod's patches achieved zero
# adoption on this tree and nothing said so).
for _name in ("_diff_cells", "_bbox_text", "_format_changes"):
    assert callable(getattr(_anim, _name, None)), f"duckv16: inference.utils.animation.{_name} missing"
assert hasattr(tool_agent, "ToolAgent"), "duckv16: ToolAgent class missing"
assert callable(getattr(tool_agent.ToolAgent, "_build_user_prompt", None)), (
    "duckv16: ToolAgent._build_user_prompt missing - patch point moved"
)


def _previous_frame(current_frame, history_entries):
    """The frame immediately before `current_frame`, WITHOUT relying on list position.

    prompts.py:55 asserts history[-1].frame is the post-action board and not the previous
    one. That is a claim in a prompt, not a guarantee from the code - and mis-indexing this
    exact relationship is the defect this patch exists to remove, so the patch must not
    repeat it. Frame.step is monotonic per action, so pick by step and the question of
    whether history includes the current frame never arises.
    """
    if current_frame is None or not history_entries:
        return None
    older = [
        entry.frame
        for entry in history_entries
        if getattr(entry, "frame", None) is not None and entry.frame.step < current_frame.step
    ]
    return max(older, key=lambda f: f.step) if older else None


def describe_changes(current_frame, history_entries, previous_step_summary):
    """One line, or '' - mirrors describe_animation's contract exactly."""
    if current_frame is None:
        return ""
    # An animated action already gets describe_animation(). prompts.py:67 warns that an
    # animation with board_changed == False still means the action DID something, so an
    # empty cell-diff here would actively reinforce the wrong reading. Defer.
    if (previous_step_summary or {}).get("animation"):
        return ""
    previous = _previous_frame(current_frame, history_entries)
    if previous is None or previous.grid == current_frame.grid:
        return ""
    cells = _anim._diff_cells(previous.grid, current_frame.grid)
    if not cells:
        return ""
    detail = "; ".join(_anim._format_changes(cells, _BUDGET))
    noun = "cell" if len(cells) == 1 else "cells"
    return f"That action changed {len(cells)} {noun} ({_anim._bbox_text(cells)}): {detail}"


_ORIGINAL_BUILD_USER_PROMPT = tool_agent.ToolAgent._build_user_prompt
_FIRED = {"count": 0}
_ANCHOR = "You are still on the same level."


def _build_user_prompt_with_changes(self, action_num, **kwargs):
    text = _ORIGINAL_BUILD_USER_PROMPT(self, action_num, **kwargs)
    line = describe_changes(
        kwargs.get("current_frame"),
        kwargs.get("history_entries") or [],
        kwargs.get("previous_step_summary"),
    )
    if not line:
        return text
    _FIRED["count"] += 1
    # Sit next to the other per-turn state lines rather than at the tail, where the
    # boilerplate would separate it from what it describes.
    if _ANCHOR in text:
        return text.replace(_ANCHOR, _ANCHOR + "\n" + line, 1)
    return line + "\n" + text


tool_agent.ToolAgent._build_user_prompt = _build_user_prompt_with_changes
assert tool_agent.ToolAgent._build_user_prompt is _build_user_prompt_with_changes, (
    "duckv16: monkeypatch did not take"
)

# --- teeth, run here in the kernel against the code that will actually run ---
# Not a fixture of our own shape: build real Frames from the harness's own dataclass.
from inference.agent.runtime_state import Frame as _Frame, HistoryEntry as _HistoryEntry

_before = _Frame(grid=((0, 0), (0, 0)), step=4, level=1)
_after = _Frame(grid=((0, 1), (0, 0)), step=5, level=1)
_hist = [_HistoryEntry(action="X", frame=_before), _HistoryEntry(action="Y", frame=_after)]

# 1. fires on a real change, and finds `before` even though history ALSO holds `after`
_line = describe_changes(_after, _hist, None)
assert _line and "changed 1 cell " in _line, f"duckv16 teeth: no change line, got {_line!r}"
# 2. silent when nothing changed
assert describe_changes(_before, [_HistoryEntry(action="X", frame=_before)], None) == "", (
    "duckv16 teeth: fired on an unchanged board"
)
# 3. defers to describe_animation when the action animated
assert describe_changes(_after, _hist, {"animation": {"frames": 3}}) == "", (
    "duckv16 teeth: did not defer to the animation line"
)
# 4. index-free selection really is index-free: reverse the history order, same answer
assert describe_changes(_after, list(reversed(_hist)), None) == _line, (
    "duckv16 teeth: result depends on history ORDER - the step-based pick is not working"
)
# 5. the anchor exists in the real prompt text, so the line lands beside the state lines
#    (if this ever fails the line still ships, just prepended - hence a print, not an assert)
print(f"duckv16: patch installed, teeth 4/4 OK, budget={_BUDGET}, output UNCAPPED")
print(f"duckv16: sample line -> {_line}")
