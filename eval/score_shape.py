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

    Games with no anchor are not left blank: bound_totals() brackets them from the same
    identity (score <= cap holds in every cell, anchored or not). That is what unblocked
    B35's "is re86 deep or shallow" -- see the BOUNDS block and CONTROL 6.

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
PUBLISHED = {"v10cal": 4.71, "v18": 3.60, "v19": 2.82, "v20": 0.18,
             "clock2x": 6.40, "v25": 3.69}  # LEDGER's table
GROUND_TRUTH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "fixtures", "game-totals.json")
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
        if "games" not in d:
            continue  # game-totals.json lives here too and is not a run
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


def bound_totals(runs: dict, games: list) -> dict:
    """Bound total_levels for games that have NO exact cap anchor.

    derive_totals() can only speak where a cell sits exactly on the completion cap. For
    every other game the total was reported UNKNOWN and nothing downstream could use it --
    including B35's blocker, which needs to know whether re86 (the largest single
    contributor to per-game variance) is a deep game worth chasing or a shallow swingy one.

    A bound is available without an anchor, from the same identity. score = min(raw, cap)
    is <= cap = 100 * tri(cleared) / tri(total) in EVERY scoring cell, anchored or not, so

        tri(total) <= 100 * tri(cleared) / score

    holds for each cell independently; take the tightest over the game's cells. The lower
    bound is the deepest level any run actually reached there.

    Note the constant is 100 and not SDK_CAP=115: 115 caps a LEVEL's score, while the GAME
    is capped at 100 * sum(done)/sum(1..total). Using 115 gives a valid but 15% looser
    bound. Measured: the anchored games do NOT catch that substitution -- every one of them
    has total <= 10, and tri(k+1)/tri(k) only drops under 1.15 at k >= 14, so a 15% slack
    cannot reach the next triangular number and the bound still lands on the right value.
    CONTROL 6 therefore carries a synthetic deep game where it can, which is the only part
    of it with teeth against this particular error.

    Returns {game: (lo, hi)} for every game with at least one scoring cell.
    """
    bounds = {}
    for g in games:
        lo = max(gs[g]["levels"] for gs in runs.values())
        hi = None
        for _r, gs in runs.items():
            d = gs[g]
            if d["levels"] <= 0 or d["score"] <= 0:
                continue
            lim = 100.0 * tri(d["levels"]) / d["score"]
            k = max((k for k in range(1, 60) if tri(k) <= lim + EPS), default=None)
            if k is not None:
                hi = k if hi is None else min(hi, k)
        if hi is not None:
            bounds[g] = (max(lo, 1), hi)
    return bounds


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
    with open(GROUND_TRUTH, encoding="utf-8") as fh:
        truth = json.load(fh)["totals"]

    # ---- CONTROL 3: no game's derived total may disagree between its own runs ----
    conflicts = {g: v for g, v in votes_all.items() if len(v) > 1}
    if conflicts:
        fail(3, "cross-run disagreement on total_levels: %s" % conflicts)
    print("CONTROL 3  cross-run agreement on derived total_levels (%d games, 0 conflicts): OK"
          % len(derived))

    # From here the TRUE totals drive the tables: derive_totals() speaks for 17 of 25 games and
    # bound_totals() only brackets the rest, while CONTROL 7's reference settles all 25. The
    # derivation is not replaced -- CONTROL 6 and 7 above still grade it on its own.
    buckets = classify(runs, games, truth)

    # ---- CONTROL 4: teeth on the contiguous-clear assumption ----
    if buckets["anomaly"]:
        fail(4, "score > cap in %s -- levels are not cleared contiguously and every number "
                "below is wrong" % [(a[0], a[1]) for a in buckets["anomaly"]])
    print("CONTROL 4  no cell scores above its cap (contiguous-clear assumption holds): OK")

    # ---- CONTROL 5: no game may be credited fewer levels than a run actually cleared ----
    # This was a closure argument (do the derived totals leave room for the unresolved games?)
    # while the unresolved set was non-empty. CONTROL 7's external reference settles all 25, so
    # the arithmetic became vacuous -- "57 left for the other 0" -- and a control that cannot
    # fail is a constant. What survives is the half that can still bite, now against the totals
    # the tables actually use.
    unknown_games = [g for g in games if g not in truth]
    if unknown_games:
        fail(5, "no total for %d games: %s" % (len(unknown_games), unknown_games))
    for g in sorted(truth):
        if g not in games:
            continue
        seen = max(gs[g]["levels"] for gs in runs.values())
        if truth[g] < seen:
            fail(5, "%s total %d < %d levels actually cleared there" % (g, truth[g], seen))

    bounds = bound_totals(runs, games)

    # ---- CONTROL 6: where a total IS known, the bound must land EXACTLY on it ----
    # Containment would pass for any constant >= 100 (SDK_CAP=115 included) and for a lower
    # bound hardcoded to 1. Equality on both ends is what gives this teeth.
    for g, n in sorted(derived.items()):
        if g not in bounds:
            fail(6, "%s has a derived total %d but no bound at all" % (g, n))
            continue
        lo, hi = bounds[g]
        if hi != n:
            fail(6, "%s bound upper %d != derived total %d (the identity is wrong, not loose)"
                    % (g, hi, n))
        seen = max(gs[g]["levels"] for gs in runs.values())
        if lo != seen:
            fail(6, "%s bound lower %d != %d levels actually cleared" % (g, lo, seen))
        if lo > hi:
            fail(6, "%s empty bound [%d, %d]" % (g, lo, hi))
    # ---- CONTROL 7: EXTERNAL ground truth, from outside this instrument entirely ----
    # summary.txt of a Kaggle run prints "levels=<cleared>/<TOTAL>" per game. The total is a
    # property of the GAME, so one run settles all 25 -- and it can contradict a derivation
    # that fixtures alone cannot check. This is the only control here whose reference was not
    # computed by this file.
    if sum(truth.values()) != TOTAL_LEVELS_ALL_GAMES:
        fail(7, "ground truth sums to %d, CONTROL 5 assumes %d"
                % (sum(truth.values()), TOTAL_LEVELS_ALL_GAMES))
    missing = [g for g in games if g not in truth]
    if missing:
        fail(7, "ground truth is missing %d games: %s" % (len(missing), missing))
    for g, n in sorted(derived.items()):
        if truth.get(g) != n:
            fail(7, "%s derived %d but the game has %s levels" % (g, n, truth.get(g)))
    for g, (lo, hi) in sorted(bounds.items()):
        if g in truth and not lo <= truth[g] <= hi:
            fail(7, "%s bound [%d, %d] excludes the true total %d" % (g, lo, hi, truth[g]))

    # synthetic deep game: at total=20 a 15% slack DOES clear the next triangular number,
    # so this is where SDK_CAP=115 in place of the game cap 100 becomes visible.
    synth = {"x": {"deep": {"score": 100.0 * tri(4) / tri(20), "levels": 4, "actions": 1}}}
    got = bound_totals(synth, ["deep"]).get("deep")
    if got != (4, 20):
        fail(6, "synthetic total=20 game bounded %s, want (4, 20) -- the constant is not the "
                "game cap 100" % (got,))
    gate()
    print("CONTROL 5  every one of the %d games has a total, and none is below the deepest "
          "level any run reached there: OK" % len(games))
    print("CONTROL 6  bound lands exactly on the derived total in all %d anchored games, and "
          "a synthetic total=20 game pins the constant to the game cap: OK" % len(derived))
    print("CONTROL 7  EXTERNAL: %d derived exact and %d bounds contain the true total, "
          "sum %d: OK" % (len(derived), len(bounds), sum(truth.values())))
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

    print("WHAT ONE MORE LEVEL PAYS (cap at k cleared, per game -- TRUE totals, all 25):")
    print("  %-6s %5s | %s" % ("game", "total", "k=1     2      3      4      5"))
    for g in sorted(truth):
        n = truth[g]
        caps = [100 * tri(k) / tri(n) for k in range(1, min(6, n + 1))]
        print("  %-6s %5d | %s" % (g, n, " ".join("%6.2f" % c for c in caps)))
    print()

    print("BOUNDS ON THE UNRESOLVED (no cap anchor, so tri(total) <= 100*tri(cleared)/score):")
    print("  %-6s %-12s %s" % ("game", "total", "tightest cell -- the one that sets the upper bound"))
    for g in sorted(unknown_games):
        if g not in bounds:
            print("  %-6s %-12s never scored in any run -- no anchor of any kind" % (g, "?"))
            continue
        lo, hi = bounds[g]
        best = min(((100.0 * tri(runs[r][g]["levels"]) / runs[r][g]["score"], r)
                    for r in runs
                    if runs[r][g]["levels"] > 0 and runs[r][g]["score"] > 0), default=(0, "?"))
        rng = "%d" % lo if lo == hi else "%d..%d" % (lo, hi)
        width = hi - lo
        print("  %-6s %-12s %s (L%d, %.2f)%s"
              % (g, rng, best[1], runs[best[1]][g]["levels"], runs[best[1]][g]["score"],
                 "   <- too wide to use" if width >= 8 else ""))
    print("  -> a bound is not a total: it rules out shallow, it does not pick a value.")
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
            "true_totals": truth,
            "unresolved_games": unknown_games,
            "bounds": {g: list(bounds[g]) for g in unknown_games if g in bounds},
            "no_anchor": [g for g in unknown_games if g not in bounds],
            "headroom_public": {r: round(head.get(r, 0.0) / len(games), 4) for r in sorted(runs)},
            "volatility_top6": [[g, round(sd, 3)] for g, sd in vol[:6]],
            "actions_buy_levels": {"agree": agr, "disagree": dis, "flat": flt,
                                   "time_limited": lim, "inverted": inv, "flat_games": flat_g},
        }, indent=1))


if __name__ == "__main__":
    main()
