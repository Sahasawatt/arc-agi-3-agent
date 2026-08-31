#!/usr/bin/env python3
"""B55 step 1 -- does the census hold anything a LATER run could have used?

B55 asks whether cross-run transfer has a target at all. The census is the only artifact that
can answer it offline: 21 runs x 25 games, with SPENT actions per level and the human baseline
beside each. No GPU slot, no Kaggle call.

The question is made paired on purpose, because the between-game confound swallows everything
otherwise -- games differ enormously in depth and cost, so any statistic pooled across games
measures the games and not the runs.

  Q1  How much of the depth outcome is RUN-specific rather than GAME-specific? If two runs of
      one game always reach the same depth, nothing run-specific exists and the row closes.

  Q2  Within one game, for every pair of runs where A went DEEPER than B: did A spend fewer
      actions on the prefix they BOTH cleared? A yes means early efficiency buys depth, and
      the transferable thing is named -- how to clear level k of this game cheaply. A no means
      the depth came from something this census cannot see, and step 1 returns nothing to build
      on.

⚠️ What a positive Q2 would NOT establish. The hidden set is 110 DIFFERENT games, so a cached
opening for a public game does not port; what would port is the claim that openings are worth
caching at all. And hidden returns one number per submission, so nothing here can be tuned on
the surface that counts. Both are B55's own stated killers and neither is touched by this run.

Controls gate every number. A failing control prints no statistics.
"""

from __future__ import annotations

import json
import pathlib
import random
import statistics as st
import sys

# Windows stdout is cp1252 and a non-ASCII print dies there (see CLAUDE.md).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = pathlib.Path(__file__).resolve().parent.parent
CENSUS = REPO / "eval" / "fixtures" / "per-level-census.json"

# B52's published figures. ⚠️ Its two headline numbers are over DIFFERENT populations and the
# first version of this probe conflated them: 477 game-runs is the whole census, while 377 cleared
# levels is over B52's "family 17x25=425". Summing levels over all 477 gives 393, and the control
# correctly refused to print anything. Reconstructed by exhaustive search: of the 19 runs carrying
# all 25 games (392 levels), exactly ONE pair can be removed to reach 377 -- {v20, v21}, and no
# other pair in the 19 does. Those are the two runs this repo's CLAUDE.md already names as NOT
# evidence (the MoE swap and reasoning_effort medium), so the family is a deliberate exclusion and
# not an accident of counting.
B52_ALL_GAME_RUNS = 477
B52_ALL_CLEARED = 393        # the whole census, measured here
B52_FAMILY_RUNS = 17
B52_FAMILY_GAME_RUNS = 425
B52_FAMILY_CLEARED = 377     # B52's published figure, over the family only

# 1-game runs cannot enter a cross-run comparison of 25-game runs: their per-game clock is the
# whole run's. v20/v21 are the degraded pair B52 excludes. clock2x is kept but flagged -- twice
# the wall per game, which is a confound for a spend comparison and is reported separately.
SOLO = {"solo-lp85", "solo-sk48"}
DEGRADED = {"v20", "v21"}
DOUBLE_CLOCK = {"clock2x"}
EXCLUDED = SOLO | DEGRADED


def load():
    d = json.loads(CENSUS.read_text(encoding="utf-8"))
    return d["runs"]


def prefix_spend(rec, k):
    """Actions spent on levels 1..k. None if the record cannot cover k."""
    per = rec["per_level"]
    if k > len(per):
        return None
    return sum(p[0] for p in per[:k])


def controls(runs):
    """Every one must hold, or no statistic is printed."""
    fails = []
    game_runs = sum(len(g) for g in runs.values())
    cleared = sum(rec["levels"] for g in runs.values() for rec in g.values())
    if game_runs != B52_ALL_GAME_RUNS:
        fails.append(f"C1 game-runs {game_runs} != B52's {B52_ALL_GAME_RUNS}")
    if cleared != B52_ALL_CLEARED:
        fails.append(f"C2 whole-census cleared {cleared} != {B52_ALL_CLEARED}")
    fam = {r: g for r, g in runs.items() if r not in EXCLUDED}
    fam_runs, fam_gr = len(fam), sum(len(g) for g in fam.values())
    fam_cleared = sum(rec["levels"] for g in fam.values() for rec in g.values())
    if (fam_runs, fam_gr, fam_cleared) != (B52_FAMILY_RUNS, B52_FAMILY_GAME_RUNS, B52_FAMILY_CLEARED):
        fails.append(f"C2b family {fam_runs}x25={fam_gr} / {fam_cleared} cleared != B52's "
                     f"{B52_FAMILY_RUNS}x25={B52_FAMILY_GAME_RUNS} / {B52_FAMILY_CLEARED}")
    # C3 -- per_level must be self-consistent with the actions total on every record it can be
    bad = 0
    for g in runs.values():
        for rec in g.values():
            if sum(p[0] for p in rec["per_level"]) != rec["actions"]:
                bad += 1
    if bad:
        fails.append(f"C3 {bad} records where per-level spend != actions")
    # C4 -- `levels` must equal the count of levels with non-zero spend that were cleared.
    # It is NOT the count of non-zero rows: a level can absorb actions and not be cleared, which
    # is the reading that inflated v10cal's mean from 4.71 to 11.47 in an earlier pass. So the
    # weaker, true invariant: levels <= number of rows with non-zero spend.
    bad = sum(1 for g in runs.values() for rec in g.values()
              if rec["levels"] > sum(1 for p in rec["per_level"] if p[0] > 0))
    if bad:
        fails.append(f"C4 {bad} records claim more cleared levels than levels they spent on")
    return fails, game_runs, cleared


def q1(runs):
    """Depth spread per game across the 25-game runs."""
    usable = {r: g for r, g in runs.items() if r not in EXCLUDED}
    per_game = {}
    for r, g in usable.items():
        for game, rec in g.items():
            per_game.setdefault(game, []).append((r, rec["levels"]))
    rows = []
    for game, xs in sorted(per_game.items()):
        lv = [v for _, v in xs]
        rows.append((game, len(lv), min(lv), max(lv), max(lv) - min(lv), st.mean(lv)))
    return rows


def q2(runs, *, shuffle=False, rng=None):
    """Paired within-game test: does the DEEPER run spend less on the shared prefix?

    Returns (deeper_cheaper, deeper_dearer, ties) over every ordered pair with a strict depth
    difference and a shared prefix of at least one level.
    """
    usable = {r: g for r, g in runs.items() if r not in EXCLUDED}
    per_game = {}
    for r, g in usable.items():
        for game, rec in g.items():
            per_game.setdefault(game, []).append((r, rec))

    cheaper = dearer = ties = 0
    for game, xs in per_game.items():
        recs = [rec for _, rec in xs]
        depths = [rec["levels"] for rec in recs]
        if shuffle:
            depths = depths[:]
            rng.shuffle(depths)
        for i in range(len(recs)):
            for j in range(len(recs)):
                if i == j:
                    continue
                da, db = depths[i], depths[j]
                if da <= db:
                    continue
                k = db  # the prefix BOTH cleared
                if k < 1:
                    continue
                sa, sb = prefix_spend(recs[i], k), prefix_spend(recs[j], k)
                if sa is None or sb is None:
                    continue
                if sa < sb:
                    cheaper += 1
                elif sa > sb:
                    dearer += 1
                else:
                    ties += 1
    return cheaper, dearer, ties


def q3(runs, *, shuffle=False, rng=None):
    """Step 2 -- a control for "A is simply a better run", oriented by an EXTERNAL yardstick.

    ⚠️ The first version of this function was VACUOUS and its output looked like a strong
    result. It walked every ORDERED pair (a,b) and (b,a). On a game where the two runs tie,
    whichever is cheaper increments the control in one direction and the dearer one increments
    it in the other, so control_cheaper == control_dearer EXACTLY and the share is 0.500 by
    construction -- in the observed data and in every permutation alike. The test then reduced
    to Q2 with extra steps, and printed "GAME-SPECIFIC, p 0.015" on a comparison against a
    mathematical identity. A control that cannot take any value but one is not a control.

    The fix orients each UNORDERED pair by something outside the comparison: total levels
    cleared across all 25 games, i.e. how good the run was overall. Pairs with equal totals
    carry no orientation and are dropped. Then:

      FOCAL    games where the globally-BETTER run also went deeper -> is it cheaper there?
      CONTROL  games where the two TIED on depth -> is the globally-better run cheaper anyway?

    "A is simply better" predicts the control share sits ABOVE 0.5 too, and by a similar
    margin. A game-specific effect predicts the control sits at chance while the focal does not.
    """
    usable = {r: g for r, g in runs.items() if r not in EXCLUDED}
    names = sorted(usable)
    depth = {r: {g: rec["levels"] for g, rec in usable[r].items()} for r in names}
    if shuffle:
        games = sorted({g for r in names for g in depth[r]})
        for g in games:
            holders = [r for r in names if g in depth[r]]
            vals = [depth[r][g] for r in holders]
            rng.shuffle(vals)
            for r, v in zip(holders, vals):
                depth[r][g] = v
    # the external yardstick, recomputed from the (possibly shuffled) depths so the null is
    # internally consistent rather than orienting on the observed totals
    total = {r: sum(depth[r].values()) for r in names}

    f_ch = f_de = c_ch = c_de = 0
    oriented = dropped = 0
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if total[a] == total[b]:
                dropped += 1
                continue
            oriented += 1
            hi, lo = (a, b) if total[a] > total[b] else (b, a)
            for g in usable[hi]:
                if g not in usable[lo]:
                    continue
                dh, dl = depth[hi][g], depth[lo][g]
                rh, rl = usable[hi][g], usable[lo][g]
                if dh > dl and dl >= 1:
                    sh_, sl = prefix_spend(rh, dl), prefix_spend(rl, dl)
                    if sh_ is None or sl is None:
                        continue
                    if sh_ < sl:
                        f_ch += 1
                    elif sh_ > sl:
                        f_de += 1
                elif dh == dl and dh >= 1:
                    sh_, sl = prefix_spend(rh, dh), prefix_spend(rl, dh)
                    if sh_ is None or sl is None:
                        continue
                    if sh_ < sl:
                        c_ch += 1
                    elif sh_ > sl:
                        c_de += 1
    fs = f_ch / (f_ch + f_de) if (f_ch + f_de) else float("nan")
    cs = c_ch / (c_ch + c_de) if (c_ch + c_de) else float("nan")
    return fs, cs, f_ch + f_de, c_ch + c_de, (oriented, dropped)


def main() -> int:
    if not CENSUS.is_file():
        print(f"FAIL: census missing: {CENSUS}", file=sys.stderr)
        return 2
    runs = load()

    fails, game_runs, cleared = controls(runs)
    if fails:
        print("CONTROLS FAILED -- no statistics printed:", file=sys.stderr)
        for f in fails:
            print("  " + f, file=sys.stderr)
        return 1
    print(f"  [ok] controls: whole census {game_runs} game-runs / {cleared} cleared, AND B52's "
          f"family {B52_FAMILY_RUNS}x25={B52_FAMILY_GAME_RUNS} / {B52_FAMILY_CLEARED} reproduced "
          f"exactly; per-level spend reconciles to actions on every record")
    print(f"  [note] excluded from the paired tests: {sorted(SOLO)} (1-game runs) and "
          f"{sorted(DEGRADED)} (B52's own exclusion); {sorted(DOUBLE_CLOCK)} kept and FLAGGED "
          f"-- twice the per-game wall is a confound for any spend comparison")

    print("\n=== Q1  is depth run-specific at all? (25-game runs only) ===")
    rows = q1(runs)
    spread = [r[4] for r in rows]
    zero = sum(1 for s in spread if s == 0)
    print(f"  games {len(rows)}   depth spread across runs: "
          f"min {min(spread)}  median {st.median(spread):.0f}  max {max(spread)}   "
          f"games with ZERO spread: {zero}")
    print("  widest games:")
    for game, n, lo, hi, sp, mean in sorted(rows, key=lambda r: -r[4])[:6]:
        print(f"    {game}  n={n}  levels {lo}..{hi}  spread {sp}  mean {mean:.2f}")
    print("  narrowest games:")
    for game, n, lo, hi, sp, mean in sorted(rows, key=lambda r: (r[4], r[0]))[:6]:
        print(f"    {game}  n={n}  levels {lo}..{hi}  spread {sp}  mean {mean:.2f}")

    print("\n=== Q2  does the DEEPER run spend less on the prefix they both cleared? ===")
    ch, de, ti = q2(runs)
    tot = ch + de + ti
    if tot == 0:
        print("  no comparable pairs -- Q2 answers nothing")
        return 1
    frac = ch / (ch + de) if (ch + de) else float("nan")
    print(f"  pairs {tot}:  deeper-CHEAPER {ch}   deeper-DEARER {de}   ties {ti}")
    print(f"  share cheaper (excluding ties): {frac:.3f}")

    # 200 permutations resolve p to ~0.005, which cannot decide a value sitting at 0.045.
    rng = random.Random(20260830)
    shuffled = []
    for _ in range(2000):
        c, d, _t = q2(runs, shuffle=True, rng=rng)
        if c + d:
            shuffled.append(c / (c + d))
    lo, hi = min(shuffled), max(shuffled)
    ge = sum(1 for s in shuffled if s >= frac)
    pval = (ge + 1) / (len(shuffled) + 1)          # add-one, so p is never reported as 0
    print(f"  shuffle baseline ({len(shuffled)} permutations of the depth labels WITHIN each "
          f"game): mean {st.mean(shuffled):.3f}  sd {st.pstdev(shuffled):.3f}  "
          f"range [{lo:.3f}, {hi:.3f}]")
    print(f"  permutation p (one-sided, share-cheaper >= observed): {pval:.3f}   "
          f"{ge} of {len(shuffled)} permutations matched or beat it")
    verdict = "a real signal" if pval < 0.05 else "NOT separable from chance"
    print(f"  -> {verdict}")

    # SENSITIVITY: clock2x had twice the per-game wall, so it should go deeper AND spend more --
    # a confound pushing AGAINST the tested direction. Removing it must not be what carries the
    # result, and if the result only survives WITH it, that is worth more than the p.
    global EXCLUDED
    keep = EXCLUDED
    EXCLUDED = EXCLUDED | DOUBLE_CLOCK
    c2, d2, t2 = q2(runs)
    f2 = c2 / (c2 + d2) if (c2 + d2) else float("nan")
    sh2 = []
    rng2 = random.Random(20260830)
    for _ in range(2000):
        a, b, _ = q2(runs, shuffle=True, rng=rng2)
        if a + b:
            sh2.append(a / (a + b))
    p2 = (sum(1 for s in sh2 if s >= f2) + 1) / (len(sh2) + 1)
    EXCLUDED = keep
    print(f"  sensitivity, clock2x also removed ({c2 + d2 + t2} pairs): share {f2:.3f}, p {p2:.3f}")
    print("  NOTE: the min/max range is NOT the test. At 200 permutations this probe printed "
          "'INSIDE the range -> not separable from chance' while the p was 0.045; the envelope "
          "of a few hundred draws is wide and says little. The permutation p decides.")
    print("")
    print("=== Q3 (step 2)  is the effect GAME-SPECIFIC, or just 'A is a better run'? ===")
    fs, cs, nf, nc, (oriented, dropped) = q3(runs)
    print(f"  FOCAL   games where A went deeper : {nf} comparisons, A cheaper on {fs:.3f}")
    print(f"  CONTROL games at EQUAL depth      : {nc} comparisons, A cheaper on {cs:.3f}")
    print(f"  difference (focal - control)      : {fs - cs:+.3f}")
    print(f"  pairs oriented by total levels: {oriented}; dropped for a tied total: {dropped}")
    rng3 = random.Random(20260830)
    sh3 = []
    for _ in range(2000):
        f, c, _a, _b, _o = q3(runs, shuffle=True, rng=rng3)
        if f == f and c == c:
            sh3.append(f - c)
    p3 = (sum(1 for s in sh3 if s >= (fs - cs)) + 1) / (len(sh3) + 1)
    print(f"  null difference over {len(sh3)} within-game permutations: "
          f"mean {st.mean(sh3):+.3f}  sd {st.pstdev(sh3):.3f}")
    print(f"  permutation p (one-sided, difference >= observed): {p3:.3f}")
    if p3 < 0.05:
        print("  -> GAME-SPECIFIC: A's cheapness concentrates where it went deeper, which "
              "'A is simply better' does not predict")
    else:
        print("  -> NOT separable from 'A is simply a better run'. Q2's signal survives as a "
              "description of run QUALITY and not as a transfer target.")
    print("  CAVEAT 1: the comparisons are NOT independent -- 17 runs generate all of them, so "
          "each run appears in many. The within-game shuffle absorbs part of that and not all, "
          "so read both p values as optimistic.")
    print("  CAVEAT 2: Q3's focal set needs the shallower run to have cleared at least one "
          "level, so the widest gaps (0 vs 2+) are excluded from it. The effect is measured on "
          "the pairs where both runs got somewhere.")
    print("  CAVEAT 3: still correlation. A census holding no trajectories cannot separate "
          "'spent less because it understood' from 'understood and therefore spent less', and "
          "only the first supports caching an opening.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
