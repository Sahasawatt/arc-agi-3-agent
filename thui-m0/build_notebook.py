"""thui-m0 -- the shipped chassis with the MTP-0 / KV-7-GiB serving profile, played at full width (25 games).

Why (2026-09-15). The bench thui-l4 re-opened axis B once the draft head was removed:
  mtp0k7s16  c25 570 tok/s (+59 % vs the shipped 359), median request 59 s (vs 114), 0 preemptions, KV 7 GiB = 263,568
             tokens (per-seq ~10.4k vs ~19k at MTP-3 -- the draft head was half the KV cost), `max Running` = the 16 cap at 67 % KV.
  mtp0k7s28  c25 722 tok/s (2x shipped), max Running 25 = every game admitted, KV 99.7 %, 2 preemptions.
Every solver turn on the shipped chassis waits in vLLM's queue: ~52 analysis turns per game at ~152 s/turn, 20-40 % of them
yielding on the 60 s turn budget without acting. Halving the per-request wall is the only lever left that changes how many
turns a game gets; whether more turns become more LEVELS is untested (corr(actions, levels) over 9 Flash draws = 0.08), so
this is a full-25 draw, not a submission.

Arms (env is the ONLY difference; every other cell is byte-identical to thui-fast-v0 apart from the mount resolver):
  default    TAAF_VLLM_MTP_TOKENS=0, TAAF_VLLM_KV_CACHE_MEMORY_BYTES=7 GiB, TAAF_VLLM_MAX_NUM_SEQS=<--seqs, default 20>
             20 is chosen from the bench's own line: 16 seats = 67 % KV, 25 seats = 99.7 % + preemptions, so ~4.2 %/seat and 20
             sits at ~84 % with headroom for long prompts. `--seqs 24` is the aggressive rung (~100 %, expect preemptions).
  --control  no delta: the shipped profile `kv5-bf16-mtp3-c8-cg32`, same day, the paired comparator.

Pre-registered read (written before the first push):
  1. MECHANISM, and it gates everything: the treatment log must show `THUI_M0_ARM` with the delta AND vLLM's own
     `GPU KV cache size:` line above 250,000 tokens AND no speculative counters > 0. Then the harness must have used the
     room: median wall per analysis turn (events) < 100 s and median analysis turns per game > 60 (shipped: ~152 s, ~52).
     If the turns did not increase, the draw is VOID for the score question (the chassis did not deliver) -- not a FAIL.
  2. PRIMARY: eval/rank_runs.py, treatment vs --control (same-day pair) and vs the Flash pool (9 draws in the census).
     Harvest both into eval/fixtures/per-level-census.json via flash_census_harvest.py.
  3. ALIVE if the treatment beats every one of the 9 Flash draws on public score (pool max ~8.3) -- a single draw cannot resolve
     less than ~4 public points (L1 full-25 p=0.369), so "above the pool max" is the only single-draw reading that means anything.
     Above control but inside the pool = draw variance = NULL, and a second draw is the owner's call.
  4. DEAD if the treatment <= control with mechanism confirmed: more turns did not become levels, which closes axis B for score
     (the tail is the search, not the queue).
  5. Nothing here is a submission. ALIVE buys a discussion with the owner about the chassis; it does not buy a leaderboard slot.

Build:  PYTHONUTF8=1 python thui-m0/build_notebook.py                 -> taaf-thui-m0-s20-full25-r1.ipynb
        PYTHONUTF8=1 python thui-m0/build_notebook.py --seqs 24       -> taaf-thui-m0-s24-full25-r1.ipynb
        PYTHONUTF8=1 python thui-m0/build_notebook.py --control       -> taaf-thui-m0-ctl-full25-r1.ipynb
Teeth:  python thui-m0/test_m0_build.py   (0 GPU: reads the built notebooks back)
Push:   python scripts/kaggle_push_kernel.py <this dir>   (from arc-agi-pub; rebuild the arm first -- code_file is shared)
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAST = HERE.parent / "thui-fast"
L1 = HERE.parent / "thui-l1" / "build_notebook.py"
SRC_NB = FAST / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
SRC_META = FAST / "upstream-kernel-metadata.json"
OWNER = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--owner=")), "sahasawatt")
CONTROL = "--control" in sys.argv
SEQS = int(next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--seqs"), "20"))
assert 8 <= SEQS <= 28, f"--seqs {SEQS}: the bench measured 16 (67 % KV) and 28 (99.7 %); stay inside"
ARM = "ctl" if CONTROL else f"s{SEQS}"
SLUG = f"thui-m0-{ARM}-full25-r1"
OUT_NB = HERE / f"taaf-{SLUG}.ipynb"
ARM_ENV = {} if CONTROL else {
    "TAAF_VLLM_MTP_TOKENS": "0",
    "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": str(7 * 1024 ** 3),
    "TAAF_VLLM_MAX_NUM_SEQS": str(SEQS),
}
PROFILE_LOOP = "for key, value in PUBLIC25_VLLM_PROFILE_ENV.items():"

sys.path.insert(0, str(FAST))
import build_notebook as fast  # noqa: E402
_spec = importlib.util.spec_from_file_location("thui_l1_builder", L1)
l1 = importlib.util.module_from_spec(_spec)
_argv, sys.argv = sys.argv, sys.argv[:1]   # the L1 builder reads its own flags at import; we only want its constants
_spec.loader.exec_module(l1)
sys.argv = _argv

CELL0_MD = f"""# {SLUG} (Thuitanium / Knowless Crew) -- the shipped chassis on the MTP-0 / KV-7-GiB serving profile

**This is a Knowless Crew / Thuitanium fork, and the solver is not ours.** Same two upstreams as `thui-fast-v0`, executed as they ship:

- **Serving**: Keith Tyser's [Duck Qwen3.8 Flash Next NVFP4 MTP](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp)
  -- his pinned `RadixArk/Qwen3.8-Flash-Next-NVFP4` asset, offline vLLM runtime, NVFP4 PLE patch, watchdog.
- **Solver**: the Tufa Labs duck harness (Harold Bessis, Jeroen Cottaar, Isaiah Pressman, Andries Smit,
  Michal Tesnar, Stefano Viel) -- his source bundle, unmodified on disk.
- **Weights**: RadixArk's NVFP4 quantisation of Qwen/Qwen3.8-Flash-Next (Qwen licence terms apply).

Every score quoted by any upstream is theirs.

## What we changed

- **cell 0 / 1** -- this header; Tufa's header reworded in the third person.
- **cell 3** -- full diagnostics on an interactive public run, minimal in a real rerun; **arm `{ARM}`**: env delta over the
  shipped profile `kv5-bf16-mtp3-c8-cg32` = `{json.dumps(ARM_ENV) or "none (control)"}`, applied after the profile, before
  any serving command runs (measured on the thui-l4 bench: MTP-0 + KV 7 GiB = 263,568 KV tokens, 570-722 tok/s at 25-way).
- **cell 5 / 15** -- the competition mount resolved (Kaggle serves two layouts). All 25 public games, upstream clock.

Build script: `thui-m0/build_notebook.py` in our agent repo (asserts exactly those cells changed). Axis B full-25 draw r1 (2026-09-15).
"""

CELL3_ARM = f"""
# thui-m0: arm env delta, applied AFTER the measured profile and BEFORE any serving setup command runs.
THUI_M0_ARM = {ARM!r}
THUI_M0_ARM_ENV = {json.dumps(ARM_ENV, indent=4)}
for key, value in THUI_M0_ARM_ENV.items():
    os.environ[key] = value
print(f"THUI_M0_ARM name={{THUI_M0_ARM}} delta={{json.dumps(THUI_M0_ARM_ENV)}}", flush=True)
"""


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
    rep(3, fast.CELL3_OLD, fast.CELL3_NEW.replace("thui-fast", "thui-m0"))
    s3 = "".join(cells[3]["source"])
    assert s3.count("PUBLIC25_VLLM_PROFILE name=") == 1 and s3.count(PROFILE_LOOP) == 1
    cells[3]["source"] = (s3 + CELL3_ARM).splitlines(keepends=True)
    rep(5, l1.CELL5_ANCHOR, "        _WHEELS,\n")
    cells[5]["source"] = (l1.CELL5_RESOLVER.replace("thui-l1", "thui-m0") + "".join(cells[5]["source"])).splitlines(keepends=True)
    rep(15, l1.CELL15_MOUNT_OLD, l1.CELL15_MOUNT_NEW.replace("thui-l1", "thui-m0"))

    after = ["".join(c["source"]) for c in cells]
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    assert changed == [0, 1, 3, 5, 15], f"cells changed {changed}"
    assert "attachments" not in cells[1] and "tufa_labs.png" not in json.dumps(nb)
    for i, c in enumerate(cells):
        if c["cell_type"] == "code":
            ast.parse("".join(c["source"]), filename=f"cell{i}")
    assert after[0].startswith(f"# {SLUG} (Thuitanium / Knowless Crew)")
    for bad in ("Tufa Labs ARC3 submission", "our milestone-winning", "attachment:"):
        assert bad not in after[1]
    # the delta must land after the profile loop, so it wins; and the solver cells stay byte-identical
    assert after[3].index(PROFILE_LOOP) < after[3].index("THUI_M0_ARM_ENV = ")
    assert after[3].count("THUI_M0_ARM") == 6 and after[3].count("TAAF_MINIMAL_DIAGNOSTICS") == 1
    assert after[7] == before[7] and after[9] == before[9] and after[11] == before[11] and after[13] == before[13]
    assert "thui-l1" not in after[5] and "thui-l1" not in after[15] and "THUI_L1" not in after[15]
    assert l1.WHEELS_NESTED not in after[5] and l1.WHEELS_NESTED not in after[15]
    assert "bm.solver.max_runtime_s_per_game = 7920.0" in after[13], "cell 13 budget line moved"
    assert after[15].count('"tn36-') == 1, "cell 15 no longer lists the 25 public ids"

    OUT_NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads(SRC_META.read_text(encoding="utf-8")); meta.pop("id_no", None)
    assert meta["model_sources"] == ["keithtyser/qwen3-8-flash-next-nvfp4/PyTorch/radixark-modelopt-fp4/1"]
    assert meta["machine_shape"] == "NvidiaRtxPro6000" and meta["enable_gpu"] is True
    meta["id"] = f"{OWNER}/{SLUG}"; meta["title"] = SLUG; meta["code_file"] = OUT_NB.name
    (HERE / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"built {OUT_NB.name}: cells changed {changed}, id {meta['id']}, arm {ARM}, env {ARM_ENV or 'control'}")


if __name__ == "__main__":
    main()
