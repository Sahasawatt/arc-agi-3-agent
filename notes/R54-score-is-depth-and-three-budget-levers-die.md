# R54 — score is depth, the efficiency channel is capped, and three budget levers die on arithmetic

**2026-09-13, offline, 0 slots, 0 GPU, 0 API calls.** `eval/depth_economics.py` over the banked
25-game fixtures and `eval/fixtures/per-level-census.json`. Companion to [R53](R53-the-draw-decides-depth.md).

## 1. Score is depth, and almost nothing else

Across every banked 25-game fixture (n=37), score against three candidate drivers:

| driver | all fixtures | excl. `v20` |
|---|---|---|
| **levels cleared** | **+0.954** | **+0.954** |
| actions (volume) | +0.161 | +0.686 |
| actions/level (efficiency) | −0.362 | **−0.028** |

🔴 **The efficiency row is a trap and it caught me first.** Read with `v20` included, −0.362 says
efficiency predicts score, and the fixture table supports the story beautifully: the best single run
in the campaign, `thui-animfast-b71-full25-r1`, scores **9.56 on 2,008 actions at 51.5 act/level**,
while its own arm sibling `thui-fast-v0` scores **8.07 on 3,925 actions at 109.0**. It is a clean
narrative and it is wrong. Dropping the one MoE outlier (`v20`, 2,552 act/level, score 0.18) takes
the correlation to **−0.028**. One run carried it.

The consequence matters for how B71 is judged. D3 names *"actions/clock, tokens/action"* as the
**low-variance** metrics to verify levers on, and that is correct — they are reproducible where
score is not. But low-variance is **not** predictive, and treating animfast's 47% better act/level
as evidence it beats the June solver would be conflating the two. On score it remains
NOT-DISTINGUISHABLE (p = 0.6762, R53).

**Why depth and not efficiency**, structurally: `docs.arcprize.org/methodology` caps a level at
**1.15×** the human baseline, so the whole efficiency channel is worth at most 15% per level, while
depth runs up to the completion cap (B20). The channel is not unimportant — it is **fenced**.

⚠️ This is an **ecological** correlation, across builds, and levels→score is **partly
definitional**: the per-game score is a level-weighted average, so more levels mechanically means
more score. The empirical content is that the *other* channel is inert.

## 2. The budget is already uniform — measured in tokens, not actions

**Actions are an OUTPUT of the clock, not an input**, and using them as the budget proxy invents an
allocation story that is not there. `tok/action` varies **573 … 5,523 (9.6×)** between games, so:

- by **actions**, spend looks wildly uneven (15 on `r11l`, 176 on `re86`) and the cheap-return games
  look starved;
- by **`generated_tokens`**, every game gets **3.1% – 4.3%** of a ~2.39M-token run, against a
  uniform share of 4.0%. That is exactly what a per-game wall hands out.

I wrote the first reading down before computing the second. It was an artefact.

Marginal value of depth, per game: clearing one more level of a `W`-level game adds
`(d+1)/(W(W+1)/2)` to that game's score and a 25th of that to the total. The return spans
**1.41 … 7.88 points per Mtok (5.6×)** on that flat spend, the top being `ft09` 7.88, `ar25` 6.78,
`vc33` 6.25, `dc22` 6.16, `cd82` 5.64 — **together only 20.1% of the budget**. Three games
(`g50t`, `sk48`, `tr87`) average **zero levels** and consume **11.4%**.

⚠️ **These are AVERAGES, not marginals, and nothing may be sized with them.** `clock2x` doubled
every game's wall and bought **+2 levels** (28 → 30) with act/level worsening 57.0 → 87.9. The
marginal rate is far below these averages, so "move 11.4% and collect ~1.6 points" is arithmetic on
a rate that has been measured not to hold.

## 3. Three levers that die here, each saving a slot

**(a) The early-exit / abandon rule — REFUTED.** The Fog lists *"an early-exit that returns a game's
unused budget to the pool"*. Swept over the 17-run family (268 game-runs cleared ≥1 level, 157 never
did):

| T (tokens) | first-level clears lost | budget freed |
|---|---|---|
| 20,000 | 222/268 (82.8%) | 29.0% |
| 40,000 | 142/268 (53.0%) | 21.8% |
| 60,000 | 89/268 (33.2%) | 14.8% |
| 80,000 | 40/268 (14.9%) | 8.0% |
| 100,000 | 16/268 (6.0%) | **2.8%** |

**No T pays.** The distributions explain it: level-1 clears land at **p50 41,898 / p90 92,029 /
p99 117,156** tokens against a per-game share of ~102,600, while runs that never clear burn a
**median 99,307** — so *"has not cleared yet"* does not separate the two until the budget is
already gone.

**(b) Per-game targeting by name — cannot ship.** The arithmetic in §2 is computed on the public 25.
The scored set is **110 hidden games** nobody has seen, so "defund `g50t`" has no hidden counterpart.
Any allocation policy has to be **game-agnostic** to transfer, and (a) is the game-agnostic form of
it, refuted above.

**(c) Buying actions by thinking less — refuted four ways, now with the extreme case.** Output cap
`v9` **0.22** · brevity prompt `v12` **3.72** · `reasoning_effort` medium `v21` **1.25** · and
`v20`, which fired **7,656 actions, the most in the campaign, for 3 levels and 0.18**. Volume
without reasoning quality produces nothing, and §1 is why: actions only matter through levels.

## 4. What the numbers point at instead

**The median successful game spends ~41% of its entire token budget clearing level 1**
(41,898 of ~102,600), and the failures spend **~97% of it for nothing**. Average depth across the
arm is ~1 level. So the budget is overwhelmingly consumed *acquiring each game's mechanics*, and it
is paid fresh every run — which is the same thing R53 measures from the other side: **19 of 25 games
disagree on depth inside one build, and 60% of stalls are on levels a sibling run cleared.**

Ranked by evidence, not by appeal:

✅ **Item 1 below was DONE on 2026-09-13 and answered NO — see R53's 🟢 block.** Tufa's framework is
vendored at `localrig/tufa-arc-agi-framework/` (23 tracked files; the earlier "not vendored" claim
searched `RHAE`, a word that code never uses). `diagnostics.py` averages passes (*"per-pass mean"*,
line 422), so `n_passes = k` buys the k=1 column, never the oracle — **the +39% is not purchasable**.
The pendant question is answered too: `actions_per_level` is a cumulative per-level counter
(*"Invariant: `sum(actions_per_level) == len(history)`"*, `game.py:259`), so **a RESET does not
re-zero a level's actions** and "explore freely, then execute cleanly" is not expressible here.

➕ **And the scorer is now runnable offline.** `game.py:381 _compute_final_score` states it *"Mirrors
`arc_agi.scorecard.EnvironmentScoreCalculator` (v0.9.8)"*; re-implemented from the census's
`per_level` + `levels` it **reproduces the recorded per-game score 25/25 on `v10cal`, `thui-v1-1` and
`v19` independently**. ⚠️ It also corrects an over-read of the `min(score, max_score)` clip: the clip
does **not** make score identical to the completion fraction everywhere, only where the completed
levels average ≥100. Measured: **7/18 scoring games on `v10cal`**, 10/15 on `thui-v1-1`, 11/16 on
`v19`. The 7 independently reproduces **B20's "7 of 25 games are already at it"**. So the efficiency
channel is **provably worth zero on those games and still live on the rest** — a sharper statement
than §1's correlation, and the first one that is per-game and computable during a run.

1. ~~**Read the `arc_agi`/`taaf` scorer for how `n_passes` aggregates — 0 slots, 0 GPU, a code read.**~~ (done, above)
   R53 leaves this branching: if passes are averaged, the +39% oracle is unreachable; if the best is
   taken, it is purchasable by a one-line patch at **cell 15** (after the cell-12 hook, so a hook
   cannot do it — a cell patch can, which this campaign does routinely). Highest value per unit
   effort on the whole list, and it is not measured anywhere in this repo.
2. **Bank the census rows for the other three `thuiv3` members** — declared byte-identical with
   `LOCAL_ANALYZER_SEED 20260825`, so their spread answers whether a pinned seed removes the draw or
   the serving stack re-introduces it. Needs Kaggle credentials, no slot.
3. **Persistent mechanics memory across levels and runs** (B62 reflection memory, B60/B61's prior,
   the AVO arm's memory + supervisor). This is the only family aimed at the 41% and at the
   re-learning, and the one outside-evidence datum is AVO reaching the full public set.
4. **Do not spend a slot on another solver patch.** Three are banked at p = 0.68 / 0.77 / 0.52
   (R53), and three more levers die in §3. ⚠️ Those p-values are **underpowered nulls**, not proofs
   of no effect — B71's +0.87 may be real and invisible at n=25.

## Reproduce

```bash
python3 eval/depth_economics.py
```

Controls run on every invocation and the script refuses to print if one fails: `thui-fast-pool` must
total the published 8.69 / 38.5; every census game-run's `per_level` must be `total` long and sum to
`actions`; and dropping `v20` must move the act/level correlation, or §1's outlier claim is wrong.
