"""Local teeth for the stuck-game backoff graft, run BEFORE any GPU.

The graft wraps ONE method: ToolAgent.analyze (one instance per game, solver.py:1189). It reads `current_frame.level`
from the runtime-state file the solver writes before every analyze and sleeps (polling should_stop) once a game has
spent THUI_BO_STALE actions on one level.

  python thui-bo/test_bo_graft.py

Seams + controls, all in one run:
  1. the real signature of `ToolAgent.analyze` (positional state_path, action_num; keyword should_stop) and the
     runtime-state writer's `current_frame.level` key are read from the real sources by ast (control (a): a fabricated
     name must be reported missing);
  2. the notebook's OWN cell-9 graft source is executed against a stub ToolAgent whose analyze records its calls;
  3. control (c): after the graft the class carries the wrapper, not the original;
  4. behaviour, with the sleep clock stubbed: below 60 stale actions -> no nap, no marker; at 60 -> nap 20 and marker;
     level change -> counter resets (no nap at the next call); should_stop() True -> the nap ends at the first poll
     (control (b): the graft must not out-sleep the clock); a missing/corrupt state file -> level None, no crash,
     delegate still called.
"""
import ast, contextlib, io, json, os, sys, tempfile, types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(S, "ds-full", "keith", "src", "ARC3-Inference", "inference", "agent", "tool_agent.py")
RTS = os.path.join(S, "ds-full", "keith", "src", "ARC3-Inference", "inference", "agent", "runtime_state.py")
NB = os.path.join(HERE, "taaf-thui-bo-v0.ipynb")
fails = []


def sig(path, cls, meth):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for f in node.body:
                if isinstance(f, ast.FunctionDef) and f.name == meth:
                    return [a.arg for a in f.args.args], [a.arg for a in f.args.kwonlyargs]
    return None


s = sig(SRC, "ToolAgent", "analyze")
print(f"ToolAgent.analyze: {s}")
if not s or s[0][:3] != ["self", "state_path", "action_num"] or "should_stop" not in s[0] + s[1]:
    fails.append(f"analyze signature changed upstream: {s}")
assert sig(SRC, "ToolAgent", "_thui_no_such_method") is None, "ast probe does not discriminate"
print("control (a) ok: a fabricated method name is reported missing")
rts = open(RTS, encoding="utf-8").read()
if '"current_frame": frame_to_payload(current_frame)' not in rts or '"level": frame.level' not in rts:
    fails.append("runtime_state.py no longer writes current_frame.level")
else:
    print("runtime-state writer carries current_frame.level")

# ---- run the notebook's own cell-9 graft against a stub ----------------------------------------------------
cell9 = "".join(json.load(open(NB, encoding="utf-8"))["cells"][9]["source"])
graft = cell9[cell9.index("# ---- thui-bo"):]
graft = graft.replace('assert "inference" not in sys.modules, "solver imported before the BO graft"\n', "")

calls = []


class _TA:
    def analyze(self, state_path, action_num, valid_actions=None, step_env=None, transcript_path=None,
                analysis_step=None, transcript_updated=None, request_timeout_seconds=None, should_stop=None):
        calls.append((str(state_path), action_num))
        return "result"


_ta = types.ModuleType("inference.agent.tool_agent"); _ta.ToolAgent = _TA; _ta.__file__ = SRC
sys.modules["inference"] = types.ModuleType("inference")
sys.modules["inference.agent"] = types.ModuleType("inference.agent")
sys.modules["inference.agent.tool_agent"] = _ta
ns = {"sys": sys, "Path": Path}
exec(graft, ns)
assert _TA.analyze.__name__ == "_thui_bo_analyze", f"graft not installed: {_TA.analyze.__name__}"
print("control (c) ok: the class now carries the wrapper, not the original")

# stub the clock: monotonic advances 1 s per sleep(1) so a nap of N takes N polls, none of them real
clock = {"t": 0.0, "sleeps": 0}
ns["_bo_time"].monotonic = lambda: clock["t"]
def _fake_sleep(d):
    clock["t"] += d; clock["sleeps"] += 1
ns["_bo_time"].sleep = _fake_sleep

tmp = tempfile.mkdtemp()
state = Path(tmp) / "state.json"


def run(level, action_num, agent, stop=False, corrupt=False):
    if corrupt:
        state.write_text("{not json", encoding="utf-8")
    else:
        state.write_text(json.dumps({"current_frame": {"level": level}}), encoding="utf-8")
    clock["sleeps"] = 0
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = agent.analyze(state, action_num, should_stop=lambda: stop)
    return r, clock["sleeps"], buf.getvalue()


a = _TA()
cases = [
    ("below threshold", dict(level=1, action_num=0), 0, False),
    ("still below (59)", dict(level=1, action_num=59), 0, False),
    ("at 60 -> nap 20", dict(level=1, action_num=60), 20, True),
    ("at 125 -> nap 40", dict(level=1, action_num=125), 40, True),
    ("level change resets", dict(level=2, action_num=126), 0, False),
    ("59 later, same level", dict(level=2, action_num=185), 0, False),
    ("60 later -> nap", dict(level=2, action_num=186), 20, True),
]
for name, kw, want_sleeps, want_marker in cases:
    r, n, out = run(agent=a, **kw)
    ok = r == "result" and n == want_sleeps and (("THUI_BO_BACKOFF" in out) == want_marker)
    print(f"  {name:24s} sleeps={n:3d} marker={'THUI_BO_BACKOFF' in out!s:5}  {'ok' if ok else 'FAIL'}")
    if not ok:
        fails.append(f"{name}: sleeps={n} want {want_sleeps}, marker={'THUI_BO_BACKOFF' in out} want {want_marker}, r={r!r}")

# control (b): should_stop True ends the nap at the first poll
b = _TA(); run(level=1, action_num=0, agent=b)
r, n, out = run(level=1, action_num=300, agent=b, stop=True)
ok = r == "result" and n == 0 and "THUI_BO_BACKOFF" in out
print(f"  {'should_stop ends nap':24s} sleeps={n:3d} marker={'THUI_BO_BACKOFF' in out!s:5}  {'ok' if ok else 'FAIL'}")
if not ok:
    fails.append(f"control (b): sleeps={n} (want 0), marker={'THUI_BO_BACKOFF' in out}, r={r!r}")

# corrupt state file: level None, no crash, delegate called, no nap
c = _TA()
r, n, out = run(level=None, action_num=0, agent=c, corrupt=True)
r2, n2, out2 = run(level=None, action_num=61, agent=c, corrupt=True)
ok = r == r2 == "result" and n == 0 and "wrapper error" not in out + out2 and n2 == 20
print(f"  {'corrupt state file':24s} sleeps={n2:3d} (level None still counts stale)  {'ok' if ok else 'FAIL'}")
if not ok:
    fails.append(f"corrupt state: r={r!r}/{r2!r} sleeps={n}/{n2} out={out+out2!r}")

before_calls = len(calls)
assert before_calls == 11, f"delegate call count {before_calls} != 11 (every wrapped call must reach the original)"
print("delegate reached on every call (11/11)")

print("\n" + ("FAIL: " + " | ".join(fails) if fails else "ALL TEETH PASS (2 seams + 3 controls + 7 cases + stop + corrupt)"))
raise SystemExit(1 if fails else 0)
