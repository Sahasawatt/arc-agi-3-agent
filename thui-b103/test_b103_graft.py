"""0-GPU test of the thui-b103 graft against the anim bundle's REAL ToolAgent (the trim method is wrapped; the class,
its estimator and the original trim/drop logic are the bundle's own).

usage: python test_b103_graft.py <anim-bundle-dir>
Checks: the original trim keeps every old board (so the graft is what changes behaviour); the arm keeps exactly the
newest board, strips the image pointer from older texts, passes non-user dicts through by identity, keeps more history
under a budget that forces eviction; the control's output equals the original's; counters and markers match.
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

POINTER = "\n\nCurrent grid image:"
B64 = "data:image/png;base64," + "A" * 6000  # ~2,000 estimator tokens, the size class of a 256x256 board


def fresh(oneboard):
    import inference.agent.tool_agent as ta
    ta = importlib.reload(ta)
    orig = ta.ToolAgent._trim_messages_for_context
    src = GRAFT if oneboard else GRAFT.replace("_THUI_B103_ONEBOARD = True", "_THUI_B103_ONEBOARD = False")
    g = {"_tool_agent": ta}
    with contextlib.redirect_stdout(io.StringIO()) as out:
        exec(src, g)
    assert f"THUI_B103_GRAFT ok oneboard={oneboard}" in out.getvalue()
    return ta, orig, g


def agent(ta, budget):
    a = ta.ToolAgent.__new__(ta.ToolAgent)
    a._context_budget_tokens = budget
    return a


def user(n):
    return {"role": "user", "content": [{"type": "text", "text": f"turn {n} state" + POINTER},
                                        {"type": "image_url", "image_url": {"url": B64}}]}


def convo(turns):
    msgs = [{"role": "system", "content": "sys"}]
    for n in range(turns):
        msgs += [user(n), {"role": "assistant", "content": f"reasoning {n} " + "x" * 300}]
    msgs.append(user(turns))
    return msgs


def images(msgs):
    return sum(1 for m in msgs if isinstance(m.get("content"), list)
               for p in m["content"] if isinstance(p, dict) and p.get("type") == "image_url")


def call(fn, a, msgs):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        res = fn(a, msgs)
    return res, out.getvalue()


fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    fails += not cond


BIG = 10 ** 9
# --- arm
ta, orig, g = fresh(True)
msgs = convo(8)
base, _ = call(orig, agent(ta, BIG), msgs)
check("original trim keeps all 9 boards", images(base) == 9)
res, out = call(ta.ToolAgent._trim_messages_for_context, agent(ta, BIG), msgs)
check("arm keeps exactly one board", images(res) == 1)
last_user = [m for m in res if m["role"] == "user"][-1]
check("the kept board is on the newest user message", images([last_user]) == 1 and last_user["content"][0]["text"].endswith(POINTER))
olds = [m for m in res if m["role"] == "user"][:-1]
check("older user messages become plain text without the pointer",
      all(isinstance(m["content"], str) and m["content"].startswith("turn ") and not m["content"].endswith(POINTER.strip())
          and "Current grid image" not in m["content"] for m in olds))
check("assistant/system dicts pass through by identity",
      all(any(r is m for r in res) for m in msgs if m["role"] != "user"))
check("input list and its dicts are not mutated", images(msgs) == 9 and msgs[1]["content"][0]["text"].endswith(POINTER))
check("marker printed on first trim", "THUI_B103_STATS oneboard=True trims=1 images_seen=9 images_dropped=8 max_images=9" in out)
s = g["_THUI_B103"]
check("est tokens drop on the arm", s["est_tokens_after"] < s["est_tokens_before"] / 3)
# budget that forces eviction: the arm keeps more history than the original
budget = ta._estimate_tokens({"messages": convo(2)})
kept_orig, _ = call(orig, agent(ta, budget), msgs)
kept_arm, _ = call(ta.ToolAgent._trim_messages_for_context, agent(ta, budget), msgs)
check(f"under eviction the arm keeps more turns ({len(kept_arm)} > {len(kept_orig)})", len(kept_arm) > len(kept_orig))
check("under eviction the arm still ends on the current board", images(kept_arm) == 1 and kept_arm[-1] is msgs[-1])
one, _ = call(ta.ToolAgent._trim_messages_for_context, agent(ta, BIG), [msgs[0], msgs[-1]])
check("a single board is left untouched", one[-1] is msgs[-1] and images(one) == 1)
plain = [{"role": "system", "content": "s"}, {"role": "user", "content": "text only"}]
p2, _ = call(ta.ToolAgent._trim_messages_for_context, agent(ta, BIG), plain)
check("text-only history passes through", p2 == plain)

# --- control
ta, orig, g = fresh(False)
msgs = convo(8)
base, _ = call(orig, agent(ta, BIG), msgs)
res, out = call(ta.ToolAgent._trim_messages_for_context, agent(ta, BIG), msgs)
check("control output equals the original's", res == base and images(res) == 9)
budget = ta._estimate_tokens({"messages": convo(2)})
check("control equals the original under eviction",
      call(ta.ToolAgent._trim_messages_for_context, agent(ta, budget), msgs)[0] == call(orig, agent(ta, budget), msgs)[0])
check("control counts but drops nothing", "oneboard=False trims=1 images_seen=9 images_dropped=0" in out
      and g["_THUI_B103"]["images_dropped"] == 0)

print("FAILS", fails)
sys.exit(1 if fails else 0)
