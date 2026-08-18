"""HUD/budget-bar auto-flagging and online transition-graph helpers for the
ARC-AGI-3 python-tool sandbox.

Standard library only, no project imports, no `from __future__` import -- so
this source can be spliced verbatim into the Python-tool sandbox bootstrap,
exactly like inference/utils/segmentation.py (same file this mirrors the
constraint from). No top-level side effects and no `__main__` guard belongs
here for the same reason segmentation.py has none: this text gets spliced
into a larger script and must not execute anything on its own when spliced.
The `__main__` self-test lives in a separate block that the notebook build
step strips before splicing (see taaf-duck-mod.ipynb cell 12 / the build
notes in results/duckmod-build-20260818.md).
"""

HUD_RATIO_THRESHOLD = 0.95
HUD_ISOLATION_MIN_COUNT = 2


def _frame_rows(frame):
    """Split a FrameView's `.ascii` into a list of character rows. `[]` if unavailable."""
    ascii_text = getattr(frame, "ascii", None) if frame is not None else None
    if not ascii_text:
        return []
    return ascii_text.split("\n")


def hud_mask(history):
    """Flag cells that behave like HUD/budget-bar chrome rather than gameplay state.

    Walks consecutive frames in `history` (each entry exposes `.frame`) and flags a
    cell `(row, col)` under either signature our campaign measured repeatedly:

    - it changes on >=95% of frame-to-frame transitions (a ticking clock/budget bar), or
    - it is, on its own, the ONLY cell that changed on at least 2 separate transitions
      (an isolated ticker -- a counter no other move affects).

    A pair of consecutive frames with mismatched shapes (a level change) is skipped,
    not counted as "unchanged". Returns a plain `set` of `(row, col)` tuples -- subtract
    it from a segmentation/diff before comparing frames or building a state key.
    """
    frames = [
        entry.frame for entry in (history or []) if getattr(entry, "frame", None) is not None
    ]
    total_transitions = 0
    change_count = {}
    isolated_count = {}

    for prev_frame, cur_frame in zip(frames, frames[1:]):
        prev_rows = _frame_rows(prev_frame)
        cur_rows = _frame_rows(cur_frame)
        if not prev_rows or not cur_rows or len(prev_rows) != len(cur_rows):
            continue
        changed_this_tick = []
        shape_ok = True
        for r in range(len(prev_rows)):
            prow, crow = prev_rows[r], cur_rows[r]
            if len(prow) != len(crow):
                shape_ok = False
                break
            for c in range(len(prow)):
                if prow[c] != crow[c]:
                    changed_this_tick.append((r, c))
        if not shape_ok:
            continue
        total_transitions += 1
        for cell in changed_this_tick:
            change_count[cell] = change_count.get(cell, 0) + 1
        if len(changed_this_tick) == 1:
            cell = changed_this_tick[0]
            isolated_count[cell] = isolated_count.get(cell, 0) + 1

    flagged = set()
    if total_transitions:
        for cell, count in change_count.items():
            if count / total_transitions >= HUD_RATIO_THRESHOLD:
                flagged.add(cell)
    for cell, count in isolated_count.items():
        if count >= HUD_ISOLATION_MIN_COUNT:
            flagged.add(cell)
    return flagged


class TransitionGraph:
    """Online state-transition graph built from *actually observed* (state, action)
    -> next_state edges. Nothing survives between python-tool calls (the sandbox is a
    fresh subprocess every call), so rebuild/feed it fresh from `history`/`transitions`
    at the start of each call by replaying `.record(...)` over what's in `history`.

    A graph built only from observed transitions can never assert a transition that
    was not actually taken -- unlike a static/guessed reachability map, which this
    campaign measured OVERCOUNTING reachability. Treat its output as a hypothesis
    generator, never an oracle: a state with no recorded edges is UNEXPLORED, not a
    dead end.
    """

    def __init__(self):
        self.edges = {}  # state_key -> {action: next_state_key}
        self.tried = {}  # state_key -> set(actions attempted from this state)

    @staticmethod
    def _key(state):
        """Make any state representation hashable. bytes/str/int/float/tuple pass
        through when they're actually hashable; anything else (list, dict, a tuple
        containing an unhashable) is coerced through `repr`."""
        if isinstance(state, (bytes, str, int, float, tuple)):
            try:
                hash(state)
                return state
            except TypeError:
                pass
        return repr(state)

    def record(self, state, action, next_state):
        """Record one observed (state, action) -> next_state edge. Returns the
        normalized key for next_state."""
        state_key = self._key(state)
        next_key = self._key(next_state)
        self.edges.setdefault(state_key, {})[action] = next_key
        self.tried.setdefault(state_key, set()).add(action)
        return next_key

    def untried(self, state, all_actions):
        """Actions not yet attempted from `state`, given the current action universe
        (pass the live `valid_actions` -- it can change turn to turn)."""
        state_key = self._key(state)
        done = self.tried.get(state_key, set())
        return [a for a in all_actions if a not in done]

    def path_to_nearest_untried(self, current_state, all_actions):
        """BFS over recorded edges from `current_state` for the nearest state (by edge
        count) that still has an untried action. Returns `{"target": key, "path": [...]}`
        where `path` is the action sequence to replay from `current_state`, or `None` if
        nothing reachable via recorded edges has an untried action."""
        start = self._key(current_state)
        if self.untried(start, all_actions):
            return {"target": start, "path": []}
        visited = {start}
        queue = [(start, [])]
        head = 0
        while head < len(queue):
            state_key, path = queue[head]
            head += 1
            for action, next_key in self.edges.get(state_key, {}).items():
                if next_key in visited:
                    continue
                visited.add(next_key)
                new_path = path + [action]
                if self.untried(next_key, all_actions):
                    return {"target": next_key, "path": new_path}
                queue.append((next_key, new_path))
        return None


def _demo():
    class _F:
        def __init__(self, ascii_text):
            self.ascii = ascii_text

    class _H:
        def __init__(self, frame):
            self.frame = frame

    # hud_mask signature 1: (0,0) ticks every frame (budget bar), (1,1) is the
    # "real" gameplay cell that moves once, mid-run.
    boards = [
        "9..\n.1.\n...",
        "0..\n.1.\n...",
        "9..\n.2.\n...",
        "0..\n.2.\n...",
        "9..\n.2.\n...",
    ]
    history = [_H(_F(b)) for b in boards]
    flagged = hud_mask(history)
    assert (0, 0) in flagged, f"clock cell not flagged: {flagged}"
    assert (1, 1) not in flagged, f"gameplay cell wrongly flagged: {flagged}"

    # hud_mask signature 2: an isolated ticker that flips alone on 2+ transitions.
    frames = ["...\n...\n...", "...\n...\n..X", "...\n...\n...", "...\n...\n..X"]
    history2 = [_H(_F(b)) for b in frames]
    flagged2 = hud_mask(history2)
    assert (2, 2) in flagged2, f"isolated ticker not flagged: {flagged2}"

    # level-change pair (mismatched shape) must be skipped, not crash / miscount.
    history3 = [_H(_F("..\n..")), _H(_F("...\n...\n..."))]
    hud_mask(history3)  # must not raise

    # TransitionGraph
    g = TransitionGraph()
    g.record("s0", "UP", "s1")
    g.record("s0", "DOWN", "s0")
    g.record("s1", "UP", "s2")
    all_actions = ["UP", "DOWN", "LEFT", "RIGHT"]
    assert set(g.untried("s0", all_actions)) == {"LEFT", "RIGHT"}
    nearest = g.path_to_nearest_untried("s0", all_actions)
    assert nearest == {"target": "s0", "path": []}, nearest

    g.record("s0", "LEFT", "s0")
    g.record("s0", "RIGHT", "s0")
    nearest2 = g.path_to_nearest_untried("s0", all_actions)
    assert nearest2 == {"target": "s1", "path": ["UP"]}, nearest2

    # unhashable state (a list) must still work via repr coercion.
    g.record([1, 2], "UP", [3, 4])
    assert g.untried([1, 2], ["UP", "DOWN"]) == ["DOWN"]

    print("duck_tools self-test OK")


if __name__ == "__main__":
    _demo()
