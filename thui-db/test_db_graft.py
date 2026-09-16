"""Local teeth for the death-blacklist graft (v1), run BEFORE any GPU.

Two wrappers on the REAL class names: ToolAgent._summarize_step_sequence (records, per level, every life that ended in death
as total / per-type counts / last type, outside _summarized_knowledge) and ToolAgent._build_user_prompt (renders budgets and
the residual fatal list before the harness's own `end of world model. `).

  python thui-db/test_db_graft.py

Seams + controls, all in one run:
  1. both real signatures read from the Kaggle-side source by ast (control (a): a fabricated name must be reported missing);
     the per-item keys the graft reads and the prompt anchor asserted present in the source exactly as the graft expects;
  2. the notebook's OWN cell-9 graft source is executed against a stub ToolAgent whose originals mimic the real ones;
  3. control (c): after the graft the class carries both wrappers, not the originals;
  4. behaviour: a death records (level, action, life) and the NEXT prompt for that level carries the fatal block before the
     anchor; the knowledge wipe leaves the ledger intact; a different level carries nothing (control (b)); a non-death step
     records nothing and returns the original summary unchanged; lives are counted from executed actions across steps (a batch
     of several actions counts each one, a RESET starts a new life); sp80-L1 shape (3 lives of 30) -> action-budget line and NO
     fatal list; sp80-L2 shape (lives ending on the 5th SPACE) -> "5th SPACE ... LIMITED RESOURCE" line, SPACE absent from the
     fatal list, a MOUSE death still listed; a prompt without the anchor still gets the block; malformed items never raise.
"""
import ast, contextlib, io, json, os, sys, types
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(S, "ds-full", "keith", "src", "ARC3-Inference", "inference", "agent", "tool_agent.py")
NB = os.path.join(HERE, "taaf-thui-db-v1.ipynb")
fails = []


def sig(path, cls, meth):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for f in node.body:
                if isinstance(f, ast.FunctionDef) and f.name == meth:
                    return [a.arg for a in f.args.args], [a.arg for a in f.args.kwonlyargs]
    return None


s1 = sig(SRC, "ToolAgent", "_summarize_step_sequence"); s2 = sig(SRC, "ToolAgent", "_build_user_prompt")
print(f"_summarize_step_sequence: {s1}\n_build_user_prompt: {s2}")
if s1 != (["self", "action_results"], []):
    fails.append(f"_summarize_step_sequence signature changed: {s1}")
if not s2 or s2[0] != ["self", "action_num"] or "current_frame" not in s2[1]:
    fails.append(f"_build_user_prompt signature changed: {s2}")
assert sig(SRC, "ToolAgent", "_thui_no_such_method") is None, "ast probe does not discriminate"
print("control (a) ok: a fabricated method name is reported missing")
src = open(SRC, encoding="utf-8").read()
for key in ('"executed": bool(payload.get("executed"))', '"game_over": bool(payload.get("game_over"))',
            '"action_display": payload.get("action_display") or payload.get("action_name")', '"level": payload.get("level")',
            'compact["executed_actions"] = [str(action).strip()'):
    if key not in src:
        fails.append(f"compact action result no longer carries {key[:40]!r}")
if src.count('lines.append("end of world model. ")') != 1:
    fails.append("prompt anchor 'end of world model. ' is not appended exactly once upstream")
else:
    print("upstream anchors present: compact-result keys + 'end of world model. ' x1")

# ---- run the notebook's own cell-9 graft against a stub ----------------------------------------------------
cell9 = "".join(json.load(open(NB, encoding="utf-8"))["cells"][9]["source"])
graft = cell9[cell9.index("# ---- thui-db"):]
graft = graft.replace('assert "inference" not in sys.modules, "solver imported before the DB graft"\n', "")


class _Frame:
    def __init__(self, level): self.level = level; self.step = 0


class _TA:
    """mimics the two originals: summary shape of tool_agent.py:1058-1070, prompt ending with the anchor"""
    def __init__(self):
        self._summarized_knowledge = {"world_model": "<wm>", "current_plan": "<plan>"}

    def _summarize_step_sequence(self, action_results):
        ex = [i for i in action_results if isinstance(i, dict) and i.get("executed")]
        if not ex:
            return None
        return {"level": ex[-1].get("level"), "game_over": any(bool(i.get("game_over")) for i in ex),
                "executed_actions": [a for i in ex for a in (i.get("executed_actions") if isinstance(i.get("executed_actions"), list) else [])]}

    def _build_user_prompt(self, action_num, *, valid_actions, current_frame=None, history_entries=None, previous_step_summary=None):
        return f"prompt step {action_num} level {getattr(current_frame, 'level', None)}\n- World model: <wm>\nend of world model. \nGround yourself."


_ta = types.ModuleType("inference.agent.tool_agent"); _ta.ToolAgent = _TA; _ta.__file__ = SRC
sys.modules["inference"] = types.ModuleType("inference")
sys.modules["inference.agent"] = types.ModuleType("inference.agent")
sys.modules["inference.agent.tool_agent"] = _ta
ns = {"sys": sys, "Path": Path}
exec(graft, ns)
assert _TA._summarize_step_sequence.__name__ == "_thui_db_summarize" and _TA._build_user_prompt.__name__ == "_thui_db_prompt", "graft not installed"
print("control (c) ok: the class now carries both wrappers, not the originals")


def step(agent, items):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = agent._summarize_step_sequence(items)
    return r, buf.getvalue()


def prompt(agent, level):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        t = agent._build_user_prompt(5, valid_actions=["UP"], current_frame=_Frame(level))
    return t, buf.getvalue()


def item(level, acts, over=False):
    return {"executed": True, "game_over": over, "level": level, "executed_actions": list(acts)}


def case(name, ok, detail=""):
    print(f"  {name:40s} {'ok' if ok else 'FAIL'}")
    if not ok:
        fails.append(f"{name}: {detail}")


a = _TA()
r, out = step(a, [item(2, ["UP"])])
case("non-death step: summary unchanged, no record", r == {"level": 2, "game_over": False, "executed_actions": ["UP"]} and "THUI_DB_RECORD" not in out
     and not getattr(a, "_thui_db", {}) and a._thui_db_life["total"] == 1, f"{r} {out!r}")
t, out = prompt(a, 2)
case("prompt with empty ledger", "Fatal actions" not in t and "THUI_DB_INJECT" not in out)
r, out = step(a, [item(2, ["LEFT"]), item(2, ["MOUSE(row=33, col=21)"], over=True)])
per = a._thui_db.get(2)
case("death recorded with its life", r["game_over"] is True and per["fatal"] == {"MOUSE(row=33, col=21)": 1}
     and per["lives"] == [{"total": 3, "counts": {"UP": 1, "LEFT": 1, "MOUSE": 1}, "last": "MOUSE"}]
     and "THUI_DB_RECORD level=2 action=MOUSE(row=33, col=21) n=1 life_total=3 deaths=1 budget_actions=None budget_types={}" in out
     and a._thui_db_life["total"] == 0, f"{per} {out!r} {a._thui_db_life}")
t, out = prompt(a, 2)
i_block, i_anchor = t.find("Fatal actions on THIS level"), t.find("end of world model. ")
case("prompt carries fatal block before anchor", 0 < i_block < i_anchor and "MOUSE(row=33, col=21) x1" in t
     and "THUI_DB_INJECT level=2 distinct=1 deaths=1 budget_actions=None budget_types={} lines=1" in out, f"{t!r} {out!r}")
for k in a._summarized_knowledge: a._summarized_knowledge[k] = ""
case("ledger survives knowledge wipe", a._thui_db[2]["fatal"] == {"MOUSE(row=33, col=21)": 1})
t, out = prompt(a, 3)
case("control (b): no leak to level 3", "Fatal actions" not in t and "THUI_DB_INJECT" not in out)
# a batch counts every action; an agent-issued RESET starts a new life without a death
step(a, [item(2, ["UP", "UP", "DOWN"]), item(2, ["RESET"]), item(2, ["LEFT", "LEFT"])])
case("batch counts each action; RESET restarts life", a._thui_db_life == {"total": 2, "counts": {"LEFT": 2}, "level": 2}, str(a._thui_db_life))
# sp80 L1 shape: three lives of 30 moves ending on different moves -> action budget 30, no fatal list
b = _TA()
for last in ("RIGHT", "DOWN", "LEFT"):
    step(b, [item(1, ["UP"] * 29), item(1, [last], over=True)])
t, out2 = prompt(b, 1)
case("action budget (3 lives of 30) -> budget line only", "BUDGET" in t and "~30 actions" in t and "Fatal actions" not in t
     and "exploration" not in t and "budget_actions=30" in out2 and "lines=1" in out2, f"{t!r} {out2!r}")
# sp80 L2 shape: four lives ending on the 5th SPACE at different totals -> type budget, SPACE absent from the fatal list
c = _TA()
for moves in (17, 24, 27, 14):
    step(c, [item(2, ["LEFT"] * moves + ["SPACE"] * 4), item(2, ["SPACE"], over=True)])
step(c, [item(2, ["MOUSE(row=1, col=2)"], over=True)])
t, out2 = prompt(c, 2)
case("type budget -> '5th SPACE' resource line", "5th SPACE" in t and "4 safe uses" in t and "Keep using it" in t
     and "budget_types={'SPACE': 5}" in out2, f"{t!r} {out2!r}")
case("SPACE absent from fatal list, MOUSE listed", "SPACE x" not in t and "MOUSE(row=1, col=2) x1" in t and "lines=2" in out2, t)
# two deaths only -> plain fatal list, no budget
d = _TA()
for _ in range(2):
    step(d, [item(1, ["UP"] * 29), item(1, ["RIGHT"], over=True)])
t, _ = prompt(d, 1)
case("two deaths -> fatal list, no budget", "RIGHT x2" in t and "BUDGET" not in t, t)
# fallback: prompt without the anchor still gets the block appended
orig = ns["_orig_db_prompt"]; ns["_orig_db_prompt"] = lambda self, n, **kw: "no anchor here"
t, out = prompt(a, 2)
ns["_orig_db_prompt"] = orig
case("fallback append without anchor", t.startswith("no anchor here") and "Fatal actions" in t, t)
# malformed items never raise and record nothing new (dicts missing keys, non-list executed_actions, non-dicts)
before = json.dumps(a._thui_db, sort_keys=True)
try:
    r, out = step(a, [{"executed": True, "game_over": True, "level": 2}, {"executed": True, "game_over": True, "level": 2, "executed_actions": "junk"}, None, "junk"])
    ok = "Traceback" not in out and "record error" not in out and json.dumps(a._thui_db, sort_keys=True) == before
except Exception as exc:
    ok = False; out = repr(exc)
case("malformed items do not raise", ok, out)

print("\n" + ("FAIL: " + " | ".join(fails) if fails else "ALL TEETH PASS (2 seams + 3 controls + 12 cases)"))
raise SystemExit(1 if fails else 0)
