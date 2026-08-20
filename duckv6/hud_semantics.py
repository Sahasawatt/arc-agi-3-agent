"""Small, server-side heuristics for identifying game HUD counters and bars."""

from collections import deque
import random

_EDGE = 3
_MIN_OBSERVATIONS = 8
_HISTORY_SIZE = 64


def _grid_from_frame(frame):
    """Return the last 2-D plane, tolerating tuples and extra plane nesting."""
    value = frame
    while (isinstance(value, (list, tuple)) and value and
           isinstance(value[0], (list, tuple)) and value[0] and
           isinstance(value[0][0], (list, tuple))):
        value = value[-1]
    if not isinstance(value, (list, tuple)):
        return []
    return [tuple(int(cell) for cell in row) for row in value
            if isinstance(row, (list, tuple))]


class HudSemantics:
    """Accumulate HUD evidence one executed action at a time."""

    def __init__(self):
        self._reset()

    def _reset(self):
        self._shape = None
        self._level = None
        self._histories = {}
        self._frames = deque(maxlen=_HISTORY_SIZE)
        self._reference = None
        self._reference_counts = {}
        self._diverged = set()

    @staticmethod
    def _background(grid):
        height = len(grid)
        width = len(grid[0]) if grid else 0
        colours = [cell for r, row in enumerate(grid) for c, cell in enumerate(row)
                   if _EDGE <= r < height - _EDGE and _EDGE <= c < width - _EDGE]
        if not colours:
            colours = [cell for row in grid for cell in row]
        return max(set(colours), key=colours.count) if colours else 0

    @staticmethod
    def _candidates(grid, background):
        height = len(grid)
        width = len(grid[0]) if grid else 0
        keys = []
        edge_rows = list(range(min(_EDGE, height))) + list(range(max(0, height - _EDGE), height))
        edge_cols = list(range(min(_EDGE, width))) + list(range(max(0, width - _EDGE), width))
        for r in edge_rows:
            keys.extend(("row", r, colour) for colour in set(grid[r]) if colour != background)
        for c in edge_cols:
            colours = {grid[r][c] for r in range(height)}
            keys.extend(("col", c, colour) for colour in colours if colour != background)
        return list(dict.fromkeys(keys))

    @staticmethod
    def _count(grid, key):
        direction, index, colour = key
        if direction == "row":
            return sum(cell == colour for cell in grid[index])
        return sum(row[index] == colour for row in grid)

    @staticmethod
    def _outside_similarity(left, right, key):
        direction, index, _ = key
        total = equal = 0
        for r, (lrow, rrow) in enumerate(zip(left, right)):
            for c, (lcell, rcell) in enumerate(zip(lrow, rrow)):
                if (direction == "row" and r == index) or (direction == "col" and c == index):
                    continue
                total += 1
                equal += lcell == rcell
        return equal / total if total else 0.0

    def feed(self, frame, action_id, level):
        grid = _grid_from_frame(frame)
        shape = (len(grid), len(grid[0]) if grid else 0)
        if self._shape != shape or self._level != level:
            self._reset()
            self._shape, self._level = shape, level
        if not grid or any(len(row) != shape[1] for row in grid):
            return

        background = self._background(grid)
        candidates = self._candidates(grid, background)
        if self._reference is None:
            self._reference = grid
            self._reference_counts = {key: self._count(grid, key) for key in candidates}
        previous = self._frames[-1] if self._frames else None
        self._frames.append(grid)
        for key in candidates:
            count = self._count(grid, key)
            history = self._histories.setdefault(key, deque(maxlen=_HISTORY_SIZE))
            outside_changed = previous is not None and self._outside_similarity(previous, grid, key) < 1.0
            if outside_changed:
                self._diverged.add(key)
            history.append((count, outside_changed, action_id))
            if (len(history) >= _MIN_OBSERVATIONS and key in self._diverged and
                    len(history) >= 2 and history[-2][0] < count and
                    count == max(item[0] for item in history) and
                    self._outside_similarity(self._reference, grid, key) > 0.60 and
                    self._reference_counts.get(key) == count):
                history.append((count, True, "__refill__"))

    def render_hint(self):
        lines = []
        for key, history in self._histories.items():
            if len(history) < _MIN_OBSERVATIONS:
                continue
            counts = [item[0] for item in history if item[2] != "__refill__"]
            if len(counts) < _MIN_OBSERVATIONS:
                continue
            if any(item[2] == "__refill__" for item in history):
                text = "refills on death/reset - it is a life/turn budget"
                if text not in lines:
                    lines.append(text)
                if len(lines) >= 5:
                    break
                continue
            diffs = [b - a for a, b in zip(counts, counts[1:])]
            if not diffs or not all(diff == diffs[0] for diff in diffs) or diffs[0] == 0:
                continue
            if any(item[1] for item in history):
                actions = {item[2] for item in history if item[2] != "__refill__"}
                if len(actions) > 1:
                    text = "counts your actions (cost), not a target"
                elif all(diff < 0 for diff in diffs):
                    text = "likely a TIMER/BUDGET: it decreases as you act; do NOT treat reaching its end as a goal; expect a reset/death when it empties"
                elif all(diff > 0 for diff in diffs):
                    text = "likely PROGRESS/SCORE indicator"
                else:
                    continue
            else:
                text = "counts your actions (cost), not a target"
            if text not in lines:
                lines.append(text)
            if len(lines) >= 5:
                break
        return "\n".join(["=== HUD SEMANTICS (auto-detected) ==="] + lines) if lines else ""


def _demo():
    def make(bar, interior, width=12):
        grid = [[0] * width for _ in range(8)]
        grid[-1][:bar] = [2] * bar
        for r in range(2):
            grid[r + 3][3:9] = interior[r]
        return grid

    rng = random.Random(7)
    hud = HudSemantics()
    for turn in range(12):
        interior = [[0, 0, 0, 0, rng.randrange(1, 4), rng.randrange(1, 4)] for _ in range(2)]
        hud.feed(make(12 - turn, interior), "A", 1)
    assert "TIMER/BUDGET" in hud.render_hint()

    control = HudSemantics()
    for _ in range(10):
        control.feed(make(0, [[1] * 6, [1] * 6]), "A", 1)
    assert control.render_hint() == ""

    refill = HudSemantics()
    baseline = [[1] * 6, [2] * 6]
    for turn in range(8):
        refill.feed(make(8 - turn, [[3] * 6, [3] * 6]), "A", 1)
    refill.feed(make(8, baseline), "B", 1)
    assert "refills" in refill.render_hint()
    print("hud_semantics self-test OK")


if __name__ == "__main__":
    _demo()
