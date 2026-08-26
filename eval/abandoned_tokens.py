"""B45 — how much of a run's generation never landed on an action.

Each game prints one `[finished]` line carrying TWO token figures:

    [finished] lp85-305b61c3 state=gave_up level=1/8 score=2.78 actions=14 \
        tokens=154026 per-level=9/17,5/38,... note="tokens=312989"

`tokens=` is what `summary.txt` totals and what the LEDGER's `Mtok` column reports. The trailing
`note="tokens=N"` is larger, and the gap is generation that was still in flight when the game hit
`max_runtime_s_per_game`. No committed artifact carries either field — they exist only in the
Kaggle kernel log, which is why nine runs of analysis never mentioned them.

⚠️ What `note=` counts is INFERRED. The reading survives three checks and none is decisive alone:
  a) games that finish cleanly give note == tokens EXACTLY, so `note` is not prompt+completion --
     at the 10.7:1 input:output ratio R35 measured that would be ~11.7x on every game, not on none;
  b) the solo `lp85` gap (158,963) matches its measured 3,717 s stall at that run's own token rate;
  c) the ACTIONS total this same regex extracts reproduces the LEDGER table exactly, 17 of 17 runs,
     which is the control printed by --check below: it proves the log is the run the row names.

Reads logs over the API rather than `kernels output`, which writes the log LAST and dies on the
250 MB `vllm-site-packages` directory. Costs no slot and no GPU.

    python eval/abandoned_tokens.py                 # every run, one row each
    python eval/abandoned_tokens.py --check         # + the actions control against LEDGER_ACTIONS
    python eval/abandoned_tokens.py --games v26     # per-game breakdown for one run
"""
import argparse
import os
import pathlib
import re
import statistics as st
import sys

# slug -> the name the LEDGER table uses. `kernels_logs` returns the LATEST version of a slug, so
# the actions control below is what ties a slug to a row; do not trust the mapping without it.
RUNS = {
    "v10cal": "sahasawatt/taaf-duck-v10",
    "v14": "sahasawatt/taaf-duck-v14",
    "v16": "sahasawatt/taaf-duck-v16",
    "v18": "sahasawatt/taaf-duck-v18",
    "v19": "sahasawatt/taaf-duck-v19",
    "v20": "sahasawatt/taaf-duck-v20",
    "v21": "sahasawatt/taaf-duck-v21",
    "v22": "sahasawatt/taaf-duck-v22",
    "v23": "sahasawatt/taaf-duck-v23",
    "v24": "sahasawatt/taaf-duck-v24",
    "v25": "sahasawatt/taaf-duck-v25",
    "v26": "sahasawatt/taaf-duck-v26",
    "thui-v1-0": "yocybercode/thui-v1-0",
    "thui-v1-1": "yocybercode/thui-v1-1",
    "thui-v1-1-r2": "yocybercode/thui-v1-1-r2",
    "thui-v2-0": "yocybercode/thui-v2-0",
    "clock2x": "yocybercode/clock-2x-v1",
    "solo-sk48": "sahasawatt/taaf-solo-sk48",
    "solo-lp85": "sahasawatt/taaf-solo-lp85",
}

# The actions column of notes/LEDGER-all-runs.md. The control asserts equality, not similarity:
# a mismatch means the slug's latest version is NOT the run that row describes.
LEDGER_ACTIONS = {
    "v10cal": 1597, "v14": 1633, "v16": 1218, "v18": 1576, "v19": 1638, "v20": 7656,
    "v21": 2921, "v22": 1612, "v23": 1634, "v24": 1196, "v25": 1341, "v26": 1165,
    "thui-v1-0": 1493, "thui-v1-1": 1325, "thui-v1-1-r2": 1260, "thui-v2-0": 1425,
    "clock2x": 2637,
}

FINISHED = re.compile(
    r"\[finished\] (\S+) state=(\S+) level=(\d+)/(\d+) score=([\d.]+) "
    r"actions=(\d+) tokens=(\d+).*?note=\\\"tokens=(\d+)\\\""
)

TOKEN_FILE = pathlib.Path.home() / "Desktop" / "ARC-AGI-3-Kaggle-Starter" / ".kaggle" / "access_token"


def _api():
    if "KAGGLE_API_TOKEN" not in os.environ:
        if not TOKEN_FILE.is_file():
            sys.exit(f"no KAGGLE_API_TOKEN in the environment and no token at {TOKEN_FILE}")
        os.environ["KAGGLE_API_TOKEN"] = TOKEN_FILE.read_text(encoding="utf-8").strip()
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    return api


def games(api, slug):
    """[(game, state, level, actions, counted, generated)] for one kernel."""
    raw = api.kernels_logs(slug)
    raw = raw if isinstance(raw, str) else str(raw)
    rows = FINISHED.findall(raw)
    if not rows:
        raise SystemExit(
            f"{slug}: no [finished] rows parsed. Either the kernel never reached the benchmark or "
            f"the line format changed -- re-read one log before trusting any zero from this tool."
        )
    return [(r[0], r[1], f"{r[2]}/{r[3]}", int(r[5]), int(r[6]), int(r[7])) for r in rows]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="assert actions match LEDGER_ACTIONS")
    ap.add_argument("--games", metavar="RUN", help="per-game breakdown for one run")
    args = ap.parse_args()
    api = _api()

    if args.games:
        if args.games not in RUNS:
            sys.exit(f"unknown run {args.games!r}; known: {', '.join(RUNS)}")
        rows = sorted(games(api, RUNS[args.games]), key=lambda r: -(r[5] - r[4]) / max(1, r[5]))
        print(f"{args.games}  ({RUNS[args.games]})")
        for g, state, lvl, acts, counted, gen in rows:
            pct = 100.0 * (gen - counted) / max(1, gen)
            print(f"  {g:18s} {state:9s} lvl={lvl:5s} actions={acts:>5} "
                  f"counted={counted:>9,} generated={gen:>9,} abandoned={pct:5.1f}%")
        return

    hdr = f"{'run':13s} {'n':>3} {'actions':>8} {'counted':>11} {'generated':>11} {'aband%':>7}   min/med/max %"
    print(hdr)
    failures = []
    for name, slug in RUNS.items():
        rows = games(api, slug)
        acts = sum(r[3] for r in rows)
        counted = sum(r[4] for r in rows)
        gen = sum(r[5] for r in rows)
        pg = sorted(100.0 * (r[5] - r[4]) / r[5] for r in rows if r[5])
        print(f"{name:13s} {len(rows):>3} {acts:>8,} {counted:>11,} {gen:>11,} "
              f"{100.0 * (gen - counted) / gen:>6.1f}%   "
              f"{pg[0]:.1f} / {st.median(pg):.1f} / {pg[-1]:.1f}")
        if args.check and name in LEDGER_ACTIONS and acts != LEDGER_ACTIONS[name]:
            failures.append(f"{name}: log says {acts} actions, LEDGER says {LEDGER_ACTIONS[name]}")

    if args.check:
        checked = [n for n in RUNS if n in LEDGER_ACTIONS]
        if failures:
            sys.exit("CONTROL FAILED -- the slug is not the run the LEDGER row names:\n  "
                     + "\n  ".join(failures))
        print(f"\nactions control: {len(checked)} of {len(checked)} runs match the LEDGER exactly")


if __name__ == "__main__":
    main()
