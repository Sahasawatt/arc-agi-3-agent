"""thui-a9: B81 (thui-a5 KV7/MTP0/seqs28) with the `World model:` line REQUIRED every turn. One change.

Design: workspace notes/DESIGN-textual-world-model-experiment-2026-09-19.md, arm A1'(a), option 1 (§5a).
The chassis already keeps seven world-model slots, parsed from the assistant's VISIBLE text and re-injected
every turn; writing them is optional ("Helpful optional prefixes are ..."), and B81 wrote `World model:` in
216 of 1,753 responses. This build makes that one line required.

Mechanism: ONE wrapper on the IMPORTED `ToolAgent._build_user_prompt` (cell 9, after the solver import;
solver tree on disk untouched). It swaps one prompt element, asserted present verbatim: B81's own prompts
carry it in 1,087 of 1,087 transcript user prompts, 25/25 games. The retry prompt inside `analyze()` (a
358-line method, `tool_agent.py:2302` @ 01e36e6) is NOT touched: recompiling it is riskier than the lever.
--control: identical notebook, no wrapper, marker `THUI_A9_GRAFT control`.

Build:  python3 thui-a9/build_notebook.py --smoke            -> out/thui-a9-wmreq-smoke
        python3 thui-a9/build_notebook.py --smoke --control  -> out/thui-a9-ctl-smoke
        python3 thui-a9/build_notebook.py [--control] [--run=N] -> out/thui-a9-{wmreq,ctl}-full25-rN
Teeth:  python3 thui-a9/test_a9_graft.py   (0 GPU: executes the GRAFT source against a stub)
Push:   python3 scripts/kaggle_push_kernel.py <out dir>   (from the workspace repo)
"""
import ast
import copy
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "thui-a5-mtp0k7s28-full25-r1.ipynb"
SRC_META = HERE.parent / "thui-a5" / "out" / "thui-a5-mtp0k7s28-full25-r1" / "kernel-metadata.json"
SMOKE = "--smoke" in sys.argv[1:]
CONTROL = "--control" in sys.argv[1:]
RUN = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--run=")), "1")
ARM = "ctl" if CONTROL else "wmreq"
SLUG = f"thui-a9-{ARM}-smoke" if SMOKE else f"thui-a9-{ARM}-full25-r{RUN}"
SMOKE_GAMES = ("tn36-ef4dde99", "vc33-5430563c", "bp35-0a0ad940")   # the thui-a3 / a6 / rank2 smoke set
SMOKE_CLOCK_S = 1800
C15_EXTRA_OLD = "    if missing or extra:\n"
C15_EXTRA_NEW = "    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):   # thui-a9 smoke: a subset leaves extras by design\n"
C15_SELECT = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"
OUT = HERE / "out" / SLUG

IMPORT_ANCHOR = "import inference.agent.tool_agent as _tool_agent\n"

OLD_ELEM = ("If you include assistant text before a tool call, keep it short and use it to update the world model. "
            "Helpful optional prefixes are `World model:`, `Goal model:`, `Action model:`, `Recent findings:`, "
            "`Open questions:`, `Plan:`, and `Cross-level notes:`.")
NEW_ELEM = ("Before every tool call, write short assistant text whose first line starts with `World model:` and "
            "states, in one or two sentences, your current best model of how this level works; revise it whenever "
            "the evidence changes. This `World model:` line is required on every turn. Other optional prefixes are "
            "`Goal model:`, `Action model:`, `Recent findings:`, `Open questions:`, `Plan:`, and `Cross-level notes:`.")

GRAFT = f'''# ---- thui-a9: the `World model:` line REQUIRED every turn (one wrapper on the imported prompt builder).
import inspect as _inspect
_A9_OLD = {OLD_ELEM!r}
_A9_NEW = {NEW_ELEM!r}
_A9_CLS = _tool_agent.ToolAgent
assert _inspect.getsource(_A9_CLS._build_user_prompt).count(_A9_OLD.split(". ")[1][:40]) == 1, \\
    "thui-a9: the optional-prefix element moved in _build_user_prompt -- re-derive"
_a9_orig = _A9_CLS._build_user_prompt
THUI_A9_COUNTS = {{"applied": 0, "miss": 0}}


def _a9_build_user_prompt(self, *args, **kwargs):
    text = _a9_orig(self, *args, **kwargs)
    if text.count(_A9_OLD) != 1:
        THUI_A9_COUNTS["miss"] += 1
        if THUI_A9_COUNTS["miss"] == 1:
            print(f"THUI_A9_MISS first count={{text.count(_A9_OLD)}}", flush=True)
        return text
    THUI_A9_COUNTS["applied"] += 1
    if THUI_A9_COUNTS["applied"] == 1:
        print("THUI_A9_APPLIED first", flush=True)
    return text.replace(_A9_OLD, _A9_NEW)


_a9_build_user_prompt.__wrapped__ = _a9_orig
_A9_CLS._build_user_prompt = _a9_build_user_prompt
assert _A9_CLS._build_user_prompt is _a9_build_user_prompt, "thui-a9: wrapper not installed"
print(f"THUI_A9_GRAFT ok cls={{_A9_CLS.__module__}}.{{_A9_CLS.__name__}} file={{_tool_agent.__file__}}", flush=True)
'''
CONTROL_MARK = 'print("THUI_A9_GRAFT control (no wrapper; prompt unchanged)", flush=True)\n'

CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — the B81 anim build, {"CONTROL (unchanged)" if CONTROL else "`World model:` line required every turn"}

{"**Smoke: 3 games at 1800 s. Numbers are not a score.**" if SMOKE else "Full public 25."}

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts, clock, games and the vLLM profile
(KV 7 GiB / MTP 0 / max_num_seqs 28) are exactly `thui-a5-mtp0k7s28-full25-r1`. {"Nothing changes: this is the same-day control for `thui-a9-wmreq`." if CONTROL else "One prompt element changes: the optional world-model prefixes become one REQUIRED `World model:` line per turn, via a wrapper on the imported prompt builder in cell 9."}

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp), harness by
[Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), anim solver
bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""


def patch_cell9(s9: str) -> str:
    assert s9.count(IMPORT_ANCHOR) == 1, f"cell 9 anchor moved -- re-derive: {IMPORT_ANCHOR!r}"
    return s9.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + (CONTROL_MARK if CONTROL else GRAFT))


def main():
    nb = json.load(open(SRC_NB))
    orig = copy.deepcopy(nb)
    cells = nb["cells"]
    assert "Knowless Crew" in "".join(cells[0]["source"])
    cells[0]["source"] = CELL0.splitlines(keepends=True)
    cells[9]["source"] = patch_cell9("".join(cells[9]["source"])).splitlines(keepends=True)
    if SMOKE:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        assert all(f'"{g}"' in m.group(0) for g in SMOKE_GAMES)
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-a9 smoke subset\n")
        assert s.count("!= 25") == 2 and s.count(C15_EXTRA_OLD) == 1 and s.count(C15_SELECT) == 1
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)").replace(C15_EXTRA_OLD, C15_EXTRA_NEW).replace(
            C15_SELECT, C15_SELECT + f"    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-a9 smoke clock\n"
            '    print(f"thui-a9: smoke {len(bm.games)} games @ {bm.solver.max_runtime_s_per_game} s", flush=True)\n')
        cells[15]["source"] = s.splitlines(keepends=True)
        compile(s, "cell15", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    changed = [i for i, (a, b) in enumerate(zip(orig["cells"], cells)) if a != b]
    assert changed == ([0, 9, 15] if SMOKE else [0, 9]), changed
    assert len(orig["cells"]) == len(cells)
    compile("".join(cells[9]["source"]), "cell9", "exec")
    meta = json.load(open(SRC_META))
    meta.update(id=f"yocybercode/{SLUG}", title=SLUG, code_file=f"{SLUG}.ipynb", is_private=True)
    assert meta["id"].startswith("yocybercode/")
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(nb, open(OUT / f"{SLUG}.ipynb", "w"), indent=1)
    json.dump(meta, open(OUT / "kernel-metadata.json", "w"), indent=2)
    print(f"built {SLUG}: cells changed {changed}, id {meta['id']}, private, datasets={meta['dataset_sources']}")


if __name__ == "__main__":
    main()
