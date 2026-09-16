"""Teeth for the thui-rs restart-at-stall graft (0 GPU). Executes the built notebook's cell-9 graft against the anim bundle's REAL
runtime_state.py and a stub ToolAgent carrying the real field names, driving the solver's call shape
(analyze(state_path, action_num, valid_actions=..., step_env=..., analysis_step=..., should_stop=...)).

    python thui-rs/test_rs_graft.py

Seam checks on the REAL tool_agent.py: the five fields the graft resets exist and are what _ensure_session resets; `_empty_world_model`
and `_LOCAL_ANALYZER_SEED` exist; analyze has an `analysis_step` kwarg and the solver passes it; the seed is passed per request.
Cases: 19 distinct steps -> no restart; 20th -> restart (history cleared, world model reset, summary/result dropped, seed +1, marker);
retries of one analysis_step count once; the count restarts after a restart; cap 2 per level; level change resets count and cap;
the wrapper still delegates and returns the original result; the no-op guard is untouched; control has no wrapper.
"""
import importlib.util
import io
import json
import sys
import tempfile
import types
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent.parent / "anim-bundle" / "src" / "ARC3-Inference" / "inference"
NB = HERE / "taaf-thui-rs-v0.ipynb"
NB_CTL = HERE / "taaf-thui-rs-ctl.ipynb"
FIELDS = ("_history_messages", "_summarized_knowledge", "_last_step_summary", "_last_action_result")


def cell9_tail(path):
    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    s = "".join(cells[9]["source"])
    return s[s.index("import inference.agent.tool_agent as _ta"):]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, BUNDLE / rel)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod; spec.loader.exec_module(mod)
    return mod


def make_modules():
    for n in ("inference", "inference.agent", "inference.utils"):
        sys.modules.setdefault(n, types.ModuleType(n))
    load("inference.utils.grid_utils", "utils/grid_utils.py")
    rs = load("inference.agent.runtime_state", "agent/runtime_state.py")
    ta = types.ModuleType("inference.agent.tool_agent"); sys.modules["inference.agent.tool_agent"] = ta
    ta._LOCAL_ANALYZER_SEED = 20260825
    ta._empty_world_model = lambda: {"world_model": "", "goal_model": ""}

    class ToolAgent:
        def __init__(self):
            self._history_messages = [{"role": "user", "content": "x"}]
            self._summarized_knowledge = {"world_model": "known", "goal_model": "known"}
            self._last_step_summary = {"game_over": False}
            self._last_action_result = {"executed": True}
            self._noop_guard = object()
            self.calls = 0

        def analyze(self, state_path, action_num, valid_actions=None, step_env=None, transcript_path=None,
                    analysis_step=None, transcript_updated=None, request_timeout_seconds=None, should_stop=None):
            self.calls += 1
            # the real analyze appends to history and fills the summary every turn
            self._history_messages.append({"role": "assistant", "content": f"turn {analysis_step}"})
            self._last_step_summary = {"step": analysis_step}
            return ("result", analysis_step)
    ta.ToolAgent = ToolAgent
    return ta, rs


def main():
    fails = []
    src = (BUNDLE / "agent" / "tool_agent.py").read_text(encoding="utf-8")
    ens = src[src.index("def _ensure_session"):src.index("def _ensure_session") + 1200]
    for f in FIELDS:
        if f"self.{f} = " not in ens: fails.append(f"seam: _ensure_session does not reset {f}")
    if "def _empty_world_model()" not in src or "_LOCAL_ANALYZER_SEED = " not in src or "seed=_LOCAL_ANALYZER_SEED" not in src:
        fails.append("seam: world-model factory / seed constant / per-request seed missing")
    if "analysis_step: int | None = None" not in src: fails.append("seam: analyze has no analysis_step kwarg")
    solver = (BUNDLE / "framework" / "solver.py").read_text(encoding="utf-8")
    if "analysis_step=analysis_step" not in solver: fails.append("seam: solver does not pass analysis_step")

    ta, rs = make_modules()
    with redirect_stdout(io.StringIO()):
        exec(cell9_tail(NB), {"_tool_agent": ta})
    if ta.ToolAgent.analyze.__name__ != "_thui_rs_analyze": fails.append("analyze not wrapped")

    tmp = Path(tempfile.mkdtemp()) / "runtime_state.json"
    grid = tuple(tuple(0 for _ in range(4)) for _ in range(4))

    def set_level(lv):
        rs.write_runtime_state(tmp, current_frame=rs.Frame(grid=grid, step=0, level=lv), history=[])
    set_level(1)
    ag = ta.ToolAgent()
    out = io.StringIO()

    def turn(step):
        with redirect_stdout(out):
            return ag.analyze(tmp, 0, valid_actions=["ACTION1"], step_env=lambda a: {}, analysis_step=step, should_stop=lambda: False)
    try:
        for s in range(1, 20):
            r = turn(s)
        if r != ("result", 19) or ag.calls != 19: fails.append("case0: wrapper did not delegate / return the original result")
        if "THUI_RS_RESTART" in out.getvalue(): fails.append("case1: restarted before 20 distinct turns")
        turn(19); turn(19)     # retries of one step count once
        if "THUI_RS_RESTART" in out.getvalue(): fails.append("case2: retries counted as turns")
        seed0 = ta._LOCAL_ANALYZER_SEED
        turn(20)
        if out.getvalue().count("THUI_RS_RESTART") != 1: fails.append("case3: 20th distinct turn did not restart exactly once")
        if ag._history_messages != [{"role": "assistant", "content": "turn 20"}]: fails.append(f"case3: history not cleared before the turn: {ag._history_messages}")
        if ag._summarized_knowledge != {"world_model": "", "goal_model": ""} : fails.append("case3: world model not reset")
        if ag._last_action_result is not None: fails.append("case3: last action result not dropped")
        if ta._LOCAL_ANALYZER_SEED != seed0 + 1: fails.append("case3: seed not bumped")
        if type(ag._noop_guard) is not object: fails.append("case3: no-op guard touched")
        if ag._thui_rs["restarts"] != 1 or ag._thui_rs["steps"] != {20}: fails.append(f"case3: counters {ag._thui_rs}")
        for s in range(21, 40):
            turn(s)
        if out.getvalue().count("THUI_RS_RESTART") != 2: fails.append("case4: second restart not at 20 turns after the first")
        for s in range(40, 80):
            turn(s)
        if out.getvalue().count("THUI_RS_RESTART") != 2: fails.append("case5: cap of 2 per level not enforced")
        set_level(2)
        for s in range(80, 99):
            turn(s)
        if out.getvalue().count("THUI_RS_RESTART") != 2: fails.append("case6: level change did not reset the turn count")
        turn(99)
        if out.getvalue().count("THUI_RS_RESTART") != 3: fails.append("case6: after a level change the cap should reopen")
        if "total=3" not in out.getvalue(): fails.append("case6: total counter wrong")
    except Exception as exc:
        fails.append(f"case crashed: {type(exc).__name__}: {exc}")

    if NB_CTL.exists():
        ctl = cell9_tail(NB_CTL)
        ta2, _ = make_modules()
        with redirect_stdout(io.StringIO()):
            exec(ctl, {"_tool_agent": ta2})
        if "_thui_rs_analyze" in ctl or ta2.ToolAgent.analyze.__name__ != "analyze": fails.append("control: wrapper present")
    else:
        fails.append("control notebook not built")

    for f in fails:
        print("FAIL", f)
    print("ALL TEETH PASS" if not fails else f"{len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
