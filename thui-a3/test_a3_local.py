"""Local teeth for thui-a3: executes a3_graft + a3_teeth against the anim bundle's REAL python_tool_sandbox, with a stub
tool_agent module (the real one imports serving deps). Then proves the teeth RED on three mutations."""
import sys, types, subprocess, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
# A3_SEAMS = a directory holding the anim bundle's inference/agent/python_tool_sandbox.py and inference/utils/{segmentation,grid_utils}.py,
# e.g. from `kaggle datasets download jakobbrggen/taaf-kaggle-source-anim-20260807-anim -f src/ARC3-Inference/inference/...`.
SEAMS = Path(os.environ.get("A3_SEAMS", "")) if os.environ.get("A3_SEAMS") else None
if SEAMS is None or not (SEAMS / "inference" / "agent" / "python_tool_sandbox.py").is_file():
    sys.exit("set A3_SEAMS to a dir containing inference/agent/python_tool_sandbox.py (the anim bundle source)")


def run(graft_src, teeth_src):
    sys.path.insert(0, str(SEAMS))
    from inference.agent.python_tool_sandbox import run_sandboxed_python
    stub = types.ModuleType("inference.agent.tool_agent")
    class ToolAgent:
        def _run_python_tool(self, state_path, arguments):
            sandbox_result = run_sandboxed_python(code="", timeout_seconds=1, initial_state={}, action_handler=None)
            return sandbox_result
        def _build_user_prompt(self, action_num, *, valid_actions, current_frame=None, history_entries=None, previous_step_summary=None):
            return "REAL"
    stub.ToolAgent = ToolAgent
    stub.run_sandboxed_python = run_sandboxed_python
    stub.__file__ = "stub"
    sys.modules["inference.agent.tool_agent"] = stub
    import inference.agent as pkg
    pkg.tool_agent = stub
    ns = {"__name__": "a3kernel"}
    exec(compile(graft_src, "a3_graft", "exec"), ns)
    exec(compile(teeth_src, "a3_teeth", "exec"), ns)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    graft = (HERE / "a3_graft.py").read_text()
    teeth = (HERE / "a3_teeth.py").read_text()
    if mode == "one":
        mut = os.environ.get("A3_MUT", "")
        if mut:
            old, new = mut.split("|||")
            assert graft.count(old) == 1, ("mutation anchor", old)
            graft = graft.replace(old, new)
        run(graft, teeth)
        print("GREEN")
        sys.exit(0)
    r = subprocess.run([sys.executable, __file__, "one"], capture_output=True, text=True)
    print("control:", r.returncode, (r.stdout.strip().splitlines() or [""])[-1], r.stderr.strip().splitlines()[-1:] )
    assert r.returncode == 0 and "teeth ok" in r.stdout
    muts = [
        "        if pred == after:|||        if True:",
        "        return 'File \"<python_tool>\", line ' + (str(n) if n > 0 else \"(saved WORLD_MODEL / helpers)\")|||        return 'File \"<python_tool>\", line ' + str(int(m.group(1)))",
        "    if agent is None:\n        return _a3_orig_sandbox(code=code, **kwargs)|||    if agent is None:\n        agent = type('X', (), {})()",
        "                and node.targets[0].id == \"WORLD_MODEL\" and isinstance(node.value, _a3_ast.Constant)|||                and node.targets[0].id == \"WORLD_MODEL\"",
    ]
    for m in muts:
        r = subprocess.run([sys.executable, __file__, "one"], capture_output=True, text=True, env={**os.environ, "A3_MUT": m})
        red = r.returncode != 0 and "GREEN" not in r.stdout
        print("mutant:", m.split("|||")[0].strip()[:60], "->", "RED" if red else "GREEN (teeth MISSING)", (r.stderr.strip().splitlines() or [""])[-1][:120])
        assert red, m
    print("ALL TEETH PASS: control green, 4 mutations red")
