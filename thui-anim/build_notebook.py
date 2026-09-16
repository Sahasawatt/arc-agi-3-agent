"""thui-anim -- Jakob Bruggen's animation-awareness duck harness on OUR chassis (Keith Tyser's Flash-Next NVFP4 serving), full-25.

Why (2026-09-15, after the top-5 research). Ranks 2-5 publish nothing; the only public artifacts above our score are the anim
harness family: `jakobbrggen/taaf-kaggle-source-anim-20260807-anim` (the solver bundle behind the "LB-9" notebook and behind
Watchara's `yocybercode/thui-animfast-b71-full25-r1`, 9.56 public / 2,008 actions -- the team's best public draw). master carries
`thui-anim-fast/build_notebook.py` (#154), which VENDORS the pushed notebooks and reproduces b71 byte-for-byte; this file is the
other shape -- it re-derives the same composition from Keith's upstream + the 7 b71 cells, so it can be re-slugged and stacked
with the MTP-0 profile (`--m0`). Same composition, two builders; b71's own header saying "no build script" predates #154.

Composition (cells vs Keith's upstream; every changed cell is taken VERBATIM from the b71 notebook except 0 and the --m0 delta):
  cell 0      our header
  cell 1      Tufa's header reworded (b71)
  cell 3      full diagnostics on an interactive run (b71) [+ --m0: MTP_TOKENS 0 / KV 7 GiB / MAX_NUM_SEQS N after the profile loop]
  cell 5, 15  competition mount resolved (b71)
  cell 7      the anim bundle attached as a third dataset; bundles located by benchmark_label (b71)
  cell 9      anim ARC3-Inference + tufa-arc-agi-framework replace his June solver trees on sys.path; thui-v3 knobs
              LOCAL_ANALYZER_SEED=20260825 / LOCAL_ANALYZER_YIELD_SECONDS=180 set after serving_setup, before import; teeth (b71)
  cell 11     benchmark + deploy target from the anim bundle (HarnessSolver.animation_awareness / hard_noop_guard) (b71)
  cells 2,4,6,8,10,12,13,14,16,17  byte-identical to Keith's upstream (asserted)

Arms:
  default      shipped profile kv5-bf16-mtp3-c8-cg32     -> taaf-thui-anim-full25-r2.ipynb   (draw 2 of b71's composition; b71 = r1)
  --m0 [--seqs N]  MTP-0 / KV 7 GiB / seqs N (default 20) -> taaf-thui-anim-m0s20-full25-r1.ipynb

Pre-registered read (written before any push):
  1. Mechanism: `THUI_ANIM_GRAFT ok` with solver path under the anim bundle, `bm.label=anim-20260807-anim`,
     animation_awareness=True; for --m0 also the thui-m0 rule-1 gate (thui-m0/turns_read.py: turns > 60, wall/turn < 100 s).
  2. Primary: eval/rank_runs.py vs b71 (same composition, draw 1) and vs the Flash pool; harvest into the census.
  3. r2 alone answers only "is 9.56 a draw or the family mean" (b71 is n=1). ALIVE for m0 = above the pool max on public.
  4. Nothing here is a submission.

Build:  PYTHONUTF8=1 python thui-anim/build_notebook.py              -> taaf-thui-anim-full25-r2.ipynb
        PYTHONUTF8=1 python thui-anim/build_notebook.py --m0         -> taaf-thui-anim-m0s20-full25-r1.ipynb
Teeth:  python thui-anim/test_anim_build.py
Push:   python scripts/kaggle_push_kernel.py <this dir>   (from arc-agi-pub; rebuild the arm first -- code_file is shared)
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAST = HERE.parent / "thui-fast"
SRC_NB = FAST / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
B71_NB = HERE / "upstream-yocybercode-thui-animfast-b71-full25-r1.ipynb"
B71_META = HERE / "upstream-yocybercode-kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
M0 = "--m0" in sys.argv
SEQS = int(next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--seqs"), "20"))
assert 8 <= SEQS <= 28, f"--seqs {SEQS}: the bench measured 16 (67 % KV) and 28 (99.7 %); stay inside"
ARM = f"m0s{SEQS}" if M0 else "base"
SLUG = f"thui-anim-m0s{SEQS}-full25-r1" if M0 else "thui-anim-full25-r2"
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
ARM_ENV = {"TAAF_VLLM_MTP_TOKENS": "0", "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(7 * 1024 ** 3), "TAAF_VLLM_MAX_NUM_SEQS": str(SEQS)} if M0 else {}
ANIM_DS = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
B71_CELLS = (1, 3, 5, 7, 9, 11, 15)
PROFILE_LOOP = "for key, value in PUBLIC25_VLLM_PROFILE_ENV.items():"

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) -- the animation-awareness duck harness on Keith Tyser's Flash-Next serving stack

**This is a Knowless Crew / Thuitanium fork.** Three upstreams, and what is ours is the graft:

- **Serving** -- Keith Tyser's [Duck Qwen3.8 Flash Next NVFP4 MTP](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp):
  the pinned `RadixArk/Qwen3.8-Flash-Next-NVFP4` checkpoint (his Kaggle model asset), his offline vLLM runtime, NVFP4 PLE patch,
  {"MTP-3 speculative decoding profile" if not M0 else "serving profile with the MTP head off and a 7 GiB KV cache (arm `" + ARM + "`, env delta `" + json.dumps(ARM_ENV) + "`)"} and server watchdog.
- **Solver** -- the Tufa Labs duck harness (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit, Michal Tesnar, Stefano Viel)
  on Jakob Bruggen's `feature/animation-awareness` branch, mounted as the `{ANIM_DS}` source bundle, executed unmodified.
- **Weights** -- RadixArk's NVFP4 quantisation of Qwen/Qwen3.8-Flash-Next (Qwen licence terms apply).

Every score quoted by any upstream is theirs.

## What we changed (the graft)

- **cell 0 / 1** -- this header; Tufa's original header reworded in the third person.
- **cell 3** -- full diagnostics on an interactive public run, minimal in a real rerun{"; the arm env delta applied after the measured profile" if M0 else ""}.
- **cell 5 / 15** -- the competition mount resolved instead of hardcoded (Kaggle serves two layouts).
- **cell 7** -- the anim source bundle attached as a third dataset; each bundle located by its `benchmark_label`.
- **cell 9** -- the anim `ARC3-Inference` + `tufa-arc-agi-framework` trees replace his June copies on `sys.path`; after his serving
  setup persists the analyzer env, `LOCAL_ANALYZER_SEED=20260825` and `LOCAL_ANALYZER_YIELD_SECONDS=180` are set before the
  solver is imported; graft teeth assert all of it.
- **cell 11** -- the benchmark and deploy target come from the anim bundle (its `HarnessSolver` carries `animation_awareness` / `hard_noop_guard`).

Composition identical to `yocybercode/thui-animfast-b71-full25-r1` (draw 1); build script `thui-anim/build_notebook.py` in our agent repo.
"""

CELL3_ARM = f"""
# thui-anim: arm env delta, applied AFTER the measured profile and BEFORE any serving setup command runs.
THUI_ANIM_ARM = {ARM!r}
THUI_ANIM_ARM_ENV = {json.dumps(ARM_ENV, indent=4)}
for key, value in THUI_ANIM_ARM_ENV.items():
    os.environ[key] = value
print(f"THUI_ANIM_ARM name={{THUI_ANIM_ARM}} delta={{json.dumps(THUI_ANIM_ARM_ENV)}}", flush=True)
"""


def main() -> None:
    nb = json.loads(SRC_NB.read_text(encoding="utf-8"))
    cells = nb["cells"]
    b71 = json.loads(B71_NB.read_text(encoding="utf-8"))["cells"]
    assert len(cells) == 18 and len(b71) == 18, (len(cells), len(b71))
    before = ["".join(c["source"]) for c in cells]
    b = ["".join(c["source"]) for c in b71]
    for i in range(18):
        if i not in (0,) + B71_CELLS:
            assert b[i] == before[i], f"b71 cell {i} differs from Keith's upstream -- composition drifted"
    assert b[7].count(ANIM_DS) == 1 and "ANIM_BUNDLE_DIR" in b[9] and "ANIM_BUNDLE_DIR" in b[11] and "_COMP_DIR" in b[15]

    cells[0]["cell_type"] = "markdown"; cells[0]["source"] = CELL0_MD.splitlines(keepends=True)
    for i in B71_CELLS:
        s = b[i].replace("thui-animfast", "thui-anim").replace("THUI_ANIMFAST_GRAFT", "THUI_ANIM_GRAFT")
        if i == 3:
            assert s.count(PROFILE_LOOP) == 1
            s += CELL3_ARM
        cells[i]["source"] = s.splitlines(keepends=True)
        cells[i].pop("attachments", None)

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (x, y) in enumerate(zip(before, after)) if x != y]
    assert changed == [0, 1, 3, 5, 7, 9, 11, 15], f"cells changed {changed}"
    assert "attachments" not in cells[1] and "tufa_labs.png" not in json.dumps(nb)
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert "animfast" not in json.dumps(after[1:]), "old marker survived"
    assert after[3].index(PROFILE_LOOP) < after[3].index("THUI_ANIM_ARM_ENV = ")
    assert after[9].count("THUI_ANIM_GRAFT ok") == 1 and '"LOCAL_ANALYZER_SEED": "20260825"' in after[9] and '"LOCAL_ANALYZER_YIELD_SECONDS": "180"' in after[9]
    assert 'bm.label == "anim-20260807-anim"' in after[11]
    assert "bm.solver.max_runtime_s_per_game = 7920.0" in after[13] and after[15].count('"tn36-') == 1

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(B71_META.read_text(encoding="utf-8")); meta.pop("id_no", None)
    assert meta["dataset_sources"][-1] == ANIM_DS and meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"]
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, arm {ARM}, env {ARM_ENV or 'shipped profile'}")


if __name__ == "__main__":
    main()
