"""Local teeth for the L1 graft, run BEFORE any GPU: does the wrapper source match the REAL harness, and does a
no-impact action flow through all four wrappers? The kernel's own teeth cover the band learner; these cover the seams.

  python scratchpad/test_l1_graft.py

Controls in the same run: (a) a method name that does NOT exist must be reported missing (proves the ast probe
discriminates); (b) an action whose changed rows fall outside the band must stay board_changed=True.
"""
import ast, json, os, sys, types

sys.stdout.reconfigure(encoding="utf-8")
S = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(S, "ds-full", "keith", "src", "ARC3-Inference", "inference")
NB = os.path.join(S, "wt-fast2", "thui-l1", "taaf-thui-l1-v0.ipynb")
fails = []


def sig(path, cls, meth):
    """(args, kwonly) of cls.meth in the real source, or None."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for f in node.body:
                if isinstance(f, ast.FunctionDef) and f.name == meth:
                    return [a.arg for a in f.args.args], [a.arg for a in f.args.kwonlyargs]
    return None


solver = os.path.join(SRC, "framework", "solver.py")
agent = os.path.join(SRC, "agent", "tool_agent.py")
want = [(solver, "_HarnessGameSession", "_execute_action"), (agent, "ToolAgent", "_compact_action_result"),
        (agent, "ToolAgent", "_summarize_step_sequence"), (agent, "ToolAgent", "_describe_last_outcome")]
for path, cls, meth in want:
    s = sig(path, cls, meth)
    print(f"{cls}.{meth}: {s}")
    if s is None:
        fails.append(f"{cls}.{meth} NOT FOUND in {os.path.basename(path)}")
# control (a): a name that must be absent
assert sig(agent, "ToolAgent", "_thui_no_such_method") is None, "ast probe does not discriminate"
print("control (a) ok: a fabricated method name is reported missing")

# _execute_action must take the action positionally and the rest keyword-only, or `**kw` forwarding breaks
ex = sig(solver, "_HarnessGameSession", "_execute_action")
if ex and ex[0][:2] != ["self", "action"]:
    fails.append(f"_execute_action positional args changed: {ex[0]}")
if ex and not {"batch_index", "batch_size"} <= set(ex[1]):
    fails.append(f"_execute_action kwonly args changed: {ex[1]}")

# ---- run the graft's own wrapper source against stubs -------------------------------------------------
cell9 = "".join(json.load(open(NB, encoding="utf-8"))["cells"][9]["source"])
graft = cell9[cell9.index("# ---- thui-l1"):]
graft = graft.replace('assert "inference" not in sys.modules, "solver imported before the L1 graft"\n', "")

_sol = types.ModuleType("inference.framework.solver")
_ta = types.ModuleType("inference.agent.tool_agent")


class _Sess:
    """The ORIGINAL the graft wraps: it mutates the board by self._pending_rows, exactly as the real one does by acting.
    It must never be reassigned after the graft installs its wrapper -- doing so silently removes the wrapper."""
    def _execute_action(self, action, *, batch_index=1, batch_size=1, generated_tokens=None, flush_viewer_payload=True):
        g = self.game
        grid = [list(r) for r in g.current_state.grid]
        for r in self._pending_rows:
            grid[r][g.n % 8] = (grid[r][g.n % 8] + 1) % 9
        g.n += 1
        g.current_state = types.SimpleNamespace(grid=tuple(tuple(r) for r in grid))
        return {"executed": True, "action_num": g.n, "board_changed": True, "level_completed": False}


class _TA:
    def _compact_action_result(self, payload):
        return {"board_changed": bool(payload.get("board_changed"))}

    def _summarize_step_sequence(self, results):
        return {"executed_count": len(results)}

    def _describe_last_outcome(self, summary):
        return "Last executed sequence produced a board change;"


_sol._HarnessGameSession = _Sess
_ta.ToolAgent = _TA
_sol._grid_from_state = lambda st: st.grid
_sol.__file__ = solver          # the real module has one; the stub needs it for the graft's marker line
_ta.__file__ = agent
grids = {"cur": None}
_ns = {"sys": sys, "Path": __import__("pathlib").Path}
sys.modules["inference"] = types.ModuleType("inference")
sys.modules["inference.framework"] = types.ModuleType("inference.framework")
sys.modules["inference.agent"] = types.ModuleType("inference.agent")
sys.modules["inference.framework.solver"] = _sol
sys.modules["inference.agent.tool_agent"] = _ta
exec(graft, _ns)

BOARD = [tuple(0 for _ in range(8)) for _ in range(8)]


class _Game:
    def __init__(self): self.n = 0; self.current_state = types.SimpleNamespace(grid=tuple(BOARD)); self.game_run = types.SimpleNamespace(game_id="tn36-test")


class _Action:
    def __init__(self, name): self.id = types.SimpleNamespace(name=name)


sess = _Sess(); sess.game = _Game()
ta = _TA()


# the wrapper must be installed on the class before any step runs, or this file measures nothing
assert _Sess._execute_action.__name__ == "_thui_exec", f"graft not installed: {_Sess._execute_action.__name__}"
print("control (c) ok: the class now carries the wrapper, not the original")


def step(rows):
    """drive one action whose changed rows are `rows`, THROUGH the installed wrapper"""
    sess._pending_rows = rows
    return sess._execute_action(_Action("ACTION6"), batch_index=1, batch_size=1)


for i in range(24):
    step({0, 2 + (i % 5)})
p_hud = step({0})                      # only the counter row
p_real = step({0, 4})                  # counter + a real row -> must stay a change
print(f"after learning: no_impact on counter-only={p_hud.get('no_impact')}, on counter+row4={p_real.get('no_impact')}")
if not p_hud.get("no_impact") or p_hud.get("board_changed") is not False:
    fails.append(f"counter-only action was not flagged: {p_hud}")
if p_real.get("no_impact") or p_real.get("board_changed") is not True:
    fails.append(f"control (b) FAILED, a real change was flagged: {p_real}")
else:
    print("control (b) ok: an action touching a non-band row stays board_changed=True")

compact = ta._compact_action_result(p_hud)
summary = ta._summarize_step_sequence([p_hud, p_hud, p_real])
text = ta._describe_last_outcome(summary)
print("compact:", compact)
print("summary:", {k: summary[k] for k in ("no_impact_count", "hud_rows") if k in summary})
print("prompt text:", text)
if not compact.get("no_impact"):
    fails.append("compact result lost no_impact")
if summary.get("no_impact_count") != 2:
    fails.append(f"summary miscounted no-impact: {summary.get('no_impact_count')}")
if "NO impact" not in text:
    fails.append("outcome text does not tell the model")

print("\n" + ("FAIL: " + " | ".join(fails) if fails else "ALL TEETH PASS (4 seams + 2 controls)"))
raise SystemExit(1 if fails else 0)
