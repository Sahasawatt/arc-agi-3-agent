"""Teeth for the thui-m0 notebooks (0 GPU): the env the server will see, read by EXECUTING cell 3's profile+delta slice.

    python thui-m0/test_m0_build.py

Cases (each arm's notebook must already be built):
  1. treatment s20 / s24: executing the profile block followed by the delta leaves MTP 0, KV 7 GiB, seqs N in the env --
     i.e. the delta lands after the profile loop and wins. Control: MTP 3, KV 5 GiB, seqs 8 -- the shipped profile, untouched.
  2. cells 7, 9, 11, 13 (bundle, serving setup, watchdog, solver config) are byte-identical to the upstream notebook in all arms.
  3. s20 and s24 differ from each other ONLY in the seqs value and the slug (cells 0 and 3); ctl differs from s20 only in 0 and 3.
  4. cell 15 still plays the 25 public games (no smoke subset), cell 13 keeps the upstream 7920 s clock.
Negative control: the same reader on the UPSTREAM notebook's cell 3 must return MTP 3 / seqs 8 (proves the exec reads the profile).
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UP = HERE.parent / "thui-fast" / "upstream-keithtyser-duck-qwen3-8-flash-next-nvfp4-mtp.ipynb"
ARMS = {"s20": ("0", str(7 * 1024 ** 3), "20"), "s24": ("0", str(7 * 1024 ** 3), "24"), "ctl": ("3", "5368709120", "8")}
KEYS = ("TAAF_VLLM_MTP_TOKENS", "TAAF_VLLM_KV_CACHE_MEMORY_BYTES", "TAAF_VLLM_MAX_NUM_SEQS")


def cells(path):
    return ["".join(c["source"]) for c in json.loads(path.read_text(encoding="utf-8"))["cells"]]


def served_env(cell3):
    """Execute the profile block (and the delta if present) against a fresh fake environ; return the three knobs."""
    start = cell3.index("PUBLIC25_VLLM_PROFILE_NAME = ")
    src = cell3[start:]
    src = src[:src.index("# Pin arc_agi")] + (src[src.index("# thui-m0: arm env delta"):] if "# thui-m0: arm env delta" in src else "")

    class _OS:
        environ = {}
    g = {"os": _OS, "json": json, "print": lambda *a, **k: None}
    exec(src, g)
    return tuple(_OS.environ.get(k) for k in KEYS)


def main():
    fails = []
    up = cells(UP)
    got = served_env(up[3])
    if got != ("3", "5368709120", "8"):
        fails.append(f"negative control: upstream cell 3 read {got}")
    built = {}
    for arm, want in ARMS.items():
        p = HERE / f"taaf-thui-m0-{arm}-full25-r1.ipynb"
        if not p.exists():
            fails.append(f"{arm}: notebook not built"); continue
        c = cells(p); built[arm] = c
        got = served_env(c[3])
        if got != want:
            fails.append(f"{arm}: served env {got} != {want}")
        if arm != "ctl" and c[3].index("for key, value in PUBLIC25_VLLM_PROFILE_ENV.items():") > c[3].index("THUI_M0_ARM_ENV = "):
            fails.append(f"{arm}: delta before the profile loop")
        for i in (7, 9, 11, 13):
            if c[i] != up[i]:
                fails.append(f"{arm}: cell {i} differs from upstream")
        if "smoke" in c[15] or c[15].count('"tn36-') != 1 or "!= 25" not in c[15]:
            fails.append(f"{arm}: cell 15 does not play the 25 public games")
        if "bm.solver.max_runtime_s_per_game = 7920.0" not in c[13]:
            fails.append(f"{arm}: cell 13 clock changed")
        print(f"{arm}: served env {dict(zip(KEYS, got))}")
    if {"s20", "s24", "ctl"} <= built.keys():
        d = [i for i in range(18) if built["s20"][i] != built["s24"][i]]
        if d != [0, 3]:
            fails.append(f"s20 vs s24 differ in cells {d}, expected [0, 3]")
        else:
            a, b = built["s20"][3].replace("s20", "sXX").replace('"20"', '"XX"'), built["s24"][3].replace("s24", "sXX").replace('"24"', '"XX"')
            if a != b:
                fails.append("s20 vs s24 cell 3 differs beyond the seqs value")
        d = [i for i in range(18) if built["s20"][i] != built["ctl"][i]]
        if d != [0, 3]:
            fails.append(f"s20 vs ctl differ in cells {d}, expected [0, 3]")
    for f in fails:
        print("FAIL", f)
    print("ALL TEETH PASS" if not fails else f"{len(fails)} FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
