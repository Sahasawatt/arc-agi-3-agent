"""Assert-based, 0-GPU teeth for the built B99 graft against real localrig tool_agent."""
import contextlib
import copy
import importlib
import io
import json
import sys
import types
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "localrig" / "ARC3-Inference"))

# Stdlib-only test runner: stub only heavy/unused import surfaces before loading real tool_agent.py.
if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")

    class RequestException(Exception):
        pass

    class HTTPError(RequestException):
        pass

    requests_stub.RequestException = RequestException
    requests_stub.HTTPError = HTTPError
    requests_stub.Response = object
    requests_stub.post = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("network is forbidden in test_b99_graft.py")
    )
    sys.modules["requests"] = requests_stub

vision_stub = types.ModuleType("inference.agent.vision_context")
vision_stub.current_grid_image_enabled = lambda: False
vision_stub.current_grid_image_part = lambda frame: None
sys.modules["inference.agent.vision_context"] = vision_stub

import inference.agent.tool_agent as real  # noqa: E402


def cell9():
    slug = "thui-b99-rungpin-smoke"
    path = HERE / "out" / slug / f"{slug}.ipynb"
    notebook = json.loads(path.read_text())
    return "".join(notebook["cells"][9]["source"])


def graft_text():
    source = cell9()
    anchor = "import inference.agent.tool_agent as _tool_agent\n"
    start = source.index(anchor) + len(anchor)
    end_marker = 'print("THUI_B99_GRAFT ok", flush=True)\n'
    end = source.index(end_marker, start) + len(end_marker)
    return source[start:end]


GRAFT = graft_text()


def install(graft=GRAFT):
    module = importlib.reload(real)
    namespace = {"_tool_agent": module}
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(graft, namespace)
    return module, namespace, output.getvalue()


def bare_agent(module, game_id):
    agent = object.__new__(module.ToolAgent)
    agent._session_runtime_dir = Path("/runs") / game_id
    agent._b99_game_id = game_id
    agent._b99_verified_previous_rung = ""
    agent._last_step_summary = None
    agent._last_action_result = None
    return agent


def fake_dispatch(agent, namespace, state_path, reasoning, *, clear, level, action, result):
    agent._last_step_summary = {
        "level_transition": clear,
        "level": level,
        "executed_actions": [action],
    }
    agent._last_action_result = dict(result)

    class Dispatch:
        step_executed = True
        content = "unused-heavy-tool-output"

    namespace["_b99_orig_dispatch"] = lambda self, path, name, arguments: Dispatch()

    # This frame intentionally has a local named `reasoning`, as real analyze does at 2246/2338.
    return agent._dispatch_tool(state_path, "python", {"code": "action(...)"})


def injected_messages(agent, namespace, messages):
    captured = {}

    def capture(self, sent, **kwargs):
        captured["messages"] = sent
        return "ok"

    namespace["_b99_orig_chat"] = capture
    assert agent._chat_completion(messages, tools=[]) == "ok"
    return captured["messages"]


module, namespace, output = install()
assert output.strip() == "THUI_B99_GRAFT ok"
game1 = bare_agent(module, "tn36-ef4dde99")
history = [{"role": "system", "content": "system"}, {"role": "user", "content": "current"}]

# No block before a clear.
before = copy.deepcopy(history)
sent = injected_messages(game1, namespace, history)
assert sent == history
assert history == before

# Exact capture after one clear.
result1 = {"executed": True, "level": 2, "level_completed": True, "score": 1}
log = io.StringIO()
with contextlib.redirect_stdout(log):
    fake_dispatch(game1, namespace, Path("/runs/tn36-ef4dde99/state.json"), "reason one", clear=True,
                  level=2, action="LEFT", result=result1)
expected1 = namespace["_b99_make_pin"](
    "reason one",
    '["LEFT"]',
    namespace["_b99_compact_result"](game1),
)
assert game1._b99_verified_previous_rung == expected1
assert f"THUI_B99_PIN game=tn36-ef4dde99 level=2 chars={len(expected1)}" in log.getvalue()
stored_before = copy.deepcopy(history)
sent = injected_messages(game1, namespace, history)
assert sent[1] == {"role": "user", "content": expected1}
assert history == stored_before

# Cap enforced by truncating reasoning first while action and result remain intact.
long_reasoning = "R" * 10000
with contextlib.redirect_stdout(io.StringIO()):
    fake_dispatch(game1, namespace, Path("/runs/tn36-ef4dde99/state.json"), long_reasoning, clear=True,
                  level=3, action="DOWN", result={"executed": True, "level": 3, "level_completed": True})
assert len(game1._b99_verified_previous_rung) == 2048
assert "... [reasoning truncated]" in game1._b99_verified_previous_rung
assert 'Action: ["DOWN"]' in game1._b99_verified_previous_rung
assert '"level_completed":true' in game1._b99_verified_previous_rung

# A second clear replaces, rather than appends, the first pin.
with contextlib.redirect_stdout(io.StringIO()):
    fake_dispatch(game1, namespace, Path("/runs/tn36-ef4dde99/state.json"), "reason two", clear=True,
                  level=4, action="RIGHT", result={"executed": True, "level": 4, "level_completed": True})
assert "reason two" in game1._b99_verified_previous_rung
assert "reason one" not in game1._b99_verified_previous_rung
assert game1._b99_verified_previous_rung.count("VERIFIED PREVIOUS RUNG") == 1

# Two ToolAgent instances (the real harness model: one analyzer per game) are isolated.
game2 = bare_agent(module, "vc33-5430563c")
assert game2._b99_verified_previous_rung == ""
with contextlib.redirect_stdout(io.StringIO()):
    fake_dispatch(game2, namespace, Path("/runs/vc33-5430563c/state.json"), "game two", clear=True,
                  level=2, action="UP", result={"executed": True, "level": 2, "level_completed": True})
assert "game two" in game2._b99_verified_previous_rung
assert "reason two" in game1._b99_verified_previous_rung

# Mutation proof: invert the exact clear predicate in the built graft; the positive check must fail.
needle = 'summary.get("level_transition")'
assert GRAFT.count(needle) == 1
mutated = GRAFT.replace(needle, 'not summary.get("level_transition")')
mut_module, mut_namespace, _ = install(mutated)
mut_agent = bare_agent(mut_module, "bp35-0a0ad940")
try:
    with contextlib.redirect_stdout(io.StringIO()):
        fake_dispatch(mut_agent, mut_namespace, Path("/runs/bp35-0a0ad940/state.json"), "must pin", clear=True,
                      level=2, action="LEFT", result={"executed": True, "level": 2, "level_completed": True})
    assert mut_agent._b99_verified_previous_rung, "mutated clear predicate suppressed a required pin"
except AssertionError as error:
    assert "suppressed a required pin" in str(error)
else:
    raise AssertionError("mutation proof did not make the clear check fail")

importlib.reload(real)
print("ALL OK")
