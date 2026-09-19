"""0-GPU teeth for thui-a10: execute the cell-9 GRAFT exactly as it sits in the BUILT notebook, against the REAL
chassis module (localrig/ARC3-Inference inference.agent.tool_agent, the source Step 0 lifted its extractor from).

Poles (any failure exits 1):
  positive  reasoning carries `World model:` (1,000 chars) + `Plan:`, visible carries `Plan:` only ->
            world_model filled and capped, current_plan NOT written by the wrapper (visible wins), meta string
            byte-identical to the unwrapped function's, counts responses_filled=1 slots_filled=1
  no-self   called from a frame with no ToolAgent `self` -> knowledge untouched, no_self=1
  error     agent lacking `_summarized_knowledge` -> meta string still returned, errors=1
  moved     a ToolAgent whose analyze() source lacks the call site -> the cell-9 assert fires, nothing installed
  control   the control notebook's cell 9 carries the control marker and no wrapper
Run after building --smoke and --smoke --control, with the localrig venv python:
  localrig/.venv/bin/python thui-a10/test_a10_graft.py
"""
import contextlib
import importlib
import io
import json
import sys
import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "localrig" / "ARC3-Inference"))
import inference.agent.tool_agent as real  # noqa: E402

FAIL = []


def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name} {detail}")
    if not ok:
        FAIL.append(name)


def cell9(slug):
    nb = json.load(open(HERE / "out" / slug / f"{slug}.ipynb"))
    return "".join(nb["cells"][9]["source"])


anchor = "import inference.agent.tool_agent as _tool_agent\n"
s = cell9("thui-a10-thk-smoke")
i = s.index(anchor) + len(anchor)
j = s.index("flush=True)\n", s.index("THUI_A10_GRAFT ok")) + len("flush=True)\n")
GRAFT = s[i:j]
META = dict(finish_reason="stop", tool_calls=[], tool_call_markup_in_text=False,
            recovered_tool_calls_from_markup=False, malformed_argument_errors=[])


def install():
    mod = importlib.reload(real)
    ns = {"_tool_agent": mod}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(GRAFT, ns)
    return mod, ns, buf.getvalue()


def call_as_analyze(self, mod, reasoning, content):   # a caller frame with a local `self`, like analyze()
    return mod._format_model_response_meta(reasoning=reasoning, content=content, **META)


# positive
mod, ns, out = install()
check("graft ok printed", "THUI_A10_GRAFT ok cap=488" in out, repr(out[:80]))
agent = object.__new__(mod.ToolAgent)
agent._summarized_knowledge = mod._empty_world_model()
R = "Let me think.\nWorld model: " + "w" * 1000 + "\nPlan: thinking plan"
C = "Plan: visible plan"
want = ns["_a10_meta"].__wrapped__(reasoning=R, content=C, **META)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    got = call_as_analyze(agent, mod, R, C)
wm = agent._summarized_knowledge["world_model"]
check("meta string unchanged", got == want)
check("world_model filled from reasoning", wm.startswith("w" * 100), repr(wm[:20]))
check("world_model capped", len(wm) < 488 + 40 and wm.endswith("chars omitted]"), f"len={len(wm)}")
check("visible slot left to visible path", agent._summarized_knowledge["current_plan"] == "",
      repr(agent._summarized_knowledge["current_plan"]))
c = ns["THUI_A10_COUNTS"]
check("counts", (c["responses_filled"], c["slots_filled"], c["no_self"], c["errors"]) == (1, 1, 0, 0), str(c))
check("APPLIED + FILLED printed", "THUI_A10_APPLIED first" in buf.getvalue() and "THUI_A10_FILLED" in buf.getvalue())

# no-self
mod, ns, _ = install()
with contextlib.redirect_stdout(io.StringIO()):
    mod._format_model_response_meta(reasoning=R, content="", **META)
check("no-self counted", ns["THUI_A10_COUNTS"]["no_self"] == 1, str(ns["THUI_A10_COUNTS"]))

# error
mod, ns, _ = install()
bare = object.__new__(mod.ToolAgent)
with contextlib.redirect_stdout(io.StringIO()):
    got = call_as_analyze(bare, mod, R, "")
check("error swallowed, meta returned", ns["THUI_A10_COUNTS"]["errors"] == 1 and "finish_reason" in got,
      str(ns["THUI_A10_COUNTS"]))

# moved
tmp = Path(tempfile.mkdtemp()) / "fake_tool_agent.py"   # getsource needs a real file
tmp.write_text("class ToolAgent:\n    def analyze(self):\n        return None\n\n\n"
               "def _format_model_response_meta(**k):\n    return 'x'\n")
spec = importlib.util.spec_from_file_location("fake_tool_agent", tmp)
fake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fake)
try:
    with contextlib.redirect_stdout(io.StringIO()):
        exec(GRAFT, {"_tool_agent": fake})
    check("moved -> assert", False, "no assert fired")
except AssertionError as e:
    check("moved -> assert", "call site moved" in str(e) and fake._format_model_response_meta(a=1) == "x", str(e))

# control
cs = cell9("thui-a10-ctl-smoke")
check("control marker, no wrapper", "THUI_A10_GRAFT control" in cs and "_a10_meta" not in cs)

importlib.reload(real)
print("ALL OK" if not FAIL else f"FAILED: {FAIL}")
sys.exit(1 if FAIL else 0)
