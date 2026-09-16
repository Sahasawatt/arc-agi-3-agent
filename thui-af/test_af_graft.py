"""Teeth for the thui-af action floor (0 GPU). Executes the built notebook's cell-9 graft against the anim bundle's REAL
runtime_state.py / action_names.py (scratchpad/anim-bundle) and a stub ToolAgent.analyze, driving the solver's call shape
(analyze(state_path, action_num, valid_actions=..., step_env=..., should_stop=...)).

    python thui-af/test_af_graft.py

Cases: 1 no-action turn -> nothing; 2nd -> ONE floor action via step_env, MOUSE on a non-background cell; executed turn resets the
counter; every later no-action turn fires again; used cells never repeat; level change resets counter/cap/used; cap per level;
should_stop blocks; retryable failure ignored; no MOUSE -> non-mouse random, never RESET; non-executed payload not counted;
control notebook has no wrapper. Seam check: the real solver passes step_env/valid_actions/should_stop as kwargs.
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
NB = HERE / "taaf-thui-af-v0.ipynb"
NB_CTL = HERE / "taaf-thui-af-ctl.ipynb"


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
    load("inference.agent.action_names", "agent/action_names.py")
    ta = types.ModuleType("inference.agent.tool_agent"); sys.modules["inference.agent.tool_agent"] = ta

    class Result:
        def __init__(self, step_executed, yielded=False, retryable=False):
            self.step_executed = step_executed; self.yielded_control = yielded; self.retryable_failure = retryable

    class ToolAgent:
        next_result = Result(False, yielded=True)

        def analyze(self, state_path, action_num, valid_actions=None, step_env=None, transcript_path=None,
                    analysis_step=None, transcript_updated=None, request_timeout_seconds=None, should_stop=None):
            return ToolAgent.next_result
    ta.ToolAgent = ToolAgent; ta.Result = Result
    return ta, rs


def main():
    fails = []
    solver_src = (BUNDLE / "framework" / "solver.py").read_text(encoding="utf-8")
    call = solver_src[solver_src.index("self.analyzer.analyze("):]
    call = call[:call.index("should_stop=self.should_stop") + len("should_stop=self.should_stop")]   # the call spans nested parens
    for kw in ("valid_actions=", "step_env=self.step_env", "should_stop=self.should_stop"):
        if kw not in call: fails.append(f"seam: solver analyze call lacks {kw}")

    ta, rs = make_modules()
    with redirect_stdout(io.StringIO()):
        exec(cell9_tail(NB), {"_tool_agent": ta})
    if ta.ToolAgent.analyze.__name__ != "_thui_af_analyze": fails.append("analyze not wrapped")

    tmp = Path(tempfile.mkdtemp()) / "runtime_state.json"
    grid = tuple(tuple(0 for _ in range(8)) for _ in range(8))
    grid = tuple(tuple(3 if (r, c) in {(1, 1), (2, 5), (6, 6)} else 0 for c in range(8)) for r in range(8))
    rs.write_runtime_state(tmp, current_frame=rs.Frame(grid=grid, step=0, level=1), history=[])
    calls = []
    payload = {"executed": True, "board_changed": True}

    def step_env(args):
        calls.append(args); return dict(payload)
    ag = ta.ToolAgent()
    R = ta.Result
    kw = dict(valid_actions=["ACTION1", "ACTION2", "ACTION6", "RESET"], step_env=step_env, should_stop=lambda: False)

    def turn(res):
        ta.ToolAgent.next_result = res
        with redirect_stdout(io.StringIO()):
            return ag.analyze(tmp, 0, **kw)
    try:
        turn(R(False, yielded=True))
        if calls: fails.append("case1: fired after one no-action turn")
        turn(R(False, yielded=True))
        if len(calls) != 1: fails.append(f"case2: expected 1 floor action, got {len(calls)}")
        else:
            a = calls[0]["actions"][0]
            if a.get("action") != "MOUSE" or (a["row"], a["col"]) not in {(1, 1), (2, 5), (6, 6)}:
                fails.append(f"case2: floor action not a rare-colour MOUSE: {a}")
        turn(R(True))
        turn(R(False, yielded=True))
        if len(calls) != 1: fails.append("case3: executed turn did not reset the counter")
        turn(R(False))            # plain no-action (not a yield) counts too
        turn(R(False, yielded=True))
        if len(calls) != 3: fails.append(f"case4: later no-action turns must fire each time, got {len(calls)}")
        cells = {(c["actions"][0]["row"], c["actions"][0]["col"]) for c in calls}
        if len(cells) != 3: fails.append("case5: floor repeated a cell")
        turn(R(False, yielded=True))    # rare cells exhausted -> non-mouse
        if calls[-1]["actions"][0]["action"] not in {"UP", "DOWN"}: fails.append(f"case6: expected non-mouse fallback, got {calls[-1]}")
        # level change resets: new level, same cells available again
        rs.write_runtime_state(tmp, current_frame=rs.Frame(grid=grid, step=5, level=2), history=[])
        n0 = len(calls)
        turn(R(False, yielded=True))
        if len(calls) != n0: fails.append("case7: level change did not reset the stall counter")
        turn(R(False, yielded=True))
        if len(calls) != n0 + 1 or calls[-1]["actions"][0]["action"] != "MOUSE": fails.append("case7: after level change the floor should fire a MOUSE again")
        # cap per level
        for _ in range(60):
            turn(R(False, yielded=True))
        if ag._thui_af["n"] != 40: fails.append(f"case8: cap per level not enforced ({ag._thui_af['n']})")
        # should_stop blocks
        rs.write_runtime_state(tmp, current_frame=rs.Frame(grid=grid, step=9, level=3), history=[])
        kw["should_stop"] = lambda: True
        n0 = len(calls)
        turn(R(False, yielded=True)); turn(R(False, yielded=True))
        if len(calls) != n0: fails.append("case9: fired while should_stop() is true")
        kw["should_stop"] = lambda: False
        # retryable failure ignored
        n0 = len(calls)
        turn(R(False, retryable=True)); turn(R(False, retryable=True)); turn(R(False, retryable=True))
        if len(calls) != n0: fails.append("case10: retryable failures counted as stalls")
        # never RESET, and non-executed payloads are not counted
        rs.write_runtime_state(tmp, current_frame=rs.Frame(grid=grid, step=9, level=4), history=[])
        kw["valid_actions"] = ["RESET"]
        n0 = len(calls)
        turn(R(False, yielded=True)); turn(R(False, yielded=True))
        if len(calls) != n0: fails.append("case11: fired with only RESET available")
        kw["valid_actions"] = ["ACTION1"]
        payload = {"executed": False}
        turn(R(False, yielded=True))
        if calls[-1]["actions"][0]["action"] != "UP" or ag._thui_af["n"] != 0: fails.append("case12: non-executed payload counted or wrong action")
        # the wrapper returns the original result object untouched
        r = turn(R(False, yielded=True))
        if r is not ta.ToolAgent.next_result: fails.append("case13: wrapper replaced the result")
    except Exception as exc:
        fails.append(f"case crashed: {type(exc).__name__}: {exc}")

    if NB_CTL.exists():
        ctl = cell9_tail(NB_CTL)
        ta2, _ = make_modules()
        with redirect_stdout(io.StringIO()):
            exec(ctl, {"_tool_agent": ta2})
        if "_thui_af_analyze" in ctl or ta2.ToolAgent.analyze.__name__ != "analyze": fails.append("control: wrapper present")
    else:
        fails.append("control notebook not built")

    for f in fails:
        print("FAIL", f)
    print("ALL TEETH PASS" if not fails else f"{len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
