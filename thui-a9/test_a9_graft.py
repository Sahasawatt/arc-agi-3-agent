"""0-GPU teeth for thui-a9: execute the cell-9 GRAFT exactly as it sits in the BUILT notebook, against stubs.

Poles (all must hold; any failure exits 1):
  positive  stub prompt carries the old element -> wrapper swaps it, counts applied=1, prints APPLIED + GRAFT ok
  miss      stub prompt lacks the old element at runtime -> text unchanged, counts miss=1, prints MISS
  moved     stub SOURCE lacks the element -> the cell-9 assert fires before any wrapper is installed
  control   the control notebook's cell 9 carries the control marker and no wrapper
Run after building: --smoke and --smoke --control.
"""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("a9b", HERE / "build_notebook.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def cell9(slug):
    nb = json.load(open(HERE / "out" / slug / f"{slug}.ipynb"))
    return "".join(nb["cells"][9]["source"])


def graft_from_notebook(slug):
    s = cell9(slug)
    i = s.index(b.IMPORT_ANCHOR) + len(b.IMPORT_ANCHOR)
    j = s.index("flush=True)\n", s.index("THUI_A9_GRAFT ok")) + len("flush=True)\n")
    return s[i:j]


def stub_module(runtime_prompt: str, source_has_element: bool):
    # The element appears in the method SOURCE at most once (like the real chassis); the runtime text comes
    # from a module global so it does not add a second literal copy to the source.
    body = b.OLD_ELEM if source_has_element else "no element here"
    src = (
        "PROMPT = ''\n"
        "class ToolAgent:\n"
        "    def _build_user_prompt(self, action_num, *, valid_actions=None):\n"
        f"        _unused = {body!r}\n"
        "        return PROMPT\n"
    )
    d = tempfile.mkdtemp()
    p = Path(d) / "stub_tool_agent.py"
    p.write_text(src)
    s = importlib.util.spec_from_file_location("stub_tool_agent", p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    m.PROMPT = runtime_prompt
    return m


def run(graft, mod):
    g = {"_tool_agent": mod}
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        exec(compile(graft, "cell9-graft", "exec"), g)
        text = mod.ToolAgent()._build_user_prompt(3, valid_actions=["ACTION1"])
    return g, text, out.getvalue()


fails = []
graft = graft_from_notebook("thui-a9-wmreq-smoke")
assert graft.startswith("# ---- thui-a9"), graft[:60]

# positive
prompt = "line A\n" + b.OLD_ELEM + "\nline B"
g, text, out = run(graft, stub_module(prompt, True))
if not (b.NEW_ELEM in text and b.OLD_ELEM not in text and g["THUI_A9_COUNTS"] == {"applied": 1, "miss": 0}
        and "THUI_A9_APPLIED first" in out and "THUI_A9_GRAFT ok" in out and text.startswith("line A\n")):
    fails.append(f"positive: counts={g['THUI_A9_COUNTS']} out={out!r}")
print("positive:", g["THUI_A9_COUNTS"], "| new element present:", b.NEW_ELEM in text)

# miss
g, text, out = run(graft, stub_module("a prompt without the element", True))
if not (text == "a prompt without the element" and g["THUI_A9_COUNTS"] == {"applied": 0, "miss": 1}
        and "THUI_A9_MISS first count=0" in out):
    fails.append(f"miss: counts={g['THUI_A9_COUNTS']} out={out!r}")
print("miss:", g["THUI_A9_COUNTS"])

# moved
try:
    run(graft, stub_module(prompt, False))
    fails.append("moved: the source assert did not fire")
    print("moved: NOT RED")
except AssertionError as e:
    print("moved: RED as required ->", e)

# control
c9 = cell9("thui-a9-ctl-smoke")
if not (b.CONTROL_MARK in c9 and "_a9_build_user_prompt" not in c9):
    fails.append("control: marker missing or wrapper present")
print("control: marker present:", b.CONTROL_MARK in c9, "| wrapper absent:", "_a9_build_user_prompt" not in c9)

if fails:
    print("TEETH FAIL:", *fails, sep="\n  ")
    sys.exit(1)
print("TEETH OK: positive, miss, moved, control -- 4 poles")
