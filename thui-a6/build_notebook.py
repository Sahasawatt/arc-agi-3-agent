"""thui-a6: B81 (thui-a5 KV7/MTP0/seqs28) with the analyzer context 32,768 -> 65,536. One change.

His serving_setup.py hardcodes `ANALYZER_CONTEXT = 32_768` (line 129): it feeds vLLM `--max-model-len`
and the persisted `LOCAL_ANALYZER_CONTEXT_WINDOW`. The bundle is a read-only Kaggle input and the script
checks its own sha256 against SOURCE_IDENTITY.json, so cell 9 builds an overlay bundle in
/kaggle/working: every top-level entry symlinked, serving_setup.py patched, SOURCE_IDENTITY.json
re-stamped with the patched sha. BUNDLE_DIR then points at the overlay.
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
SLUG = "thui-a6-ctx64-smoke" if SMOKE else "thui-a6-ctx64-full25-r1"
SMOKE_GAMES = ("tn36-ef4dde99", "vc33-5430563c", "bp35-0a0ad940")   # the thui-a3 / thui-rank2 smoke set
SMOKE_CLOCK_S = 1800
C15_EXTRA_OLD = "    if missing or extra:\n"
C15_EXTRA_NEW = "    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):   # thui-a6 smoke: a subset leaves extras by design\n"
C15_SELECT = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"
OUT = HERE / "out" / SLUG

ANCHOR = "# Solver setup commands (wheels, vLLM server startup, ...) run before the benchmark loads.\n"

OVERLAY = '''# ---- thui-a6: analyzer context 32,768 -> 65,536 via an overlay bundle (his constant is not an env knob).
import hashlib as _hashlib
import shutil as _shutil
THUI_A6_CTX = 65_536
_A6_OLD = "ANALYZER_CONTEXT = 32_768\\n"
_A6_NEW = f"ANALYZER_CONTEXT = {THUI_A6_CTX:_}\\n"
_a6_src = BUNDLE_DIR
_a6_dir = WORKING_DIR / "thui-a6-bundle-overlay"
if _a6_dir.exists():
    _shutil.rmtree(_a6_dir)
_a6_dir.mkdir(parents=True)
for _e in _a6_src.iterdir():
    if _e.name not in ("serving_setup.py", "SOURCE_IDENTITY.json"):
        (_a6_dir / _e.name).symlink_to(_e)
_a6_text = (_a6_src / "serving_setup.py").read_text()
assert _a6_text.count(_A6_OLD) == 1, "thui-a6: ANALYZER_CONTEXT literal moved -- re-derive"
_a6_text = _a6_text.replace(_A6_OLD, _A6_NEW)
(_a6_dir / "serving_setup.py").write_text(_a6_text)
_a6_ident = json.loads((_a6_src / "SOURCE_IDENTITY.json").read_text())
assert _a6_ident["serving_setup_sha256"] == _hashlib.sha256((_a6_src / "serving_setup.py").read_bytes()).hexdigest(), \\
    "thui-a6: source identity did not match the ORIGINAL setup -- refusing to re-stamp"
_a6_ident["serving_setup_sha256"] = _hashlib.sha256((_a6_dir / "serving_setup.py").read_bytes()).hexdigest()
(_a6_dir / "SOURCE_IDENTITY.json").write_text(json.dumps(_a6_ident, indent=2, sort_keys=True) + "\\n")
BUNDLE_DIR = _a6_dir
print(f"THUI_A6_OVERLAY ok ctx={THUI_A6_CTX} bundle={BUNDLE_DIR} src={_a6_src}", flush=True)

'''

TEETH_ANCHOR = "_persisted = json.loads(SETUP_ENV_PATH.read_text())\n"
TEETH = '''assert _persisted.get("LOCAL_ANALYZER_CONTEXT_WINDOW") == str(THUI_A6_CTX), (
    "thui-a6: serving_setup did not persist the patched context", _persisted.get("LOCAL_ANALYZER_CONTEXT_WINDOW"))
'''
IMPORT_ANCHOR = "import inference.agent.tool_agent as _tool_agent\n"
IMPORT_TEETH = '''assert int(getattr(_tool_agent, "_LOCAL_ANALYZER_CONTEXT_WINDOW", -1)) == THUI_A6_CTX, (
    "thui-a6: solver did not pick up the patched context", getattr(_tool_agent, "_LOCAL_ANALYZER_CONTEXT_WINDOW", None))
print(f"THUI_A6_CTX ok solver_window={_tool_agent._LOCAL_ANALYZER_CONTEXT_WINDOW}", flush=True)
'''

CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — the B81 anim build with a 65,536-token analyzer context

{"**Smoke: 3 games at 1800 s. Numbers are not a score.**" if SMOKE else "Full public 25."}

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts, clock, games and the vLLM profile
(KV 7 GiB / MTP 0 / max_num_seqs 28) are exactly `thui-a5-mtp0k7s28-full25-r1`. Only the analyzer context
changes, 32,768 -> 65,536, applied through an overlay copy of the serving bundle in cell 9.

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp), harness by
[Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), anim solver
bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""


def patch_cell9(s9: str) -> str:
    for anchor in (ANCHOR, TEETH_ANCHOR, IMPORT_ANCHOR):
        assert s9.count(anchor) == 1, f"cell 9 anchor moved -- re-derive: {anchor!r}"
    s9 = s9.replace(ANCHOR, OVERLAY + ANCHOR)
    s9 = s9.replace(TEETH_ANCHOR, TEETH_ANCHOR + TEETH)
    s9 = s9.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_TEETH)
    return s9


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
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-a6 smoke subset\n")
        assert s.count("!= 25") == 2 and s.count(C15_EXTRA_OLD) == 1 and s.count(C15_SELECT) == 1
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)").replace(C15_EXTRA_OLD, C15_EXTRA_NEW).replace(
            C15_SELECT, C15_SELECT + f"    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-a6 smoke clock\n"
            '    print(f"thui-a6: smoke {len(bm.games)} games @ {bm.solver.max_runtime_s_per_game} s", flush=True)\n')
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
