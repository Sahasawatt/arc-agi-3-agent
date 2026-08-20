"""v6 transition digest: v5 bookkeeping plus conservative HUD-aware outcomes."""
from __future__ import annotations

MAX_ACTIONS_SHOWN = 8
LAST_N_ACTIONS = 5
MAX_LEVELS_SHOWN = 6
MIN_ACTIONS_SINCE_LEVEL_ENTRY_FOR_RESET = 3
_PATCH_MARKER = "_duckv6_digest_patched"


def _grid_diff_cells(prev_grid, cur_grid):
    if prev_grid is None or cur_grid is None or len(prev_grid) != len(cur_grid):
        return []
    cells = []
    for r, (prow, crow) in enumerate(zip(prev_grid, cur_grid)):
        if len(prow) != len(crow):
            return []
        cells.extend((r, c) for c, (a, b) in enumerate(zip(prow, crow)) if a != b)
    return cells


def _grid_diff_nonempty(prev_grid, cur_grid):
    return bool(_grid_diff_cells(prev_grid, cur_grid))


def _normalize_action_name(action):
    return str(action).split("(", 1)[0].strip() if action else ""


class TransitionDigest:
    def __init__(self):
        self._reset()

    def _reset(self):
        self._processed_len = 0
        self.total_actions = 0
        self.action_counts = {}  # name -> [tried, gameplay_changed, hud_only, uncertain, noop]
        self.level_first_seen = {}
        self.level_entry_grid = {}
        self.last_actions = []  # (name, outcome, level_progress)
        self.last_level = None
        self._actions_since_reset = 0
        self._actions_since_level_up = 0
        self._pending_reset = None
        self._observed_reset_thresholds = []
        self._reset_sequences = []
        self._level_ups = 0
        self.hud = HudSemantics()

    def _record_level(self, level, grid):
        if level is not None and level not in self.level_first_seen:
            self.level_first_seen[level] = self.total_actions
            self.level_entry_grid[level] = grid

    def _is_reset(self, prev_frame, cur_frame):
        if cur_frame.level < prev_frame.level:
            return True
        if cur_frame.level != prev_frame.level:
            return False
        entry = self.level_entry_grid.get(cur_frame.level)
        if entry is None or cur_frame.grid != entry or prev_frame.grid == entry:
            return False
        since_entry = self.total_actions - self.level_first_seen.get(cur_frame.level, 0)
        return since_entry >= MIN_ACTIONS_SINCE_LEVEL_ENTRY_FOR_RESET

    def _confident_regions(self):
        """Return row/column HUD masks exposed by HudSemantics' confidence ledger."""
        regions = []
        for key, history in getattr(self.hud, "_histories", {}).items():
            if len(history) >= 8 and key in getattr(self.hud, "_diverged", set()):
                regions.append(key)
        return regions

    def classify_change(self, prev_frame, cur_frame):
        cells = _grid_diff_cells(
            getattr(prev_frame, "grid", None), getattr(cur_frame, "grid", None))
        if not cells:
            return "noop"
        regions = self._confident_regions()
        if not regions:
            return "uncertain"
        hud_cells = set()
        for direction, index, _colour in regions:
            if direction == "row":
                hud_cells.update((r, c) for r, c in cells if r == index)
            else:
                hud_cells.update((r, c) for r, c in cells if c == index)
        return "hud_only" if len(hud_cells) == len(cells) else "gameplay_changed"

    def _ingest(self, history_entries):
        n = len(history_entries)
        if n < self._processed_len:
            self._reset()
        start = self._processed_len
        if start == 0 and n:
            first = history_entries[0].frame
            if first is not None:
                self._record_level(first.level, first.grid)
                self.last_level = first.level
                self.hud.feed(first, "", first.level)

        for i in range(max(start, 1), n):
            prev = history_entries[i - 1].frame
            cur = history_entries[i].frame
            name = _normalize_action_name(history_entries[i].action)
            self.total_actions += 1
            self._actions_since_reset += 1
            self._actions_since_level_up += 1
            counts = self.action_counts.setdefault(name, [0, 0, 0, 0, 0])
            counts[0] += 1
            if prev is None or cur is None:
                outcome = "noop"
            elif self._is_reset(prev, cur):
                outcome = "reset"
            elif cur.level > prev.level:
                outcome = "level_up"
            else:
                outcome = self.classify_change(prev, cur)
            if outcome == "gameplay_changed" or outcome == "level_up":
                counts[1] += 1
            elif outcome == "hud_only":
                counts[2] += 1
            elif outcome == "uncertain":
                counts[3] += 1
            else:
                counts[4] += 1
            if cur is not None:
                self.hud.feed(cur, self.total_actions, cur.level)
            level_progress = outcome == "level_up"
            if level_progress:
                self._level_ups += 1
                self._actions_since_level_up = 0
            self.last_actions.append((name, outcome, level_progress))
            if len(self.last_actions) > 64:
                self.last_actions.pop(0)
            if cur is not None:
                self._record_level(cur.level, cur.grid)
            if outcome == "reset":
                self._observed_reset_thresholds.append(self._actions_since_level_up)
                self._reset_sequences.append(tuple(x[0] for x in self.last_actions[-5:]))
                lost = self._actions_since_reset
                self._pending_reset = (
                    f"!!! GAME RESET: level went {prev.level}->{cur.level}, "
                    f"{lost} actions of progress lost; your position/state assumptions "
                    "are now invalid !!!"
                )
                self._actions_since_reset = 0
            if cur is not None:
                self.last_level = cur.level
        self._processed_len = n

    def _warnings(self):
        if not self.last_actions or any(x[2] for x in self.last_actions[-15:]):
            return []
        names = [x[0] for x in self.last_actions]
        warnings = []
        current = names[-1]
        streak = 0
        for item in reversed(self.last_actions):
            if item[0] != current or item[1] not in ("noop", "reset"):
                break
            streak += 1
        if streak >= 12:
            warnings.append(f"ADVISORY: {current} has {streak} no-op actions; consider switching to a different action family")
        for size in range(2, 7):
            if len(names) < size * 8:
                continue
            tail = names[-size:]
            if names[-size * 8:] == tail * 8:
                warnings.append(f"ADVISORY: action cycle {','.join(tail)} repeated 8 times; consider switching to a different action family")
                break
        if any(abs(self._actions_since_level_up - t) <= 15 for t in self._observed_reset_thresholds):
            warnings.append("ADVISORY: action count is near a previously observed reset threshold; consider switching to a different action family")
        if len(names) >= 5 and tuple(names[-5:]) in self._reset_sequences:
            warnings.append("ADVISORY: this 5-action sequence previously ended in a reset; consider switching to a different action family")
        return warnings

    def render(self, history_entries):
        self._ingest(history_entries or [])
        lines = ["=== PROGRESS DIGEST (auto-tracked, no action needed) ===", f"actions so far: {self.total_actions}"]
        levels = sorted(self.level_first_seen.items())[-MAX_LEVELS_SHOWN:]
        lines.append("levels reached: " + (", ".join(f"L{l}@a{i}" for l, i in levels) if levels else f"L{self.last_level or 1}@a0"))
        lines.append("action outcomes tried/gameplay_changed/hud_only/uncertain/noop:")
        for name, values in sorted(self.action_counts.items())[:MAX_ACTIONS_SHOWN]:
            lines.append(f"  {name}: " + "/".join(map(str, values)))
        lines.append("  (no actions taken yet)" if not self.action_counts else "last 5 actions: " + ", ".join(f"{n}:{o}" for n, o, _ in self.last_actions[-LAST_N_ACTIONS:]))
        lines.append("=== END DIGEST ===")
        lines.extend(self._warnings())
        banner = self._pending_reset
        self._pending_reset = None
        if banner:
            lines.insert(0, banner)
        hint = self.hud.render_hint()
        return "\n".join(lines) + ("\n" + hint if hint else "")


def install_patch(tool_agent_module):
    cls = tool_agent_module.ToolAgent
    if getattr(cls, _PATCH_MARKER, False):
        return
    original = cls._build_user_prompt

    def _patched(self, action_num, *, valid_actions=None, current_frame=None, history_entries=None, previous_step_summary=None):
        base = original(self, action_num, valid_actions=valid_actions, current_frame=current_frame,
                        history_entries=history_entries, previous_step_summary=previous_step_summary)
        digest = getattr(self, "_duckv6_digest", None)
        if digest is None:
            digest = TransitionDigest()
            self._duckv6_digest = digest
        return base + "\n" + digest.render(history_entries or [])

    setattr(cls, _PATCH_MARKER, True)
    cls._build_user_prompt = _patched


def _demo():
    class F:
        def __init__(self, grid, level=1): self.grid, self.level = grid, level
    class H:
        def __init__(self, action, grid, level=1): self.action, self.frame = action, F(grid, level)
    def board(v): return ((0, 0, 0), (0, v, 0), (0, 0, 0))
    def hist(actions, grids=None):
        grids = grids or [board(0)] * (len(actions) + 1)
        return [H(a, g) for a, g in zip([""] + actions, grids)]
    noop = TransitionDigest()
    assert "consider" in noop.render(hist(["A"] * 12))
    cycle = TransitionDigest()
    assert "action cycle" in cycle.render(hist(list("AB") * 8))
    productive = TransitionDigest()
    productive_actions = list("AB") * 8 + ["A"] + ["B"] * 4
    h = [H("", board(0), 1)]
    h.extend(H(action, board(0), 2 if i >= 16 else 1)
             for i, action in enumerate(productive_actions))
    assert "ADVISORY" not in productive.render(h)
    d = TransitionDigest()
    d.hud._histories = {("row", 0, 2): [(1, True, i) for i in range(8)]}
    d.hud._diverged = {("row", 0, 2)}
    assert d.classify_change(F(((2, 0), (0, 0))), F(((0, 0), (0, 0)))) == "hud_only"
    assert d.classify_change(F(((0, 0), (0, 0))), F(((0, 0), (1, 0)))) == "gameplay_changed"
    assert TransitionDigest().classify_change(F(((0,),)), F(((1,),))) == "uncertain"
    print("duckv6_digest self-test OK")


if __name__ == "__main__":
    if "HudSemantics" not in globals():
        from pathlib import Path
        _hud_path = Path(__file__).with_name("hud_semantics.py")
        _hud_ns = {"__name__": "duckv6_hud_semantics"}
        exec(compile(_hud_path.read_text(encoding="utf-8"), str(_hud_path), "exec"), _hud_ns)
        HudSemantics = _hud_ns["HudSemantics"]
    _demo()
