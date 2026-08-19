"""Auto-recorded transition digest + reset banner for the ARC-AGI-3 duck harness
(duckv5, features 2 and 3).

R6 (results/wayfinder/R6-thrash-forensics.md) measured Mode 2 across the 9 worst-thrashing
games: zero real `TransitionGraph()`/`hud_mask()` calls in 9/9 games -- the anti-loop
tooling duckmod exposes is never invoked under turn-time pressure. And Mode 3: a silent
mid-run GAME_OVER erased 75-300 actions of progress in 6-7/9 games, with the model taking
a full turn (or never) to even notice. Both are targeted the same way duckv3 targeted
"the model doesn't call a tool for this": the harness computes the bookkeeping itself,
server-side, from data it already has (`history_entries`, the same
`(action, before-frame, after-frame)` stream `_build_user_prompt` already receives), and
injects a small fixed-format block into every turn's prompt. The model calls nothing.

Same patch point and same class-level monkeypatch mechanics duckv3 used for
`_build_user_prompt` (tool_agent.py:1161, results/duckv3-build-20260819.md sec1-2) -- the
closest prior art for this design, reused here rather than re-derived. One `TransitionDigest`
instance is attached per `ToolAgent` INSTANCE (`self._duckv5_digest`, lazily created), the
same instance-attribute-not-dict pattern duckv3 chose specifically to avoid ever needing to
key state on a session/agent object (sidesteps the `_HarnessGameSession`-is-unhashable trap
R7 sec-world-model-cap flags for any registry keyed that way -- there is no registry here).

Reset detection is NOT just "level number went down". R6's own header line: "All 9 games in
this report were stuck on level 1 for the entire run" -- so a GAME_OVER on any of the exact
games this feature targets can never show a level regression, because the level number never
had anywhere to fall from. The signature R6 actually measured, verbatim, twice ("reset the
board to the exact turn-1 layout"), is the GRID reverting to the state it was in when the
CURRENT level was first entered, after having visibly diverged from it. That is what this
module detects: per level, the grid recorded the moment that level was first seen is kept as
its "entry state"; a later frame at the SAME level that matches the entry state again, having
differed from it in between, is a reset. A level regression (level number decreasing) is also
always a reset and is checked first, cheaply, for games that DO demote the level number.
"""
from __future__ import annotations

MAX_ACTIONS_SHOWN = 8
LAST_N_ACTIONS = 5
MAX_LEVELS_SHOWN = 6

# ponytail: a flat action-count floor, not a learned one -- R6 doesn't cite a
# minimum, only the shape of the failure (resets erasing 75-300 actions, i.e. two
# orders of magnitude above this floor). Exists only to reject the trivial one-move-
# then-back-again oscillation right after entering a level as a false "reset"; real
# silent resets in R6 are never this close to a level's own entry point.
MIN_ACTIONS_SINCE_LEVEL_ENTRY_FOR_RESET = 3

_PATCH_MARKER = "_duckv5_digest_patched"


def _grid_diff_nonempty(prev_grid, cur_grid):
    """True if any cell differs; False if identical or shapes don't line up (treated
    as no evidence of a gameplay change either way -- never crashes)."""
    if prev_grid is None or cur_grid is None:
        return False
    if len(prev_grid) != len(cur_grid):
        return False
    for prow, crow in zip(prev_grid, cur_grid):
        if len(prow) != len(crow):
            return False
        if prow != crow:
            return True
    return False


def _normalize_action_name(action):
    """Strip MOUSE(row,col)-style args down to the bare action symbol."""
    if not action:
        return ""
    return str(action).split("(", 1)[0].strip()


class TransitionDigest:
    """Per-game state: per-action tried/changed/noop tallies, the action-index (and
    entry grid) each level was first seen at, the last N actions with their outcomes,
    and single-shot reset-banner text -- all built only from transitions actually
    present in `history_entries` (never guessed)."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._processed_len = 0
        self.total_actions = 0
        self.action_counts = {}  # name -> [tried, changed, noop]
        self.level_first_seen = {}  # level -> action index it was first observed at
        self.level_entry_grid = {}  # level -> grid recorded when that level was first seen
        self.last_actions = []  # list of (name, outcome), most-recent-last, capped
        self.last_level = None
        self._actions_since_reset = 0
        self._pending_reset = None  # str or None; consumed (single-shot) by render()

    def _record_level(self, level, grid):
        if level is not None and level not in self.level_first_seen:
            self.level_first_seen[level] = self.total_actions
            self.level_entry_grid[level] = grid

    def _is_reset(self, prev_frame, cur_frame) -> bool:
        if cur_frame.level < prev_frame.level:
            return True  # explicit level demotion -- always a reset
        if cur_frame.level != prev_frame.level:
            return False  # a level-up is handled separately, never a reset
        entry_grid = self.level_entry_grid.get(cur_frame.level)
        if entry_grid is None or cur_frame.grid != entry_grid:
            return False
        if prev_frame.grid == entry_grid:
            return False  # never left the entry state -- not a reversion, nothing lost
        since_entry = self.total_actions - self.level_first_seen.get(cur_frame.level, 0)
        return since_entry >= MIN_ACTIONS_SINCE_LEVEL_ENTRY_FOR_RESET

    def _ingest(self, history_entries):
        n = len(history_entries)
        if n < self._processed_len:
            # history shrank: a new session reused this instance (shouldn't happen in
            # the per-game-instance design, but a stale block is worse than a fresh one).
            self._reset()
        start = self._processed_len
        if start == 0 and n >= 1:
            first_frame = history_entries[0].frame
            if first_frame is not None:
                self._record_level(first_frame.level, first_frame.grid)
                self.last_level = first_frame.level

        for i in range(max(start, 1), n):
            prev_frame = history_entries[i - 1].frame
            cur_frame = history_entries[i].frame
            action_name = _normalize_action_name(history_entries[i].action)

            self.total_actions += 1
            self._actions_since_reset += 1
            counts = self.action_counts.setdefault(action_name, [0, 0, 0])
            counts[0] += 1  # tried

            if prev_frame is None or cur_frame is None:
                outcome = "noop"
            elif self._is_reset(prev_frame, cur_frame):
                outcome = "reset"
            elif cur_frame.level > prev_frame.level:
                outcome = "level_up"
            elif _grid_diff_nonempty(prev_frame.grid, cur_frame.grid):
                outcome = "changed"
            else:
                outcome = "noop"

            if outcome in ("changed", "level_up"):
                counts[1] += 1  # changed
            else:
                counts[2] += 1  # noop (also covers 'reset' -- see module docstring scope)

            self.last_actions.append((action_name, outcome))
            if len(self.last_actions) > LAST_N_ACTIONS:
                self.last_actions.pop(0)

            if cur_frame is not None:
                self._record_level(cur_frame.level, cur_frame.grid)

            if outcome == "reset":
                lost = self._actions_since_reset
                before_level = prev_frame.level
                after_level = cur_frame.level
                self._pending_reset = (
                    f"!!! GAME RESET: level went {before_level}->{after_level}, "
                    f"{lost} actions of progress lost; your position/state assumptions "
                    f"are now invalid !!!"
                )
                self._actions_since_reset = 0

            if cur_frame is not None:
                self.last_level = cur_frame.level

        self._processed_len = n

    def render(self, history_entries):
        """Return the compact PROGRESS DIGEST block (plus a leading one-shot reset
        banner, if a reset was just ingested) for this turn."""
        self._ingest(history_entries or [])

        lines = ["=== PROGRESS DIGEST (auto-tracked, no action needed) ==="]
        lines.append(f"actions so far: {self.total_actions}")

        levels_sorted = sorted(self.level_first_seen.items())[-MAX_LEVELS_SHOWN:]
        if levels_sorted:
            levels_text = ", ".join(f"L{lvl}@a{idx}" for lvl, idx in levels_sorted)
        else:
            levels_text = f"L{self.last_level or 1}@a0"
        lines.append(f"levels reached: {levels_text}")

        lines.append("action outcomes tried/changed/noop:")
        shown = sorted(self.action_counts.items())[:MAX_ACTIONS_SHOWN]
        if shown:
            for name, (tried, changed, noop) in shown:
                lines.append(f"  {name}: {tried}/{changed}/{noop}")
        else:
            lines.append("  (no actions taken yet)")

        last_text = ", ".join(f"{name}:{outcome}" for name, outcome in self.last_actions) or "(none yet)"
        lines.append(f"last {LAST_N_ACTIONS} actions: {last_text}")
        lines.append("=== END DIGEST ===")

        banner = self._pending_reset
        self._pending_reset = None
        if banner:
            lines.insert(0, banner)

        return "\n".join(lines)


def install_patch(tool_agent_module) -> None:
    """Monkeypatch tool_agent_module.ToolAgent._build_user_prompt so every turn's user
    prompt gets an auto-computed PROGRESS DIGEST block (+ a one-shot reset banner)
    appended. Idempotent -- a second call does not double-wrap."""
    cls = tool_agent_module.ToolAgent
    if getattr(cls, _PATCH_MARKER, False):
        return
    original = cls._build_user_prompt

    def _patched(self, action_num, *, valid_actions=None, current_frame=None, history_entries=None, previous_step_summary=None):
        base = original(
            self,
            action_num,
            valid_actions=valid_actions,
            current_frame=current_frame,
            history_entries=history_entries,
            previous_step_summary=previous_step_summary,
        )
        digest = getattr(self, "_duckv5_digest", None)
        if digest is None:
            digest = TransitionDigest()
            self._duckv5_digest = digest
        block = digest.render(history_entries or [])
        return base + "\n" + block

    setattr(cls, _PATCH_MARKER, True)
    cls._build_user_prompt = _patched


def _demo() -> None:
    class _F:
        def __init__(self, grid, level=1):
            self.grid = grid
            self.level = level

    class _H:
        def __init__(self, action, grid, level=1):
            self.action = action
            self.frame = _F(grid, level)

    def board(mid):
        return ((0, 0, 0), (0, mid, 0), (0, 0, 0))

    # --- (a) basic tallies: tried/changed/noop counts, last-N, levels reached ---
    # entry grid uses a value (9) never revisited later, so returning to mid=0 later
    # in this same test is an ordinary state, not a reversion to the level's entry.
    d = TransitionDigest()
    history = [
        _H("", board(9)),
        _H("UP", board(1)),  # changed
        _H("UP", board(1)),  # noop (mid unchanged)
        _H("DOWN", board(0)),  # changed
        _H("DOWN", board(0)),  # noop
        _H("RIGHT", board(0)),  # noop
    ]
    block = d.render(history)
    lines = block.split("\n")
    assert lines[0] == "=== PROGRESS DIGEST (auto-tracked, no action needed) ===", block
    assert "actions so far: 5" in block, block
    assert "L1@a0" in block, block
    assert "UP: 2/1/1" in block, block
    assert "DOWN: 2/1/1" in block, block
    assert "RIGHT: 1/0/1" in block, block
    assert "last 5 actions: UP:changed, UP:noop, DOWN:changed, DOWN:noop, RIGHT:noop" in block, block
    assert len(lines) <= 25, f"block too long: {len(lines)} lines"
    assert len(lines) >= 5, f"block suspiciously short: {len(lines)} lines"

    # --- level-up: recorded in tallies AND in levels_reached, never flagged reset ---
    d2 = TransitionDigest()
    history2 = [
        _H("", board(0), level=1),
        _H("ACTION5", board(0), level=2),  # level_up
    ]
    block2 = d2.render(history2)
    assert "ACTION5: 1/1/0" in block2, block2
    assert "L1@a0" in block2 and "L2@a1" in block2, block2
    assert "!!!" not in block2, "no reset must be flagged on a level-UP"

    # --- (c1) reset banner via explicit level regression: fires exactly once, on the
    # observation right after the regression, never again. ---
    d3 = TransitionDigest()
    history3 = [
        _H("", board(0), level=1),
        _H("UP", board(1), level=2),  # level_up to 2
        _H("UP", board(1), level=2),  # ordinary action on level 2
    ]
    block3a = d3.render(history3)
    assert "!!!" not in block3a, "no reset yet"

    history3 = history3 + [_H("DOWN", board(0), level=1)]  # regression 2 -> 1
    block3b = d3.render(history3)
    assert "!!! GAME RESET: level went 2->1" in block3b, block3b
    assert "actions of progress lost" in block3b, block3b

    history3 = history3 + [_H("UP", board(1), level=1)]  # ordinary turn after the reset
    block3c = d3.render(history3)
    assert "!!!" not in block3c, "banner must be single-shot: gone on the NEXT render"

    history3 = history3 + [_H("UP", board(1), level=1)]
    block3d = d3.render(history3)
    assert "!!!" not in block3d, "banner must stay gone on every later render"

    # --- (c2) THE MOTIVATING CASE: a GAME_OVER on a game stuck at level 1 the whole
    # run, per R6's own header finding ("All 9 games in this report were stuck on
    # level 1 for the entire run"). Level number can never regress here -- it starts
    # and stays at 1 -- so this can ONLY be caught by the grid reverting to its own
    # level-1 entry state after having visibly diverged from it. ---
    d4 = TransitionDigest()
    genesis = board(0)
    history4 = [
        _H("", genesis, level=1),  # entry state for level 1
        _H("UP", board(1), level=1),  # diverges
        _H("RIGHT", board(2), level=1),  # diverges further
        _H("DOWN", board(3), level=1),  # diverges further still
    ]
    block4a = d4.render(history4)
    assert "!!!" not in block4a, "no reset yet -- board hasn't reverted"

    history4 = history4 + [_H("MOUSE(1,1)", genesis, level=1)]  # silent GAME_OVER: reverts to genesis
    block4b = d4.render(history4)
    assert "!!! GAME RESET: level went 1->1" in block4b, block4b
    assert "4 actions of progress lost" in block4b, block4b

    history4 = history4 + [_H("UP", board(1), level=1)]
    block4c = d4.render(history4)
    assert "!!!" not in block4c, "single-shot banner must be gone the turn after"

    # false-positive guard: a board that legitimately never left its own entry state
    # must not be flagged (this is NOT a revert, nothing was lost).
    d5 = TransitionDigest()
    history5 = [_H("", genesis, level=1), _H("UP", genesis, level=1)]  # no-op press
    block5 = d5.render(history5)
    assert "!!!" not in block5, "never having diverged from entry state is not a reset"

    # false-positive guard: an immediate one-move-then-back oscillation right after
    # entering a level must not trip the MIN_ACTIONS_SINCE_LEVEL_ENTRY_FOR_RESET floor.
    d6 = TransitionDigest()
    history6 = [_H("", genesis, level=1), _H("UP", board(1), level=1), _H("DOWN", genesis, level=1)]
    block6 = d6.render(history6)
    assert "!!!" not in block6, "a same-level bounce this close to level entry must not be flagged"

    # --- action names normalize (MOUSE(r,c) collapses to MOUSE) ---
    d7 = TransitionDigest()
    history7 = [
        _H("", board(0)),
        _H("MOUSE(3,4)", board(1)),
        _H("MOUSE(5,6)", board(0)),
    ]
    block7 = d7.render(history7)
    assert "MOUSE: 2/2/0" in block7, block7

    # --- shape-mismatch frame (a level-glitch) must not crash; same-level treated as noop ---
    d8 = TransitionDigest()
    history8 = [
        _H("", ((1, 2), (3, 4)), level=1),
        _H("A", ((1, 2, 3), (4, 5, 6), (7, 8, 9)), level=1),  # same level, shape changed
    ]
    d8.render(history8)  # must not raise

    print("duckv5_digest self-test OK")


if __name__ == "__main__":
    _demo()
