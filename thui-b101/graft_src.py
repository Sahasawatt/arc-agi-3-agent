
# ---- thui-b101 KeepOnDeath (MAP B101, bar pre-registered in thui-b101/PREDICTIONS.md 2026-09-26): the harness wipes the
# six summarized-knowledge slots on level_transition OR run_complete OR game_over. With the KEEP flag on, a
# death alone no longer wipes; the level-transition and run-complete wipes stay. With it off (the control) the wipe is
# exactly B81's. Both arms print the same counters and per-event markers, so the bar is read from the log alone:
#   THUI_B101_DEATH agent=<id> level=<L> slots=<non-empty of six> kept=<bool>
#   THUI_B101_CLEAR agent=<id> level=<L>          (a level_transition out of level L)
import threading as _thui_b101_threading

_THUI_B101_KEEP = True
_THUI_B101_SLOTS = ("world_model", "goal_model", "action_model", "recent_findings", "open_questions", "current_plan")
_THUI_B101_LOCK = _thui_b101_threading.Lock()
_THUI_B101 = {"deaths": 0, "qualifying_deaths": 0, "kept": 0, "wiped_on_death": 0, "level_wipes": 0, "clears": 0}


def _thui_b101_update(self):
    summary = self._last_step_summary
    if not summary:
        return
    death = bool(summary.get("game_over"))
    other = bool(summary.get("level_transition") or summary.get("run_complete"))
    if not (death or other):
        return
    filled = sum(1 for k in _THUI_B101_SLOTS if self._summarized_knowledge.get(k))
    keep = death and not other and _THUI_B101_KEEP
    with _THUI_B101_LOCK:
        if death:
            _THUI_B101["deaths"] += 1
            if filled:
                _THUI_B101["qualifying_deaths"] += 1
                _THUI_B101["kept" if keep else "wiped_on_death"] += 1
        if other:
            _THUI_B101["level_wipes"] += 1
        if summary.get("level_transition"):
            _THUI_B101["clears"] += 1
        snap = dict(_THUI_B101)
    if death:
        print(f"THUI_B101_DEATH agent={id(self):x} level={summary.get('level')} slots={filled} kept={keep}", flush=True)
    if summary.get("level_transition"):
        print(f"THUI_B101_CLEAR agent={id(self):x} level={summary.get('level')}", flush=True)
    if death or snap["level_wipes"] % 10 == 1:
        print("THUI_B101_STATS keep=" + str(_THUI_B101_KEEP) + " "
              + " ".join(f"{k}={v}" for k, v in snap.items()), flush=True)
    if keep:
        return
    for k in _THUI_B101_SLOTS:
        self._summarized_knowledge[k] = ""


_tool_agent.ToolAgent._update_summarized_knowledge_from_step_summary = _thui_b101_update
assert _tool_agent.ToolAgent._update_summarized_knowledge_from_step_summary is _thui_b101_update
print(f"THUI_B101_GRAFT ok keep={_THUI_B101_KEEP}", flush=True)
