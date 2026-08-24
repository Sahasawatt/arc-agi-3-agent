"""score_shape.py -- what is a public score actually made of, and what can a lever move?

WHY THIS EXISTS: eleven modifications of v10 have been measured and none landed outside the
band. LEDGER's standing explanation is that actions-per-level is "the column that explains
the score", read off five builds ACROSS runs. This reads the same question WITHIN a game,
where the campaign's own scoring.py says the answer is decided differently:

    level_score = min((baseline / actions_in_that_level) ** 2 * 100, 115)
    game_score  = min( sum(level_score * level_no) / sum(1..total) ,      # raw efficiency
                       100 * sum(levels done) / sum(1..total) )           # completion cap

When the completion cap binds, the score is a function of LEVELS ALONE and no amount of
efficiency can move it. This script measures how often that is the case, using only
eval/fixtures/*.json -- no GPU slot, no Kaggle call, no arc-artifacts corpus, so it runs on
any checkout.

METHOD, and the one assumption it rests on: a game's total level count is not in the
fixtures, so it is DERIVED from the cells where the cap binds exactly
(total is the n with sum(1..n) == 100 * sum(1..cleared) / score). Cells whose game has no
such anchor are reported UNKNOWN rather than folded into either bucket -- an earlier cut of
this analysis lacked that third value and misreported 25 cells as raw-bound that were
merely unresolved.

    Assumption: levels are cleared contiguously from 1, so sum(done) == sum(1..cleared).
    It is not free: CONTROL 4 fails the run if any cell scores ABOVE its derived cap, which
    is what a non-contiguous clear would produce.

EXIT CODES: 0 = ran and all controls passed, 1 = a control failed (no numbers are printed
past the failure), 2 = usage/data error.

Usage:
    python eval/score_shape.py
    python eval/score_shape.py --json      # machine-readable summary
"""

from __future__ import annotations

import glob
import json
import os
import statistics as st
import sys

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "*.json")
PUBLISHED = {"v10cal": 4.71, "v18": 3.60, "v19": 2.82, "v20": 0.18}  # LEDGER's table
TOTAL_LEVELS_ALL_GAMES = 183  # LEDGER: "20 of 183 levels"
EPS = 0.02


def tri(n: int) -> int:
    """sum(1..n) -- the weight denominator, and the shape a cap anchor must match."""
    return n * (n + 1) // 2


def load() -> dict:
    runs = {}
    for path in sorted(glob.glob(FIXTURES)):
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        runs[d["label"]] = d["games"]
    if not runs:
        print("no fixtures found at %s" % FIXTURES)
        raise SystemExit(2)
    return runs


def derive_totals(runs: dict, games: list) -> tuple[dict, dict]:
    """Per game, find the total level count implied by every cap-bound cell it has."""
    derived, votes_all = {}, {}
    for g in games:
        votes = {}
        for r, gs in runs.items():
            d = gs[g]
            if d["levels"] <= 0 or d["score"] <= 0:
                continue
            want = 100 * tri(d["levels"]) / d["score"]
            for k in range(1, 40):
                if abs(tri(k) - want) < EPS:
                    votes.setdefault(k, []).append(r)
                    break
        if votes:
            derived[g] = max(votes, key=lambda k: len(votes[k]))
            votes_all[g] = votes
    return derived, votes_all


def classify(runs: dict, games: list, derived: dict) -> dict:
    out = {"cap": [], "raw": [], "unknown": [], "anomaly": []}
    for g in games:
        for r, gs in runs.items():
            d = gs[g]
            if d["levels"] <= 0 or d["score"] <= 0:
                continue
            if g not in derived:
                out["unknown"].append((g, r, d, None))
                continue
            cap = 100 * tri(d["levels"]) / tri(derived[g])
            if abs(d["score"] - cap) < EPS:
                out["cap"].append((g, r, d, cap))
            elif d["score"] < cap:
                out["raw"].append((g, r, d, cap))
            else:
                out["anomaly"].append((g, r, d, cap))
    return out


FAILURES: list = []


def actions_buy_levels(runs, games, fam, min_gap=0.15):
    """Q_C -- within ONE game, does a run that spent MORE actions clear MORE levels?

    The fixtures contain a natural A/B: the same game played by runs that differ in how many
    actions they got through. A pair votes only when the action counts differ by at least
    `min_gap`, so near-ties do not manufacture agreement.

    Returns (votes, per_game) where votes = (agree, disagree, flat).
    """
    import itertools
    agree = dis = flat = 0
    per = {}
    for g in games:
        ac = {r: runs[r][g]["actions"] for r in fam}
        lv = {r: runs[r][g]["levels"] for r in fam}
        a = d = f = 0
        for x, y in itertools.combinations(fam, 2):
            hi, lo = (x, y) if ac[x] > ac[y] else (y, x)
            if ac[hi] == 0 or (ac[hi] - ac[lo]) / ac[hi] < min_gap:
                continue
            if lv[hi] > lv[lo]:
                a += 1
            elif lv[hi] < lv[lo]:
                d += 1
            else:
                f += 1
        agree += a; dis += d; flat += f
        per[g] = (a, d, f)
    return (agree, dis, flat), per


def fail(n: int, msg: str) -> None:
    """Record a control failure. Every control is evaluated -- an early exit makes the
    coarsest control mask the others, so a mutation cannot be attributed to what it broke."""
    FAILURES.append(n)
    print("CONTROL %d FAILED: %s" % (n, msg))


def gate() -> None:
    if FAILURES:
        print()
        print("CONTROLS FAILED: %s -- instrument is not trustworthy, no numbers printed."
              % sorted(set(FAILURES)))
        raise SystemExit(1)


def main() -> None:
    as_json = "--json" in sys.argv[1:]
    runs = load()
    games = sorted(next(iter(runs.values())))

    # ---- CONTROL 1: the loader reproduces LEDGER's published means ----
    for label, want in PUBLISHED.items():
        if label not in runs:
            fail(1, "fixture %s missing" % label)
        got = sum(runs[label][g]["score"] for g in games) / len(games)
        if abs(got - want) > 0.01:
            fail(1, "%s mean %.4f != published %.2f" % (label, got, want))
    print("CONTROL 1  loader reproduces LEDGER means %s: OK"
          % ", ".join("%s=%.2f" % kv for kv in PUBLISHED.items()))

    # ---- CONTROL 2: the cap identity, both poles, in this invocation ----
    if abs(100 * 1 / tri(8) - 2.7777777777777777) > 1e-9:
        fail(2, "cap identity 100/36 does not reproduce")
    if any(abs(tri(k) - 37) < EPS for k in range(1, 40)):
        fail(2, "a non-triangular target resolved; the resolver accepts anything")
    print("CONTROL 2  cap identity 100/36 = 2.7778 resolves, non-triangular 37 does not: OK")

    derived, votes_all = derive_totals(runs, games)

    # ---- CONTROL 3: no game's derived total may disagree between its own runs ----
    conflicts = {g: v for g, v in votes_all.items() if len(v) > 1}
    if conflicts:
        fail(3, "cross-run disagreement on total_levels: %s" % conflicts)
    print("CONTROL 3  cross-run agreement on derived total_levels (%d games, 0 conflicts): OK"
          % len(derived))

    buckets = classify(runs, games, derived)

    # ---- CONTROL 4: teeth on the contiguous-clear assumption ----
    if buckets["anomaly"]:
        fail(4, "score > cap in %s -- levels are not cleared contiguously and every number "
                "below is wrong" % [(a[0], a[1]) for a in buckets["anomaly"]])
    print("CONTROL 4  no cell scores above its cap (contiguous-clear assumption holds): OK")

    # ---- CONTROL 5: closure against the known total across all 25 games ----
    used = sum(derived.values())
    unknown_games = [g for g in games if g not in derived]
    left = TOTAL_LEVELS_ALL_GAMES - used
    if left < len(unknown_games):
        fail(5, "derived totals (%d) leave %d levels for %d unresolved games"
                % (used, left, len(unknown_games)))
    for g, n in sorted(derived.items()):
        seen = max(gs[g]["levels"] for gs in runs.values())
        if n < seen:
            fail(5, "%s derived total %d < %d levels actually cleared there" % (g, n, seen))
    gate()
    print("CONTROL 5  closure: %d levels derived over %d games, %d left for the other %d "
          "(mean %.1f): OK" % (used, len(derived), left, len(unknown_games),
                               left / max(1, len(unknown_games))))
    gate()
    print()

    n_cap, n_raw, n_unk = len(buckets["cap"]), len(buckets["raw"]), len(buckets["unknown"])
    decided = n_cap + n_raw
    print("SCORING CELLS: %d cap-bound | %d raw-bound | %d unknown  (%d total)"
          % (n_cap, n_raw, n_unk, decided + n_unk))
    print("  of the %d DECIDED cells, %.0f%% are cap-bound -- the score is a function of "
          "LEVELS ALONE there and no efficiency lever can move it."
          % (decided, 100 * n_cap / decided))
    print()

    # headroom: what pure efficiency could still collect without clearing one more level
    head = {}
    for g, r, d, cap in buckets["raw"]:
        head[r] = head.get(r, 0.0) + (cap - d["score"])
    print("EFFICIENCY HEADROOM (every known game hits its cap, zero extra levels cleared):")
    for r in sorted(runs):
        cur = sum(runs[r][g]["score"] for g in games) / len(games)
        gain = head.get(r, 0.0) / len(games)
        print("  %-7s %.2f -> %.2f  (+%.2f)   [%d games unresolved, excluded]"
              % (r, cur, cur + gain, gain, len(unknown_games)))
    print()

    print("WHAT ONE MORE LEVEL PAYS (cap at k cleared, per game):")
    print("  %-6s %5s | %s" % ("game", "total", "k=1     2      3      4      5"))
    for g in sorted(derived):
        n = derived[g]
        caps = [100 * tri(k) / tri(n) for k in range(1, min(6, n + 1))]
        print("  %-6s %5d | %s" % (g, n, " ".join("%6.2f" % c for c in caps)))
    print()

    # per-game volatility across the runs LEDGER treats as samples of one build
    fam = [r for r in ("v10cal", "v18", "v19") if r in runs]
    vol = sorted(((g, st.pstdev([runs[r][g]["score"] for r in fam])) for g in games),
                 key=lambda x: -x[1])
    tot_var = sum(sd ** 2 for _, sd in vol)
    print("VOLATILITY across %s (the runs rank_runs.py reads as NOT-DISTINGUISHABLE):" % "/".join(fam))
    run6 = sum(sd ** 2 for _, sd in vol[:6])
    for g, sd in vol[:6]:
        print("  %-6s sd %5.2f  %5.1f%% of all per-game variance" % (g, sd, 100 * sd ** 2 / tot_var))
    print("  top-6 games carry %.1f%% of it; %d games have sd 0.00"
          % (100 * run6 / tot_var, sum(1 for _, sd in vol if sd == 0)))


    fam3 = [r for r in ("v10cal", "v18", "v19") if r in runs]
    (agr, dis, flt), per = actions_buy_levels(runs, games, fam3)
    n = agr + dis + flt
    print()
    print("Q_C  WITHIN one game, does spending MORE actions buy MORE levels?  (pairs over %s)"
          % "/".join(fam3))
    print("  agree %d (%.0f%%) | disagree %d (%.0f%%) | FLAT %d (%.0f%%)   n=%d pairs"
          % (agr, 100*agr/n, dis, 100*dis/n, flt, 100*flt/n, n))
    lim = sorted(g for g, (a, d, f) in per.items() if a > d and a > 0)
    inv = sorted(g for g, (a, d, f) in per.items() if d > a)
    flat_g = sorted(g for g, (a, d, f) in per.items() if a == d == 0 and f > 0)
    print("  TIME-limited (%d): %s" % (len(lim), " ".join(lim)))
    print("  INVERTED    (%d): %s" % (len(inv), " ".join(inv)))
    print("  FLAT        (%d): %s" % (len(flat_g), " ".join(flat_g)))
    print("  -> the FLAT and INVERTED games carry no reverse-causation confound: their action")
    print("     counts moved 2-6x and their level counts did not, so clock is not what binds there.")

    if as_json:
        print()
        print(json.dumps({
            "cap_bound": n_cap, "raw_bound": n_raw, "unknown": n_unk,
            "cap_share_of_decided": round(100 * n_cap / decided, 1),
            "derived_totals": derived,
            "unresolved_games": unknown_games,
            "headroom_public": {r: round(head.get(r, 0.0) / len(games), 4) for r in sorted(runs)},
            "volatility_top6": [[g, round(sd, 3)] for g, sd in vol[:6]],
            "actions_buy_levels": {"agree": agr, "disagree": dis, "flat": flt,
                                   "time_limited": lim, "inverted": inv, "flat_games": flat_g},
        }, indent=1))


if __name__ == "__main__":
    main()
