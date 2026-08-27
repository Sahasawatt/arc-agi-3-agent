r"""B45 — how much of a run's generation never landed on an action.

Each game prints one `[finished]` line carrying TWO token figures:

    [finished] lp85-305b61c3 state=gave_up level=1/8 score=2.78 actions=14 \
        tokens=154026 per-level=9/17,5/38,... note="tokens=312989"

`tokens=` is what `summary.txt` totals and what the LEDGER's `Mtok` column reports. The trailing
`note="tokens=N"` is larger, and the gap is generation that RETURNED but was never credited to an
action. No committed artifact carries either field -- they exist only in the Kaggle kernel log,
which is why nine runs of analysis never mentioned them.

The gap was first read as generation still IN FLIGHT at the wall. That is refuted, from two
instruments: per-request usage rows on thui-v1-1-r2 sum to exactly N on 25 of 25 games (a request
in flight writes no row, so in-flight would give a sum BELOW N -- Watchara, arc-agi-pub #146), and
in the solo runs a 3,682 s stall printed no 900 s timeout, which a single long request could not
do. See --shape.

⚠️ What `note=` counts is INFERRED. The reading survives three checks and none is decisive alone:
  a) games that finish cleanly give note == tokens EXACTLY, so `note` is not prompt+completion --
     at the 10.7:1 input:output ratio R35 measured that would be ~11.7x on every game, not on none;
  b) the solo `lp85` gap (158,963) matches its measured 3,717 s stall at that run's own token rate;
  c) the ACTIONS total this same regex extracts reproduces the LEDGER table exactly, 17 of 17 runs,
     which is the control printed by --check below: it proves the log is the run the row names.

Reads logs over the API rather than a whole-output download, which writes the log LAST and dies on
the 250 MB `vllm-site-packages` directory. Costs no slot and no GPU.

That trap is avoidable and this module first said it was not. `kernels_output` takes a
`file_pattern` REGEX, so a run's output can be fetched selectively -- measured 2026-08-27 on
`yocybercode/thui-v1-1-r2`, `file_pattern=r".*_usage\.jsonl"` returned all 25 usage files, largest
20 KB, no blob. `kernels_list_files` enumerates first (209 files there). --fetch-usage below is
that call; it is what makes a per-request question answerable on any run carrying thuiv1's probe.

    python eval/abandoned_tokens.py                 # every run, one row each
    python eval/abandoned_tokens.py --check         # + the actions control against LEDGER_ACTIONS
    python eval/abandoned_tokens.py --games v26     # per-game breakdown for one run
    python eval/abandoned_tokens.py --fetch-usage thui-v1-1-r2 --out /tmp/u   # per-request rows
    python eval/abandoned_tokens.py --steps /tmp/u0 /tmp/u1 /tmp/u2   # can a step cap bind?
"""
import argparse
import json
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


FAILED = re.compile(r"analyzer request failed at action (\d+): .*?\(read timeout=([\d.]+)\)")
PER_GAME_CFG = re.compile(r"max_runtime_s_per_game=([\d.]+)")


def timeouts(api, slug):
    """Unique (t, action, read_timeout) triples. Every log duplicates stderr exactly x2."""
    raw = api.kernels_logs(slug)
    raw = raw if isinstance(raw, str) else str(raw)
    recs = json.loads(raw)
    ev = {(round(r.get("time", 0), 2), int(m.group(1)), float(m.group(2)))
          for r in recs for line in r.get("data", "").split("\n")
          if (m := FAILED.search(line))}
    return raw, recs, sorted(ev)


USAGE_PATTERN = r".*_usage\.jsonl"


def fetch_usage(api, run, out_dir):
    """Download ONLY a run's per-request usage rows, not its whole output.

    `kernels_output` takes a file_pattern regex. Without it the call pulls the entire output --
    on these runs 209 files including a 250 MB vllm-site-packages tree -- and dies before it
    writes the log. With it, thui-v1-1-r2's 25 usage files arrive in seconds, largest 20 KB.
    Measured 2026-08-27; the trap had been recorded here as unavoidable.

    Only runs carrying thuiv1's request_usage_probe write these: thui-v1-0, thui-v1-1,
    thui-v1-1-r2. duckv10 does not, so neither solo run has them.
    """
    if run not in RUNS:
        raise SystemExit(f"unknown run {run!r}; known: {', '.join(RUNS)}")
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    api.kernels_output(RUNS[run], str(out), file_pattern=USAGE_PATTERN, page_size=200)
    got = sorted(out.glob("*_usage.jsonl"))
    if not got:
        raise SystemExit(
            f"{run}: no *_usage.jsonl in the output. Only runs carrying thuiv1's probe have them."
        )
    print(f"{run} -> {out}  ({len(got)} files, largest {max(p.stat().st_size for p in got):,} B)")
    for p in got:
        print(f"  {p.name}  {p.stat().st_size:>8,} B")


def steps(dirs):
    r"""Steps per turn, and the token-budget fit, over directories of *_usage.jsonl.

    A turn is one analyze() call, and req_in_turn restarts at 1 in each -- so the runs of rows
    between successive 1s ARE the turns. Feed it directories written by --fetch-usage.

    What it answers: whether a LOCAL_ANALYZER_TOOL_STEPS cap could bind. Measured over the three
    runs that carry the probe (2026-08-27): 3,948 requests, 3,090 turns, and a cap of 12 cuts
    ZERO turns. But the deepest turn anywhere is 11, so the margin is ONE -- the same shape R43
    showed to be untrustworthy for B38's k=20. It did not bind; it is not shown that it cannot.

    The bound is always the 60 s budget, never the count: the six deepest turns are all one game
    (thui-v1-1 bp35, action 63) whose requests cost 4.6-12.0 s against a corpus median of 101.9,
    and each of those turns totals ~60 s. Reaching 12 needs <= 5.0 s per request; the deepest
    turn averaged 5.44.
    """
    import collections, json, pathlib
    per_turn, pts, sums = [], [], {}
    for d in dirs:
        p = pathlib.Path(d)
        files = sorted(p.glob("*_usage.jsonl"))
        if not files:
            raise SystemExit(f"{d}: no *_usage.jsonl -- run --fetch-usage first")
        n, cur_total = 0, 0
        for f in files:
            rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
            if not rows or "req_in_turn" not in rows[0]:
                raise SystemExit(f"{f.name}: no req_in_turn -- not a probe usage file")
            n += len(rows)
            turn = 0
            for r in rows:
                if r["req_in_turn"] == 1:
                    if turn:
                        per_turn.append(turn)
                    turn = 1
                else:
                    turn += 1
                if r.get("completion_tokens") is not None and r.get("wall_s") is not None:
                    pts.append((r["completion_tokens"], r["wall_s"]))
                    cur_total += r["completion_tokens"]
            if turn:
                per_turn.append(turn)
        sums[p.name] = (n, cur_total)
    if sum(per_turn) != sum(v[0] for v in sums.values()):
        raise SystemExit("closure failed: turns do not account for every row")
    dist = collections.Counter(per_turn)
    print(f"requests {sum(v[0] for v in sums.values()):,}   turns {len(per_turn):,}   "
          f"deepest {max(per_turn)}")
    for k in sorted(dist):
        print(f"  {k:>3} steps: {dist[k]:>5}")
    for cap in (2, 4, 5, 12):
        print(f"  cap={cap:<3} cuts {sum(v for k, v in dist.items() if k > cap):>5} turns")
    # wall_s = a + b*completion_tokens. #65 measured -1.6 + 0.0786x, R^2 0.9835 on thui-v1-1-r2.
    n = len(pts); mx = sum(p[0] for p in pts)/n; my = sum(p[1] for p in pts)/n
    b = sum((x-mx)*(y-my) for x, y in pts) / sum((x-mx)**2 for x, _ in pts)
    a = my - b*mx
    ss_res = sum((y-(a+b*x))**2 for x, y in pts)
    ss_tot = sum((y-my)**2 for _, y in pts)
    print(f"\nwall_s = {a:.2f} + {b:.4f} * completion_tokens   R^2 {1-ss_res/ss_tot:.4f}   "
          f"decode {1/b:.1f} tok/s   60 s ~= {(60-a)/b:.0f} tokens")
    for name, (rows, ct) in sums.items():
        print(f"  {name}: {rows:,} rows, {ct:,} completion tokens")


def shape(api):
    """B46 -- which of the two candidate mechanisms the abandoned generation is in.

    Split the only error line any run prints by its read-timeout VALUE:
      == 900.0  a request killed at analyzer_timeout, mid-run. The action RETRIES: v26 fires
                action 18 at t=6434.8 and 7335.9, 48 at 6660.6 and 7561.8, 37 at 6813.4 and
                7714.5 -- deltas 901.1 / 901.2 / 901.1, and nothing bounds the count.
      <  900.0  the terminal cancellation at the wall, one per game still mid-request. Always
                inside the last 1% of the run; the value is the budget that was left.

    Then ask whether those two account for the abandonment, pricing each interval at the run's
    average per-game token rate. They do not: the residual is the work inside actions that never
    terminated, with LOCAL_ANALYZER_TOOL_STEPS = 0.

    WARNING: this module first said the loop is "bounded by nothing but the game wall". The
    tool-step loop also carries LOCAL_ANALYZER_YIELD_SECONDS = 60, checked at the TOP of every
    iteration (tool_agent.py:2161,2167), so at the measured 72-126 s per request it breaks after
    ONE step and a cap of 12 could never bind. Whether the runaway is that loop or the outer turn
    loop (solver.py:316, which has no counter on any of its three no-action continues) is
    UNRESOLVED; req_in_turn in the banked usage rows separates them. See the LEDGER section
    "Can a TOOL_STEPS cap even bind".

    The residual is an ESTIMATE for a 25-game run (a hung request may generate at a rate other
    than the average). It is NOT an estimate for the solo runs: they log zero hangs, so there is
    nothing to model and ~98% of their abandonment is measured directly.
    """
    print(f"{'run':14s} {'wall(cfg)':>9} {'wall(log)':>9} {'hung':>5} {'term':>5} "
          f"{'abandoned':>10} {'hung tok':>9} {'term tok':>8} {'RESIDUAL':>10} {'%':>5}")
    for name, slug in RUNS.items():
        raw, recs, ev = timeouts(api, slug)
        rows = games(api, slug)
        n = len(rows)
        gen = sum(r[5] for r in rows)
        aband = gen - sum(r[4] for r in rows)
        t0 = min((r["time"] for r in recs if "benchmark.label" in r.get("data", "")), default=0)
        t1 = max((r["time"] for r in recs if "[finished]" in r.get("data", "")), default=0)
        wall_log = t1 - t0
        wall_cfg = float(PER_GAME_CFG.findall(raw)[0])
        rate = gen / n / wall_log
        hung_ev = [e for e in ev if abs(e[2] - 900.0) < 0.01]
        term_ev = [e for e in ev if abs(e[2] - 900.0) >= 0.01]
        hung = 900.0 * len(hung_ev) * rate
        term = sum(e[2] for e in term_ev) * rate
        res = aband - hung - term
        # The config echo is printed BEFORE any override lands: clock2x says 7920 and gave its
        # games 15,890 s. Flag it rather than trusting either number silently.
        flag = "  <- cfg != actual" if abs(wall_cfg - wall_log) > 300 else ""
        print(f"{name:14s} {wall_cfg:>9.0f} {wall_log:>9.0f} {len(hung_ev):>5} {len(term_ev):>5} "
              f"{aband:>10,} {hung:>9,.0f} {term:>8,.0f} {res:>10,.0f} "
              f"{100.0 * res / aband:>4.0f}%{flag}")

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="assert actions match LEDGER_ACTIONS")
    ap.add_argument("--games", metavar="RUN", help="per-game breakdown for one run")
    ap.add_argument("--fetch-usage", metavar="RUN", dest="fetch_usage",
                    help="download ONLY that run's *_usage.jsonl (needs --out)")
    ap.add_argument("--out", default="usage", help="directory for --fetch-usage")
    ap.add_argument("--steps", nargs="+", metavar="DIR",
                    help="steps per turn + the token-budget fit over --fetch-usage dirs")
    ap.add_argument("--shape", action="store_true",
                    help="B46: split the abandonment into hung / terminal / unbounded-loop")
    args = ap.parse_args()
    api = _api()

    if args.steps:
        steps(args.steps)
        return

    if args.fetch_usage:
        fetch_usage(api, args.fetch_usage, args.out)
        return

    if args.shape:
        shape(api)
        return

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
