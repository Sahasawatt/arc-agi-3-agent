"""Teeth for the thui-anim notebooks (0 GPU). Reads the built notebooks back; both arms must exist.

    python thui-anim/test_anim_build.py

  1. Served env by EXECUTING cell 3's profile(+delta) slice: base -> (MTP 3, KV 5 GiB, seqs 8); m0s20 -> (0, 7 GiB, 20).
     Negative control: Keith's upstream cell 3 reads (3, 5 GiB, 8).
  2. Composition = b71: cells 5, 7, 9, 11, 15 equal the b71 notebook's after the marker rename; cells 2,4,6,8,10,12,13,14,16,17
     equal Keith's upstream; base vs m0 differ only in cells [0, 3].
  3. The anim bundle is attached (cell 7 DATASET_SOURCES) and declared (kernel-metadata dataset_sources), and cell 9 asserts the
     solver import resolves under it; cell 11 asserts bm.label / animation_awareness.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UP = HERE.parent / "thui-fast" / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
B71 = HERE / "upstream-yocybercode-thui-animfast-b71-full25-r1.ipynb"
ANIM_DS = "jakobbrggen/taaf-kaggle-source-anim-20260807-anim"
KEYS = ("TAAF_VLLM_MTP_TOKENS", "TAAF_VLLM_KV_CACHE_MEMORY_BYTES", "TAAF_VLLM_MAX_NUM_SEQS")
ARMS = {"taaf-thui-anim-full25-r2.ipynb": ("3", "5368709120", "8"), "taaf-thui-anim-m0s20-full25-r1.ipynb": ("0", str(7 * 1024 ** 3), "20")}


def cells(path):
    return ["".join(c["source"]) for c in json.loads(path.read_text(encoding="utf-8"))["cells"]]


def served_env(cell3):
    src = cell3[cell3.index("PUBLIC25_VLLM_PROFILE_NAME = "):]
    src = src[:src.index("# Pin arc_agi")] + (src[src.index("# thui-anim: arm env delta"):] if "# thui-anim: arm env delta" in src else "")

    class _OS:
        environ = {}
    exec(src, {"os": _OS, "json": json, "print": lambda *a, **k: None})
    return tuple(_OS.environ.get(k) for k in KEYS)


def main():
    fails = []
    up, b71 = cells(UP), cells(B71)
    if served_env(up[3]) != ("3", "5368709120", "8"):
        fails.append("negative control: upstream cell 3 misread")
    built = {}
    for name, want in ARMS.items():
        p = HERE / name
        if not p.exists():
            fails.append(f"{name}: not built"); continue
        c = cells(p); built[name] = c
        got = served_env(c[3])
        if got != want:
            fails.append(f"{name}: served env {got} != {want}")
        for i in (5, 7, 9, 11, 15):
            if c[i] != b71[i].replace("thui-animfast", "thui-anim").replace("THUI_ANIMFAST_GRAFT", "THUI_ANIM_GRAFT"):
                fails.append(f"{name}: cell {i} is not b71's composition")
        for i in (2, 4, 6, 8, 10, 12, 13, 14, 16, 17):
            if c[i] != up[i]:
                fails.append(f"{name}: cell {i} differs from Keith's upstream")
        if c[7].count(f'"{ANIM_DS}"') != 1 or "ANIM_BUNDLE_DIR.resolve()" not in c[9] or 'bm.label == "anim-20260807-anim"' not in c[11]:
            fails.append(f"{name}: anim bundle not wired in cells 7/9/11")
        print(f"{name}: served env {dict(zip(KEYS, got))}")
    if len(built) == 2:
        a, b = built.values()
        d = [i for i in range(18) if a[i] != b[i]]
        if d != [0, 3]:
            fails.append(f"base vs m0 differ in cells {d}, expected [0, 3]")
    meta = json.loads((HERE / "kernel-metadata.json").read_text(encoding="utf-8"))
    if meta.get("dataset_sources", [])[-1:] != [ANIM_DS]:
        fails.append(f"kernel-metadata dataset_sources lacks the anim bundle: {meta.get('dataset_sources')}")
    for f in fails:
        print("FAIL", f)
    print("ALL TEETH PASS" if not fails else f"{len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
