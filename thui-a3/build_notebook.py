#!/usr/bin/env python3
"""thui-a3 -- A3: an executable world model the agent writes, keeps across python calls, and verifies against recorded
transitions. Base: the B71 anim build (thui-anim-fast/thui-animfast-b71-full25-r1.ipynb), serving profile unchanged.

Evidence that motivated it (2026-09-16 think-research, SYNTHESIS.md): arXiv 2605.05138 / 2607.15439 / Tycho -- frontier API
models on the public 25 gain from an agent-authored executable model + replay verification; the ablation also says model
capability moves more than the variant, so the prior on a local model is low-medium. Our own B26/B27 found the goal model
usually right and the TRANSITION model wrong -- verification targets exactly that.

Edits: cell 0 (header), cell 13 (graft + teeth + install appended after the settings), smoke only: cell 15 (3 games @ 1800 s,
the thui-l1/thui-rank2 recipe). Graft source: a3_graft.py, a3_teeth.py, a3_install.py (plain files, no f-string escaping).

Build:  python3 thui-a3/build_notebook.py [--full] [--suffix=-r1]
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ARG = {a.split("=", 1)[0]: (a.split("=", 1)[1] if "=" in a else True) for a in sys.argv[1:]}
FULL = bool(ARG.get("--full"))
SUFFIX = ARG.get("--suffix", "")
SLUG = "thui-a3-wm-" + ("full25" if FULL else "smoke") + SUFFIX
OUT_DIR = HERE / "out" / SLUG
OUT_NB = OUT_DIR / f"{SLUG}.ipynb"
SMOKE_GAMES = ("tn36-ef4dde99", "vc33-5430563c", "bp35-0a0ad940")
SMOKE_CLOCK_S = 1800

GRAFT = (HERE / "a3_graft.py").read_text() + "\n" + (HERE / "a3_teeth.py").read_text() + "\n" + (HERE / "a3_install.py").read_text()

CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — A3: an executable world model, kept and verified

**This is a Knowless Crew / Thuitanium experiment notebook.** It is `thui-animfast-b71-full25-r1` with one change in
cell 13: the agent may save a Python world model (`WORLD_MODEL = '''...'''`) that is loaded at the top of every later
python call, and `verify_world_model()` replays recorded transitions through its `predict(rows, action)`. A short block
appended to each user prompt explains this and reports the model's status. Serving profile, solver and clock unchanged.
{"Smoke: 3 games at 1800 s." if not FULL else "Full public 25."}

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp), harness by
[Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), anim solver
bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`. Idea after arXiv 2605.05138 / 2607.15439 and NIMI's Tycho.
"""

C15_EXTRA_OLD = "    if missing or extra:\n"
C15_EXTRA_NEW = "    if missing or (extra and len(PUBLIC_GAME_IDS) == 25):   # thui-a3 smoke: a subset leaves extras by design\n"
C15_SELECT = "    bm.games = [offline_by_id[game_id] for game_id in PUBLIC_GAME_IDS]\n"


def main() -> None:
    nb = json.loads((REPO / "thui-anim-fast" / "thui-animfast-b71-full25-r1.ipynb").read_text(encoding="utf-8"))
    meta = json.loads((REPO / "thui-anim-fast" / "kernel-metadata.json").read_text(encoding="utf-8"))
    assert meta["id"] == "yocybercode/thui-animfast-b71-full25-r1"
    cells = nb["cells"]
    assert len(cells) == 18, len(cells)
    before = ["".join(c["source"]) for c in cells]
    assert before[13].startswith("# Exact public-25 and competition settings.") and "concurrency = 28" in before[13]
    assert "THUI_ANIMFAST_GRAFT ok" in before[9] and "import inference.agent.tool_agent as _tool_agent" in before[9]

    cells[0]["cell_type"] = "markdown"
    cells[0]["source"] = CELL0.splitlines(keepends=True)
    cells[13]["source"] = (before[13].rstrip("\n") + "\n\n" + GRAFT).splitlines(keepends=True)
    if not FULL:
        s = before[15]
        m = re.search(r"PUBLIC_GAME_IDS = tuple\(\[\n(?:    \"[a-z0-9]{4}-[0-9a-f]{8}\",?\n){25}\]\)\n", s)
        assert m, "cell 15: the 25-game PUBLIC_GAME_IDS tuple not found"
        assert all(f'"{g}"' in m.group(0) for g in SMOKE_GAMES)
        s = s.replace(m.group(0), "PUBLIC_GAME_IDS = tuple(" + repr(list(SMOKE_GAMES)) + ")   # thui-a3 smoke subset\n")
        assert s.count("!= 25") == 2 and s.count(C15_EXTRA_OLD) == 1 and s.count(C15_SELECT) == 1
        s = s.replace("!= 25", "!= len(PUBLIC_GAME_IDS)").replace(C15_EXTRA_OLD, C15_EXTRA_NEW).replace(
            C15_SELECT, C15_SELECT + f"    bm.solver.max_runtime_s_per_game = {SMOKE_CLOCK_S}.0   # thui-a3 smoke clock\n"
            '    print(f"thui-a3: smoke {len(bm.games)} games @ {bm.solver.max_runtime_s_per_game} s", flush=True)\n')
        cells[15]["source"] = s.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == ([0, 13] if FULL else [0, 13, 15]), changed
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    a0 = after[0]
    assert a0.startswith(f"# {SLUG} (Thuitanium / Knowless Crew)") and a0.index("Thuitanium") < min(a0.index("Tufa Labs"), a0.index("Keith Tyser"))
    assert after[13].count("THUI_A3_GRAFT ok") == 1 and after[13].count("\n_a3_teeth()\n") == 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta.update(id=f"yocybercode/{SLUG}", title=SLUG, code_file=OUT_NB.name, is_private=True)
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    (OUT_DIR / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, private, datasets={meta['dataset_sources']}")


if __name__ == "__main__":
    main()
