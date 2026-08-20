# ARC-AGI-3 per-game score stability report

## Executive conclusion

The reliable base is **not flat across the six runs**.

Across the seven games classified RELIABLE, the mean score ranges from **4.13 to 7.24 per reliable game**, a **75% max/min spread**. Expressed as contribution to the 25-game public mean, it ranges from **1.156 to 2.026**. Therefore, the six files do **not** support the conclusion that every measured design delta was lottery noise.

Lottery games still account for a material and unstable share of each run:

- **15.8%–37.0%** of total public score comes from LOTTERY games.
- The V5 identical-code pair is especially revealing: its public means are close, **2.426 vs 2.371**, but this masks large and offsetting per-game changes—including a **16.37-point** swing on `re86` and a **14.29-point** one-run score on otherwise-DEAD `sc25`.
- Identical-code action counts are also unstable, but action swings do not track score swings consistently. Large score changes sometimes occur with almost unchanged action counts.

## Sources and method

Every score and action count below was read from the corresponding `benchmark.json`:

| Column | Run | Source |
|---|---|---|
| DM1 | duck-mod run 1 | [benchmark.json](/mnt/c/Users/Vampi/AppData/Local/Temp/duckmodout/benchmark.json) |
| DM2 | duck-mod rerun | [benchmark.json](/mnt/c/Users/Vampi/AppData/Local/Temp/duckmodcal/benchmark.json) |
| V4 | v4 | [benchmark.json](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv4out2/benchmark.json) |
| V5a | v5 run 1 | [benchmark.json](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv5out/benchmark.json) |
| V5b | v5 rerun | [benchmark.json](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv5cal/benchmark.json) |
| V6 | v6 | [benchmark.json](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv6out/benchmark.json) |

The corresponding `summary.txt` files were checked against the rounded per-game scores and action totals: [DM1](/mnt/c/Users/Vampi/AppData/Local/Temp/duckmodout/summary.txt), [DM2](/mnt/c/Users/Vampi/AppData/Local/Temp/duckmodcal/summary.txt), [V4](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv4out2/summary.txt), [V5a](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv5out/summary.txt), [V5b](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv5cal/summary.txt), and [V6](/mnt/c/Users/Vampi/AppData/Local/Temp/duckv6out/summary.txt).

The JSON records do not contain a literal `num_actions` field. The summaries’ `actions=` value equals `sum(actions_per_level)`, so that sum is used as the per-game action count.

Classification was applied in this order:

1. **DEAD:** zero in at least 5/6 runs.
2. **RELIABLE:** positive in at least 5/6 runs and nonzero maximum/minimum no greater than 3×.
3. **LOTTERY:** everything else—intermittent zeros or greater than 3× nonzero variation.

All arithmetic used the full-precision JSON values. Displayed matrix values are rounded to two decimals.

## 1. Score matrix

| Game | DM1 | DM2 | V4 | V5a | V5b | V6 | Classification |
|---|---:|---:|---:|---:|---:|---:|---|
| `ar25-0c556536` | 7.73 | 0.00 | 6.29 | 8.33 | 2.78 | 7.26 | RELIABLE |
| `bp35-0a0ad940` | 0.28 | 0.00 | 0.06 | 0.25 | 0.44 | 0.58 | LOTTERY |
| `cd82-fb555c5d` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | DEAD |
| `cn04-2fe56bfb` | 0.00 | 0.00 | 0.00 | 0.89 | 0.00 | 0.00 | DEAD |
| `dc22-fdcac232` | 0.00 | 0.00 | 0.00 | 1.66 | 4.76 | 0.00 | LOTTERY |
| `ft09-0d8bbf25` | 28.57 | 27.91 | 14.29 | 16.98 | 14.09 | 14.29 | RELIABLE |
| `g50t-5849a774` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | DEAD |
| `ka59-38d34dbb` | 0.00 | 0.96 | 1.08 | 0.00 | 0.00 | 0.00 | LOTTERY |
| `lf52-271a04aa` | 1.82 | 1.82 | 1.22 | 1.82 | 0.00 | 1.82 | RELIABLE |
| `lp85-305b61c3` | 2.78 | 2.78 | 2.78 | 2.78 | 2.78 | 2.78 | RELIABLE |
| `ls20-9607627b` | 2.06 | 0.32 | 0.00 | 0.00 | 0.00 | 0.00 | LOTTERY |
| `m0r0-492f87ba` | 0.00 | 0.49 | 0.00 | 0.00 | 0.00 | 2.12 | LOTTERY |
| `r11l-495a7899` | 4.76 | 1.99 | 4.76 | 2.40 | 4.76 | 0.00 | RELIABLE |
| `re86-8af5384d` | 0.89 | 1.73 | 2.51 | 16.67 | 0.30 | 6.58 | LOTTERY |
| `s5i5-18d95033` | 0.08 | 0.00 | 0.00 | 0.27 | 2.78 | 0.00 | LOTTERY |
| `sb26-7fbdac44` | 2.78 | 2.78 | 2.78 | 2.78 | 2.78 | 2.78 | RELIABLE |
| `sc25-635fd71a` | 0.00 | 0.00 | 0.00 | 0.00 | 14.29 | 0.00 | DEAD |
| `sk48-d8078629` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | DEAD |
| `sp80-589a99af` | 4.76 | 0.25 | 4.76 | 0.00 | 4.53 | 1.61 | LOTTERY |
| `su15-1944f8ab` | 2.22 | 2.22 | 2.03 | 2.22 | 1.72 | 2.22 | RELIABLE |
| `tn36-ef4dde99` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | DEAD |
| `tr87-cd924810` | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | DEAD |
| `tu93-0768757b` | 1.46 | 4.85 | 0.00 | 2.70 | 3.08 | 4.24 | LOTTERY |
| `vc33-5430563c` | 0.00 | 5.98 | 0.04 | 0.90 | 0.19 | 0.00 | LOTTERY |
| `wa30-ee6fef47` | 0.00 | 0.00 | 0.69 | 0.00 | 0.00 | 0.00 | DEAD |

## 2. Classification and lottery swings

There are **7 RELIABLE, 10 LOTTERY, and 8 DEAD** games.

### RELIABLE

| Game | Positive runs | Nonzero range | Nonzero ratio |
|---|---:|---:|---:|
| `ar25-0c556536` | 5/6 | 2.78–8.33 | 3.00× |
| `ft09-0d8bbf25` | 6/6 | 14.09–28.57 | 2.03× |
| `lf52-271a04aa` | 5/6 | 1.22–1.82 | 1.49× |
| `lp85-305b61c3` | 6/6 | 2.78–2.78 | 1.00× |
| `r11l-495a7899` | 5/6 | 1.99–4.76 | 2.39× |
| `sb26-7fbdac44` | 6/6 | 2.78–2.78 | 1.00× |
| `su15-1944f8ab` | 6/6 | 1.72–2.22 | 1.29× |

Only `lp85` and `sb26` are numerically invariant. The RELIABLE label means recurrent, not perfectly stable: `ft09` alone moves by **14.48 score points** across the six runs.

### LOTTERY

“Swing” is the six-run maximum minus minimum. Where zeros occur, the nonzero fold ratio is also shown.

| Game | Positive runs | Six-run range | Swing | Nonzero ratio |
|---|---:|---:|---:|---:|
| `bp35-0a0ad940` | 5/6 | 0.00–0.58 | 0.58 | 9.15× |
| `dc22-fdcac232` | 2/6 | 0.00–4.76 | 4.76 | 2.87× |
| `ka59-38d34dbb` | 2/6 | 0.00–1.08 | 1.08 | 1.12× |
| `ls20-9607627b` | 2/6 | 0.00–2.06 | 2.06 | 6.34× |
| `m0r0-492f87ba` | 2/6 | 0.00–2.12 | 2.12 | 4.36× |
| `re86-8af5384d` | 6/6 | 0.30–16.67 | 16.37 | 55.39× |
| `s5i5-18d95033` | 3/6 | 0.00–2.78 | 2.78 | 33.06× |
| `sp80-589a99af` | 5/6 | 0.00–4.76 | 4.76 | 19.22× |
| `tu93-0768757b` | 5/6 | 0.00–4.85 | 4.85 | 3.32× |
| `vc33-5430563c` | 4/6 | 0.00–5.98 | 5.98 | 139.96× |

The largest lottery is `re86`: it scores in every run but varies **55.39×**, including **16.67 → 0.30** between identical-code V5 reruns.

### DEAD

| Game | Zero runs | Exceptional nonzero result |
|---|---:|---:|
| `cd82-fb555c5d` | 6/6 | None |
| `cn04-2fe56bfb` | 5/6 | 0.89 in V5a |
| `g50t-5849a774` | 6/6 | None |
| `sc25-635fd71a` | 5/6 | 14.29 in V5b |
| `sk48-d8078629` | 6/6 | None |
| `tn36-ef4dde99` | 6/6 | None |
| `tr87-cd924810` | 6/6 | None |
| `wa30-ee6fef47` | 5/6 | 0.69 in V4 |

`sc25` is classified DEAD by the stipulated ≥5/6-zero rule even though its single V5b hit contributes **0.5714** to that run’s overall mean. That exceptional contribution must not be mistaken for reliable base.

## 3. Fraction of each run attributable to lottery games

“Lottery mean contribution” is the sum over the ten LOTTERY games divided by all 25 games. “Fraction of total” divides that lottery sum by the run’s total score.

| Run | Public mean | Reliable contribution | Lottery contribution | Dead contribution | Lottery fraction of total |
|---|---:|---:|---:|---:|---:|
| DM1 | 2.4077 | 2.0265 | 0.3812 | 0.0000 | **15.8%** |
| DM2 | 2.1631 | 1.5800 | 0.5830 | 0.0000 | **27.0%** |
| V4 | 1.7318 | 1.3660 | 0.3381 | 0.0278 | **19.5%** |
| V5a | 2.4256 | 1.4924 | 0.8974 | 0.0357 | **37.0%** |
| V5b | 2.3708 | 1.1561 | 0.6432 | 0.5714 | **27.1%** |
| V6 | 1.8509 | 1.2458 | 0.6051 | 0.0000 | **32.7%** |

The decomposition is exact apart from displayed rounding:

`public mean = reliable contribution + lottery contribution + dead contribution`

### What explains the headline mean differences?

Relative to V4:

| Comparison | Public-mean delta | Reliable delta | Lottery delta | Dead delta |
|---|---:|---:|---:|---:|
| DM1 − V4 | +0.6758 | **+0.6605** | +0.0431 | −0.0278 |
| V5a − V4 | +0.6937 | +0.1265 | **+0.5593** | +0.0079 |
| V5b − V4 | +0.6390 | −0.2098 | +0.3051 | **+0.5436** |

Thus:

- The **DM1 2.41 vs V4 1.73** gap is almost entirely reliable-category movement under this classification, principally affected by the high-scoring reliable games.
- The **V5a 2.43 vs V4 1.73** gap is mostly lottery contribution.
- The **V5b 2.37 vs V4 1.73** gap is mostly the one-run `sc25` DEAD-category hit plus lottery contribution, despite a lower reliable contribution than V4.

### Identical-code mean decomposition

| Pair | Public-mean change | Reliable change | Lottery change | Dead change |
|---|---:|---:|---:|---:|
| DM1 − DM2 | +0.2446 | +0.4465 | −0.2019 | 0.0000 |
| V5a − V5b | +0.0548 | +0.3363 | +0.2542 | −0.5357 |

The near-equal V5 public means are not evidence of per-game stability. Large components cancel:

- V5a has **+0.3363** more reliable contribution and **+0.2542** more lottery contribution.
- V5b receives **+0.5357** more contribution from DEAD games, almost entirely `sc25`.

## 4. Reliable-base score

Because “mean over reliable games only” can be read two ways, both forms are provided.

| Run | Reliable score sum | Mean over 7 reliable games | Contribution to 25-game public mean |
|---|---:|---:|---:|
| DM1 | 50.6624 | **7.2375** | 2.0265 |
| DM2 | 39.5011 | **5.6430** | 1.5800 |
| V4 | 34.1489 | **4.8784** | 1.3660 |
| V5a | 37.3104 | **5.3301** | 1.4924 |
| V5b | 28.9030 | **4.1290** | 1.1561 |
| V6 | 31.1460 | **4.4494** | 1.2458 |

**This reliable base is not stable.** Its maximum/minimum ratio is **1.75×**, and the range is **3.1085 points per reliable game**.

Even the pure identical-code reruns move materially:

- Duck-mod: **7.2375 → 5.6430**, down **1.5945** per reliable game.
- V5: **5.3301 → 4.1290**, down **1.2011** per reliable game.

Accordingly, the data does not permit treating cross-design reliable-base changes as clean design effects: the identical-code pairs demonstrate substantial variance inside the reliable category itself.

## 5. Identical-code action counts versus scores

### Aggregate action variability

For each game, the action ratio is the larger identical-pair count divided by the smaller.

| Pair | Median action ratio | Maximum action ratio | Median symmetric action change | Games with >3× action change | Score-changing games | Score zero/nonzero flips |
|---|---:|---:|---:|---:|---:|---:|
| DM1 vs DM2 | 1.91× | 5.57× | 62.5% | 4/25 | 12/25 | 6/25 |
| V5a vs V5b | 1.48× | 7.47× | 39.0% | 2/25 | 14/25 | 4/25 |

Action counts therefore **do swing substantially**, including on games whose scores do not change. But they do **not swing in step with scores**, and the score outcomes are more discontinuous because they include zero/nonzero flips and very large score ratios.

### Per-game action evidence

| Pair/game | Score change | Actions | Action ratio | Reading |
|---|---:|---:|---:|---|
| DM `sp80` | 4.76 → 0.25 | 194 → 198 | 1.02× | Large score collapse with nearly identical actions |
| DM `vc33` | 0.00 → 5.98 | 34 → 52 | 1.53× | Zero-to-hit score flip without comparable action swing |
| DM `ft09` | 28.57 → 27.91 | 44 → 132 | 3.00× | Actions triple while score remains nearly stable |
| DM `lf52` | 1.82 → 1.82 | 234 → 42 | 5.57× | Identical score despite the pair’s largest action ratio |
| DM `g50t` | 0.00 → 0.00 | 53 → 262 | 4.94× | Large action swing, no score movement |
| V5 `re86` | 16.67 → 0.30 | 151 → 181 | 1.20× | 16.37 score swing with only 20% action-ratio growth |
| V5 `sc25` | 0.00 → 14.29 | 145 → 150 | 1.03× | Huge score flip with almost unchanged actions |
| V5 `lp85` | 2.78 → 2.78 | 49 → 366 | 7.47× | Pair’s largest action ratio, identical score |
| V5 `m0r0` | 0.00 → 0.00 | 608 → 85 | 7.15× | Very large action swing, no score movement |
| V5 `tu93` | 2.70 → 3.08 | 104 → 104 | 1.00× | Identical action count, modest score movement |

The answer to “do action counts swing as much as scores?” is therefore:

- **Action counts are themselves highly unstable:** median pairwise ratios of 1.48×–1.91× and maxima of 5.57×–7.47×.
- **They do not explain the score lottery arithmetically:** some of the largest score swings occur with only 1.02×–1.20× action changes, while the largest action swings produce identical zero or identical positive scores.
- No causal interpretation beyond that mismatch is supported by these six files.