r"""Where the levels actually are, and what the union of every run would score.

The campaign's remaining question is depth: the efficiency ceiling is ~2.1 hidden against a bar
that moved to 3.58 on 2026-08-31, so a build has to clear MORE, not clear the same cheaper. B52
priced the headroom at 47 levels across runs against 30 for the best single run. This prices what
that headroom is WORTH, and says whether it is concentrated enough to aim at.

The scoring is the competition's own, lifted from the harness rather than restated:
`inference/tools/traces.py` -- a level scores `min((baseline/spent)**2 * 100, 115)` when cleared
and 0 otherwise, a game is the level-weighted mean of those CAPPED by
`completed_weight/total_weight * 100`, and a run is the mean over its 25 games. The completion cap
is why efficiency alone cannot reach the bar: clear a third of the weight and no per-level score,
however good, lifts the game above 33.

THE ORACLE is the pointwise best: for every (game, level) any run ever cleared, the FEWEST actions
any run spent clearing it. It is not a run anyone could have had -- no single draw is best
everywhere -- it is the ceiling on what pooling across draws could ever be worth.

CONTROL. The same arithmetic is run over each real run and printed against `notes/LEDGER-all-runs.md`.
A calculator that cannot reproduce the published public scores has nothing to say about a
hypothetical one, and the census carries `spent`/`human` per level for exactly this.

    python eval/oracle_ceiling.py
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CENSUS = os.path.join(HERE, "fixtures", "per-level-census.json")

LEVEL_CAP, GAME_CAP = 115.0, 100.0

# Published public means, from notes/LEDGER-all-runs.md (the authority). Only runs whose census
# row is a full 25 games can be checked; the two solo runs played one game and are excluded.
LEDGER_PUBLIC = {
    "v10cal": 4.71, "v25": 3.69, "thui-v1-1": 5.24, "thui-v1-1-r2": 4.33, "thui-v2-0": 2.86,
    "thui-v3-0": 4.01, "thui-v4-0": 1.92, "clock2x": 6.40, "v26": 3.19, "v24": 3.78,
    "v23": 3.32, "thui-v1-0": 3.20, "v22": 2.84, "v21": 1.25, "v20": 0.18, "v19": 2.82,
    "v18": 3.60, "v16": 3.51, "v14": 2.87,
}


def level_score(spent: int, human: int) -> float:
    if spent <= 0 or human <= 0:
        return 0.0
    return min((human / spent) ** 2 * 100.0, LEVEL_CAP)


def game_score(levels: list[float]) -> float:
    """levels[i] is the score of level i+1 (0 when not cleared). Weight is the level number."""
    w = [i + 1 for i in range(len(levels))]
    tw = sum(w)
    if tw <= 0:
        return 0.0
    raw = sum(s * wi for s, wi in zip(levels, w)) / tw
    done = sum(wi for s, wi in zip(levels, w) if s > 0.0)
    return min(raw, done / tw * GAME_CAP)


def run_scores(rec_by_game: dict) -> tuple[float, int, int]:
    gs, lv, act = [], 0, 0
    for rec in rec_by_game.values():
        per, k = rec["per_level"], rec["levels"]
        scores = [level_score(per[i][0], per[i][1]) if i < k else 0.0 for i in range(len(per))]
        gs.append(game_score(scores))
        lv += k
        act += rec["actions"]
    return (st.mean(gs) if gs else 0.0), lv, act


def main() -> int:
    runs = json.loads(open(CENSUS, encoding="utf-8").read())["runs"]
    full = {r: g for r, g in runs.items() if len(g) == 25}

    # ---- CONTROL: reproduce the ledger
    print("CONTROL  the scorer against notes/LEDGER-all-runs.md")
    off, checked = [], 0
    for r in sorted(full):
        if r not in LEDGER_PUBLIC:
            continue
        mine, lv, _ = run_scores(full[r])
        want = LEDGER_PUBLIC[r]
        d = abs(mine - want)
        checked += 1
        if d > 0.05:
            off.append((r, mine, want))
        print(f"    {r:14s} levels {lv:3d}  computed {mine:5.2f}  ledger {want:5.2f}  "
              f"{'ok' if d <= 0.05 else 'OFF by %.2f' % d}")
    print(f"  {checked - len(off)} of {checked} within 0.05")
    if len(off) > checked // 4:
        print("  [FAIL] the scorer does not reproduce the ledger -- nothing below is meaningful")
        return 1

    # ---- the oracle: pointwise fewest actions, over every run that cleared that level
    games = sorted(next(iter(full.values())))
    oracle, reach = {}, {}
    for g in games:
        per_len = max(len(full[r][g]["per_level"]) for r in full)
        human = [0] * per_len
        best = [None] * per_len
        who = [0] * per_len
        for r in full:
            rec = full[r][g]
            for i in range(rec["levels"]):
                spent, h = rec["per_level"][i]
                human[i] = h
                who[i] += 1
                if best[i] is None or spent < best[i]:
                    best[i] = spent
        oracle[g] = (best, human)
        reach[g] = who

    o_scores, o_levels = [], 0
    for g in games:
        best, human = oracle[g]
        scores = [level_score(b, h) if b else 0.0 for b, h in zip(best, human)]
        o_scores.append(game_score(scores))
        o_levels += sum(1 for b in best if b)
    o_public = st.mean(o_scores)

    best_run = max(full, key=lambda r: run_scores(full[r])[0])
    b_public, b_levels, _ = run_scores(full[best_run])
    deep_run = max(full, key=lambda r: run_scores(full[r])[1])
    d_public, d_levels, _ = run_scores(full[deep_run])

    print(f"\nORACLE over {len(full)} full-25 runs")
    print(f"  best run by SCORE   {best_run:14s} public {b_public:5.2f}  levels {b_levels:3d}")
    print(f"  best run by DEPTH   {deep_run:14s} public {d_public:5.2f}  levels {d_levels:3d}")
    print(f"  pointwise oracle    {'(no run had it)':14s} public {o_public:5.2f}  levels {o_levels:3d}")
    print(f"  headroom over the best-scoring run: +{o_public - b_public:.2f} public, "
          f"+{o_levels - b_levels} levels")

    # ---- concentration: is the gap a few games or spread thin?
    print("\nWHERE THE MISSING LEVELS ARE, against the deepest single run")
    dr = full[deep_run]
    rows = []
    for g in games:
        best, _ = oracle[g]
        o = sum(1 for b in best if b)
        mine = dr[g]["levels"]
        if o > mine:
            # for each level the deepest run missed, how many of the runs DID clear it
            missed = [(i + 1, reach[g][i]) for i in range(len(best)) if best[i] and i >= mine]
            rows.append((o - mine, g, mine, o, missed))
    rows.sort(reverse=True)
    tot = sum(r[0] for r in rows)
    print(f"  {len(rows)} of 25 games hold the gap, {tot} levels in total")
    for gap, g, mine, o, missed in rows:
        m = " ".join(f"L{lv}x{n}" for lv, n in missed)
        print(f"    {g}  {mine} -> {o}  (+{gap})   cleared by: {m}")
    lucky = sum(1 for _, _, _, _, ms in rows for _, n in ms if n == 1)
    print(f"\n  of those {tot} levels, {lucky} were cleared by exactly ONE of the "
          f"{len(full)} runs -- a single draw, not a reproducible target")

    # ---- DROPPED GAMES. The gap above is dominated by LEVEL 1 of games most runs clear, which
    # is not a depth failure at all. Count, per run, the games it took nothing from while a
    # majority of runs took at least one level -- and ask what it SPENT there, because a drop
    # that burned the whole budget and a drop that stopped early need opposite fixes.
    maj = {}
    for g in games:
        n = sum(1 for r in full if full[r][g]["levels"] > 0)
        maj[g] = n
    half = len(full) / 2.0
    print(f"\nDROPPED GAMES -- cleared 0 levels where more than half of the {len(full)} runs "
          f"cleared at least one")
    print(f"{'run':14s} {'lvls':>4s} {'drop':>4s}  {'spent on the dropped games':>26s}   games")
    drops = []
    for r in sorted(full, key=lambda r: -run_scores(full[r])[1]):
        d = [g for g in games if full[r][g]["levels"] == 0 and maj[g] > half]
        spend = sum(full[r][g]["actions"] for g in d)
        lv = run_scores(full[r])[1]
        drops.append((r, lv, len(d), spend, d))
        detail = " ".join("%s(%d)" % (g, full[r][g]["actions"]) for g in d)
        print(f"{r:14s} {lv:4d} {len(d):4d}  {spend:12d} actions          {detail}")
    tot_drop = sum(x[2] for x in drops)
    print(f"\n  {tot_drop} dropped games across {len(full)} runs, "
          f"median {st.median([x[2] for x in drops]):.0f} per run")

    # ---- THE REPRODUCIBILITY LADDER. The oracle is the union of 19 draws, so most of it may be
    # luck nobody can aim at. Re-price it keeping only the (game, level) pairs at least K runs
    # cleared: K=1 is the raw oracle, and the high K end is what a build that RELIABLY does what
    # these builds already do would score. Where that curve crosses the best single run is the
    # honest answer to "how much depth is left on this agent".
    print(f"\nREPRODUCIBILITY LADDER -- keep only levels at least K of the {len(full)} runs cleared")
    print(f"{'K':>3s} {'share':>6s} {'levels':>7s} {'public':>7s}   reading")
    for k in (1, 2, 3, 5, 7, 10, 13, 16, 19):
        sc, lv = [], 0
        for g in games:
            best, human = oracle[g]
            keep = [level_score(b, h) if (b and reach[g][i] >= k) else 0.0
                    for i, (b, h) in enumerate(zip(best, human))]
            sc.append(game_score(keep))
            lv += sum(1 for i, b in enumerate(best) if b and reach[g][i] >= k)
        note = ""
        if lv <= d_levels and not note:
            note = f"at or below the best single run ({deep_run} {d_levels})"
        print(f"{k:3d} {k / len(full) * 100:5.0f}% {lv:7d} {st.mean(sc):7.2f}   {note}")
    print(f"\n  the best single run sits at {d_levels} levels / {d_public:.2f} public, so every "
          f"rung the ladder falls below it is oracle that no reliable build can reach")

    # ---- WHAT DEPTH IS WORTH AT ANY PRICE. The completion cap means a level cleared badly still
    # raises the cap, while efficiency on levels already cleared is bounded by it. So price the
    # trade directly: give a run ONE more level per game, cleared at m times the human baseline,
    # and see what m it stops being worth. This is the number that decides whether a retry-style
    # lever -- more attempts at the same level, paid for in actions -- can pay at all.
    print("\nWHAT ONE MORE LEVEL PER GAME IS WORTH, at m times the human baseline")
    print(f"{'run':14s} {'now':>6s} " + " ".join(f"{'m=' + str(m):>7s}" for m in (1, 2, 3, 5, 10, 20)))
    for r in (deep_run, best_run, "v10cal", "thui-v1-1"):
        if r not in full:
            continue
        base = run_scores(full[r])[0]
        cells = []
        for m in (1, 2, 3, 5, 10, 20):
            sc = []
            for g in games:
                rec = full[r][g]
                per, k = rec["per_level"], rec["levels"]
                s = [level_score(per[i][0], per[i][1]) if i < k else 0.0 for i in range(len(per))]
                if k < len(per):                      # the level it died on, cleared at m x human
                    s[k] = level_score(int(per[k][1] * m) or 1, per[k][1])
                sc.append(game_score(s))
            cells.append(st.mean(sc))
        print(f"{r:14s} {base:6.2f} " + " ".join(f"{c:7.2f}" for c in cells))
    print("\n  m is how many actions the extra level costs as a multiple of the human baseline.")
    print("  A level cleared at 20x human still lifts the score, because the completion cap and")
    print("  not the per-level term is what binds -- depth bought at any price beats efficiency.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
