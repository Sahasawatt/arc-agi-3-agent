"""0-GPU test of the thui-b105 graft against the anim bundle's REAL ToolAgent (summarize and render are wrapped; the
payload assembly they sit inside is checked at source level, since running `_run_python_tool` needs the sandbox).

usage: python test_b105_graft.py <anim-bundle-dir>
Checks: the source still drops the action result when stdout is present (the defect exists at this bundle); the source
calls summarize then render with no other render between; the arm adds `action_outcome` exactly when actions executed
and the payload has no `result`, including on error; a stale summary from another agent or an earlier call is never
attached; non-python payloads pass through; the control counts the same case and changes nothing.
"""
import ast, contextlib, importlib, io, json, sys, types
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = Path(sys.argv[1]) / "src" / "ARC3-Inference"
sys.path.insert(0, str(BUNDLE))
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
try:
    import PIL.Image  # noqa: F401
except ImportError:
    _pil = types.ModuleType("PIL"); _pil.Image = types.ModuleType("PIL.Image")
    sys.modules["PIL"], sys.modules["PIL.Image"] = _pil, _pil.Image

fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    fails += not cond


# --- source-level: the defect and the call order the graft relies on
src = (BUNDLE / "inference" / "agent" / "tool_agent.py").read_text(encoding="utf-8")
fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "_run_python_tool")
body = ast.get_source_segment(src, fn)
i_out, i_res, i_act = body.find('payload["stdout"] = rendered_stdout\n            elif sandbox_result.get("result")'), \
    body.find('elif sandbox_result.get("result") is not None'), body.find("elif action_results:")
check("defect present: action result only reached via elif after stdout and result", -1 not in (i_out, i_res, i_act) and i_out < i_res < i_act)
calls = [n.func.attr for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
         and n.func.attr in ("_summarize_step_sequence", "_render_tool_payload")]
lines = sorted((n.lineno, n.func.attr) for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr in ("_summarize_step_sequence", "_render_tool_payload"))
check(f"source order: summarize then render, once each ({[a for _, a in lines]})",
      [a for _, a in lines] == ["_summarize_step_sequence", "_render_tool_payload"])


def fresh(on):
    import inference.agent.tool_agent as ta
    ta = importlib.reload(ta)
    s = GRAFT if on else GRAFT.replace("_THUI_B105_OUTCOME = True", "_THUI_B105_OUTCOME = False")
    g = {"_tool_agent": ta}
    with contextlib.redirect_stdout(io.StringIO()) as out:
        exec(s, g)
    assert f"THUI_B105_GRAFT ok outcome={on}" in out.getvalue()
    return ta, g


def agent(ta):
    a = ta.ToolAgent.__new__(ta.ToolAgent)
    a._tool_output_tokens, a._tool_output_chars = 1024, 4096
    return a


RESULTS = [{"executed": True, "action_num": 12, "level": 2, "board_changed": True, "level_completed": False,
            "run_complete": False, "game_over": False, "stop_reason": None, "action_display": "UP"}]


def call(ta, a, payload, results=RESULTS):
    """Replays _run_python_tool's tail: summarize when an action executed, then render."""
    with contextlib.redirect_stdout(io.StringIO()) as out:
        if results:
            a._last_step_summary = ta.ToolAgent._summarize_step_sequence(a, results)
        rendered = ta.ToolAgent._render_tool_payload(a, payload, truncate_fields=("stdout", "error", "result"))
    return json.loads(rendered), out.getvalue()


ta, g = fresh(True)
a = agent(ta)
r, out = call(ta, a, {"tool": "python", "returncode": 0, "stdout": "moved"})
check("arm: stdout + actions -> action_outcome added", r.get("action_outcome", {}).get("board_changed") is True
      and r["action_outcome"].get("end_action_num") == 12 and r["stdout"] == "moved")
check("arm: marker printed on first acting call", "THUI_B105_STATS outcome=True python_calls=1 acting=1 missing=1 added=1 acting_with_stdout=1" in out)
r, _ = call(ta, a, {"tool": "python", "error": "boom", "stdout": "x"})
check("arm: error after actions executed -> outcome added", "action_outcome" in r and r["error"] == "boom")
r, _ = call(ta, a, {"tool": "python", "returncode": 0, "result": RESULTS[-1]})
check("arm: result already present -> untouched", "action_outcome" not in r)
r, _ = call(ta, a, {"tool": "python", "returncode": 0, "stdout": "no actions"}, results=None)
check("arm: no action executed -> untouched (pending cleared by the previous render)", "action_outcome" not in r)
with contextlib.redirect_stdout(io.StringIO()):
    ta.ToolAgent._summarize_step_sequence(agent(ta), RESULTS)   # another agent summarizes...
    r = json.loads(ta.ToolAgent._render_tool_payload(a, {"tool": "python", "stdout": "s"}))  # ...a different one renders
check("arm: a summary from another agent is never attached", "action_outcome" not in r)
with contextlib.redirect_stdout(io.StringIO()):
    ta.ToolAgent._summarize_step_sequence(a, RESULTS)
    other = json.loads(ta.ToolAgent._render_tool_payload(a, {"tool": "other", "x": 1}))
    r = json.loads(ta.ToolAgent._render_tool_payload(a, {"tool": "python", "stdout": "late"}))
check("non-python payload passes through and consumes the pending summary", other == {"tool": "other", "x": 1} and "action_outcome" not in r)
s = g["_THUI_B105"]
check(f"counters consistent ({s})", s["added"] == s["missing"] == 2 and s["acting"] == 3 and s["python_calls"] == 6)

ta, g = fresh(False)
a = agent(ta)
r, out = call(ta, a, {"tool": "python", "returncode": 0, "stdout": "moved"})
check("control: response unchanged", "action_outcome" not in r and r["stdout"] == "moved")
check("control: same case counted, nothing added", "THUI_B105_STATS outcome=False python_calls=1 acting=1 missing=1 added=0" in out)
print("FAILS", fails)
sys.exit(1 if fails else 0)
