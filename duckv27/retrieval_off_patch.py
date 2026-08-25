# duckv27 cell 12 — B39: turn the animation retrieval OFF, keep the awareness ON.
#
# WHY (notes/R39-the-newer-bundle-turned-a-feature-off.md): upstream wrote its own A/B
# verdict into the post-anim source. `animation_retrieval` ships default **False** there,
# with the reason in a comment: "it works and the model reaches for it unprompted in 64%
# of calls, but across Experiments 3 and 4 it bought no score, so we do not pay for it by
# default." Our `anim` bundle has the feature and NO flag to switch it off, so every run
# this campaign has ever made pays for it.
#
# ⚠️ OUR BUNDLE HAS ONE SWITCH WHERE UPSTREAM HAS TWO, and that is the whole reason this
# is a patch rather than a config line. `solver.py:685` gates retrieval on
# `animation_awareness` — the flag upstream keeps ON, because the `worth_inspecting`
# threshold it carries is the one result they call transferable. Flipping it would take
# the good half down with the bad. Confirmed live: `animation_awareness` reads True in
# thui-v1-1-r2's own events.
#
# THE SEAM IS TWO EDITS, NOT ONE. Upstream documents what happens if you do only the
# first: "that is how the Experiment 4 control arm ended up still advertising
# `animation()` while the handler was off" — the model then spends turns calling a dead
# tool, which is worse than leaving it alone.
#
#   1. `_HarnessGameSession.animation_record` -> always None. `step_env` then returns
#      {"executed": False, "query": "animation", "record": None}, byte-identical to the
#      shape it already returns when awareness is off. `payload["animation"]` is written
#      one line ABOVE the history append (`solver.py:857`), so the awareness channel the
#      model reads inline is untouched.
#   2. Drop the three `animation()` advertisement lines from the system prompt. The four
#      neighbouring lines that describe `last_action_result['animation']` are the
#      AWARENESS half and MUST survive — the asserts below check both directions.
#
# ⚠️ THE PROMPT REBIND MUST TARGET tool_agent, NOT prompts. `tool_agent.py:21` imports the
# addendum BY VALUE and `_build_system_prompt` (:499) reads its own module global, so
# rebinding `prompts.STRUCTURED_RUNTIME_STATE_ADDENDUM` changes nothing, prints nothing,
# and ships a run that measures nothing. That is the failure this file asserts against.
#
# WHAT THIS CANNOT TELL YOU: upstream's "bought no score" is upstream's measurement on
# upstream's runs — a strong prior, not our data. Ten of 25 games never execute
# `animation()` at all, so whatever the removal is worth it is worth nothing in those ten.
# And a removal is still a behaviour change: it needs a public run to rank, like every
# other candidate (B30).
import inference.agent.tool_agent as _ta
import inference.framework.solver as _solver

# --- edit 1: retrieval returns nothing ---------------------------------------------
_sess = getattr(_solver, "_HarnessGameSession", None)
assert _sess is not None, "duckv27: _HarnessGameSession not found in inference.framework.solver"
assert hasattr(_sess, "animation_record"), "duckv27: animation_record is gone -- bundle changed"

_orig_animation_record = _sess.animation_record


def _no_retrieval(self, action_num=None):
    """Upstream's animation_retrieval=False, expressed where our bundle allows it."""
    return None


_sess.animation_record = _no_retrieval

# --- edit 2: stop advertising the dead tool ----------------------------------------
# Exact prefixes. They must not match the awareness lines, which begin
# "- When an action animated," / "- `animation['board_unchanged']`" / "- When there is no".
_ADVERT = (
    "- `animation()` returns",
    "- `animation(frame=k)`",
    "- `animation(action_num=n)`",
)
_AWARE = (
    "- When an action animated,",
    "- `animation['board_unchanged']`",
    "- When there is no `animation` key,",
)

_before = _ta.STRUCTURED_RUNTIME_STATE_ADDENDUM
assert isinstance(_before, str) and _before, "duckv27: addendum missing from tool_agent"
_lines = _before.split("\n")
_kept = [ln for ln in _lines if not any(ln.startswith(p) for p in _ADVERT)]
_removed = len(_lines) - len(_kept)
assert _removed == 3, f"duckv27: expected to drop 3 advertisement lines, dropped {_removed}"

_after = "\n".join(_kept)
for _p in _AWARE:
    assert _p in _after, f"duckv27: awareness line was destroyed: {_p!r}"
assert "animation(" not in _after, "duckv27: an animation() advertisement survived the cut"

_ta.STRUCTURED_RUNTIME_STATE_ADDENDUM = _after
# Read it back off the module the prompt builder actually reads, not off our local name.
assert _ta.STRUCTURED_RUNTIME_STATE_ADDENDUM == _after, "duckv27: rebind did not stick"
assert "animation(" not in _ta._build_system_prompt(tool_output_tokens=1024), (
    "duckv27: the built prompt still advertises animation() -- the rebind missed its target"
)

print(
    f"duckv27: retrieval OFF (animation_record -> None), prompt -{_removed} advert lines, "
    f"{len(_before) - len(_after)} chars; awareness lines kept",
    flush=True,
)
