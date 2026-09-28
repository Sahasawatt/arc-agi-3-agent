"""0-GPU test of the CognitiveMap graft against the anim bundle's real ToolAgent."""

import ast
import contextlib
import importlib
import io
import json
import sys
import types
from pathlib import Path


HERE = Path(__file__).resolve().parent
BUNDLE = Path(sys.argv[1]) / "src" / "ARC3-Inference"
sys.path.insert(0, str(BUNDLE))
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
try:
    import PIL.Image  # noqa: F401
except ImportError:
    _pil = types.ModuleType("PIL")
    _pil.Image = types.ModuleType("PIL.Image")
    sys.modules["PIL"], sys.modules["PIL.Image"] = _pil, _pil.Image

fails = 0


def check(name, condition):
    global fails
    print(("ok   " if condition else "FAIL ") + name)
    fails += not condition


src = (BUNDLE / "inference" / "agent" / "tool_agent.py").read_text(encoding="utf-8")
guard_src = (BUNDLE / "inference" / "agent" / "noop_guard.py").read_text(encoding="utf-8")
tree = ast.parse(src)
ensure = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_ensure_session")
prompt = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_build_user_prompt")
prompt_args = {arg.arg for arg in prompt.args.args + prompt.args.kwonlyargs}
check("source: _ensure_session sets self._noop_guard", "self._noop_guard" in ast.get_source_segment(src, ensure))
check("source: prompt accepts current_frame and valid_actions", {"current_frame", "valid_actions"} <= prompt_args)
check("source: noop_guard exposes board_signature", "def board_signature" in guard_src)
check("source: guard has is_known_noop and observe", "def is_known_noop" in guard_src and "def observe" in guard_src)
check("graft has no Spanish prompt strings", not any(word in GRAFT for word in
      ("MAPA", "desde este estado", "nunca han", "celdas", "ATENCION")))


class Frame:
    level = 1
    step = 0
    grid = [[1, 0], [0, 1]]


def fresh(on):
    import inference.agent.tool_agent as ta
    import inference.agent.noop_guard as ng
    ta = importlib.reload(ta)
    original_ensure = ta.ToolAgent._ensure_session
    original_prompt = ta.ToolAgent._build_user_prompt

    def stub_ensure(agent, state_path):
        agent._noop_guard = ng.NoopGuard()

    def stub_prompt(agent, action_num, *, valid_actions=None, current_frame=None, **kwargs):
        return "BASE"

    ta.ToolAgent._ensure_session = stub_ensure
    ta.ToolAgent._build_user_prompt = stub_prompt
    source = GRAFT if on else GRAFT.replace("_THUI_B106_MAP = True", "_THUI_B106_MAP = False")
    namespace = {"_thui_b106_test_original_ensure": original_ensure,
                 "_thui_b106_test_original_prompt": original_prompt}
    with contextlib.redirect_stdout(io.StringIO()) as output:
        exec(source, namespace)
    check(f"graft installs ({'arm' if on else 'control'})", f"THUI_B106_GRAFT ok map={on}" in output.getvalue())
    return ta, ng, namespace


def make_agent(ta):
    agent = ta.ToolAgent.__new__(ta.ToolAgent)
    agent._noop_guard = None
    return agent


ta, ng, arm = fresh(True)
agent = make_agent(ta)
ta.ToolAgent._ensure_session(agent, Path("/tmp/state/game.json"))
check("ensure wrapper installs MapRecorder around real guard",
      isinstance(agent._noop_guard, arm["_thui_b106_MapRecorder"]) and isinstance(agent._noop_guard._inner, ng.NoopGuard))
recorder = agent._noop_guard
recorder.observe(level=1, board_before_sig="A", action_sig="UP", board_changed=False)
recorder.observe(level=1, board_before_sig="A", action_sig="LEFT", board_changed=True)
recorder.observe(level=1, board_before_sig="A", action_sig="MOUSE(row=2, col=3)", board_changed=True)
recorder.observe(level=1, board_before_sig="A", action_sig="RIGHT", board_changed=False, animated=True)
recorder.observe(level=1, board_before_sig="A", action_sig="UP", board_changed=False)
note = arm["_thui_b106_render_map_note"](recorder.registros, 1, "A", ["UP", "DOWN", "MOUSE", "JUMP"])
for expected in ("HOST MAP", "from this state you already tried:", "from this state you have NOT tried:",
                 "never did anything on this level:", "clicks that DID do something:",
                 "action(s) had an effect ONLY in the animation", "WARNING: this state was already visited"):
    check(f"render includes {expected}", expected in note)
never = next((l for l in note.splitlines() if l.startswith("- never did anything")), "")
check("animation-only action counts as an effect (not listed as inert)",
      "RIGHT (no effect)" not in note and "RIGHT" not in never and "UP" in never)
check("render returns empty with no records", arm["_thui_b106_render_map_note"]([], 1, "A", ["UP"]) == "")

prompt_result = ta.ToolAgent._build_user_prompt(agent, 0, valid_actions=["UP"], current_frame=Frame())
check("arm prompt appends newline plus note", prompt_result.startswith("BASE\nHOST MAP"))
check("arm counters record a prompt and note", arm["_thui_b106_stats"]["prompts"] >= 1 and arm["_thui_b106_stats"]["notes"] >= 1)

ta, ng, control = fresh(False)
agent = make_agent(ta)
ta.ToolAgent._ensure_session(agent, Path("/tmp/state/control.json"))
agent._noop_guard.observe(level=1, board_before_sig="A", action_sig="UP", board_changed=True)
result = ta.ToolAgent._build_user_prompt(agent, 0, valid_actions=["UP"], current_frame=Frame())
check("control returns base byte-identical", result == "BASE")
check("control computes and counts note", control["_thui_b106_stats"]["prompts"] == 1 and control["_thui_b106_stats"]["notes"] >= 1)

original_render = control["_thui_b106_render_map_note"]
control["_thui_b106_render_map_note"] = lambda *args: (_ for _ in ()).throw(RuntimeError("synthetic"))
result = ta.ToolAgent._build_user_prompt(agent, 0, valid_actions=["UP"], current_frame=Frame())
check("prompt note exception falls back to base", result == "BASE")
check("prompt note exception increments errors", control["_thui_b106_stats"]["errors"] == 1)
control["_thui_b106_render_map_note"] = original_render

print("FAILS", fails)
sys.exit(1 if fails else 0)
