# The MoE run — the first decisive number this campaign has produced

2026-08-23. v20 = v10 with one change: Qwen3.8-27B-FP8 (dense) → Qwen3.6-35B-A3B-FP8
(MoE, 256 experts, 8 active per token, ~3B active of 35B).

## Result

| run | mean | scoring | levels | actions | act/lvl |
|---|---|---|---|---|---|
| v10cal | 4.71 | 18 | 28 | 1,597 | 57.0 |
| v18 | 3.60 | 15 | 22 | 1,576 | 71.6 |
| v19 | 2.82 | 16 | 20 | 1,638 | 81.9 |
| **v20 (MoE)** | **0.18** | **3** | **3** | **7,656** | **2,552** |

**This is the first result outside the [2.82, 4.71] spread that the same build produces**
(LEDGER CORRECTION 3, n=3). Every prior "closed" direction was decided on a gap smaller than
that spread. This one is 15× below its floor, so a single run is enough.

## What it settles

The mechanism was not in doubt — vLLM 0.19.0 loaded the MoE, generated (`2 + 2 equals 4` in
the boot smoke), and the unchanged `qwen3_coder` parser handled its tool calls. The agent
played: **7,656 actions, 4.7× v10's 1,597.**

And it cleared **3 levels against v10's 28.**

R24 concluded by elimination that the bottleneck is the model's ability to find the sequence
that clears a level, not any mechanical property of the harness. v20 is the direct test of
that, and it was run for a different reason:

- if the bottleneck were **throughput / attempts**, a model with ~3B active params — far
  faster per token, and demonstrably able to fire 4.7× the actions — should have scored
  BETTER.
- if the bottleneck is **reasoning per decision**, dropping from 27B dense to ~3B active
  should collapse the score while the action count rises.

The second happened, at 26× on score and 45× on act/lvl. **R24's conclusion now rests on a
measurement rather than on elimination.**

It is also v14's shape, magnified: v14 raised inference throughput 26% and spent it on
attempts instead of levels (2.87). v20 raised the action budget 4.7× and spent all of it the
same way. Two independent points on the same axis, and the axis reads: **capacity added to
this harness becomes attempts, never depth.**

## What it does NOT settle

- **35B-A3B is one generation behind** the 3.8 we run, and that generation was worth +37%
  measured the other way (duck-mod 2.41 → v8out 3.31). Some of the 0.18 is the generation,
  not the architecture. Nothing here separates the two.
- It says nothing about a **larger dense** model, which is the direction it actually points.
- `states: {'gave_up': 25}` again. **Still 0 games won, ever.**

## The direction it points, and the cost of following it

More reasoning per decision, not more decisions. On this hardware (one RTX PRO 6000, 96 GB)
with no internet at scoring, that means a dense model larger than 27B in FP8 — roughly 70 GB
of weights leaves ~26 GB for KV, which v14's numbers suggest is survivable since KV capacity
was never the binding constraint.

⚠️ Whether such a model exists on Kaggle in a loadable format is **not answered**, and the
last two times this campaign said "it isn't there" it was wrong in the same way both times:
R20 searched one registry with three terms and concluded MoE was unavailable; it was in the
Models registry AND in datasets under a fourth term. Any search that concludes "not
available" needs both registries and several spellings before it goes in the ledger.
