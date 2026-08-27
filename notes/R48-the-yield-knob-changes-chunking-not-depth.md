# R48 — the yield knob changes CHUNKING, not depth

**2026-08-27 · offline · 0 slots · `scripts/b27/r48_chunking.py`**

`B48` raised `LOCAL_ANALYZER_YIELD_SECONDS` 60 → 180 and closed **NOT MEASURABLE** on score
(public 4.01 against 4.33, `p = 0.5370 / 0.8145 / 0.4759`, levels **23 = 23**). `R47` proved the
gate itself moved: `thui-v3-0` breaks the 60 s bound on 96 of 297 multi-request turns and never
breaks 180 s. Neither said what the agent *did* with the budget, because `*_usage.jsonl` carries
requests and turns and no decision boundary at all.

The event logs carry both. Reading them, **the knob did not buy more deliberation. It bought
fewer, longer reasoning rounds — and less total reasoning per decision.**

## The measurement

Paired, 25 games, same 25 in both runs, one variable.

| | A = 60 s (`thuiv1-1r2`) | B = 180 s (`thui-v3-0`) | Δ |
|---|---:|---:|---:|
| decisions (`analysis_step`) | 428 | 429 | **+0.2%** |
| reasoning rounds (`analysis` events) | 1,070 | 719 | −32.8% |
| **rounds per decision** | **2.50** | **1.68** | **−33.0%** |
| chars per reasoning round | 26,306 | 30,386 | +15.5% |
| **transcript chars per decision** | **65,765** | **50,926** | **−22.6%** |
| actions per decision | 2.94 | 3.27 | +10.9% |
| levels | 23 | 23 | 0 |

The decision count is unchanged to within one. Each round is 15.5% longer, but there are 33%
fewer of them, so the agent spent **22.6% less reasoning text per decision** at three times the
budget.

## It ranks, unlike the score

Eight runs on disk carry an events log. Six state `LOCAL_ANALYZER_YIELD_SECONDS: 60` in their own
`taaf_setup_env.json`; `thuiv1` and `v10cal` predate that artifact, so their setting is **inferred**
and they are carried separately rather than folded into a figure quoted as measured.

| run | yield | rounds/dec | chars/dec |
|---|---|---:|---:|
| `clock2x` | 60 confirmed | 2.74 | 75,012 |
| `v25seed` | 60 confirmed | 2.61 | 73,505 |
| `thuiv1-1r2` | 60 confirmed | 2.50 | 65,765 |
| `v23` | 60 confirmed | 2.44 | 66,963 |
| `v18` | 60 confirmed | 2.34 | 63,174 |
| `v19` | 60 confirmed | 2.18 | 59,474 |
| `thuiv1` | 60 *inferred* | 2.35 | 64,019 |
| `v10cal` | 60 *inferred* | 2.14 | 57,986 |
| **`thui-v3-0`** | **180 confirmed** | **1.68** | **50,926** |

- confirmed cohort (n=6): mean **2.47**, sd **0.196**, range 2.18–2.74 → **z = −4.04**
- paired within the shared 25 games: rounds/decision fell in **21 of 25**, rose in 4,
  two-sided exact binomial **p = 0.00091**
- `chars/dec` of the treated run is below **every** member of the cohort, confirmed or inferred

`B48`'s own score was inside the same-build band and ranked nothing. This does.

## Why it is the opposite sign from B48's premise

`B48` was proposed on `R44`'s arithmetic: 60 s buys ~784 completion tokens at 12.7 tok/s against a
**1,368**-token median, so ordinary reasoning is **1.74×** the turn budget. The reading was that the
gate was *cutting reasoning short* and lifting it would let a round finish.

What the gate actually does is force a **yield and re-entry**. The interrupted reasoning did not
vanish — it resumed as another `analyze()` call, and at 60 s that produced **2.50 rounds per
decision**. Raising the ceiling removed most of those re-entries. So the gate was not a cap on
thinking; it was a mechanism that *multiplied* it, and B48 removed the multiplier.

That reframes the whole family. `B25` (MoE), `B34` (clock 2×) and `B48` were all read as
"more reasoning per decision, no score". Only two of them actually delivered more reasoning per
decision. `B48` delivered less, and scored the same.

## The unit, which is the whole finding

Two groupings live in the event log and the repo calls both of them "turn":

| grouping | `thuiv1-1r2` | used by |
|---|---:|---|
| `analysis_step` | **428** | the workspace `CLAUDE.md` replay-player note |
| `analysis` event = one `analyze()` call | **1,070** | `scripts/b27/corpus.py`, `scripts/b27/r44_turn_budget.py`, `R29`, `R44`, `R47` |

They differ by **2.5×**. `R44`'s published `requests = 1306` equals this run's usage-row count
exactly and its `turns = 1070` equals its analysis-event count exactly, so R44/R47 are keyed to the
`analyze()` call — which is the correct unit for a question about the yield gate, because the gate
is tested once per `analyze()`. The hazard is a reader cross-applying the other definition and
dividing a published R44 figure by 2.5.

## Controls

`scripts/b27/r48_chunking.py --selftest` refuses to report anything until it reproduces
`R44`'s 1,306 / 1,070 and `corpus.py`'s 1,973 / 5,052 / 125 from the same corpus, plus a
reachability control and a nonexistent-run negative control. **Teeth proven by mutation**: grouping
by `analysis_step` instead of `analysis` events — the exact error this instrument exists to catch —
turns four gates red and exits 1, while the unmutated file exits 0. An off-by-one in a reference
figure also reddens. Without that gate a wrong grouping would print a plausible table 2.5× off in
the right units and nothing downstream would catch it.

## What this does NOT show

- ⚠️ **n = 1 at the treated setting.** The cohort bounds the *null* spread; nothing here estimates
  the spread of a 180 s run. `B37` already put one build's two runs 0.91 apart on score.
- ⚠️ **It explains no score.** Levels are identical, 23 = 23. This is a statement about the
  mechanism, not about why the mechanism did not pay.
- Whether *fewer, longer* rounds are better or worse than *more, shorter* ones is untested. The
  score says nothing separates them; this note says they are genuinely different behaviours.
- The re-entry account of the gate is read off the deltas, not off `tool_agent.py`. It predicts
  that a run at yield → ∞ converges toward 1.00 rounds per decision, which is checkable and
  unchecked.
