"""thui-a5: the B71 anim build with the serving profile moved to MTP 0 + KV 7 GiB + max_num_seqs 28.

Why: in thui-rank2-anim-full25-r1 (2026-09-16) vLLM's own log shows median Running 3 / Waiting 22 across the whole run and
75% of requests carry > 20k prompt tokens; the 5 GiB KV admits ~3 real-size sequences for 25 games. The arena-3 bench
(2026-09-15) measured MTP 0 at KV 7 GiB = 263,568 KV tokens, no OOM, c25 570 tok/s vs 359. This arm is that profile at
full width on the B71 chassis, nothing else changed. Cells changed: [0, 3] only.
"""
import json, sys, copy
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_NB = HERE.parent / "thui-anim-fast" / "thui-animfast-b71-full25-r1.ipynb"
SRC_META = HERE.parent / "thui-anim-fast" / "kernel-metadata.json"
SLUG = "thui-a5-mtp0k7s28-full25-r1"
OUT = HERE / "out" / SLUG

OLD_PROFILE = '''PUBLIC25_VLLM_PROFILE_NAME = 'kv5-bf16-mtp3-c8-cg32'
PUBLIC25_VLLM_PROFILE_ENV = {
    "TAAF_VLLM_ENABLE_PREFIX_CACHING": "0",
    "TAAF_VLLM_KV_CACHE_DTYPE": "auto",
    "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": "5368709120",
    "TAAF_VLLM_MAX_CUDAGRAPH_CAPTURE_SIZE": "32",
    "TAAF_VLLM_MAX_NUM_BATCHED_TOKENS": "8192",
    "TAAF_VLLM_MAX_NUM_SEQS": "8",
    "TAAF_VLLM_MTP_TOKENS": "3",
    "TAAF_VLLM_OMP_THREADS": "1"
}'''
NEW_PROFILE = '''PUBLIC25_VLLM_PROFILE_NAME = 'kv7-bf16-mtp0-c28-cg32'   # thui-a5: was kv5-bf16-mtp3-c8-cg32
PUBLIC25_VLLM_PROFILE_ENV = {
    "TAAF_VLLM_ENABLE_PREFIX_CACHING": "0",
    "TAAF_VLLM_KV_CACHE_DTYPE": "auto",
    "TAAF_VLLM_KV_CACHE_MEMORY_BYTES": "7516192768",
    "TAAF_VLLM_MAX_CUDAGRAPH_CAPTURE_SIZE": "32",
    "TAAF_VLLM_MAX_NUM_BATCHED_TOKENS": "8192",
    "TAAF_VLLM_MAX_NUM_SEQS": "28",
    "TAAF_VLLM_MTP_TOKENS": "0",
    "TAAF_VLLM_OMP_THREADS": "1"
}
assert PUBLIC25_VLLM_PROFILE_ENV["TAAF_VLLM_KV_CACHE_MEMORY_BYTES"] == str(7 * 1024 ** 3)
print("THUI_A5_PROFILE ok mtp=0 kv=7GiB seqs=28", flush=True)'''

CELL0 = f"""# {SLUG} (Thuitanium / Knowless Crew) — the B71 anim build on a KV-7 / MTP-0 / seqs-28 serving profile

**This is a Knowless Crew / Thuitanium experiment notebook.** Solver, prompts, clock and games are exactly
`thui-animfast-b71-full25-r1`. Only the vLLM profile in cell 3 changes: MTP 3 -> 0, KV cache 5 -> 7 GiB,
max_num_seqs 8 -> 28.

Why: in our 2026-09-16 full run vLLM's log shows a median of 3 running and 22 waiting requests for 25 games, with
most prompts above 20k tokens. A bench on 2026-09-15 measured this profile starting cleanly with 263,568 KV tokens.

Serving stack by [Keith Tyser](https://www.kaggle.com/code/keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp), harness by
[Tufa Labs](https://www.kaggle.com/code/jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner), anim solver
bundle `jakobbrggen/taaf-kaggle-source-anim-20260807-anim`.
"""

nb = json.load(open(SRC_NB))
orig = copy.deepcopy(nb)
cells = nb["cells"]
s3 = "".join(cells[3]["source"])
assert s3.count(OLD_PROFILE) == 1, "cell 3 profile block moved -- re-derive"
cells[3]["source"] = s3.replace(OLD_PROFILE, NEW_PROFILE).splitlines(keepends=True)
assert "Knowless Crew" in "".join(cells[0]["source"])
cells[0]["source"] = CELL0.splitlines(keepends=True)
changed = [i for i, (a, b) in enumerate(zip(orig["cells"], cells)) if a != b]
assert changed == [0, 3], changed
assert len(orig["cells"]) == len(cells)
# teeth: the new cell 3 must execute its own assert against the literal it carries
ns = {}
exec(compile(NEW_PROFILE, "cell3-profile", "exec"), {"print": lambda *a, **k: None}, ns)
assert ns["PUBLIC25_VLLM_PROFILE_ENV"]["TAAF_VLLM_MTP_TOKENS"] == "0" and ns["PUBLIC25_VLLM_PROFILE_ENV"]["TAAF_VLLM_MAX_NUM_SEQS"] == "28"

meta = json.load(open(SRC_META))
meta.update(id=f"yocybercode/{SLUG}", title=SLUG, code_file=f"{SLUG}.ipynb", is_private=True)
assert meta["id"].startswith("yocybercode/")
OUT.mkdir(parents=True, exist_ok=True)
json.dump(nb, open(OUT / f"{SLUG}.ipynb", "w"), indent=1)
json.dump(meta, open(OUT / "kernel-metadata.json", "w"), indent=2)
print(f"built {SLUG}: cells changed {changed}, id {meta['id']}, private, datasets={meta['dataset_sources']}")
