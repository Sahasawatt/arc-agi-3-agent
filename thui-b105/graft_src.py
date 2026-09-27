
# ---- thui-b105 ActionOutcome (MAP B105, bar pre-registered in thui-b105/PREDICTIONS.md): `_run_python_tool` puts the
# executed actions' result into the tool response ONLY when the snippet printed nothing and returned nothing
# (`elif action_results:` after `if rendered_stdout:` / `elif result is not None:`), so a snippet that prints anything
# gets back its own stdout and no word from the harness on what its actions did. With the OUTCOME flag on, every python
# tool response whose snippet executed >= 1 action and carries no `result` gains an `action_outcome` field: the
# harness's own step summary of that call (actions executed, level, level_transition, run_complete, game_over,
# board_changed, stop_reason, animation). With the flag off (the control) the same case is detected and counted and the
# response is unchanged, so the bar is read from the log:
#   THUI_B105_STATS outcome=<bool> python_calls=<n> acting=<n> missing=<n> added=<n> acting_with_stdout=<n>
import threading as _thui_b105_threading

_THUI_B105_OUTCOME = True
_THUI_B105_KEYS = ("start_action_num", "end_action_num", "executed_count", "level", "level_transition", "run_complete",
                   "game_over", "board_changed", "stop_reason", "animation")
_THUI_B105_LOCK = _thui_b105_threading.Lock()
_THUI_B105 = {"python_calls": 0, "acting": 0, "missing": 0, "added": 0, "acting_with_stdout": 0}
_THUI_B105_TLS = _thui_b105_threading.local()
_thui_b105_orig_summarize = _tool_agent.ToolAgent._summarize_step_sequence
_thui_b105_orig_render = _tool_agent.ToolAgent._render_tool_payload


def _thui_b105_summarize(self, action_results):
    summary = _thui_b105_orig_summarize(self, action_results)
    # consumed by the very next python render on this thread; set only when actions executed
    _THUI_B105_TLS.pending = (id(self), summary) if summary else None
    return summary


def _thui_b105_render(self, payload, *args, **kwargs):
    pending = getattr(_THUI_B105_TLS, "pending", None)
    _THUI_B105_TLS.pending = None
    if not isinstance(payload, dict) or payload.get("tool") != "python":
        return _thui_b105_orig_render(self, payload, *args, **kwargs)
    summary = pending[1] if pending and pending[0] == id(self) else None
    missing = bool(summary) and "result" not in payload
    with _THUI_B105_LOCK:
        _THUI_B105["python_calls"] += 1
        if summary:
            _THUI_B105["acting"] += 1
            if payload.get("stdout"):
                _THUI_B105["acting_with_stdout"] += 1
        if missing:
            _THUI_B105["missing"] += 1
            if _THUI_B105_OUTCOME:
                _THUI_B105["added"] += 1
        snap = dict(_THUI_B105)
    if summary and snap["acting"] % 100 == 1:
        print("THUI_B105_STATS outcome=" + str(_THUI_B105_OUTCOME) + " "
              + " ".join(f"{k}={v}" for k, v in snap.items()), flush=True)
    if missing and _THUI_B105_OUTCOME:
        outcome = {k: summary[k] for k in _THUI_B105_KEYS if k in summary}
        payload = {**payload, "action_outcome": outcome}
    return _thui_b105_orig_render(self, payload, *args, **kwargs)


_tool_agent.ToolAgent._summarize_step_sequence = _thui_b105_summarize
_tool_agent.ToolAgent._render_tool_payload = _thui_b105_render
assert _tool_agent.ToolAgent._summarize_step_sequence is _thui_b105_summarize
assert _tool_agent.ToolAgent._render_tool_payload is _thui_b105_render
print(f"THUI_B105_GRAFT ok outcome={_THUI_B105_OUTCOME}", flush=True)
