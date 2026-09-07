"""thui-fast-v0 -- Keith Tyser's Flash-Next serving stack under the unchanged duck solver, run on our slug.

Provenance (2026-09-07). The public kernel `keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp` is Tufa Labs'
June duck bundle (ARC3-Inference aa69123, solver.py / kaggle.py byte-identical to our anim bundle's) with
ONLY the model serving replaced: `RadixArk/Qwen3.8-Flash-Next-NVFP4` (~180B MoE, 512 experts / top-10,
NVFP4 experts, 1 MTP layer) on a pinned vLLM image with 3-token MTP speculative decoding, async
scheduling, chunked prefill, CUDA graphs, prefix caching off. Its latest public-25 log:

    mean 6.76 | 36 levels | 19/25 scoring | 3,695 actions (148/game) | wall 8,587 s

against our same-wall family (v10 band 4.55-4.71, thui-v1-1 5.24, clock2x 6.40 only at 2x the wall,
actions 1,285-1,697). n=1; same-build spread on this harness is ~0.4-0.5 public, so the number ranks
only after a second draw. The serving stack is the ONE axis this campaign never measured on Qwen3.8
(B6 -- the model swap -- is the only lever that ever moved the score).

What this build changes against the vendored upstream notebook (asserted below):
  cell 0  -- our identity first (G2), crediting Keith Tyser (serving), Tufa Labs (duck), RadixArk (weights)
  cell 1  -- Tufa's original header rewritten in the third person (the submit gate's hard markers: their
             "ARC3 submission" H1 and "our milestone-winning" are never legitimate under our slug); links kept
  cell 3  -- TAAF_MINIMAL_DIAGNOSTICS "1" -> "1" only under a real submission, so a public run writes the
             per-game usage / events / transcript sidecars every read instrument in eval/ expects
Everything else -- serving profile, watchdog, budget 7920 s / 28 concurrency, frozen scorer -- is his.

Build:  PYTHONUTF8=1 python thui-fast/build_notebook.py            (writes taaf-thui-fast-v0.ipynb + kernel-metadata.json)
Push:   python scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-fast   (from arc-agi-pub; token = sahasawatt)
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
SRC_META = HERE / "upstream-kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
SLUG = "thui-fast-v0"
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"

CELL0_MD = """# thui-fast-v0 (Thuitanium / Knowless Crew) — the duck solver on a faster serving stack

**This is a Knowless Crew / Thuitanium fork, and the solver is not ours.** Two upstreams, executed as
they ship:

- **Serving**: Keith Tyser's [Duck Qwen3.8 Flash Next NVFP4 MTP](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp)
  — the pinned `RadixArk/Qwen3.8-Flash-Next-NVFP4` checkpoint (his Kaggle model asset), his offline
  vLLM runtime, NVFP4 PLE patch, MTP-3 speculative decoding profile and server watchdog. This notebook
  is his, cell for cell, except the three edits listed below.
- **Solver**: the Tufa Labs duck harness (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
  Michal Tesnar, Stefano Viel) — mounted as his source bundle and executed unmodified.
- **Weights**: RadixArk's NVFP4 quantisation of Qwen/Qwen3.8-Flash-Next (Qwen licence terms apply).

⚠️ Every score quoted by either upstream is theirs. Nothing on this page reports their numbers as ours.

## What we changed

- **cell 0** — this header.
- **cell 1** — Tufa Labs' original header, reworded in the third person so no upstream claim reads as ours.
- **cell 3** — `TAAF_MINIMAL_DIAGNOSTICS` is `1` only inside a real competition rerun, so an interactive
  public-25 run writes the per-game usage / events / transcript sidecars our read instruments expect.

Build script: `thui-fast/build_notebook.py` in our agent repo (diffs this notebook against the vendored
upstream copy and asserts exactly those three cells changed).
"""

CELL1_MD = """## Upstream notes — the Tufa Labs duck harness (their text, reworded in the third person)

The duck harness notebook this fork descends from is Tufa Labs' "duck harness" (their June 30 milestone
winner). Their own note on it: the readable notebook scored Tufa Labs' milestone-winning 1.21, and later
runs of it did not repeat that result; the original, less readable notebook is also shared at
https://www.kaggle.com/code/jeroencottaar/taaf-duck-harness-kaggle and is not recommended.

- Tufa Labs' writeup of what the solver does: https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3/discussion/717133
- Machine Learning Street Talk interview by Tim Scarfe about the duck harness: https://x.com/MLStreetTalk/status/2072326433922297975?s=20

The solver was written by the Tufa Labs team; in alphabetical order: Harold Bessis, Jeroen Cottaar,
Isaiah Pressman, Andries Smit, Michal Tesnar, and Stefano Viel. The notebook holds infrastructure and
diagnostics only; the solver code lives in the attached source bundle. It installs the ARC runtime from the
competition wheelhouse, makes the bundled source snapshot importable, runs the solver setup commands, loads
the pickled benchmark, plays the competition games, and writes results to `/kaggle/working`. Diagnostics are
minimised during a real competition rerun (`KAGGLE_IS_COMPETITION_RERUN`) and kept full otherwise. A copy of
this notebook must select the RTX Pro 6000 GPU manually.
"""

CELL3_OLD = 'os.environ["TAAF_MINIMAL_DIAGNOSTICS"] = "1"\n'
CELL3_NEW = ('# thui-fast: full diagnostics on an interactive public run (usage/events/transcript sidecars); minimal in a rerun.\n'
             'os.environ["TAAF_MINIMAL_DIAGNOSTICS"] = "1" if TRUE_SUBMISSION else "0"\n')


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    assert len(cells) == 18, f"{SRC_NB.name}: expected 18 cells, found {len(cells)}"
    before = ["".join(c["source"]) for c in cells]
    assert before[0].startswith("## About this fork"), "cell 0 is not Keith's fork note -- upstream changed"
    assert before[1].startswith("# Tufa Labs ARC3 submission"), "cell 1 is not Tufa's header -- upstream changed"
    assert before[3].count(CELL3_OLD) == 1, "cell 3 diagnostics line not found exactly once"
    assert "keithtyser/duck-qwen38-nvfp4-mtp-vllm-smoke-v1" in before[7], "cell 7 no longer names his source bundle"
    assert "bm.solver.max_runtime_s_per_game = 7920.0" in before[13], "cell 13 budget line moved"

    cells[0]["cell_type"] = "markdown"
    cells[0]["source"] = CELL0_MD.splitlines(keepends=True)
    cells[1]["source"] = CELL1_MD.splitlines(keepends=True)
    cells[1].pop("attachments", None)   # the upstream logo png rode in cell 1's attachments
    cells[3]["source"] = before[3].replace(CELL3_OLD, CELL3_NEW).splitlines(keepends=True)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 1, 3], f"cells changed {changed}, expected [0, 1, 3]"
    assert "attachments" not in cells[1] and "tufa_labs.png" not in json.dumps(nb), "logo attachment survived"
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    # G2 shape: our identity opens the first markdown cell, upstream names come after it
    first_md = after[0]
    assert first_md.startswith("# thui-fast-v0 (Thuitanium / Knowless Crew)"), "G2: cell 0 must open with our identity"
    assert first_md.index("Thuitanium") < first_md.index("Tufa Labs") and first_md.index("Thuitanium") < first_md.index("Keith Tyser")
    for bad in ("Tufa Labs ARC3 submission", "our milestone-winning", "attachment:"):
        assert bad not in after[1], f"cell 1 still carries {bad!r}"
    assert "TRUE_SUBMISSION" in after[3] and after[3].count("TAAF_MINIMAL_DIAGNOSTICS") == 1

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(SRC_META.read_text(encoding="utf-8"))
    for k in ("id_no",):
        meta.pop(k, None)
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"], meta["model_sources"]
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}")
    print(f"dataset_sources: {meta['dataset_sources']}\nmodel_sources: {meta['model_sources']}")
    print("push with: python scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-fast  (from arc-agi-pub)")


if __name__ == "__main__":
    main()
