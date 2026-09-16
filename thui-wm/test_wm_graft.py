"""Local teeth for the wipe-guard graft (ARENA 3 lever found by A's refuter), run BEFORE any GPU.

The graft wraps ONE method: ToolAgent._update_summarized_knowledge_from_step_summary. Upstream wipes the six
summarized-knowledge fields whenever the last step summary carries level_transition, run_complete OR game_over
(tool_agent.py:1113-1126). game_over is a within-level death followed by an auto-RESET of the same level
(solver.py:718 / :663), so the wipe throws away everything the agent wrote down about the level it is about to
replay. The guard: keep the knowledge on a game_over that is NOT also a level transition / run completion.

  python thui-wm/test_wm_graft.py

Seams + controls, all in one run:
  1. the real signature of the wrapped method is read from the real source by ast (control (a): a fabricated name
     must be reported missing);
  2. the notebook's OWN cell-9 graft source is executed against a stub ToolAgent whose original really wipes;
  3. control (c): after the graft the class carries the wrapper, not the original -- a test that reassigns the
     method after grafting measures nothing (the L1 teeth learned this the hard way);
  4. behaviour: game_over alone -> KEPT (all six fields intact, marker printed); level_transition -> WIPED;
     run_complete -> WIPED; game_over + level_transition -> WIPED (control (b): the guard must not over-reach).
"""
import ast, json, os, sys, types, io, contextlib

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(S, "ds-full", "keith", "src", "ARC3-Inference", "inference", "agent", "tool_agent.py")
NB = os.path.join(HERE, "taaf-thui-wm-v0.ipynb")
FIELDS = ("world_model", "goal_model", "action_model", "recent_findings", "open_questions", "current_plan")
fails = []


def sig(path, cls, meth):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for f in node.body:
                if isinstance(f, ast.FunctionDef) and f.name == meth:
                    return [a.arg for a in f.args.args]
    return None


s = sig(SRC, "ToolAgent", "_update_summarized_knowledge_from_step_summary")
print(f"ToolAgent._update_summarized_knowledge_from_step_summary: {s}")
if s != ["self"]:
    fails.append(f"signature changed upstream: {s}")
assert sig(SRC, "ToolAgent", "_thui_no_such_method") is None, "ast probe does not discriminate"
print("control (a) ok: a fabricated method name is reported missing")

# the wipe condition must still be the one the graft assumes -- read it from the source, not from memory
src = open(SRC, encoding="utf-8").read()
if 'summary.get("level_transition") or summary.get("run_complete") or summary.get("game_over")' not in src:
    fails.append("upstream wipe condition is no longer level_transition|run_complete|game_over")
else:
    print("upstream wipe condition present verbatim")

# ---- run the notebook's own cell-9 graft against a stub ----------------------------------------------------
cell9 = "".join(json.load(open(NB, encoding="utf-8"))["cells"][9]["source"])
graft = cell9[cell9.index("# ---- thui-wm"):]
graft = graft.replace('assert "inference" not in sys.modules, "solver imported before the WM graft"\n', "")


class _TA:
    """the ORIGINAL: wipes exactly as tool_agent.py:1113-1126 does"""
    def __init__(self):
        self._summarized_knowledge = {k: f"<{k}>" for k in FIELDS}
        self._last_step_summary = None

    def _update_summarized_knowledge_from_step_summary(self):
        summary = self._last_step_summary
        if not summary:
            return
        if summary.get("level_transition") or summary.get("run_complete") or summary.get("game_over"):
            for key in FIELDS:
                self._summarized_knowledge[key] = ""


_ta = types.ModuleType("inference.agent.tool_agent"); _ta.ToolAgent = _TA; _ta.__file__ = SRC
sys.modules["inference"] = types.ModuleType("inference")
sys.modules["inference.agent"] = types.ModuleType("inference.agent")
sys.modules["inference.agent.tool_agent"] = _ta
ns = {"sys": sys, "Path": __import__("pathlib").Path}
exec(graft, ns)

assert _TA._update_summarized_knowledge_from_step_summary.__name__ == "_thui_wm_update", \
    f"graft not installed: {_TA._update_summarized_knowledge_from_step_summary.__name__}"
print("control (c) ok: the class now carries the wrapper, not the original")


def run(summary):
    a = _TA(); a._last_step_summary = summary
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        a._update_summarized_knowledge_from_step_summary()
    kept = all(a._summarized_knowledge[k] == f"<{k}>" for k in FIELDS)
    wiped = all(a._summarized_knowledge[k] == "" for k in FIELDS)
    return kept, wiped, buf.getvalue()


cases = [
    ({"game_over": True, "level": 2, "action_span": "40-41"}, "KEPT"),
    ({"level_transition": True, "level": 3}, "WIPED"),
    ({"run_complete": True}, "WIPED"),
    ({"game_over": True, "level_transition": True}, "WIPED"),      # control (b): the guard must not over-reach
    ({"board_changed": True}, "KEPT-TRIVIAL"),                     # no terminal flag: upstream never wiped either
]
for summary, want in cases:
    kept, wiped, out = run(summary)
    got = "KEPT" if kept else ("WIPED" if wiped else "MIXED")
    marker = "THUI_WM_KEPT" in out
    ok = (want == "KEPT" and got == "KEPT" and marker) or (want == "WIPED" and got == "WIPED" and not marker) \
         or (want == "KEPT-TRIVIAL" and got == "KEPT" and not marker)
    print(f"  {json.dumps(summary):58s} -> {got:6s} marker={marker}  {'ok' if ok else 'FAIL (want ' + want + ')'}")
    if not ok:
        fails.append(f"{summary} -> {got}, marker={marker}, wanted {want}")

print("\n" + ("FAIL: " + " | ".join(fails) if fails else "ALL TEETH PASS (1 seam + 3 controls + 5 cases)"))
raise SystemExit(1 if fails else 0)
