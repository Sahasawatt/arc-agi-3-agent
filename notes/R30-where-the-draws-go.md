# R30 — where the remaining hidden draws go

2026-08-24. Answers **B30** offline, 0 slots. Instrument: `scripts/b30_draws.py`, run as

```bash
KAGGLE_API_TOKEN=$(op read 'op://Personal/Kaggle - Arc AGI API/credential') \
  .venv/bin/kaggle competitions leaderboard -c arc-prize-2026-arc-agi-3 --download -p <dir>
python scripts/b30_draws.py <dir>/arc-prize-2026-arc-agi-3-publicleaderboard-*.csv
```

Two controls gate it and it exits 1 before printing any new number if either fails:
the per-game loader must reproduce all five published public means
(`v10cal` 4.71 · `thuiv1` 3.20 · `v18` 3.60 · `v19` 2.82 · `v23` 3.32), and the board must
still hold the six teams R21 named by hand on 2026-08-22 with submission counts that have
not shrunk. Both passed.

## The answer

**Neither of the ticket's two options. Do not spend a hidden draw at all until a candidate
is DISTINGUISHABLE from v10 on public.**

B30 offered "re-measure v10's mean" against "test one candidate". The first is refuted
below. The second is not currently available: every build since v10 that has a public
number sits inside the same-build band `[2.82, 4.71]` and `rank_runs.py` reads every one of
them NOT-DISTINGUISHABLE from `v10cal` — `v18` p=0.51, `v23` p=0.41, `v19` p=0.21,
`thuiv1` p=0.3027. **A hidden draw on a build public cannot separate from v10 IS a v10
re-draw wearing another name**, and is worth the same +0.04.

Only two builds have ever landed outside that band — `v20` (0.18, p=0.0001) and `v21`
(1.25, p=0.0052) — and both are WORSE. So the campaign has not produced a candidate worth a
hidden draw since v10 on 2026-08-21.

**The submission quota is not the binding constraint. The supply of rankable builds is.**
We hold ~7 draws a week and zero builds that public can rank.

## 1. Re-drawing v10 cannot reach the bar

Kaggle keeps the best submission — **confirmed from the board itself** this round, not from
our own notes, which were the only prior source (7 mentions, all internal): the leaderboard
shows `Thuitanium` at **1.70** on **10 submissions**, and our two v10 draws were 1.70 and
1.32. It reports the max.

So a further draw is not a measurement, it is a lottery ticket, and it only counts if it
beats the 1.70 already banked. With v10's hidden mean at 1.51:

| σ | one more draw | 3 draws | 7 draws (a full week of quota) |
|---|---|---|---|
| 0.269 | **+0.038** | 1.74 (+0.04) | 1.87 (+0.17) |
| 0.376 | **+0.074** | 1.83 (+0.13) | 2.02 (+0.32) |

To reach the top-5 bar of 2.88 in 7 re-draws would need **σ = 1.01**, which is **2.7×** the
larger of the two measured values. Refuted.

### The σ is not a single reading any more

The 0.38 hidden gap is n=2, and LEDGER CORRECTION 2 correctly says so. A second,
**independent** estimate exists and nobody had taken it: the four same-build public draws
`[4.71, 4.55, 3.20, 2.82]` have CV **0.249**, and transferring that onto the hidden mean
(assuming the noise is multiplicative — stated, not proven) gives σ = **0.376** against the
pair's own **0.269**. They agree within a factor of 1.40. Neither is anywhere near 1.0,
which is what the decision above needs.

## 2. What a draw buys, bounded by 2,506 teams

`SubmissionCount` is a column of the public leaderboard. R21 downloaded the board on
2026-08-22 and did not keep the file, so this has been available all campaign and unread.

| submissions | teams | median | mean | max |
|---|---|---|---|---|
| 1 | 572 | 0.15 | 0.29 | 1.81 |
| 2–3 | 535 | 0.21 | 0.44 | 2.70 |
| 4–7 | 453 | 0.26 | 0.55 | 2.43 |
| 8–15 | 364 | 0.54 | 0.82 | 3.17 |
| 16–31 | 237 | 1.17 | 1.10 | 2.45 |
| 32–63 | 142 | 1.48 | 1.40 | 3.57 |
| 64+ | 66 | 1.83 | 1.81 | 4.58 |

⚠️ **This table is confounded and reads as an UPPER BOUND, never as an effect.** Teams that
submit more are teams that iterate more, so every rise here is draws *plus* better builds.
It is quoted because even the overstated version does not reach: our bucket (8–15) to the
top bucket (64+) is +1.29 median for **54 more draws**, against a gap to the bar of +1.37.

Three rows refute the lottery directly, and they do not need the confound resolved:

- **`wking edewd` scored 2.70 — rank 10 — on 3 submissions.**
- **`0xbr4h1m` beat our 1.70 on 1 submission** (1.81).
- Of the **682** teams with ≥10 submissions, **489 score below our 1.70.**

The five teams at or above the 2.88 bar used `[11, 34, 41, 50, 116]` submissions. The
minimum is 11 — one more than we have already spent.

## 3. Two numbers in working memory are stale or mixed

**The top-5 bar is 2.88, not 2.57.** MAP.md's goal line still carries 2.57, dated
2026-08-19. The board moved hard in two days: `Tufa Labs` went 3.04 → **4.58** and now leads
by a full point. The gap from v10's hidden mean is **+1.37**, not +1.06.

**The shrink factor mixes a max with a mean.** LEDGER CORRECTION 2 prints 3.05× from
"public [4.55, 4.71] against a hidden mean of ~1.51" — the top TWO public draws over the
MEAN of the hidden ones. That is the same error the correction flags one paragraph earlier
about having quoted 1.70. Means on both sides — 3.82 public over 1.51 hidden — give
**2.53×**, and it moves the target the *easy* way: a candidate needs public **7.29** to sit
at the bar, not 8.83. B20's efficiency ceiling of 5.80 public is **2.29 hidden** on the
corrected factor, still below 2.88, so **depth remains the only axis** — that conclusion is
unchanged.

## 4. B30's own premise: the second data point contributes nothing

The row argues "variance grows with score (v9-lite A/A spread 0.00 vs duck-v10 0.38)".

A **constant coefficient of variation** already predicts exactly that, and the CV is
measured twice — 0.249 public, 0.178 hidden. At v9-lite's 0.10 the same CV predicts
σ = **0.025**: the pair had almost no room to differ, whatever the truth about how variance
scales. So the 0.00 is what the v10 pair alone already implies; it is not a second
measurement, and "variance grows with score" is a restatement of multiplicative noise
rather than a finding.

The row's **conclusion** — 2+ draws to rank a high build — stands. It rests on one pair.

## What is NOT established

- **The confound in §2 is not resolved.** Nothing here separates "more draws" from "more
  iterations"; the argument only needs the upper bound, and says so.
- **The CV transfer in §1 assumes the noise is multiplicative.** Two estimates agreeing
  within 1.40 is corroboration, not proof, and both rest on ≤4 samples.
- **Normality of a hidden draw is assumed** by the max-of-n arithmetic. The per-game
  evidence (R29 §9, `rank_runs.py`'s own docstring) says the per-game deltas are heavy
  tailed; a heavier tail would make the lottery *better* than computed here, but it would
  need σ to be 2.7× off, not the shape.
- **2.88 is today's reading.** The bar moved 2.57 → 2.88 in five days. Re-download before
  quoting it.
