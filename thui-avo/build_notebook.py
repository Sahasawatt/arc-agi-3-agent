#!/usr/bin/env python3
"""thui-avo-v0 -- the AVO arm: Tufa's 08-31 bundle, run as they ship it.

WHY THIS ARM EXISTS. Every optimisation axis inside the duck harness is closed by
measurement (MAP B8..B58), and at the live bar the shrink arithmetic needs public ~12 --
unreachable by any closed axis. The one externally-evidenced mean-mover left is the
upstream's own AVO agent: `jakobbrggen/taaf-kaggle-source` (branch `experiment/avo`,
git_status clean @ 49720d3) ships `deploy_target.pkl` with **avo_agent=True**, i.e. the
bundle IS Tufa's AVO Kaggle run, published as they run it. AvoAgent subclasses ToolAgent
with durable memory + inspect/plan/implement/evaluate + a stagnation supervisor
(notes/tufa-current-vs-fork-2026-09-01.md). Precedent: duck-v10's own 2.41 -> 4.55 came
from adopting a newer upstream bundle and DELETING fork patches -- this build repeats
that move on the next bundle.

WHAT THE BUILD IS. thui-v1-1 byte-for-byte except:
  cell 0  markdown (attribution, what this run is)
  cell 6  DATASET_SOURCES[0]: taaf-kaggle-source-anim-20260807-anim -> taaf-kaggle-source
  cell 8  the v10-exactness upscale tooth is RELAXED to a print (see below)
Everything else inherits: the seed pin and the wheelhouse.

⚠️ THE LIVE DATASET MOVES UNDER YOU. v0's first push died on the inherited tooth
`'MULTIMODAL_UPSCALE': '4'` even though the locally-diffed copy carried '4' -- because
`taaf-kaggle-source` had been re-versioned since that diff: the mounted LATEST is branch
`experiment/avo-v2` @ 74ff3df ("pin the kaggle-avo arm to the control run's model"),
which sets MULTIMODAL_UPSCALE '8' + MULTIMODAL_GRID_LINES '1' AND natively pins
`jakobbrggen/qwen3-8-27b-fp8-hf-snapshot` / `SERVED_MODEL_NAME = 'Qwen/Qwen3.8-27B-FP8'`
-- the exact model our fork used to swap in by hand. Consequences:
  * the three model .replace() calls in cell 8 now find nothing and no-op, which is
    CORRECT (their asserts test the negative and still hold);
  * the seed-pin anchor and temperature 0.6 survive verbatim (verified on the live
    bytes, count 1 each);
  * the upscale pin is upstream's own v2 setting paired with their vision handling, so
    for an as-shipped arm it must not be pinned back to 4 -- the builder swaps that
    assert for a print of the value actually in force.
Makefile pins unchanged live-vs-0831; avo package still imports only the bundle's own
`inference` package -- the wheelhouse suffices.

WHAT A FAILURE LOOKS LIKE. The chassis is proven; the new variable is the whole bundle.
If it dies it dies in setup/serve (first ~15 min), which is cheap. A completed run is a
25-game public number to rank against v10cal with eval/rank_runs.py -- and per B37/B58,
ONE run ranks nothing inside the same-build band; only outside [2.82, 5.24] does a single
draw speak.

    python3 build_notebook.py    # writes taaf-thui-avo-v0.ipynb + kernel-metadata.json
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SRC_NB = REPO / "thuiv1" / "v1-1" / "taaf-thui-v1-1.ipynb"
OUT_NB = HERE / "taaf-thui-avo-v0.ipynb"
OWNER = "sahasawatt"
SLUG = "thui-avo-v0"

OLD_BUNDLE = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
NEW_BUNDLE = "jakobbrggen/taaf-kaggle-source"

# The inherited v10-exactness tooth, verbatim from thui-v1-1's cell 8. For the AVO arm
# upstream's own value must stand (avo-v2 ships upscale 8 + grid lines 1), so the assert
# becomes a report of what is in force.
UPSCALE_TOOTH = (
    '    assert "\'MULTIMODAL_UPSCALE\': \'4\'" in command, (\n'
    '        "thui-v1-1 TEETH FAIL: upscale must stay 4 (v10 exact, B23 measured in-noise)"\n'
    '    )\n'
)
UPSCALE_REPORT = (
    "    _ups = re.search(r\"'MULTIMODAL_UPSCALE': '([^']*)'\", command)\n"
    "    print(f\"thui-avo-v0: upstream MULTIMODAL_UPSCALE={_ups.group(1) if _ups else 'ABSENT'} \"\n"
    "          \"(as shipped -- deliberately not pinned to 4)\", flush=True)\n"
)

CELL0_MD = """# thui-avo-v0 (Thuitanium / Knowless Crew) — the upstream AVO bundle, unmodified, on the thui chassis

**This kernel swaps ONE thing against `thui-v1-1`: the source bundle.**
`jakobbrggen/taaf-kaggle-source` (branch `experiment/avo`) ships `avo_agent=True` in its
own `deploy_target.pkl`, so the run executes Tufa's AVO agent — durable memory,
inspect/plan/implement/evaluate, stagnation supervisor — exactly as they publish it.
Sampler seed and the Qwen3.8-27B-FP8 model swap are inherited from `thui-v1-1` unchanged.

Solver credit: Tufa Labs (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
Michal Tesnar, Stefano Viel) — executed unmodified from their attached dataset. This is a
Knowless Crew / Thuitanium fork; none of their scores are ours.
"""


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 17, f"thui-v1-1 source expected 17 cells, found {len(cells)}"

    before = ["".join(c["source"]) for c in cells]

    cells[0]["source"] = CELL0_MD.splitlines(keepends=True)

    c6 = "".join(cells[6]["source"])
    assert c6.count(f'"{OLD_BUNDLE}"') == 1, "bundle slug not found exactly once in cell 6"
    assert NEW_BUNDLE + '"' not in c6, "cell 6 already carries the new bundle -- double build?"
    cells[6]["source"] = c6.replace(f'"{OLD_BUNDLE}"', f'"{NEW_BUNDLE}"').splitlines(keepends=True)

    c8 = "".join(cells[8]["source"])
    assert c8.count(UPSCALE_TOOTH) == 1, "upscale tooth not found verbatim in cell 8 -- source moved"
    c8 = c8.replace(UPSCALE_TOOTH, UPSCALE_REPORT)
    if "\nimport re\n" not in c8 and not c8.startswith("import re\n"):
        c8 = "import re\n" + c8
    cells[8]["source"] = c8.splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 6, 8], f"cells changed {changed}, expected [0, 6, 8]"

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads((REPO / "thuiv1" / "v1-1" / "kernel-metadata.json").read_text(encoding="utf-8"))
    meta["id"] = f"{OWNER}/{SLUG}"
    meta["title"] = SLUG
    meta["code_file"] = OUT_NB.name
    srcs = [NEW_BUNDLE if s == OLD_BUNDLE else s for s in meta["dataset_sources"]]
    assert NEW_BUNDLE in srcs and OLD_BUNDLE not in srcs, "metadata source swap failed"
    meta["dataset_sources"] = srcs
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}")
    print(f"dataset_sources: {srcs}")
    print("push with: python3 scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-avo  (from arc-agi-pub)")


if __name__ == "__main__":
    main()
