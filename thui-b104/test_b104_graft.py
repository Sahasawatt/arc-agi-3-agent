"""0-GPU test of the thui-b104 graft against the anim bundle's REAL ToolAgent and REAL vision_context (the two
methods are wrapped; image rendering of the stock board, the estimator and the trim logic are the bundle's own).

usage: python test_b104_graft.py <anim-bundle-dir>          (needs Pillow; MULTIMODAL_CONTEXT is set here)
Checks: the original build carries no sheet; the arm attaches one sheet, before the stock board, only when the action
just before the call animated; <= 8 panels with first and last kept; the PNG decodes to the expected size; older
sheets are stripped at trim and stock boards are not; errors leave the message unchanged; the control counts the same
eligibility and attaches nothing; the estimator cost of a full sheet is measured and printed.
"""
import base64, contextlib, importlib, io, os, sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(sys.argv[1]) / "src" / "ARC3-Inference"))
os.environ["MULTIMODAL_CONTEXT"] = "current_grid"
os.environ["MULTIMODAL_UPSCALE"] = "4"
GRAFT = (HERE / "graft_src.py").read_text(encoding="utf-8")
from PIL import Image  # noqa: E402

MARK_START = "Animation of your last action"


def fresh(sheet):
    import inference.agent.tool_agent as ta
    ta = importlib.reload(ta)
    ob, ot = ta.ToolAgent._build_user_message, ta.ToolAgent._trim_messages_for_context
    src = GRAFT if sheet else GRAFT.replace("_THUI_B104_SHEET = True", "_THUI_B104_SHEET = False")
    g = {"_tool_agent": ta}
    with contextlib.redirect_stdout(io.StringIO()) as out:
        exec(src, g)
    assert f"THUI_B104_GRAFT ok sheet={sheet}" in out.getvalue()
    return ta, ob, ot, g


def grid(k):
    g = [[0] * 64 for _ in range(64)]
    for r in range(10 + k, 20 + k):
        for c in range(5, 15):
            g[r][c] = 9
    g[0] = [3] * 64
    return tuple(tuple(r) for r in g)


def agent(ta, rec=None, raises=False, cb=True, aware=True):
    a = ta.ToolAgent.__new__(ta.ToolAgent)
    a._context_budget_tokens = 10 ** 9
    a._animation_awareness_enabled = aware

    def step_env(req):
        if raises:
            raise RuntimeError("boom")
        assert req == {"query": "animation", "action_num": None}
        return {"executed": False, "query": "animation", "record": rec}
    a._step_env_callback = step_env if cb else None
    return a


def frame(step):
    return SimpleNamespace(grid=grid(0), step=step, level=1)


def record(action_num, n):
    return {"action_num": action_num, "frames": [grid(i) for i in range(n)], "summary": {}}


def build(fn, a, step, prompt="state"):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        m = fn(a, prompt, frame(step))
    return m, out.getvalue()


def imgs(m):
    return [p for p in m["content"] if isinstance(p, dict) and p.get("type") == "image_url"] if isinstance(m["content"], list) else []


def has_mark(m):
    return isinstance(m["content"], list) and any(isinstance(p, dict) and str(p.get("text", "")).startswith(MARK_START) for p in m["content"])


def decode(url):
    return Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))


fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    fails += not cond


ta, ob, ot, g = fresh(True)
B = ta.ToolAgent._build_user_message
m0, _ = build(ob, agent(ta, record(7, 5)), 7)
check("original build: one image, no sheet", len(imgs(m0)) == 1 and not has_mark(m0))
m, out = build(B, agent(ta, record(7, 5)), 7)
check("arm: sheet attached when the last action animated", has_mark(m) and len(imgs(m)) == 2)
check("stock board image stays LAST and is the original's bytes", m["content"][-1] == m0["content"][-1])
check("prompt text first, pointer text right before the board",
      m["content"][0]["text"] == "state" and m["content"][-2]["text"] == "Current grid image:")
check("marker printed on first eligible build", "THUI_B104_STATS sheet=True builds=1 eligible=1 attached=1" in out)
im = decode(imgs(m)[0]["image_url"]["url"])
check(f"5 frames -> 4x2 grid of 128x139 panels ({im.size})", im.size == (4 * 128 + 5 * 2, 2 * (128 + 11) + 3 * 2))
check("panel pixel is the ARC colour of the frame (row 12, col 6 = 9 blue)",
      im.getpixel((2 + 6 * 2, 2 + 11 + 12 * 2)) == (30, 147, 255))
for label, a, step in [("older record (action 6, step 7)", agent(ta, record(6, 5)), 7),
                       ("no record", agent(ta, None), 7),
                       ("single-frame record", agent(ta, record(7, 1)), 7),
                       ("no step_env callback", agent(ta, record(7, 5), cb=False), 7),
                       ("animation awareness off", agent(ta, record(7, 5), aware=False), 7)]:
    mm, _ = build(B, a, step)
    check(f"no sheet: {label}", not has_mark(mm) and mm == build(ob, a, step)[0])
before = dict(g["_THUI_B104"])
mm, _ = build(B, agent(ta, record(7, 5), raises=True), 7)
check("callback raising leaves the message unchanged and is counted",
      not has_mark(mm) and g["_THUI_B104"]["query_errors"] == before["query_errors"] + 1)
check("pick: 42 frames -> 8 panels, first and last kept",
      g["_thui_b104_pick"](42)[0] == 0 and g["_thui_b104_pick"](42)[-1] == 41 and len(g["_thui_b104_pick"](42)) == 8)
check("pick: 3 frames -> all", g["_thui_b104_pick"](3) == [0, 1, 2])
big, _ = build(B, agent(ta, record(7, 42)), 7)
bim = decode(imgs(big)[0]["image_url"]["url"])
url = imgs(big)[0]["image_url"]["url"]
est_sheet = ta._estimate_tokens({"u": url})
est_board = ta._estimate_tokens({"u": imgs(m0)[0]["image_url"]["url"]})
print(f"     measured: 8-panel sheet {bim.size}, base64 {len(url)} chars, estimator {est_sheet} tok; stock board {est_board} tok")
check("42 frames -> 8-panel sheet of 4x2", bim.size == im.size)
# trim: three turns each with a sheet; only the newest keeps it, every stock board survives
sys_msg = {"role": "system", "content": "sys"}
t1, _ = build(B, agent(ta, record(3, 4)), 3, "t1")
t2, _ = build(B, agent(ta, record(5, 4)), 5, "t2")
t3, _ = build(B, agent(ta, record(7, 4)), 7, "t3")
msgs = [sys_msg, t1, {"role": "assistant", "content": "a1"}, t2, {"role": "assistant", "content": "a2"}, t3]
res = ta.ToolAgent._trim_messages_for_context(agent(ta), msgs)
users = [x for x in res if x["role"] == "user"]
check("trim: only the newest user message keeps its sheet", [has_mark(u) for u in users] == [False, False, True])
check("trim: every stock board survives", [len(imgs(u)) for u in users] == [1, 1, 2])
check("trim: stripped messages keep prompt + pointer + board", users[0]["content"][0]["text"] == "t1" and users[0]["content"][-1] == t1["content"][-1])
check("trim: input list not mutated", has_mark(msgs[1]) and has_mark(msgs[3]))

ta, ob, ot, g = fresh(False)
B = ta.ToolAgent._build_user_message
m, out = build(B, agent(ta, record(7, 5)), 7)
check("control: nothing attached, output equals original", m == build(ob, agent(ta, record(7, 5)), 7)[0])
check("control: eligibility counted and reported on the same schedule",
      "THUI_B104_STATS sheet=False builds=1 eligible=1 attached=0" in out)
print("FAILS", fails)
sys.exit(1 if fails else 0)
