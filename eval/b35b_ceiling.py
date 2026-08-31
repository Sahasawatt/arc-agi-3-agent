r"""What a PERFECT early detector could buy -- the ceiling on B35-b, priced before it is built.

B35-b is the last offline detection route B35 has: R45 found no early EVENT-LOG feature separates
a game that will score from one that never does, and R50 found the transcript's one candidate was
a leak. The board is untouched. Building that detector is a session; pricing its ceiling is this
script, and the order matters -- B55 closed on 0.42% of the budget without a build, and this asks
the same question of this row.

THE CEILING IS THE ORACLE DETECTOR, not a heuristic. A real detector can only ever approach perfect
foreknowledge of which games never score, so: abandon exactly those at action k, hand their
remaining clock to the survivors, and let the survivors buy their next levels at the CHEAPEST price
any run in the census ever paid for that (game, level). Nothing a board feature could do beats
that. Two generosities are deliberate and both inflate the answer:

  * the clock is treated as FUNGIBLE across games, which is what B36 proposes and the runtime does
    not do today (`max_runtime_s_per_game` is per game);
  * actions convert to levels at the campaign's best observed price for that exact level, i.e. the
    pointwise oracle of `eval/oracle_ceiling.py`. A level no run ever cleared cannot be bought at
    any price -- that is the one bound not relaxed, because the corpus has no evidence it is
    reachable.

A ceiling with ONE generosity setting is not a bracket, and the second generosity above is the
strong one: the minimum over 19 draws is an order statistic, so it prices every bought level at a
speed one run once hit and eighteen did not, and then scores it at that speed too. Both poles are
therefore reported. `--price self` buys at the RUN'S OWN median spend per cleared level, which is
what that build actually does when it clears something; `--price oracle` keeps the minimum. The
honest answer to "what is B35-b worth" is the interval between them, never either endpoint.

The achievable end is reported beside it: R45's SILENT-AT-K rule, which abandons every game that
has not cleared level 1 by action k and therefore destroys the late scorers. The gap between the
two rows is what a perfect detector is worth OVER the cheap rule everyone already has.

SCORING is not restated here. `eval/oracle_ceiling.py` lifts it from `inference/tools/traces.py`
and carries the control that matters -- reproducing 19 published public means from the census --
and this script imports those functions rather than copying them, so there is one implementation
and one place for it to be wrong.

CONTROLS (`--selftest`, real census, both directions, same invocation):
  ledger      the imported scorer still reproduces 19 of 19 published means (C1 of oracle_ceiling)
  identity    with nothing abandoned, the reallocation machinery reproduces each run EXACTLY
  no-budget   with the freed clock forced to 0, the ceiling equals the baseline for every run
  monotone    buying a level never lowers a game's score (the cap and the weighted mean both rise)
  partition   every game is in exactly one of {abandoned, survivor}, and totals close
  direction   destroyed levels are non-increasing in k, and so is the freed clock
  unbuyable   a level no run ever cleared has no price and is never bought
  abandon     abandoning a scoring game with an empty purse must LOWER that run's score. Without
              this the level override is unobserved: every other control compares states where the
              override happens to equal the census, so a scorer that ignored it would pass them all
  gate        the buyable set shrinks as the reproducibility K rises, and empties at K=19

EXIT CODES: 0 = ran, 2 = usage, 3 = a control failed (no numbers are printed -- a pricing bug
becomes a decision one paragraph later).

    python eval/b35b_ceiling.py
    python eval/b35b_ceiling.py --selftest
"""
from __future__ import annotations

import importlib.util
import json
import os
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("oracle_ceiling", os.path.join(HERE, "oracle_ceiling.py"))
oc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oc)

WINDOWS = (5, 10, 20, 40)


def load_full() -> dict:
    runs = json.loads(open(oc.CENSUS, encoding="utf-8").read())["runs"]
    return {r: g for r, g in runs.items() if len(g) == 25}


def never_scores(rec: dict) -> bool:
    return rec["levels"] == 0


def silent_at(rec: dict, k: int) -> bool:
    """Level 1 not cleared by action k. per_level[0][0] is the spend on level 1 either way."""
    return rec["levels"] == 0 or rec["per_level"][0][0] > k


def self_prices(full: dict) -> dict:
    """{run: median spend per level that run actually cleared}. What this build costs, not the
    cheapest any build ever managed."""
    out = {}
    for r, games in full.items():
        spends = [rec["per_level"][i][0] for rec in games.values()
                  for i in range(rec["levels"]) if rec["per_level"][i][0] > 0]
        out[r] = st.median(spends) if spends else None
    return out


def prices(full: dict, min_runs: int = 1) -> dict:
    """{(game, level_index): (spent, human)}. Absent = not buyable.

    min_runs is B35's own reproducibility gate, applied to the price rather than to the oracle
    total: a (game, level) only becomes buyable once at least min_runs of the 19 draws cleared it,
    and it is then priced at the MEDIAN of those draws rather than at their minimum. min_runs=1 at
    the median is still generous; min_runs=1 at the minimum is the K=1 rung this row already
    measured as a 26%-reproducible draw rather than a capability."""
    seen: dict = {}
    for r, games in full.items():
        for g, rec in games.items():
            for i in range(rec["levels"]):
                spent, human = rec["per_level"][i][0], rec["per_level"][i][1]
                if spent <= 0:
                    continue
                seen.setdefault((g, i), (human, []))[1].append(spent)
    return {k: (st.median(v[1]), v[0]) for k, v in seen.items() if len(v[1]) >= min_runs}


def cheapest_prices(full: dict) -> dict:
    """The K=1 minimum -- kept only so the two can be printed side by side."""
    out: dict = {}
    for r, games in full.items():
        for g, rec in games.items():
            for i in range(rec["levels"]):
                spent, human = rec["per_level"][i][0], rec["per_level"][i][1]
                if spent <= 0:
                    continue
                cur = out.get((g, i))
                if cur is None or spent < cur[0]:
                    out[(g, i)] = (spent, human)
    return out


def score_run(rec_by_game: dict, levels_by_game: dict, spend_by_game: dict) -> float:
    """levels_by_game overrides the cleared count; spend_by_game[(g,i)] overrides one level's spend."""
    gs = []
    for g, rec in rec_by_game.items():
        per, k = rec["per_level"], levels_by_game[g]
        row = []
        for i in range(len(per)):
            if i >= k:
                row.append(0.0)
                continue
            spent = spend_by_game.get((g, i), per[i][0])
            row.append(oc.level_score(spent, per[i][1]))
        gs.append(oc.game_score(row))
    return st.mean(gs) if gs else 0.0


def reallocate(rec_by_game: dict, k: int, price: dict, rule: str, budget_scale: float = 1.0,
               flat_price: float | None = None) -> dict:
    """rule 'oracle' abandons only games that never score; 'silent' abandons every game silent at k.

    flat_price, when given, overrides the per-level cost with this run's own median spend -- the
    level must still be one some run cleared (its human baseline has to come from somewhere), but
    it is bought at this build's price rather than at the corpus minimum."""
    drop = {g for g, rec in rec_by_game.items()
            if (never_scores(rec) if rule == "oracle" else silent_at(rec, k))}
    levels = {g: (0 if g in drop else rec["levels"]) for g, rec in rec_by_game.items()}
    destroyed = sum(rec["levels"] for g, rec in rec_by_game.items() if g in drop)
    freed = sum(max(0, rec["actions"] - k) for g, rec in rec_by_game.items() if g in drop)
    freed = int(freed * budget_scale)

    spend: dict = {}
    bought = 0
    budget = freed
    while True:
        best = None
        for g in rec_by_game:
            if g in drop:
                continue
            i = levels[g]
            if i >= len(rec_by_game[g]["per_level"]):
                continue
            p = price.get((g, i))
            if p is None:                       # no run ever cleared it: unbuyable at any price
                continue
            cost = p[0] if flat_price is None else flat_price
            if cost > budget:
                continue
            if best is None or cost < best[1]:
                best = (g, cost)
        if best is None:
            break
        g, cost = best
        spend[(g, levels[g])] = cost
        if flat_price is not None and cost <= 0:
            break                               # a zero price would buy every level for nothing
        levels[g] += 1
        budget -= cost
        bought += 1

    return {"drop": sorted(drop), "destroyed": destroyed, "freed": freed, "bought": bought,
            "left": budget, "score": score_run(rec_by_game, levels, spend),
            "levels": sum(levels.values())}


def selftest(full: dict, price: dict) -> int:
    fails = []

    # ledger -- the imported scorer, re-checked here because everything below rides on it
    ok = 0
    for r, want in oc.LEDGER_PUBLIC.items():
        if r in full and abs(oc.run_scores(full[r])[0] - want) <= 0.05:
            ok += 1
    if ok < 19:
        fails.append(f"ledger: scorer reproduces only {ok} of 19 published means")

    for r, games in full.items():
        base, base_lv, _ = oc.run_scores(games)

        # identity -- nothing abandoned, nothing bought, must reproduce the run exactly
        ident = score_run(games, {g: rec["levels"] for g, rec in games.items()}, {})
        if abs(ident - base) > 1e-9:
            fails.append(f"identity: {r} {ident:.6f} != {base:.6f}")

        # no-budget -- oracle abandonment with a zero purse cannot move a run that scores nothing
        # in the games it drops
        z = reallocate(games, 5, price, "oracle", budget_scale=0.0)
        if abs(z["score"] - base) > 1e-9 or z["destroyed"] != 0 or z["bought"] != 0:
            fails.append(f"no-budget: {r} moved {base:.4f} -> {z['score']:.4f} "
                         f"(destroyed {z['destroyed']}, bought {z['bought']})")

        # partition -- abandoned and survivors are disjoint and exhaustive
        d = reallocate(games, 20, price, "silent")
        surv = [g for g in games if g not in d["drop"]]
        if len(d["drop"]) + len(surv) != 25 or set(d["drop"]) & set(surv):
            fails.append(f"partition: {r} {len(d['drop'])} + {len(surv)} != 25")

        # direction -- more window destroys no more, and frees no more
        des = [reallocate(games, k, price, "silent")["destroyed"] for k in WINDOWS]
        fre = [reallocate(games, k, price, "silent")["freed"] for k in WINDOWS]
        if any(b > a for a, b in zip(des, des[1:])):
            fails.append(f"direction: {r} destroyed not non-increasing in k: {des}")
        if any(b > a for a, b in zip(fre, fre[1:])):
            fails.append(f"direction: {r} freed not non-increasing in k: {fre}")

    # monotone -- buying a level never lowers a game's score
    r0 = sorted(full)[0]
    for g, rec in full[r0].items():
        i = rec["levels"]
        if i >= len(rec["per_level"]) or (g, i) not in price:
            continue
        a = oc.game_score([oc.level_score(*rec["per_level"][j]) if j < i else 0.0
                           for j in range(len(rec["per_level"]))])
        b = oc.game_score([(oc.level_score(price[(g, i)][0], rec["per_level"][j][1]) if j == i
                            else oc.level_score(*rec["per_level"][j])) if j <= i else 0.0
                           for j in range(len(rec["per_level"]))])
        if b < a - 1e-9:
            fails.append(f"monotone: {r0}/{g} buying level {i + 1} lowered {a:.4f} -> {b:.4f}")

    # abandon -- the silent rule with a zero purse drops real levels, and that must cost score
    for r, games in full.items():
        base, _, _ = oc.run_scores(games)
        d = reallocate(games, 20, price, "silent", budget_scale=0.0)
        if d["destroyed"] > 0 and not d["score"] < base - 1e-9:
            fails.append(f"abandon: {r} destroyed {d['destroyed']} levels and score did not fall "
                         f"({base:.4f} -> {d['score']:.4f})")
        if d["score"] > base + 1e-9:
            fails.append(f"abandon: {r} abandoning games RAISED the score {base:.4f} -> {d['score']:.4f}")

    # gate -- more required draws means fewer buyable levels, and 19 of 19 leaves almost nothing
    sizes = [len(prices(full, K)) for K in (1, 3, 5, 10, 19)]
    if any(b > a for a, b in zip(sizes, sizes[1:])):
        fails.append(f"gate: buyable set not non-increasing in K: {sizes}")
    if sizes[-1] >= sizes[0]:
        fails.append(f"gate: K=19 is not stricter than K=1: {sizes}")

    # unbuyable -- a level nobody cleared has no price, so it can never be bought
    ghost = [(g, i) for (g, i), _ in price.items() if _[0] <= 0]
    if ghost:
        fails.append(f"unbuyable: {len(ghost)} priced levels were never actually cleared")
    seen = {(g, i) for r in full for g, rec in full[r].items() for i in range(rec["levels"])}
    if not set(price).issubset(seen):
        fails.append("unbuyable: a price exists for a (game, level) no run ever cleared")

    if fails:
        print("SELFTEST FAIL -- no numbers are printed, a pricing bug becomes a decision:")
        for f in fails:
            print("  " + f)
        return 3
    print(f"SELFTEST OK: ledger, identity, no-budget, partition, direction, monotone, unbuyable, "
          f"abandon, gate — 9 controls over {len(full)} runs")
    return 0


def main(argv: list[str]) -> int:
    full = load_full()
    price = cheapest_prices(full)
    if argv == ["--selftest"]:
        return selftest(full, price)
    if argv:
        print(__doc__)
        return 2
    rc = selftest(full, price)
    if rc:
        return rc

    selfp = self_prices(full)
    print(f"\nB35-b CEILING over {len(full)} full-25 runs, census {os.path.basename(oc.CENSUS)}")
    print("  oracle = abandon exactly the games that never score (a perfect detector)")
    print("  silent = abandon every game that has not cleared level 1 by action k (R45's rule)\n")
    print(f"  {'k':>4}  {'rule':7} {'base':>6} {'ceiling':>8} {'delta':>7} {'lv':>4} {'dropped':>8} "
          f"{'destroyed':>10} {'freed':>9} {'bought':>7} {'unspent':>8}")
    summary, per_run = {}, {}
    for mode in ("oracle", "self"):
      _why = "cheapest any run ever paid" if mode == "oracle" else "this run's own median"
      print(f"\n  --- level price: {mode} ({_why}) ---")
      for k in WINDOWS:
        for rule in ("oracle", "silent"):
            rows = []
            for r in sorted(full):
                base, base_lv, _ = oc.run_scores(full[r])
                d = reallocate(full[r], k, price, rule,
                               flat_price=(None if mode == "oracle" else selfp[r]))
                rows.append((base, d))
            mb = st.mean(x[0] for x in rows)
            mc = st.mean(x[1]["score"] for x in rows)
            summary[(k, rule, mode)] = (mb, mc)
            if mode == "oracle" and rule == "oracle":
                per_run[k] = {r: (oc.run_scores(full[r])[0], d["score"])
                              for (r, (_, d)) in zip(sorted(full), rows)}
            print(f"  {k:>4}  {rule:7} {mb:6.2f} {mc:8.2f} {mc - mb:+7.2f} "
                  f"{st.mean(x[1]['levels'] for x in rows):4.1f} "
                  f"{st.mean(len(x[1]['drop']) for x in rows):8.1f} "
                  f"{st.mean(x[1]['destroyed'] for x in rows):10.1f} "
                  f"{st.mean(x[1]['freed'] for x in rows):9.0f} "
                  f"{st.mean(x[1]['bought'] for x in rows):7.1f} "
                  f"{st.mean(x[1]['left'] for x in rows):8.0f}")

    best = max(summary.items(), key=lambda kv: kv[1][1])
    print(f"\n  best cell: k={best[0][0]} {best[0][1]} rule, {best[0][2]} price  "
          f"{best[1][0]:.2f} -> {best[1][1]:.2f} ({best[1][1] - best[1][0]:+.2f} public)")
    print("\n  PER RUN at the most generous cell (k=5, oracle rule, oracle price) -- the mean above")
    print("  is over 19 builds most of which nobody would ship; what matters is the best ones:")
    pr = per_run.get(5, {})
    for r in sorted(pr, key=lambda x: -pr[x][0])[:5]:
        b, c = pr[r]
        print(f"    {r:14s} {b:5.2f} -> {c:5.2f}  ({c - b:+.2f})")
    print("  ⚠️ every number above is a CEILING under a fungible clock and oracle level prices;")
    print("     a real board detector is bounded by the 'oracle' rows, never by the 'silent' ones.")

    # ---- the reproducibility gate, B35's own instrument applied to the PRICE
    print("\n  REPRODUCIBILITY GATE — a level is buyable only once >= K of 19 draws cleared it,")
    print("  and is then priced at the MEDIAN of those draws. K=1-at-the-minimum is the row above.")
    print(f"  {'K':>3}  {'buyable':>8}  {'ceiling':>8}  {'delta':>7}  {'bought':>7}  {'act/lvl':>8}")
    for K in (1, 3, 5, 10, 19):
        pk = prices(full, K)
        rows = []
        for r in sorted(full):
            base, _, _ = oc.run_scores(full[r])
            d = reallocate(full[r], 5, pk, "oracle")
            rows.append((base, d))
        mb = st.mean(x[0] for x in rows)
        mc = st.mean(x[1]["score"] for x in rows)
        bought = st.mean(x[1]["bought"] for x in rows)
        used = st.mean(x[1]["freed"] - x[1]["left"] for x in rows)
        print(f"  {K:>3}  {len(pk):>8}  {mc:8.2f}  {mc - mb:+7.2f}  {bought:7.1f}  "
              f"{(used / bought if bought else float('nan')):8.0f}")

    # ---- the model reports its own implied conversion against the one experiment that bought clock
    pk = prices(full, 1)
    rows = [reallocate(full[r], 5, pk, "oracle") for r in sorted(full)]
    used = st.mean(d["freed"] - d["left"] for d in rows)
    bought = st.mean(d["bought"] for d in rows)
    print(f"\n  ⚠️ SELF-CHECK against B34, the only run that ever bought clock. This model implies")
    print(f"     {used / bought:.0f} actions per marginal level (K=1, median price). `clock2x` doubled")
    print(f"     v10cal's clock — about +1,000 actions — and cleared +2 levels, i.e. ~500 actions per")
    print(f"     marginal level at p=0.2761. The model is {500 / (used / bought):.1f}x more generous than the")
    print(f"     measurement, in the direction that flatters the lever. Read every ceiling above as")
    print(f"     bounded by that ratio, and note B34's +2 is itself NOT-DISTINGUISHABLE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
