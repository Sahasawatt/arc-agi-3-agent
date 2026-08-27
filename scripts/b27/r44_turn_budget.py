#!/usr/bin/env python3
"""R44's turn-budget measurement, over N runs instead of one.

R44 measured the yield loop on `thui-v1-1-r2` alone and said so loudly: *"n = 1 run. No other
run carries the probe."* `thui-v3-0` (B48) is the second, and it is not a repeat -- it ran with
`LOCAL_ANALYZER_YIELD_SECONDS` at **180** where every earlier run had **60**. So the pair is not
two samples of one quantity; it is the same mechanism observed at two settings of its own knob,
which is the only shape that can test R44 section 6.

Section 6 refused to build a counterfactual: predicting how many turns reach iteration 2 from
each turn's first-request time over-predicted by 43% at YIELD=60 (266 predicted, 186 observed),
because 95% of the gap was turns that ended CORRECTLY on `tool_calls`. It could not tell an
inflated rule from a wrong one with a single value on the x-axis. There are two now.

⚠️ THE INSTRUMENT'S OWN CONTROL COMES FIRST. `--selftest` re-derives R44's published figures
from the same corpus and refuses to run if any of them misses. A parser that groups turns
slightly differently produces a plausible table on the new run and nothing would catch it --
the failure mode is a number in the right units, not a crash.

Usage:
    python3 scripts/b27/r44_turn_budget.py --selftest
    python3 scripts/b27/r44_turn_budget.py \
        "v1-1-r2=60=$HOME/Claude/arc-artifacts/thuiv1-1r2" \
        "v3-0=180=/path/to/notes/runs/thui-v3-0"
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys

# R44's published figures, for the selftest. Sources: notes/R44-the-turn-budget-is-a-token-budget.md
# sections 1, 3, 4, 5 and 6. Tolerances are the note's own rounding, never a fudge factor.
R44 = {
    "requests": 1306, "turns": 1070, "multi": 186, "depth": {1: 1070, 2: 186, 3: 40, 4: 9, 5: 1},
    "gate_hold": 100.0, "ctrl_a": 91.0, "ctrl_b": 5.9, "tok_s": 12.7, "r2": 0.9835,
    "median_completion": 1368, "median_prompt": 22349, "none_completion": 30,
    "cf_predicted": 266, "cf_observed": 186,
}


def load(d: str) -> list[dict]:
    fs = sorted(glob.glob(os.path.join(os.path.expanduser(d), "*_usage.jsonl")))
    if not fs:
        sys.exit(f"no *_usage.jsonl under {d}")
    rows = []
    for f in fs:
        for line in open(f):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def turns(rows: list[dict]) -> list[list[dict]]:
    """Group into analyze() calls. A turn starts wherever req_in_turn resets to 1; rows are kept
    in file order, which is emission order within a game."""
    out, cur = [], []
    for r in rows:
        if r.get("req_in_turn") == 1 and cur:
            out.append(cur); cur = []
        cur.append(r)
    if cur:
        out.append(cur)
    return out


def fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Least squares y = a + b*x, returned with R^2. Two lines of algebra beats a dependency."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    a = my - b * mx
    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return a, b, 1 - ss_res / ss_tot


def measure(rows: list[dict], y: float) -> dict:
    ts = turns(rows)
    multi = [t for t in ts if len(t) > 1]
    single = [t for t in ts if len(t) == 1]
    depth = {}
    for r in rows:
        k = r.get("req_in_turn")
        depth[k] = depth.get(k, 0) + 1

    def cum_but_last(t):
        return sum(r["wall_s"] for r in t[:-1])

    hold = sum(1 for t in multi if cum_but_last(t) < y)
    ctrl_a = sum(1 for t in single if t[0]["wall_s"] > y)
    ctrl_b = sum(1 for t in multi if sum(r["wall_s"] for r in t) < y)

    usable = [r for r in rows if r.get("completion_tokens") is not None]
    a, b, r2 = fit([float(r["completion_tokens"]) for r in usable],
                   [float(r["wall_s"]) for r in usable])

    # section 6's rule, applied at THIS run's own yield: a turn should reach iteration 2 whenever
    # its first request finished inside the budget.
    cf_pred = sum(1 for t in ts if t[0]["wall_s"] < y)
    gap = [t for t in ts if t[0]["wall_s"] < y and len(t) == 1]
    gap_toolcalls = sum(1 for t in gap if t[0].get("finish_reason") == "tool_calls")

    return {
        "requests": len(rows), "turns": len(ts), "multi": len(multi), "single": len(single),
        "depth": depth, "max_depth": max(depth), "games": len({r["game"] for r in rows}),
        "gate_hold": 100.0 * hold / len(multi) if multi else float("nan"), "gate_hold_n": hold,
        "ctrl_a": 100.0 * ctrl_a / len(single) if single else float("nan"), "ctrl_a_n": ctrl_a,
        "ctrl_b": 100.0 * ctrl_b / len(multi) if multi else float("nan"),
        "intercept": a, "slope": b, "r2": r2, "tok_s": 1 / b,
        "median_completion": statistics.median(r["completion_tokens"] for r in usable),
        "median_prompt": statistics.median(r["prompt_tokens"] for r in usable),
        "none_completion": len(rows) - len(usable),
        "budget_tokens": (y - a) / b,
        "over_budget_pct": 100.0 * sum(1 for r in usable if r["wall_s"] > y) / len(usable),
        "cf_pred": cf_pred, "cf_obs": len(multi),
        "cf_gap": len(gap), "cf_gap_toolcalls": gap_toolcalls,
        "req_per_turn": len(rows) / len(ts),
        "timeouts": sum(1 for r in rows if str(r.get("finish_reason", "")).startswith("__exception__")),
    }


def cross_gate(rows: list[dict], y: float) -> tuple[int, int]:
    """How many of THIS run's multi-request turns would have satisfied gate `y`?
    The discriminating test the n=1 corpus could not run: if the bound is really
    LOCAL_ANALYZER_YIELD_SECONDS, then a run at 180 must hold at 180 and must BREAK 60."""
    multi = [t for t in turns(rows) if len(t) > 1]
    return sum(1 for t in multi if sum(r["wall_s"] for r in t[:-1]) < y), len(multi)


def selftest() -> int:
    d = os.path.expanduser("~/Claude/arc-artifacts/thuiv1-1r2")
    if not glob.glob(os.path.join(d, "*_usage.jsonl")):
        sys.exit("SELFTEST CANNOT RUN: the n=1 corpus is not on this disk. That is not a pass.")
    m = measure(load(d), 60.0)
    checks = [
        ("requests", m["requests"], R44["requests"], 0),
        ("analyze() calls", m["turns"], R44["turns"], 0),
        ("multi-request turns", m["multi"], R44["multi"], 0),
        ("gate hold %", m["gate_hold"], R44["gate_hold"], 0.05),
        ("CONTROL A %", m["ctrl_a"], R44["ctrl_a"], 0.05),
        ("CONTROL B %", m["ctrl_b"], R44["ctrl_b"], 0.05),
        ("decode tok/s", m["tok_s"], R44["tok_s"], 0.05),
        ("fit R^2", m["r2"], R44["r2"], 0.0005),
        ("median completion", m["median_completion"], R44["median_completion"], 0.5),
        ("median prompt", m["median_prompt"], R44["median_prompt"], 0.5),
        ("None completion", m["none_completion"], R44["none_completion"], 0),
        ("s6 predicted", m["cf_pred"], R44["cf_predicted"], 0),
        ("s6 observed", m["cf_obs"], R44["cf_observed"], 0),
    ]
    bad = 0
    for name, got, want, tol in checks:
        ok = abs(got - want) <= tol
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:<22} got {got!r:>12}  R44 says {want!r}")
    if m["depth"] != R44["depth"]:
        print(f"  FAIL  req_in_turn depth        got {m['depth']}  R44 says {R44['depth']}"); bad += 1
    else:
        print(f"  ok    req_in_turn depth        {m['depth']}")
    # negative control: the gate must NOT hold at an absurd budget, or "100%" means nothing
    hold_1s, n = cross_gate(load(d), 1.0)
    ok = hold_1s < n
    print(f"  {'ok  ' if ok else 'FAIL'}  negative control       gate at 1s holds {hold_1s}/{n} (must be < {n})")
    bad += not ok
    if bad:
        print(f"\nSELFTEST FAILED ({bad}) -- this parser does not reproduce R44. Its numbers on any\n"
              "other run are not comparable to R44's and must not be published.")
        return 1
    print("\nSELFTEST OK: the parser reproduces every published R44 figure; n>1 output is comparable.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("runs", nargs="*", help="label=yield_seconds=dir")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.runs:
        ap.error("give at least one label=yield=dir, or --selftest")

    specs = []
    for s in a.runs:
        label, y, d = s.split("=", 2)
        specs.append((label, float(y), load(d)))

    ms = [(label, y, measure(rows, y)) for label, y, rows in specs]
    w = max(len(l) for l, _, _ in ms) + 2

    def row(name, f):
        print(f"  {name:<26}" + "".join(f"{f(m):>{w+12}}" for _, _, m in ms))

    print("\n=== corpus ===")
    print(f"  {'':<26}" + "".join(f"{l+' (Y='+str(int(y))+')':>{w+12}}" for l, y, _ in ms))
    row("games", lambda m: m["games"])
    row("requests", lambda m: m["requests"])
    row("analyze() calls", lambda m: m["turns"])
    row("requests / call", lambda m: f"{m['req_per_turn']:.2f}")
    row("max req_in_turn", lambda m: m["max_depth"])
    row("__exception__ rows", lambda m: m["timeouts"])

    print("\n=== the gate, each run read at ITS OWN yield ===")
    row("multi-request turns", lambda m: m["multi"])
    row("  cum(but last) < Y", lambda m: f"{m['gate_hold_n']}/{m['multi']} = {m['gate_hold']:.1f}%")
    row("CONTROL A  1-req > Y", lambda m: f"{m['ctrl_a']:.1f}%")
    row("CONTROL B  cum(all)<Y", lambda m: f"{m['ctrl_b']:.1f}%")

    print("\n=== decode fit (a property of the MACHINE, so it doubles as a control) ===")
    row("tok/s", lambda m: f"{m['tok_s']:.1f}")
    row("R^2", lambda m: f"{m['r2']:.4f}")
    row("median completion tok", lambda m: m["median_completion"])
    row("Y buys (tokens)", lambda m: f"{m['budget_tokens']:.0f}")
    row("median / budget", lambda m: f"{m['median_completion'] / m['budget_tokens']:.2f}x")
    row("requests over Y", lambda m: f"{m['over_budget_pct']:.1f}%")

    print("\n=== R44 section 6: the counterfactual, now at TWO values ===")
    row("predicted reach iter2", lambda m: m["cf_pred"])
    row("observed reach iter2", lambda m: m["cf_obs"])
    row("over-prediction", lambda m: f"{100.0 * (m['cf_pred'] - m['cf_obs']) / m['cf_obs']:.0f}%")
    row("gap ending tool_calls", lambda m: f"{m['cf_gap_toolcalls']}/{m['cf_gap']}"
        + (f" = {100.0 * m['cf_gap_toolcalls'] / m['cf_gap']:.0f}%" if m["cf_gap"] else ""))

    if len(ms) > 1:
        print("\n=== CROSS-GATE: does each run's bound move with the knob? ===")
        print("  (a run at Y must hold at Y and BREAK the other run's Y -- otherwise the bound")
        print("   is not the knob, and R44 section 3 measured a coincidence)")
        ys = sorted({y for _, y, _ in ms})
        for label, own_y, rows in specs:
            for y in ys:
                h, n = cross_gate(rows, y)
                tag = " <- own" if y == own_y else ""
                print(f"    {label:<10} gate {int(y):>4}s: {h:>4}/{n} = {100.0*h/n:5.1f}%{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
