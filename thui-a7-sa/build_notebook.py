"""thui-a7 -- the fast base (B69: Keith Tyser's Flash-Next serving under the June duck) with ONE line added: ACTION7 mapped (B76).

Why (2026-09-08, B73 / B74 read of thui-fast-v0 v2's own events). Six of the 25 public games offer `ACTION7` in their
valid-action set every turn (ar25, bp35, lf52, sb26, sk48, su15) and the harness cannot press it: `inference/agent/
action_names.py` maps ACTION1-6 + RESET only, so `to_engine_action("ACTION7")` is None and `solver.py` answers
`Unknown action at index i: 'ACTION7'` (executed=False) -- while `_engine_action_names` passes the same name into the
prompt's "Valid actions right now" line. The model tried it 30 times in that draw and on sb26 reasoned "maybe need
SPACE or ACTION7 to submit". What ACTION7 does in those games is unknown (arcengine 0.9.3: a SimpleAction, undocumented).

This build = thui-fast/build_notebook.py's three edits + the competition-mount resolver (B71's cells 5/15) + a cell-9
suffix that adds "ACTION7" to both maps in the imported module and asserts the round trip, + the smoke subset.
Everything else -- serving profile, watchdog, June solver bytes, 7920 s / 28 -- is his; the solver TREE is untouched
(the patch is applied to the module object after import, so the vendored bundle stays byte-identical).

Pre-registered read (smoke, sb26 / su15 / sk48 at 1800 s each):
  1. THUI_A7_PATCH ok in the log (teeth: to_engine_action / to_model_actions round-trip, solver uses the same function).
  2. events show >= 1 EXECUTED ACTION7 action (action_name == "ACTION7") on at least one of the three games -- the model
     already tries it unprompted; if it never executes, the patch did not reach the executor and the run measured nothing.
  3. PASS = any of the three games lands a level thui-fast-v0 v2 did not reach (sb26 > 1, su15 > 1, sk48 > 0) inside 1800 s,
     or an executed ACTION7 changes the board (board_changed True) on a level where every MOUSE click had not.
     FAIL = ACTION7 executes and never changes the board on any of the three -> a no-op in those games; the seam is cosmetic.
  4. Wall ~ 40 min; 0 slots.

Build:  PYTHONUTF8=1 python thui-a7-sa/build_notebook.py            -> taaf-thui-a7-v0.ipynb (smoke)
        PYTHONUTF8=1 python thui-a7-sa/build_notebook.py --full     -> taaf-thui-a7-v1.ipynb (25 games)
(lives in thui-a7-sa/ because thui-a7/ on master is Watchara's re-derivation of this build from the public kernel, #146;
         cell 0 still says thui-a7/ on purpose -- the pushed kernels carry that text and the builder must reproduce their bytes)
Push:   python scripts/kaggle_push_kernel.py <this dir>   (from arc-agi-pub; token = sahasawatt)
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAST = HERE.parent / "thui-fast"
SRC_NB = FAST / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
SRC_META = FAST / "upstream-kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
FULL = "--full" in sys.argv
SLUG = "thui-a7-v1" if FULL else "thui-a7-v0"
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
SMOKE_GAMES = ("sb26-7fbdac44", "su15-1944f8ab", "sk48-d8078629")   # the three ACTION7 games that stalled / scored 0 in thui-fast-v0 v2
SMOKE_CLOCK_S = 1800
COMP = "arc-prize-2026-arc-agi-3"
WHEELS_NESTED = "/kaggle/input/competitions/" + COMP + "/arc_agi_3_wheels"

sys.path.insert(0, str(FAST))
import build_notebook as fast  # noqa: E402  -- reuse the B69 header texts and cell-3 edit verbatim

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) — the fast base with ACTION7 mapped

**This is a Knowless Crew / Thuitanium fork, and the solver is not ours.** Same two upstreams as `thui-fast-v0`,
executed as they ship:

- **Serving**: Keith Tyser's [Duck Qwen3.8 Flash Next NVFP4 MTP](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp)
  — his pinned `RadixArk/Qwen3.8-Flash-Next-NVFP4` asset, offline vLLM runtime, NVFP4 PLE patch, MTP-3 profile, watchdog.
- **Solver**: the Tufa Labs duck harness (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
  Michal Tesnar, Stefano Viel) — his source bundle, executed unmodified on disk.
- **Weights**: RadixArk's NVFP4 quantisation of Qwen/Qwen3.8-Flash-Next (Qwen licence terms apply).

⚠️ Every score quoted by either upstream is theirs.

## What we changed

- **cell 0 / 1** — this header; Tufa's header reworded in the third person.
- **cell 3** — full diagnostics on an interactive public run, minimal in a real rerun.
- **cell 5 / 15** — the competition mount resolved (Kaggle serves two layouts).
- **cell 9** — after the solver tree is importable: `ACTION7` added to `inference.agent.action_names`'s two maps
  (the harness lists it as valid on six public games and could not execute it), with teeth asserting the round trip.
{"- **cell 15** — smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each." if not FULL else ""}

Build script: `thui-a7/build_notebook.py` in our agent repo (asserts exactly those cells changed). Ticket B76.
"""

CELL5_ANCHOR = '        "' + WHEELS_NESTED + '",\n'
CELL5_RESOLVER = """# thui-a7: resolve the competition mount instead of assuming its layout (Kaggle serves either
# /kaggle/input/competitions/<comp> or /kaggle/input/<comp>, varying between runs).
_COMP_CANDIDATES = ["/kaggle/input/competitions/__COMP__", "/kaggle/input/__COMP__"]
_COMP_DIR = next((_p for _p in _COMP_CANDIDATES if os.path.isdir(_p)), None)
assert _COMP_DIR is not None, "thui-a7: no competition mount found; /kaggle/input holds " + repr(
    sorted(os.listdir("/kaggle/input")) if os.path.isdir("/kaggle/input") else "MISSING")
_WHEELS = os.path.join(_COMP_DIR, "arc_agi_3_wheels")
assert os.path.isdir(_WHEELS), "thui-a7: resolved wheels dir is not a directory: " + _WHEELS
print("thui-a7: competition mount = " + _COMP_DIR, flush=True)
""".replace("__COMP__", COMP)

CELL9_SUFFIX = '''
# ---- thui-a7 (B76): map ACTION7 in the imported module. The solver tree on disk is untouched; solver.py and
# tool_agent.py import to_engine_action / to_model_actions by name and those read these dicts at call time.
assert "inference" not in sys.modules, "inference imported before the ACTION7 patch -- move the patch earlier"
import inference.agent.action_names as _an
assert _an.to_engine_action("ACTION7") is None, "upstream already maps ACTION7 -- this build is moot"
_an.ENGINE_TO_MODEL_ACTION["ACTION7"] = "ACTION7"
_an.MODEL_TO_ENGINE_ACTION["ACTION7"] = "ACTION7"
assert _an.to_engine_action("ACTION7") == "ACTION7" and _an.to_engine_action("action7") == "ACTION7"
assert _an.to_model_actions(["ACTION1", "ACTION7"]) == ["UP", "ACTION7"]
import inference.framework.solver as _solver
import inference.agent.tool_agent as _tool_agent
assert _solver.to_engine_action is _an.to_engine_action and _tool_agent.to_engine_action is _an.to_engine_action
import arcengine as _arcengine
assert _arcengine.GameAction.from_name("ACTION7") is _arcengine.GameAction.ACTION7
print(f"THUI_A7_PATCH ok engine_map={sorted(_an.ENGINE_TO_MODEL_ACTION)} solver={Path(_solver.__file__)}", flush=True)
'''

CELL15_MOUNT_OLD = 'competition_env_files = str(Path("' + WHEELS_NESTED + '").parent / "environment_files")'
CELL15_MOUNT_NEW = 'competition_env_files = str(Path(_COMP_DIR) / "environment_files")   # thui-a7: resolved in cell 5'
CELL15_EXTRA_OLD = '    if missing or extra:\n'
CELL15_EXTRA_NEW = '    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):   # thui-a7 smoke: a subset leaves extras by design\n'
CELL15_SELECT_OLD = '    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n'
CELL15_SELECT_SMOKE = (CELL15_SELECT_OLD +
                       f'    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-a7 smoke clock\n'
                       f'    print(f"thui-a7: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 18, f"{SRC_NB.name}: expected 18 cells, found {len(cells)}"
    before = ["".join(c["source"]) for c in cells]
    assert before[0].startswith("## About this fork") and before[1].startswith("# Tufa Labs ARC3 submission")

    def rep(i: int, old: str, new: str) -> None:
        s = "".join(cells[i]["source"])
        assert s.count(old) == 1, f"cell {i}: anchor not found exactly once ({s.count(old)}): {old[:70]!r}"
        cells[i]["source"] = s.replace(old, new).splitlines(keepends=True)

    cells[0]["cell_type"] = "markdown"; cells[0]["source"] = CELL0_MD.splitlines(keepends=True)
    cells[1]["source"] = fast.CELL1_MD.splitlines(keepends=True); cells[1].pop("attachments", None)
    rep(3, fast.CELL3_OLD, fast.CELL3_NEW.replace("thui-fast", "thui-a7"))
    rep(5, CELL5_ANCHOR, "        _WHEELS,\n")
    cells[5]["source"] = (CELL5_RESOLVER + "".join(cells[5]["source"])).splitlines(keepends=True)
    cells[9]["source"] = ("".join(cells[9]["source"]) + CELL9_SUFFIX).splitlines(keepends=True)
    rep(15, CELL15_MOUNT_OLD, CELL15_MOUNT_NEW)
    if not FULL:
        s = "".join(cells[15]["source"])
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        for g in SMOKE_GAMES:
            assert f'"{g}"' in m.group(0), f"{g} is not one of the 25 public ids"
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-a7 smoke subset\n")
        assert s.count("!= 25") == 2, s.count("!= 25")
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)")
        assert s.count(CELL15_EXTRA_OLD) == 1 and s.count(CELL15_SELECT_OLD) == 1
        s = s.replace(CELL15_EXTRA_OLD, CELL15_EXTRA_NEW).replace(CELL15_SELECT_OLD, CELL15_SELECT_SMOKE)
        cells[15]["source"] = s.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 1, 3, 5, 9, 15], f"cells changed {changed}"
    assert "attachments" not in cells[1] and "tufa_labs.png" not in json.dumps(nb)
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert after[0].startswith(f"# {SLUG} (Thuitanium / Knowless Crew)")
    assert after[0].index("Thuitanium") < min(after[0].index("Tufa Labs"), after[0].index("Keith Tyser"))
    for bad in ("Tufa Labs ARC3 submission", "our milestone-winning", "attachment:"):
        assert bad not in after[1]
    assert after[9].count("THUI_A7_PATCH") == 1 and after[7] == before[7] and after[11] == before[11]
    assert WHEELS_NESTED not in after[5] and WHEELS_NESTED not in after[15]
    assert ("smoke" in after[15]) == (not FULL)

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(SRC_META.read_text(encoding="utf-8")); meta.pop("id_no", None)
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"]
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, smoke={not FULL}")


if __name__ == "__main__":
    main()
