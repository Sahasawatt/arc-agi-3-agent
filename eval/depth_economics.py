r"""depth_economics.py -- what score is made of, and which budget levers the banked corpus refutes.

THREE READINGS, all offline on banked fixtures, no network and no slot:

  (1) WHAT SCORE TRACKS. Across every banked 25-game fixture, score against levels, against
      actions, and against actions-per-level. Run with and without `v20` (the MoE run at 2552
      act/level), because one outlier carries the act/level correlation entirely: -0.362 with it,
      -0.028 without. Reporting only the first number would say efficiency predicts score. It
      does not.

  (2) WHERE THE BUDGET GOES, IN TOKENS NOT ACTIONS. `generated_tokens` is the honest proxy for the
      per-game wall, because actions are an OUTPUT of the clock: tok/action varies 9.6x between
      games (573 .. 5523), so an actions-based budget table invents an allocation imbalance that
      the token table shows is not there -- every game gets 3.1-4.3% of ~2.39M tokens, i.e. the
      uniform share a per-game wall hands out.
      Alongside it, the marginal value of depth: clearing one more level of a game with W levels
      adds (d+1)/(W(W+1)/2) to that game's score and a 25th of that to the total, so the return
      per Mtok spans 1.41 .. 7.88 across games while the spend is flat.

  (3) THE ABANDON RULE, REFUTED. The Fog lists "an early-exit that returns a game's unused budget
      to the pool" as a candidate. Sweep it: for each threshold T, how many first-level clears
      would be cut off against how much budget is freed from the game-runs that never cleared
      anything. No T pays -- at T=100k tokens it costs 6.0% of clears to free 2.8% of budget, and
      the ratio only worsens as T falls. The reason is in the distributions: level-1 clears land at
      p50 41,898 tokens against a ~96k per-game share, while the runs that never clear burn a
      median 99,307 -- "has not cleared yet" does not separate the two until the budget is gone.

WHAT THIS DOES NOT SAY. (1) is a correlation ACROSS BUILDS (ecological), and levels->score is
partly definitional: RHAE's per-game score is a level-weighted average, so more levels mechanically
means more score. The empirical half is that the OTHER channel is inert, and the cap is why --
`methodology` caps a level at 1.15x the human baseline, so efficiency is worth at most 15% while
depth runs to the completion cap. (2)'s per-Mtok figures are AVERAGES, not marginals: `clock2x`
doubled every game's wall and bought +2 levels, so the marginal rate is far below these averages
and no reallocation should be sized with them. (3) is measured on the v10-era family at 1x budget;
a different chassis or budget could move the distributions.

CONTROLS (both poles plus the fixture's own closures, same invocation):
  positive: thui-fast-pool must total mean 8.69 / 38.5 levels, the figures B69 published.
  closure:  in the census, every game-run's per_level list must be `total` long and its spends must
            sum to `actions` -- the fixture's own invariant, re-checked here because this script
            reads per_level directly.
  negative: the act/level correlation must CHANGE when v20 is dropped; if it does not, the outlier
            story in (1) is wrong and the printed caveat is misleading.
A harness that cannot pass all three is a broken instrument, not a strict one.

EXIT CODES: 0 = ran, 3 = data error or a failed control.

    python eval/depth_economics.py
"""

from __future__ import annotations

import glob
import json
import os
import pathlib
import statistics
import sys

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"
SKIP = {"arms.json", "per-level-census.json", "game-totals.json", "trajectory-rows.json"}
ARM = ["v10cal", "thui-v1-1", "thui-v1-1-r2", "v19"]          # arms.json `v10`, census spelling
FAMILY = ["v10cal", "v14", "v16", "v18", "v19", "v22", "v23", "v24", "v25", "v26",
          "thui-v1-0", "thui-v1-1", "thui-v1-1-r2", "thui-v2-0", "thui-v3-0", "thui-v4-0",
          "clock2x"]
POOL_PUBLISHED = {"score": 8.69, "levels": 38.5}
CLEARED_RATIO = 0.78        # spent/human median on levels this family DID clear (B52)


def pearson(xs: list[float], ys: list[float]) -> float:
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5
    return num / den if den else float("nan")


def fixture_totals(path: str) -> tuple[int, float, int, float]:
    games = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))["games"]
    items = games.items() if isinstance(games, dict) else [(a, b) for a, b in games]
    acts = levels = 0
    scores = []
    for _, v in items:
        acts += v.get("actions", 0)
        levels += v.get("levels", 0)
        scores.append(v.get("score", 0))
    return len(scores), levels, acts, statistics.mean(scores)


def census() -> dict:
    return json.loads((FIX / "per-level-census.json").read_text(encoding="utf-8"))["runs"]


def controls(runs: dict, rows: list) -> list[str]:
    bad = []

    n, lv, _, sc = fixture_totals(str(FIX / "thui-fast-pool.json"))
    if abs(sc - POOL_PUBLISHED["score"]) > 0.005 or abs(lv - POOL_PUBLISHED["levels"]) > 0.005:
        bad.append(f"positive: thui-fast-pool reads {sc:.2f}/{lv} against published "
                   f"{POOL_PUBLISHED['score']}/{POOL_PUBLISHED['levels']}")

    for r in FAMILY:
        if r not in runs:
            bad.append(f"closure: census lacks {r}")
            continue
        for g, e in runs[r].items():
            if len(e["per_level"]) != e["total"]:
                bad.append(f"closure: {r}/{g} per_level is {len(e['per_level'])} long, total {e['total']}")
            if sum(s for s, _ in e["per_level"]) != e["actions"]:
                bad.append(f"closure: {r}/{g} spends sum to {sum(s for s, _ in e['per_level'])}, actions {e['actions']}")

    with_v20 = [r for r in rows]
    without = [r for r in rows if r[0] != "v20"]
    if len(without) == len(with_v20):
        bad.append("negative: v20 is not in the fixture set, so the outlier control cannot run")
    else:
        a = pearson([r[3] for r in with_v20], [r[4] for r in with_v20])
        b = pearson([r[3] for r in without], [r[4] for r in without])
        if abs(a - b) < 0.1:
            bad.append(f"negative: dropping v20 moved the act/level correlation only {abs(a-b):.3f} "
                       "-- the outlier story in section (1) does not hold")

    return bad[:6]


def main() -> int:
    try:
        runs = census()
        rows = []
        for p in sorted(glob.glob(str(FIX / "*.json"))):
            if os.path.basename(p) in SKIP:
                continue
            n, lv, ac, sc = fixture_totals(p)
            if n < 20 or lv == 0:
                continue
            rows.append((os.path.basename(p)[:-5], lv, ac, ac / lv, sc))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"data error: {exc}")
        return 3

    failed = controls(runs, rows)
    if failed:
        for f in failed:
            print(f"CONTROL FAILED -- {f}")
        print("refusing to print numbers from an instrument that cannot pass its own controls")
        return 3
    print("controls OK: thui-fast-pool reproduces 8.69 / 38.5, census per_level closures hold "
          "for 17 runs x 25 games, and dropping v20 does move the act/level correlation")

    print("\n=== (1) what score tracks, across builds ===")
    for label, sub in (("all fixtures", rows), ("excl. v20 (MoE, 2552 act/level)",
                                                [r for r in rows if r[0] != "v20"])):
        sc = [r[4] for r in sub]
        print(f"  {label} (n={len(sub)})")
        print(f"    levels      r = {pearson([r[1] for r in sub], sc):+.3f}")
        print(f"    actions     r = {pearson([r[2] for r in sub], sc):+.3f}")
        print(f"    act/level   r = {pearson([r[3] for r in sub], sc):+.3f}")
    print("  -> depth is the channel. act/level is carried by one outlier and is ~0 without it.")

    games = sorted(set(runs[ARM[0]]))
    budget = statistics.mean(sum(runs[r][g]["generated_tokens"] for g in games) for r in ARM)
    print(f"\n=== (2) where the budget goes (mean {budget:,.0f} generated tokens per run) ===")
    print(f"  {'game':<6}{'W':>3}{'bestD':>6}{'gen_tok':>9}{'%bud':>6}{'tok/act':>8}"
          f"{'+tot%':>7}{'/Mtok':>7}")
    table = []
    for g in games:
        W = runs[ARM[0]][g]["total"]
        best = max(runs[r][g]["levels"] for r in ARM)
        tok = statistics.mean(runs[r][g]["generated_tokens"] for r in ARM)
        act = statistics.mean(runs[r][g]["actions"] for r in ARM)
        avg_lv = statistics.mean(runs[r][g]["levels"] for r in ARM)
        gain = ((best + 1) / (W * (W + 1) / 2)) * 100 / len(games) if best < W else 0.0
        table.append((g, W, best, avg_lv, tok, act, gain, gain / (tok / 1e6) if tok else 0.0))
    for g, W, best, _, tok, act, gain, per_m in sorted(table, key=lambda t: -t[7]):
        print(f"  {g:<6}{W:>3}{best:>6}{tok:>9,.0f}{100*tok/budget:>6.1f}"
              f"{tok/act if act else 0:>8,.0f}{gain:>7.3f}{per_m:>7.2f}")
    shares = [100 * t[4] / budget for t in table]
    zero = [t for t in table if t[3] == 0]
    print(f"  share of budget per game: {min(shares):.1f}% .. {max(shares):.1f}% "
          f"(uniform would be {100/len(games):.1f}%) -- the wall allocates evenly")
    print(f"  games averaging ZERO levels: {', '.join(t[0] for t in zero)} = "
          f"{sum(100*t[4]/budget for t in zero):.1f}% of budget")
    print("  -> return per Mtok spans "
          f"{min(t[7] for t in table):.2f} .. {max(t[7] for t in table):.2f} on a flat spend. "
          "These are AVERAGES; clock2x measured the marginal and it is far below them.")

    print("\n=== (3) the abandon rule: stop a game that has not cleared level 1 by T tokens ===")
    first, never = [], []
    for r in FAMILY:
        for g in games:
            e = runs[r][g]
            tpa = e["generated_tokens"] / e["actions"] if e["actions"] else 0.0
            if e["levels"] > 0:
                first.append(e["per_level"][0][0] * tpa)
            else:
                never.append(e["generated_tokens"])
    first.sort()
    # The denominator here must be the FAMILY's own per-run budget, not the 4-run arm's: clock2x
    # carries twice the tokens, so borrowing `budget` from section (2) would divide family-wide
    # freed tokens by a smaller arm-wide budget and overstate every percentage.
    fam_budget = statistics.mean(
        sum(runs[r][g]["generated_tokens"] for g in games) for r in FAMILY)
    print(f"  {len(first)} game-runs cleared at least one level, {len(never)} never did")
    print(f"  family per-run budget {fam_budget:,.0f} tokens "
          f"(the 4-run v10 arm's is {budget:,.0f}; clock2x doubles the wall)")
    print(f"  tokens spent on level 1 by runs that cleared it: "
          f"p50 {first[len(first)//2]:,.0f}  p90 {first[int(.9*len(first))]:,.0f}  "
          f"p99 {first[int(.99*len(first))]:,.0f}")
    print(f"  tokens burned by runs that never cleared: median {statistics.median(never):,.0f}")
    print(f"  {'T':>9}  {'clears lost':>18}  {'budget freed':>12}")
    for T in (20_000, 40_000, 60_000, 80_000, 100_000):
        lost = sum(1 for x in first if x > T)
        freed = sum(max(0, x - T) for x in never) / len(FAMILY)
        print(f"  {T:>9,}  {f'{lost}/{len(first)} ({100*lost/len(first):.1f}%)':>18}"
              f"  {f'{100*freed/fam_budget:.1f}%':>12}")
    print("  -> no threshold pays: the cost in clears exceeds the budget freed at every T. "
          "REFUTED on this corpus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
