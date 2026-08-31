# R52 — B35-b closes without a detector: its ceiling is short of the bar at every honest rung

**2026-08-31, offline, 0 slots, 0 GPU.** `eval/b35b_ceiling.py`, nine controls, teeth proven by
five mutations each red on exactly the control that owns it, tree restored byte-identical.

`B35-b` — can the BOARD separate a game that will eventually score from one that never does,
early enough to act — was the last offline detection route B35 had. R45 found no early
event-log feature; R50 found the transcript's one candidate was a leak under a third holdout.
Building the board detector is a session's work. **This priced its ceiling first, and the ceiling
does not reach.**

## 1. What was measured

The ceiling on any detector is **perfect foreknowledge**. So: at action `k`, abandon exactly the
games that never score, hand their remaining clock to the survivors, and let the survivors buy
their next levels. Nothing a board feature could do beats that.

Two generosities are deliberate and both inflate the answer:

- the clock is treated as **fungible** across games, which is what B36 proposes and the runtime
  does not do (`max_runtime_s_per_game` is per game);
- levels are bought at prices drawn from the census of what runs actually paid.

A level **no run ever cleared cannot be bought at any price** — the one bound not relaxed,
because the corpus carries no evidence it is reachable.

Scoring is not restated: the script imports `level_score` / `game_score` / `run_scores` from
`eval/oracle_ceiling.py`, which lifts them from `inference/tools/traces.py` and carries the
control that matters — reproducing **19 of 19** published public means from the census. One
implementation, one place for it to be wrong.

## 2. The headline, and why it is not the answer

At `k=5`, oracle rule, levels priced at the **cheapest any of the 19 draws ever paid**:

| | mean over 19 runs | `clock2x` | `thui-v1-1` | `v10cal` |
|---|---|---|---|---|
| base | 3.35 | 6.40 | 5.24 | 4.71 |
| ceiling | **8.34** | 9.99 | 9.98 | 9.80 |

That reads like the largest lever ever priced in this campaign. It is an artifact of the price.

The two pricing poles are close — the run's **own median** spend per cleared level gives 7.86
against the corpus minimum's 8.34 — so the inflation is **not** in the speed assumption. It is in
*which levels are for sale*.

## 3. The reproducibility gate kills it

The minimum over 19 draws is an order statistic. B35's own row already measured what that means:
of the 47-level pointwise oracle, **exactly one** (game, level) pair was cleared by every run, and
`clock2x`'s 30 levels sit on the **K=5 (26%)** rung. Applying that gate to the *price* — a level
is buyable only once at least K of 19 draws cleared it, then priced at the median of those draws:

| K | buyable levels | ceiling | delta | bought | actions/level |
|---|---|---|---|---|---|
| 1 | 47 | 8.00 | **+4.65** | 12.3 | 27 |
| 3 | 34 | 5.17 | **+1.81** | 5.9 | 29 |
| **5** | **30** | **4.21** | **+0.86** | 2.9 | 26 |
| 10 | 20 | 3.63 | +0.28 | 1.2 | 22 |
| 19 | 1 | 3.35 | +0.00 | 0.0 | — |

**At the rung the campaign's best run actually occupies, a perfect detector buys +0.86 public.**

## 4. The model contradicts the one experiment that bought clock

The script reports its own implied conversion rather than leaving it to be inferred: **27 actions
per marginal level**. `clock2x` (B34) doubled `v10cal`'s clock — about +1,000 actions — and cleared
**+2** levels, i.e. **~500 actions per marginal level**, at `p = 0.2761`.

**The model is 18.5× more generous than the measurement, in the direction that flatters the
lever.** Every ceiling above is bounded by that ratio. ⚠️ B34's +2 is itself NOT-DISTINGUISHABLE,
so the denominator is soft — but it is the only direct measurement of buying clock that exists,
and it points the same way as the reproducibility gate.

## 5. Against the bar

Leaderboard re-downloaded **2026-08-31T16:52:49Z** (not quoted from a stored reading): the top-5
bar is **4.27** (`Tong Hui Kang`), field 2,664, we are rank 191 at 2.02. At the LEDGER's
2.68×–2.91× shrink a candidate needs public **11.44 – 12.43**.

- best shippable base today: `thui-v1-1` **5.24** (`clock2x`'s 6.40 cannot ship — cell 12 degrades
  to v10 under `TRUE_SUBMISSION`)
- the **unreproducible K=1** ceiling takes it to 9.98 — still short
- the **honest K=5** ceiling takes it to ~6.1 — short by more than the whole gap

## 6. The finding that outlives the row

**Detection is only worth anything EARLY, and early is exactly where two modalities have already
come up empty.** Beside the oracle rows, the cheap rule that needs no detector at all — R45's
*abandon every game that has not cleared level 1 by action k* — closes the gap as k rises:

| k | perfect detector | R45's cheap rule | what detection is worth |
|---|---|---|---|
| 5 | 8.34 | 0.56 | +7.78 |
| 10 | 8.19 | 3.02 | +5.17 |
| 20 | 7.97 | 5.42 | +2.55 |
| 40 | 6.89 | 6.97 | **−0.08** |

At `k=40` the cheap rule has **already matched** perfect foreknowledge. R45's own conclusion —
*by k=40, 105 of 200 cells have already levelled up, the level-up IS the signal* — is the same
fact from the other side: past k=40 there is nothing left to predict.

## 7. Verdict

**`B35-b` is CLOSED. Do not build the board detector.** The frame `B35` stays open: a per-game
lever keyed on something the runtime already prints (`levels=<cleared>/<TOTAL>`) is untouched by
this, and this result is about *clock reallocation*, which is the only consumer detection has.
It also prices `B36` independently and more tightly than before — at the honest rung, **+0.86**.

## 8. Limits

1. **19 full-25 runs of the same 25 public games.** The hidden 110 is a different population.
2. **The clock is fungible here and is not in the runtime.** Making it so is B36's build, not free.
3. **Only levels some run cleared can be bought.** The ceiling is silent about levels nobody has
   ever cleared — which is where the remaining 3 never-scored games live.
4. **B34's +2 is NOT-DISTINGUISHABLE**, so §4's ratio has a soft denominator.
5. **The bar is a dated reading and moves** — 4.05 → 4.27 inside 7h40m on the day this was written.
   Re-download before re-deriving §5.

## 9. Reproduce

```bash
python eval/b35b_ceiling.py --selftest   # 9 controls over the real census, no corpus needed
python eval/b35b_ceiling.py              # the tables above
```
