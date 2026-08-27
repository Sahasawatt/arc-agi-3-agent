#!/usr/bin/env python3
"""R48: what the yield knob actually moved -- chunking, not depth.

B48 raised `LOCAL_ANALYZER_YIELD_SECONDS` 60 -> 180 and closed NOT MEASURABLE on score
(4.01 vs 4.33, p = 0.54..0.81, levels 23 = 23). R47 proved the gate itself moved. Neither
answered what the agent DID with the budget, because `*_usage.jsonl` carries no decision
boundary -- only requests and turns.

The event logs carry both, and they are two different groupings that the repo calls by two
different names:

    analysis_step   -- the decision. 428 in thuiv1-1r2.
    analysis event  -- one analyze() call, i.e. one reasoning round. 1,070 in the same run.

⚠️ THE UNIT IS THE WHOLE FINDING, so the selftest gates on it. `scripts/b27/corpus.py` and
`scripts/b27/r44_turn_budget.py` both mean the SECOND one when they say "turn" -- corpus.py
counts analysis events and validates against R29's 1,973 / 5,052, and R44's published
`turns = 1070` equals this run's analysis-event count exactly while its `requests = 1306`
equals the usage-row count exactly. A parser that grouped by `analysis_step` instead would
produce a plausible table 2.5x off in the right units, and nothing downstream would catch it.

What it measures: reasoning rounds per decision, and the text spent per decision, for every
run on disk that carries an events log -- against the one run that moved the knob.

Usage:
    python3 scripts/b27/r48_chunking.py --selftest
    python3 scripts/b27/r48_chunking.py --treated /path/to/notes/runs/thui-v3-0
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import statistics
import sys

BASE = os.path.expanduser("~/Claude/arc-artifacts")

# Published figures this instrument must reproduce before it is allowed to report anything.
# Sources: notes/R44-the-turn-budget-is-a-token-budget.md (requests/turns);
# scripts/b27/corpus.py (PAIR/ALL5/run-games, themselves validated against R29).
GATE = {
    "r44_requests": 1306,
    "r44_turns": 1070,
    "corpus_pair": 1973,
    "corpus_all5": 5052,
    "corpus_games": 125,
}
RUNS5 = ["v10cal", "thuiv1", "v18", "v19", "v23"]

# yield=60 confirmed by the run's own taaf_setup_env.json. thuiv1 and v10cal predate that
# artifact, so they are carried separately and labelled INFERRED -- never folded into a
# figure quoted as measured.
COHORT_CONFIRMED = ["thuiv1-1r2", "clock2x", "v18", "v19", "v23", "v25seed"]
COHORT_INFERRED = ["thuiv1", "v10cal"]


def load_events(path: str) -> list[dict]:
    out = []
    for line in open(path, errors="replace"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def game_files(root: str) -> list[str]:
    return sorted(glob.glob(os.path.join(os.path.expanduser(root), "artifacts", "*_events.jsonl")))


def per_game(root: str) -> dict[str, dict]:
    """Per game: decisions (analysis_step), rounds (analysis events), transcript chars, actions."""
    out = {}
    for p in game_files(root):
        rows = load_events(p)
        steps = {r["analysis_step"] for r in rows if r.get("analysis_step") is not None}
        rounds = [r for r in rows if r.get("type") == "analysis"]
        out[os.path.basename(p).split("_p0_events.jsonl")[0]] = {
            "decisions": len(steps),
            "rounds": len(rounds),
            "chars": sum(len(str(r.get("transcript") or "")) for r in rounds),
            "actions": sum(1 for r in rows if r.get("type") == "action"),
            "levels": max((r.get("score") or 0) for r in rows) if rows else 0,
        }
    return out


def totals(d: dict) -> dict:
    t = {k: sum(g[k] for g in d.values()) for k in ("decisions", "rounds", "chars", "actions", "levels")}
    t["games"] = len(d)
    t["rounds_per_decision"] = t["rounds"] / t["decisions"] if t["decisions"] else 0.0
    return t


def usage_rows(root: str) -> int:
    n = 0
    for f in sorted(glob.glob(os.path.join(os.path.expanduser(root), "*_usage.jsonl"))):
        n += sum(1 for line in open(f, errors="replace") if line.strip())
    return n


def sign_test(a: list[float], b: list[float]) -> tuple[int, int, int, float]:
    """Two-sided exact binomial on the paired directions. Ties are dropped, which is the
    conservative choice -- a tie cannot support either direction."""
    down = sum(1 for x, y in zip(a, b) if y < x)
    up = sum(1 for x, y in zip(a, b) if y > x)
    n = down + up
    if n == 0:
        return down, up, 0, 1.0
    k = max(down, up)
    p = 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return down, up, n, min(p, 1.0)


def selftest() -> int:
    """Reproduce the published mapping. A miss here means the grouping is wrong and every
    number below it would be wrong in the right units."""
    fails = []

    # Control 0 -- the corpus is reachable at all. A zero here reads exactly like a clean
    # result from a broken path, so it fails loudly rather than reporting 0 of 0.
    if not os.path.isdir(BASE):
        print(f"FAIL control-0: corpus root missing: {BASE}")
        return 1
    seen = {r: len(game_files(os.path.join(BASE, r))) for r in RUNS5}
    if sum(seen.values()) == 0:
        print(f"FAIL control-0: no event logs under {BASE} for {RUNS5}")
        return 1
    print(f"ok  control-0  event logs reachable: {seen}")

    # Control 1 -- negative. A run that does not exist must come back empty, or the loader
    # is matching something it should not and every cohort figure is suspect.
    if game_files(os.path.join(BASE, "no-such-run-xyz")):
        print("FAIL control-1: a nonexistent run returned files")
        return 1
    print("ok  control-1  nonexistent run returns nothing")

    # Gate A -- R44's own two numbers, on R44's own run.
    ref = per_game(os.path.join(BASE, "thuiv1-1r2"))
    t = totals(ref)
    req = usage_rows(os.path.join(BASE, "thuiv1-1r2"))
    for name, got, want in (
        ("r44_requests (usage rows)", req, GATE["r44_requests"]),
        ("r44_turns (analysis events)", t["rounds"], GATE["r44_turns"]),
    ):
        ok = got == want
        print(f"{'ok ' if ok else 'FAIL'} gate-A  {name}: {got} (R44 says {want})")
        if not ok:
            fails.append(name)

    # Gate B -- corpus.py's counts, which are themselves gated on R29. This is what pins
    # "turn == analysis event" as the repo-wide convention rather than this file's opinion.
    pair = sum(totals(per_game(os.path.join(BASE, r)))["rounds"] for r in ("v10cal", "thuiv1"))
    all5 = sum(totals(per_game(os.path.join(BASE, r)))["rounds"] for r in RUNS5)
    games = sum(totals(per_game(os.path.join(BASE, r)))["games"] for r in RUNS5)
    for name, got, want in (
        ("corpus PAIR v10cal+thuiv1", pair, GATE["corpus_pair"]),
        ("corpus ALL5", all5, GATE["corpus_all5"]),
        ("corpus run-games", games, GATE["corpus_games"]),
    ):
        ok = got == want
        print(f"{'ok ' if ok else 'FAIL'} gate-B  {name}: {got} (corpus.py says {want})")
        if not ok:
            fails.append(name)

    # Gate C -- the two groupings must actually differ, or this instrument is measuring
    # nothing. 428 decisions against 1,070 rounds is the whole premise.
    ok = t["decisions"] < t["rounds"]
    print(f"{'ok ' if ok else 'FAIL'} gate-C  decisions {t['decisions']} < rounds {t['rounds']}")
    if not ok:
        fails.append("gate-C")

    print()
    if fails:
        print(f"SELFTEST FAILED: {', '.join(fails)}")
        return 1
    print("SELFTEST PASSED -- the grouping reproduces every published figure it can be checked against")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--treated", default=None, help="path to the yield=180 run (thui-v3-0)")
    ap.add_argument("--baseline", default="thuiv1-1r2", help="paired yield=60 arm")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if selftest() != 0:
        return 1
    if not a.treated:
        sys.exit("--treated is required (path to the yield=180 run)")
    print()

    rows = []
    for label, run in (
        *[(f"{r} (60 confirmed)", os.path.join(BASE, r)) for r in COHORT_CONFIRMED],
        *[(f"{r} (60 INFERRED)", os.path.join(BASE, r)) for r in COHORT_INFERRED],
    ):
        d = per_game(run)
        if d:
            rows.append((label, totals(d), "confirmed" if "confirmed" in label else "inferred"))
    treated = per_game(a.treated)
    if not treated:
        sys.exit(f"no event logs under {a.treated}/artifacts")
    rows.append(("thui-v3-0 (180 confirmed)", totals(treated), "treated"))

    print(f"{'run':<28}{'games':>6}{'decisions':>11}{'rounds':>8}{'rounds/dec':>12}{'chars/dec':>12}{'act/dec':>9}")
    for label, t, _ in rows:
        print(f"{label:<28}{t['games']:>6}{t['decisions']:>11}{t['rounds']:>8}"
              f"{t['rounds_per_decision']:>12.2f}{t['chars']/t['decisions']:>12,.0f}"
              f"{t['actions']/t['decisions']:>9.2f}")

    conf = [t["rounds_per_decision"] for _, t, k in rows if k == "confirmed"]
    infr = [t["rounds_per_decision"] for _, t, k in rows if k == "inferred"]
    tr = rows[-1][1]["rounds_per_decision"]
    m, s = statistics.mean(conf), statistics.stdev(conf)
    print(f"\nyield=60 CONFIRMED cohort (n={len(conf)}): mean {m:.2f}  sd {s:.3f}  range {min(conf):.2f}-{max(conf):.2f}")
    print(f"yield=60 inferred, carried separately (n={len(infr)}): {', '.join(f'{x:.2f}' for x in infr)}")
    print(f"yield=180 (n=1): {tr:.2f}   z against the confirmed cohort = {(tr - m) / s:+.2f}")

    base = per_game(os.path.join(BASE, a.baseline))
    shared = sorted(set(base) & set(treated))
    print(f"\npaired on {len(shared)} games shared with {a.baseline} "
          f"(control: {len(base)} baseline games, {len(treated)} treated games)")
    pa = [base[g]["rounds"] / base[g]["decisions"] for g in shared if base[g]["decisions"]]
    pb = [treated[g]["rounds"] / treated[g]["decisions"] for g in shared if base[g]["decisions"]]
    down, up, n, p = sign_test(pa, pb)
    print(f"rounds/decision fell in {down} of {n} non-tied games (rose in {up})  two-sided exact p = {p:.5f}")
    print(f"levels: baseline {totals(base)['levels']}  treated {totals(treated)['levels']}")
    print("\n⚠️  n = 1 at the treated setting. The cohort bounds the NULL spread; it does not")
    print("    estimate the spread of a 180 s run. And this measures the MECHANISM only --")
    print("    levels are identical, so nothing here explains the score.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
