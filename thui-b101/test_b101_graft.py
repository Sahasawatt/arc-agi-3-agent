"""0-GPU test of the thui-b101 graft against the anim bundle's REAL ToolAgent (the method is replaced; the class,
its _summarized_knowledge dict and the original method are the bundle's own).

usage: python test_b101_graft.py <anim-bundle-dir>
Checks, both arms: the original method still wipes on a death (so the graft is what changes behaviour); the arm keeps
all six slots on a death and wipes on a level transition, run completion, and death+transition; the control wipes on
all of them exactly as the original; cross_level_notes is never touched; counters and markers match.
"""
import contextlib, importlib, io, sys, types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(sys.argv[1]) / "src" / "ARC3-Inference"))
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
try:
    import PIL.Image  # noqa: F401
except ImportError:
    _pil = types.ModuleType("PIL"); _pil.Image = types.ModuleType("PIL.Image")
    sys.modules["PIL"], sys.modules["PIL.Image"] = _pil, _pil.Image

SLOTS = ("world_model", "goal_model", "action_model", "recent_findings", "open_questions", "current_plan")


def fresh(keep):
    import inference.agent.tool_agent as ta
    ta = importlib.reload(ta)
    orig = ta.ToolAgent._update_summarized_knowledge_from_step_summary
    src = GRAFT if keep else GRAFT.replace("_THUI_B101_KEEP = True", "_THUI_B101_KEEP = False")
    g = {"_tool_agent": ta}
    with contextlib.redirect_stdout(io.StringIO()) as out:
        exec(src, g)
    assert f"THUI_B101_GRAFT ok keep={keep}" in out.getvalue()
    return ta, orig, g


def agent(ta, filled=True):
    a = ta.ToolAgent.__new__(ta.ToolAgent)
    a._summarized_knowledge = {k: (f"text-{k}" if filled else "") for k in SLOTS}
    a._summarized_knowledge["cross_level_notes"] = "keep-me"
    return a


def step(a, **flags):
    a._last_step_summary = {"level": 2, "level_transition": False, "run_complete": False, "game_over": False, **flags}
    with contextlib.redirect_stdout(io.StringIO()) as out:
        type(a)._update_summarized_knowledge_from_step_summary(a)
    return out.getvalue()


def slots(a):
    return [a._summarized_knowledge[k] for k in SLOTS]


fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    fails += not cond


# the bundle's own method wipes on a death -- otherwise the graft changes nothing
ta, orig, _ = fresh(True)
a = agent(ta); a._last_step_summary = {"game_over": True}; orig(a)
check("original wipes on game_over", slots(a) == [""] * 6)

for keep in (True, False):
    ta, orig, g = fresh(keep)
    tag = "arm" if keep else "ctl"
    a = agent(ta); out = step(a, game_over=True)
    check(f"{tag}: death {'keeps' if keep else 'wipes'} six slots", slots(a) == ([f"text-{k}" for k in SLOTS] if keep else [""] * 6))
    check(f"{tag}: DEATH marker slots=6 kept={keep}", f"slots=6 kept={keep}" in out and "THUI_B101_DEATH" in out)
    check(f"{tag}: cross_level_notes untouched", a._summarized_knowledge["cross_level_notes"] == "keep-me")
    for flags in ({"level_transition": True}, {"run_complete": True}, {"game_over": True, "level_transition": True}):
        a = agent(ta); out = step(a, **flags)
        check(f"{tag}: {sorted(flags)} wipes", slots(a) == [""] * 6)
    check(f"{tag}: CLEAR marker on transition", "THUI_B101_CLEAR" in out)
    a = agent(ta, filled=False); step(a, game_over=True)
    a = agent(ta); step(a)  # nothing happened: no wipe, no count
    check(f"{tag}: no-event step leaves slots", slots(a) == [f"text-{k}" for k in SLOTS])
    s = g["_THUI_B101"]
    want = {"deaths": 3, "qualifying_deaths": 2, "kept": 1 if keep else 0, "wiped_on_death": 1 if keep else 2,
            "level_wipes": 3, "clears": 2}
    check(f"{tag}: counters {s}", s == want)

print(f"\n{'all pass' if not fails else str(fails) + ' FAILED'}")
sys.exit(1 if fails else 0)
