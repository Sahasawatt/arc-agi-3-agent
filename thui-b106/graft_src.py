# Ported from juliancamilovilla/arc-agi3-animfast-map cell 14 (Apache-2.0):
# https://www.kaggle.com/code/juliancamilovilla/arc-agi3-animfast-map
# Logic kept line-for-line; Spanish module identifiers/strings are translated to English.
# 1:1 mapping: MapRecorder->_thui_b106_MapRecorder, construir_grafo->
# _thui_b106_construir_grafo, render_map_note->_thui_b106_render_map_note.

import threading as _thui_b106_threading
import inference.agent.tool_agent as _thui_b106_tool_agent
import inference.agent.noop_guard as _thui_b106_noop_guard

_thui_b106_MAX_LIST = 6
_thui_b106_MAX_CLICK_CELLS = 8


class _thui_b106_MapRecorder:
    """Wrapper around NoopGuard that also records the state graph."""

    def __init__(self, inner):
        self._inner = inner
        self.registros: list[dict] = []

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def is_known_noop(self, level, board_sig, action_sig):
        return self._inner.is_known_noop(level, board_sig, action_sig)

    def observe(self, *, level, board_before_sig, action_sig, board_changed,
                animated=False, **kw):
        try:
            self.registros.append({
                "level": _thui_b106_integer(level),
                "before": str(board_before_sig),
                "action": " ".join(str(action_sig or "").split()),
                "effect": bool(board_changed) or bool(animated),
                "animation_only": bool(animated) and not bool(board_changed),
            })
        except Exception:
            pass
        return self._inner.observe(
            level=level, board_before_sig=board_before_sig, action_sig=action_sig,
            board_changed=board_changed, animated=animated, **kw)

    def reset(self) -> None:
        self.registros = []


def _thui_b106_integer(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _thui_b106_action_name(action: str) -> str:
    return (action or "").split("(")[0].strip().upper()


def _thui_b106_cell(action: str):
    text = action or ""
    if "row=" not in text or "col=" not in text:
        return None
    try:
        row = int(text.split("row=", 1)[1].split(",", 1)[0].strip(") "))
        col = int(text.split("col=", 1)[1].split(",", 1)[0].strip(") "))
        return row, col
    except (ValueError, IndexError):
        return None


def _thui_b106_construir_grafo(records: list[dict], level: int) -> dict:
    """Graph for the indicated level: edges, states, and affordances."""
    level_records = [r for r in records if r.get("level") == level]
    edges: list[tuple[str, str, str, bool]] = []
    for i, record in enumerate(level_records):
        destination = level_records[i + 1]["before"] if i + 1 < len(level_records) else None
        edges.append((record["before"], record["action"], destination, record["effect"]))

    states: dict[str, int] = {}
    for record in level_records:
        states[record["before"]] = states.get(record["before"], 0) + 1

    useful: set[str] = set()
    inert: dict[str, int] = {}
    useful_cells: list[tuple[int, int]] = []
    animation_only = 0
    for record in level_records:
        name = _thui_b106_action_name(record["action"])
        if record["effect"]:
            useful.add(name)
            cell = _thui_b106_cell(record["action"])
            if cell and cell not in useful_cells:
                useful_cells.append(cell)
        else:
            inert[name] = inert.get(name, 0) + 1
        if record.get("animation_only"):
            animation_only += 1

    return {
        "edges": edges,
        "states": states,
        "useful": useful,
        "never_useful": {name for name in inert if name not in useful},
        "useful_cells": useful_cells,
        "animation_only": animation_only,
        "action_count": len(level_records),
    }


def _thui_b106_render_map_note(records: list[dict], level: int, current_signature=None,
                               valid_actions=None) -> str:
    """Compact prompt note. Returns empty when there is nothing to add."""
    if not records:
        return ""
    graph = _thui_b106_construir_grafo(records, level)
    if not graph["edges"]:
        return ""

    lines: list[str] = []
    state_count = len(graph["states"])
    visits = graph["states"].get(current_signature or "", 0)

    header = (f"HOST MAP (level {level}, {graph['action_count']} actions here, "
              f"{state_count} distinct states)")
    lines.append(header)

    if current_signature:
        from_state = [(action, destination, effect) for (origin, action, destination, effect)
                      in graph["edges"] if origin == current_signature]
        if from_state:
            tried: dict[str, bool] = {}
            for action, _destination, effect in from_state:
                tried[action] = tried.get(action, False) or effect
            done = [f"{action}{'' if effect else ' (no effect)'}"
                    for action, effect in list(tried.items())[:_thui_b106_MAX_LIST]]
            lines.append(f"- from this state you already tried: {', '.join(done)}")
        if visits > 1:
            lines.append(f"- WARNING: this state was already visited {visits} times "
                         "(possible loop)")

        if valid_actions:
            tried_names = {_thui_b106_action_name(action) for (origin, action, _destination, _effect)
                           in graph["edges"] if origin == current_signature}
            frontier = [action for action in valid_actions
                        if action.upper() not in tried_names
                        and action.upper() not in graph["never_useful"]
                        and action.upper() != "MOUSE"]
            if frontier:
                lines.append(f"- from this state you have NOT tried: "
                             f"{', '.join(frontier[:_thui_b106_MAX_LIST])}")

    if graph["never_useful"]:
        lines.append(f"- never did anything on this level: "
                     f"{', '.join(sorted(graph['never_useful'])[:_thui_b106_MAX_LIST])}")
    if graph["useful_cells"]:
        cells = graph["useful_cells"]
        if len(cells) <= _thui_b106_MAX_CLICK_CELLS:
            text = ", ".join(f"({row},{col})" for row, col in cells)
        else:
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            text = (f"{len(cells)} cells in rows {min(rows)}-{max(rows)}, "
                    f"cols {min(cols)}-{max(cols)}")
        lines.append(f"- clicks that DID do something: {text}")

    if graph["animation_only"]:
        lines.append(f"- {graph['animation_only']} action(s) had an effect ONLY in the animation "
                     "(final board identical): they are NOT inert")

    if len(lines) == 1:
        return ""
    return "\n".join(lines)


_THUI_B106_MAP = True
_thui_b106_orig_ensure = _thui_b106_tool_agent.ToolAgent._ensure_session
_thui_b106_orig_prompt = _thui_b106_tool_agent.ToolAgent._build_user_prompt
_thui_b106_lock = _thui_b106_threading.Lock()
_thui_b106_stats = {"prompts": 0, "notes": 0, "chars": 0, "errors": 0}


def _thui_b106_ensure_session(self, state_path):
    _thui_b106_orig_ensure(self, state_path)
    try:
        guard = getattr(self, "_noop_guard", None)
        if guard is not None and not isinstance(guard, _thui_b106_MapRecorder):
            self._noop_guard = _thui_b106_MapRecorder(guard)
    except Exception:
        pass


def _thui_b106_build_user_prompt(self, action_num, *, valid_actions=None, current_frame=None, **kw):
    base = _thui_b106_orig_prompt(self, action_num, valid_actions=valid_actions,
                                  current_frame=current_frame, **kw)
    note = ""
    try:
        recorder = getattr(self, "_noop_guard", None)
        if isinstance(recorder, _thui_b106_MapRecorder):
            level = current_frame.level if current_frame is not None else 1
            signature = (_thui_b106_noop_guard.board_signature(current_frame.grid)
                         if current_frame is not None else None)
            note = _thui_b106_render_map_note(recorder.registros, level, signature, valid_actions)
    except Exception:
        with _thui_b106_lock:
            _thui_b106_stats["errors"] += 1
        note = ""
    with _thui_b106_lock:
        _thui_b106_stats["prompts"] += 1
        if note:
            _thui_b106_stats["notes"] += 1
            _thui_b106_stats["chars"] += len(note)
        snapshot = dict(_thui_b106_stats)
    if snapshot["prompts"] % 100 == 1:
        print("THUI_B106_STATS map=" + str(_THUI_B106_MAP) + " "
              + " ".join(f"{key}={value}" for key, value in snapshot.items()), flush=True)
    return base + "\n" + note if _THUI_B106_MAP and note else base


try:
    _thui_b106_tool_agent.ToolAgent._ensure_session = _thui_b106_ensure_session
    _thui_b106_tool_agent.ToolAgent._build_user_prompt = _thui_b106_build_user_prompt
    print(f"THUI_B106_GRAFT ok map={_THUI_B106_MAP} recorder={_thui_b106_MapRecorder.__name__}", flush=True)
except Exception as _thui_b106_exc:
    print(f"THUI_B106_GRAFT FAIL {_thui_b106_exc}", flush=True)
