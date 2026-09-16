"""thui-cap -- the fast base (B69) with ONE knob set: a per-turn completion cap, LOCAL_ANALYZER_MAX_OUTPUT (B75).

Why (2026-09-09, B72/B74 read of thui-fast-v0 v2). Three games spent 270-320 s and 3-4 k generated tokens per action (bp35 d1,
r11l d2, lp85 d1: 25-30 actions in 7,920 s), and the deep-tail games that reached their last level with < 2,000 s left (tr87 L5,
lp85 L6, sc25 L4) had burned the wall on the levels before it. The June solver sends NO max_tokens (tool_agent.py:137
`_LOCAL_ANALYZER_MAX_OUTPUT = _get_env_int(..., 0)` -> server default) with thinking on, so one turn can run to the 32 k context.
V2's per-turn output (reasoning + content chars, 1,331 turns): p50 2,415 / p90 8,929 / p95 11,905 / max 32,473 chars
(~3.5 chars per token -> p90 ~2.5 k tok, p95 ~3.4 k tok); finish_reason=length occurred 5 times.

This build = thui-fast's three edits + the competition-mount resolver (B71 cells 5/15) + a cell-9 suffix that persists
LOCAL_ANALYZER_MAX_OUTPUT=3072 into his analyzer env after serving_setup.py and before the first `inference` import
(tool_agent reads it at import time), with teeth. Nothing else changes: no ACTION7 patch (B76 read in band), seed/yield his.

Pre-registered read (smoke, bp35 / r11l / lp85 at 1800 s each):
  1. THUI_CAP ok in the log with max_output=3072; the analyzer's request payloads carry max_tokens 3072 (prompts/*.log).
  2. Cost side: turns ending finish_reason=length <= 15 % of turns on the three games (V2: 5 of 1,331 overall). Above that the cap
     is eating tool calls, and the run measured a broken turn shape, not a faster one.
  3. PASS = actions on the three games >= 1.5x V2's count in the same games' first 1,800 s (V2: bp35 ?, r11l ?, lp85 ? -- read from
     V2's history at wallclock <= 1800 s when the smoke lands) AND levels >= V2's at 1,800 s on each; FAIL = actions up, levels down
     (the thinking was buying the level), or actions not up (time was not in generation).
  4. Wall ~40 min; 0 slots.

Build:  PYTHONUTF8=1 python thui-cap/build_notebook.py            -> taaf-thui-cap-v0.ipynb (smoke)
        PYTHONUTF8=1 python thui-cap/build_notebook.py --full     -> taaf-thui-cap-v1.ipynb (25 games)
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
CONTROL = "--control" in sys.argv   # same three games, same 3-way smoke clock, NO cap: the concurrency-matched baseline
assert not (FULL and CONTROL)
SLUG = "thui-cap-v1" if FULL else ("thui-cap-ctl" if CONTROL else "thui-cap-v0")
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
MAX_OUTPUT = 0 if CONTROL else 3072   # 0 = the June default (no max_tokens sent); the control persists nothing
SMOKE_GAMES = ("bp35-0a0ad940", "r11l-495a7899", "lp85-305b61c3")   # the three thinking-bound games of the B72 census
SMOKE_CLOCK_S = 1800
COMP = "arc-prize-2026-arc-agi-3"
WHEELS_NESTED = "/kaggle/input/competitions/" + COMP + "/arc_agi_3_wheels"

sys.path.insert(0, str(FAST))
import build_notebook as fast  # noqa: E402

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) — the fast base with a per-turn completion cap

**This is a Knowless Crew / Thuitanium fork, and the solver is not ours.** Same two upstreams as `thui-fast-v0`, executed as they ship:

- **Serving**: Keith Tyser's [Duck Qwen3.8 Flash Next NVFP4 MTP](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp)
  — his pinned `RadixArk/Qwen3.8-Flash-Next-NVFP4` asset, offline vLLM runtime, NVFP4 PLE patch, MTP-3 profile, watchdog.
- **Solver**: the Tufa Labs duck harness (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
  Michal Tesnar, Stefano Viel) — his source bundle, executed unmodified.
- **Weights**: RadixArk's NVFP4 quantisation of Qwen/Qwen3.8-Flash-Next (Qwen licence terms apply).

⚠️ Every score quoted by either upstream is theirs.

## What we changed

- **cell 0 / 1** — this header; Tufa's header reworded in the third person.
- **cell 3** — full diagnostics on an interactive public run, minimal in a real rerun.
- **cell 5 / 15** — the competition mount resolved (Kaggle serves two layouts).
- **cell 9** — `LOCAL_ANALYZER_MAX_OUTPUT={MAX_OUTPUT}` persisted into the analyzer env after his serving setup and before the
  solver is imported (the June solver sends no `max_tokens`), with teeth asserting the module read it.
{"- **cell 15** — smoke: " + ", ".join(SMOKE_GAMES) + f" at {SMOKE_CLOCK_S} s each." if not FULL else ""}

Build script: `thui-cap/build_notebook.py` in our agent repo (asserts exactly those cells changed). Ticket B75.
"""

CELL5_ANCHOR = '        "' + WHEELS_NESTED + '",\n'
CELL5_RESOLVER = """# thui-cap: resolve the competition mount instead of assuming its layout (Kaggle serves either
# /kaggle/input/competitions/<comp> or /kaggle/input/<comp>, varying between runs).
_COMP_CANDIDATES = ["/kaggle/input/competitions/__COMP__", "/kaggle/input/__COMP__"]
_COMP_DIR = next((_p for _p in _COMP_CANDIDATES if os.path.isdir(_p)), None)
assert _COMP_DIR is not None, "thui-cap: no competition mount found; /kaggle/input holds " + repr(
    sorted(os.listdir("/kaggle/input")) if os.path.isdir("/kaggle/input") else "MISSING")
_WHEELS = os.path.join(_COMP_DIR, "arc_agi_3_wheels")
assert os.path.isdir(_WHEELS), "thui-cap: resolved wheels dir is not a directory: " + _WHEELS
print("thui-cap: competition mount = " + _COMP_DIR, flush=True)
""".replace("__COMP__", COMP)

CELL9_SET = f'''_persisted["LOCAL_ANALYZER_MAX_OUTPUT"] = "{MAX_OUTPUT}"
SETUP_ENV_PATH.write_text(json.dumps(_persisted, indent=2, sort_keys=True) + "\\n")
os.environ["LOCAL_ANALYZER_MAX_OUTPUT"] = "{MAX_OUTPUT}"
''' if not CONTROL else '''# thui-cap CONTROL: no cap is set; the env is left exactly as his serving_setup persisted it.
assert str(os.environ.get("LOCAL_ANALYZER_MAX_OUTPUT", "0")) == "0", os.environ.get("LOCAL_ANALYZER_MAX_OUTPUT")
'''
CELL9_SUFFIX = f'''
# ---- thui-cap (B75): a per-turn completion cap, set AFTER his serving_setup persisted the analyzer env and BEFORE any
# `inference` import (tool_agent reads LOCAL_ANALYZER_MAX_OUTPUT at import time). Nothing else in the env is touched.
_persisted = json.loads(SETUP_ENV_PATH.read_text())
assert _persisted.get("LOCAL_ANALYZER_MODEL_ID") == "Qwen/Qwen3.8-Flash-Next-NVFP4", _persisted.get("LOCAL_ANALYZER_MODEL_ID")
# his serving_setup persists the key with the June default "0" (= no max_tokens sent); anything else is a cap we did not price
assert str(_persisted.get("LOCAL_ANALYZER_MAX_OUTPUT", "0")) == "0", "his setup now persists a cap -- re-derive this build: " + repr(_persisted.get("LOCAL_ANALYZER_MAX_OUTPUT"))
{CELL9_SET}assert "inference" not in sys.modules, "solver imported before the cap override"
import inference.agent.tool_agent as _tool_agent
assert _tool_agent._LOCAL_ANALYZER_MAX_OUTPUT == {MAX_OUTPUT}, _tool_agent._LOCAL_ANALYZER_MAX_OUTPUT
assert _tool_agent._LOCAL_ANALYZER_ENABLE_THINKING is True
print(f"THUI_CAP ok max_output={{_tool_agent._LOCAL_ANALYZER_MAX_OUTPUT}} thinking={{_tool_agent._LOCAL_ANALYZER_ENABLE_THINKING}} "
      f"yield={{_tool_agent._LOCAL_ANALYZER_YIELD_SECONDS}} seed={{_tool_agent._LOCAL_ANALYZER_SEED}} model={{os.environ['LOCAL_ANALYZER_MODEL_ID']}}", flush=True)
'''

CELL15_MOUNT_OLD = 'competition_env_files = str(Path("' + WHEELS_NESTED + '").parent / "environment_files")'
CELL15_MOUNT_NEW = 'competition_env_files = str(Path(_COMP_DIR) / "environment_files")   # thui-cap: resolved in cell 5'
CELL15_EXTRA_OLD = '    if missing or extra:\n'
CELL15_EXTRA_NEW = '    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):   # thui-cap smoke: a subset leaves extras by design\n'
CELL15_SELECT_OLD = '    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n'
CELL15_SELECT_SMOKE = (CELL15_SELECT_OLD +
                       f'    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-cap smoke clock\n'
                       f'    print(f"thui-cap: smoke {{len(bm.games)}} games @ {{bm.solver.max_runtime_s_per_game}} s", flush=True)\n')


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 18, f"{SRC_NB.name}: expected 18 cells, found {len(cells)}"
    before = ["".join(c["source"]) for c in cells]
    assert before[0].startswith("## About this fork") and before[1].startswith("# Tufa Labs ARC3 submission")
    assert "SETUP_ENV_PATH" in before[9], "cell 9 no longer persists the analyzer env at SETUP_ENV_PATH"

    def rep(i: int, old: str, new: str) -> None:
        s = "".join(cells[i]["source"])
        assert s.count(old) == 1, f"cell {i}: anchor not found exactly once ({s.count(old)}): {old[:70]!r}"
        cells[i]["source"] = s.replace(old, new).splitlines(keepends=True)

    cells[0]["cell_type"] = "markdown"; cells[0]["source"] = CELL0_MD.splitlines(keepends=True)
    cells[1]["source"] = fast.CELL1_MD.splitlines(keepends=True); cells[1].pop("attachments", None)
    rep(3, fast.CELL3_OLD, fast.CELL3_NEW.replace("thui-fast", "thui-cap"))
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
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-cap smoke subset\n")
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
    assert after[9].count("THUI_CAP") == 1 and "ACTION7" not in after[9] and after[7] == before[7] and after[11] == before[11]
    assert WHEELS_NESTED not in after[5] and WHEELS_NESTED not in after[15]
    assert ("smoke" in after[15]) == (not FULL)

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(SRC_META.read_text(encoding="utf-8")); meta.pop("id_no", None)
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"]
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, smoke={not FULL}, max_output={MAX_OUTPUT}")


if __name__ == "__main__":
    main()
