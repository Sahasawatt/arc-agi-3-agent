# B77–B79 — which part of the serving stack is worth the step, and can it be separated at all

Written 2026-09-10. `B69` says the Flash-Next stack moved the score and states plainly that it
"isolates neither model nor quant nor MTP nor scheduler". These three rows are what that sentence
turns into once the campaign's own banked runs are asked about it.

Reproduce every figure below:

```
python3 eval/b77_volume_vs_quality.py
```

Six controls — four declared-membership (an arm whose ledger rows do not match its declared members
aborts), one negative, one known-value — before any figure is printed.

## The reframe (B77)

The four components named in `B69` are not four independent axes. They fall on **two**, and the
split is decided by construction rather than by measurement:

| component | what it can change |
|---|---|
| MTP-3 speculative decoding | **volume only.** Speculative decoding is distribution-preserving: proposals are verified against the target model, so accepted tokens are what the target would have produced. It changes throughput and the realised sample, never the policy |
| scheduler / serving profile (async, chunked prefill, CUDA graphs 32, 8 seqs, KV 5 GiB, prefix caching off, PLE offload) | **volume only.** Throughput and memory placement |
| quantization (NVFP4 vs FP8) | **both** — it buys volume, and it perturbs the policy |
| model identity (~180B MoE, 512 experts / top-10, vs dense 27B) | **per-action quality** |

So the question is not *which of four*, it is **how much of the step is volume and how much is
per-action quality** — and that question has a measurable half.

## What the banked runs say

`act/lvl` — actions spent per level cleared. **Higher means each action buys less.**

| arm | n | levels | actions | act/lvl |
|---|---:|---:|---:|---:|
| 27B anim chassis | 7 | 24.3 | 1,422 | **58.5** |
| 27B + 2× clock (`B34`) | 1 | 30.0 | 2,637 | 87.9 |
| **Flash-Next (`B69`/`B76`)** | 3 | 38.3 | 3,774 | **98.4** |
| `v20` MoE-A3B (`B25`) | 1 | 3.0 | 7,656 | 2,552.0 |

**A Flash-Next action is individually WORSE than a 27B action — 98.4 against 58.5.** The stack does
not make the agent smarter per decision. It wins on **volume**: 2.65× the actions for 1.58× the
levels.

That is worth stating against `B69`'s own summary, which reads *"converts the same wall into 2.2–2.4×
the actions and those actions buy levels the 27B chassis does not reach."* The first half is right.
The second half is what three closed rows deny for the 27B chassis — `B16` (v14: actions
1,285 → 1,633, levels 22 → **19**), `B25` (v20: 7,656 actions, 3 levels), `B34` (clock2x: 2× the
wall, levels 28 → 30, `p = 0.2761`). The reconciliation is that **volume pays off at a rate set by
the model taking the actions**, which is why the same lever reads closed on one chassis and open on
another.

## Why the split is NOT determined by anything on disk (B78)

Fit `levels ~ actions^b` on the 27B chassis only (baseline → clock2x), then extrapolate to
Flash's action count and read the residual as the model's contribution:

| base used for the fit | b | predicted levels | volume | model |
|---|---:|---:|---:|---:|
| mean of the 6 anim runs | 0.342 | 33.9 | **69%** | 31% |
| `v10cal` alone — clock2x's own base | 0.138 | 31.5 | **34%** | 66% |

**Two defensible base choices, opposite verdicts.** `b` rests on two points and `clock2x` is n=1, so
this is a first decomposition, not a measurement of the split. Anyone quoting one of these numbers
without the other is quoting a free parameter.

⚠️ And a second confound sits under both: `clock2x` doubled the **wall**, which moves the scorer's
`completion_cap = 100·Σ(done levels)/W` (`B20`). Levels are comparable; its public score is not.

### The control that bounds any volume story

`v20` fired **7,656 actions — more than Flash's 3,774 — and cleared 3 levels.** The volume model
predicts 43.2 for that action count. So volume is **necessary, not sufficient**: a model can be bad
enough that its actions are worthless, and no volume argument stands without naming the model.

### The experiment that would decide it, at no submission slot

**Serve Flash-Next with MTP-3 speculative decoding OFF.** Same weights, same NVFP4 quantization,
same scheduler, same wall. Speculative decoding is distribution-preserving, so the **policy is held
fixed while volume moves** — the one clean cut through this confound. Compare levels against the two
banked Flash draws.

Cost: one public kernel run. A kernel push spends **GPU quota, not the daily submission slot** —
the two are different resources (`scripts/kaggle_push_kernel.py`: *"Compute, never a submission."*).

Pre-register before building: if levels fall roughly in proportion to the action drop, volume is the
mechanism and the model residual is small. If levels hold while actions fall, the model is doing the
work and MTP is buying nothing that matters.

## Can model and quantization be separated at all (B79)

They cannot be separated by a run, only by weights. `RadixArk/Qwen3.8-Flash-Next-NVFP4` **is** the
NVFP4 artifact; there is no FP8 Flash-Next and no NVFP4 27B in hand. Separating them needs the same
weights served at two precisions, which is a build and possibly an impossible one.

This row is **offline research, no GPU, no slot**: enumerate what actually exists as a Kaggle model
asset or on HuggingFace. If neither counterpart exists, the row closes on *not separable with
available weights* — which is a real answer and stops the question being re-asked.

## What is already public, and what that changes

`keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp` — the notebook `B69` vendored — has been a **public**
competition kernel since 2026-09-01, beside `keithtyser/duck-qwen3-8-27b-fp8`,
`jakobbrggen/taaf-anim-arc-agi-3-solver` and `jeroencottaar/tufa-labs-duck-harness-june-30-m`.

⚠️ **`wuliao0/duck-qwen3-8-anim-base` was published 2026-09-10 01:33Z** — anim on the Qwen3.8 base,
which is exactly the build `B69`'s *Not in this build* section named as ours to do next. Read it
before building it.
