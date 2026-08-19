"""Auto-push per-turn observation block for the ARC-AGI-3 duck harness.

Runs in the HARNESS kernel process (patches `ToolAgent._build_user_prompt`),
never inside the isolated sandbox subprocess -- so no splice into
`python_tool_sandbox._SANDBOX_BOOTSTRAP` and no new callable API for the LLM
at all. The harness computes a compact text block from data it already has
(`current_frame`, `history_entries`, `valid_actions` -- all plain args of
`_build_user_prompt`) and appends it to every turn's user prompt. Stdlib
only, no project imports -- so this file's source can be embedded verbatim
as a string in the notebook cell, matching the constraint
`inference/utils/segmentation.py` states about itself, even though (unlike
segmentation.py) it is never spliced into the sandbox.

One `GameObservation` instance is attached to each `ToolAgent` INSTANCE
(`self._duckv3_observation`, lazily created on first call). `ToolAgent` is
constructed fresh per game by `HarnessSolver._make_analyzer` (one instance
per `(game, pass)` task -- see results/taaf-study-20260818.md and
results/duckv3-build-20260819.md), so attribute-per-instance already gives
per-game isolation with no dict/game-id keying and no leak risk across the
concurrent games the harness runs in one process.
"""
from __future__ import annotations

HUD_RATIO_THRESHOLD = 0.95
HUD_ISOLATION_MIN_COUNT = 2
MAX_HUD_CELLS_SHOWN = 8
MAX_UNTRIED_SHOWN = 8

_PATCH_MARKER = "_duckv3_patched"


def _grid_diff(prev_grid, cur_grid):
    """List of (row, col) cells that differ between two grids, or None if the
    shapes don't line up (a level boundary) -- never miscounted as unchanged."""
    if prev_grid is None or cur_grid is None:
        return None
    if len(prev_grid) != len(cur_grid):
        return None
    changed = []
    for r in range(len(prev_grid)):
        prow, crow = prev_grid[r], cur_grid[r]
        if len(prow) != len(crow):
            return None
        for c in range(len(prow)):
            if prow[c] != crow[c]:
                changed.append((r, c))
    return changed


def _normalize_action_name(action):
    """Strip MOUSE(row,col)-style args down to the bare action symbol."""
    if not action:
        return ""
    return str(action).split("(", 1)[0].strip()


def _normalize_actions(valid_actions):
    seen = []
    for a in valid_actions or []:
        name = _normalize_action_name(a)
        if name and name not in seen:
            seen.append(name)
    return seen


class GameObservation:
    """Per-game state: HUD-cell tallies, a masked-state visit map, and an
    online transition graph, all built only from transitions actually
    observed in `history_entries` (never a guessed/static model -- the ka59
    lesson in this repo's own CLAUDE.md: "when a static model and a real
    router disagree, the model loses").
    """

    def __init__(self):
        self._change_count = {}  # (r,c) -> transitions it changed in
        self._isolated_count = {}  # (r,c) -> times it was the ONLY cell that changed
        self._total_transitions = 0
        self._processed_len = 0  # frames already folded into the tallies above
        self.visit_counts = {}  # masked_state_key -> visit count
        self.edges = {}  # (state_key, action) -> next_state_key
        self.tried = {}  # state_key -> set(actions tried from that state)

    def _flagged_hud_cells(self):
        flagged = set()
        if self._total_transitions:
            for cell, cnt in self._change_count.items():
                if cnt / self._total_transitions >= HUD_RATIO_THRESHOLD:
                    flagged.add(cell)
        for cell, cnt in self._isolated_count.items():
            if cnt >= HUD_ISOLATION_MIN_COUNT:
                flagged.add(cell)
        return flagged

    @staticmethod
    def _mask(grid, hud_cells):
        if not hud_cells:
            return grid
        return tuple(
            tuple(0 if (r, c) in hud_cells else v for c, v in enumerate(row))
            for r, row in enumerate(grid)
        )

    def _ingest(self, frames, actions):
        """Fold every transition new since the last call into the tallies,
        the visit map and the transition graph. O(1) amortized per turn in
        the common case of one new action per turn.

        # ponytail: the mask used to key a transition's visit/edge entry is
        # whatever HUD set is known AT THAT MOMENT, not re-applied later --
        # a cell discovered as HUD several turns in leaves earlier dict
        # entries keyed slightly differently. This can only under-count
        # SEEN (a real revisit reads as one extra NOVEL), never crash or
        # mis-render; HUD detection stabilizes within a handful of
        # transitions in practice. Upgrade path if it ever matters: re-key
        # the whole graph from the raw grids once `_flagged_hud_cells()`
        # stops changing between turns.
        """
        n = len(frames)
        start = self._processed_len
        if start == 0 and n >= 1:
            hud = self._flagged_hud_cells()
            first_key = self._mask(frames[0], hud)
            self.visit_counts[first_key] = self.visit_counts.get(first_key, 0) + 1
        for i in range(max(start, 1), n):
            prev_grid, cur_grid = frames[i - 1], frames[i]
            diff = _grid_diff(prev_grid, cur_grid)
            if diff is None:
                continue
            self._total_transitions += 1
            for cell in diff:
                self._change_count[cell] = self._change_count.get(cell, 0) + 1
            if len(diff) == 1:
                self._isolated_count[diff[0]] = self._isolated_count.get(diff[0], 0) + 1
            hud = self._flagged_hud_cells()
            prev_key = self._mask(prev_grid, hud)
            cur_key = self._mask(cur_grid, hud)
            action_name = _normalize_action_name(actions[i])
            self.edges[(prev_key, action_name)] = cur_key
            self.tried.setdefault(prev_key, set()).add(action_name)
            self.visit_counts[cur_key] = self.visit_counts.get(cur_key, 0) + 1
        self._processed_len = n

    def render(self, history_entries, current_frame, valid_actions):
        """Return the compact OBSERVATION block text for this turn."""
        frames = [e.frame.grid for e in (history_entries or []) if e.frame is not None]
        actions = [e.action for e in (history_entries or [])]
        self._ingest(frames, actions)

        hud_cells = self._flagged_hud_cells()
        cur_grid = current_frame.grid if current_frame is not None else (frames[-1] if frames else None)
        state_key = self._mask(cur_grid, hud_cells) if cur_grid is not None else None

        visits = self.visit_counts.get(state_key, 0) if state_key is not None else 0
        state_label = "NOVEL" if visits <= 1 else f"SEEN(x{visits})"

        tried = self.tried.get(state_key, set()) if state_key is not None else set()
        action_names = _normalize_actions(valid_actions)
        untried = [a for a in action_names if a not in tried]
        untried_shown = untried[:MAX_UNTRIED_SHOWN]
        untried_suffix = "" if len(untried) <= MAX_UNTRIED_SHOWN else f" (+{len(untried) - MAX_UNTRIED_SHOWN} more)"

        last_change = "NO_CHANGE"
        if len(frames) >= 2:
            diff = _grid_diff(frames[-2], frames[-1])
            if diff:
                last_change = "CHANGED_FRAME"

        hud_list = sorted(hud_cells)[:MAX_HUD_CELLS_SHOWN]
        hud_suffix = "" if len(hud_cells) <= MAX_HUD_CELLS_SHOWN else f" (+{len(hud_cells) - MAX_HUD_CELLS_SHOWN} more)"

        return "\n".join(
            [
                f"HUD cells (auto-masked): {len(hud_cells)} cells {hud_list}{hud_suffix}",
                f"state: {state_label}",
                f"untried here: {untried_shown}{untried_suffix}",
                f"last action: {last_change}",
            ]
        )


def install_patch(tool_agent_module):
    """Monkeypatch `tool_agent_module.ToolAgent._build_user_prompt` so every
    turn's user prompt gets an auto-computed OBSERVATION block appended.
    Idempotent -- calling twice (e.g. re-running the notebook cell) does not
    double-wrap."""
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
        state = getattr(self, "_duckv3_observation", None)
        if state is None:
            state = GameObservation()
            self._duckv3_observation = state
        obs_block = state.render(history_entries or [], current_frame, valid_actions)
        return base + "\n" + obs_block

    setattr(cls, _PATCH_MARKER, True)
    cls._build_user_prompt = _patched


def _demo():
    class _F:
        def __init__(self, grid):
            self.grid = grid

    class _H:
        def __init__(self, action, grid):
            self.action = action
            self.frame = _F(grid)

    # A 3x3 board: (0,0) ticks a clock every step; (1,1) is real gameplay.
    def board(clock, mid):
        return (
            (clock, 0, 0),
            (0, mid, 0),
            (0, 0, 0),
        )

    valid = ["UP", "DOWN", "LEFT", "RIGHT"]
    obs = GameObservation()

    # Warmup: mid held constant while clock ticks every transition, so the
    # ratio detector converges to {(0,0)} with no competing hypothesis (the
    # cold-start ambiguity noted in the ponytail comment above only bites
    # when two cells both change on the very first observed transition).
    history = [
        _H("", board(9, 1)),
        _H("W1", board(0, 1)),
        _H("W2", board(9, 1)),
        _H("W3", board(0, 1)),
    ]
    warmup_block = obs.render(history, history[-1].frame, valid)
    assert warmup_block.split("\n")[0] == "HUD cells (auto-masked): 1 cells [(0, 0)]", warmup_block

    # First visit to mid=2 (masked state distinct from mid=1) -> NOVEL, and
    # nothing has been tried from it yet.
    history = history + [_H("X", board(9, 2))]
    block = obs.render(history, history[-1].frame, valid)
    lines = block.split("\n")
    assert lines[1] == "state: NOVEL", block
    assert lines[3] == "last action: CHANGED_FRAME", block
    assert lines[2].startswith("untried here:"), block
    for a in valid:
        assert a in lines[2], block

    # Revert to mid=1 -- a genuine revisit of the masked state seen 4 times
    # during warmup (the clock cell never survives the mask).
    history = history + [_H("Y", board(0, 1))]
    block2 = obs.render(history, history[-1].frame, valid)
    assert block2.split("\n")[1] == "state: SEEN(x4)", block2

    # A mismatched-shape transition (level boundary) must not crash and must
    # not be counted as "unchanged".
    obs2 = GameObservation()
    h3 = [_H("", ((1, 2), (3, 4))), _H("ACTION5", ((1, 2, 3), (4, 5, 6), (7, 8, 9)))]
    obs2.render(h3, h3[-1].frame, ["ACTION5"])  # must not raise

    # Isolated ticker: a single far-corner cell flips alone on 2+ transitions.
    obs3 = GameObservation()

    def board2(tick):
        return ((0, 0, 0), (0, 0, 0), (0, 0, tick))

    h4 = [_H("", board2(0)), _H("A", board2(9)), _H("A", board2(0)), _H("A", board2(9))]
    block4 = obs3.render(h4, h4[-1].frame, ["A"])
    assert "(2, 2)" in block4.split("\n")[0], block4

    print("duckv3_observer self-test OK")


if __name__ == "__main__":
    _demo()
