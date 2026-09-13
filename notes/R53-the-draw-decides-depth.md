# R53 — the draw decides a third of the depth, inside one build

**2026-09-13, offline, 0 slots, 0 GPU, 0 API calls.** `eval/arm_oracle_gap.py`, reading the banked
`eval/fixtures/per-level-census.json` and the arm memberships in `eval/fixtures/arms.json`.

## The number

The `v10` arm is four runs that `arms.json` declares the SAME build (`v10cal`, `v19`, `thuiv1-1`,
`thuiv1-1-r2` — "same build as v10, lever proven inert or absent", LEDGER STRICT n=6). Their
per-run depth:

| run | levels |
|---|---|
| `v10cal` | 28 |
| `thui-v1-1` | 25 |
| `thui-v1-1-r2` | 23 |
| `v19` | 20 |

**Best single run 28 · per-game oracle 39 · gap +11 levels (+39%)**, and **19 of the 25 games
disagree on depth across the four runs**. Exact E[oracle] over every subset:

| k | E[oracle] | min | max |
|---|---|---|---|
| 1 | 24.00 | 20 | 28 |
| 2 | 31.17 | 27 | 35 |
| 3 | 35.50 | 33 | 37 |
| 4 | 39.00 | 39 | 39 |

## What this adds to B52

`per_level_census.py` already reported *"stalls BEHIND the game's own frontier: 255 (60%) ← draw
variance"* and an oracle of 47 against a best single run of 30. That population is the **17-run
FAMILY, which is 17 DIFFERENT builds** held to be in-band — so its gap mixes run-to-run variance
with whatever the eleven levers did. Restricted to a **declared single build**, the gap is still
**+39%**. So the variance is the draw, not build diversity, and B52's label was right for a reason
it could not itself show.

## Controls

- **positive**: the same code run over B52's FAMILY list reproduces that script's published
  **oracle 47 / best single 30**. The expected values come from the repo, not from this note.
- **negative**: a one-run arm reports gap 0 — an oracle over one run is that run.
- **closure**: at k = n there is exactly one subset, so E[oracle] must equal the oracle; it does.

All three run on every invocation and the script refuses to print arm numbers if any fails.

## What it REFUTES — both obvious remedies

1. **`bm.n_passes = k` does not buy it.** `pool_runs.py` states its own LIMITS as *"equal weight
   per run, which is what `n_passes` does"* — equal weight is the **mean** of the draws, i.e. the
   **k=1 column (24.00)**, not the max (39). It is also hardcoded to 1 in cell 14 *after* the
   customization hook, so a build cannot set it at all.
2. **Pinning the sampler does not buy it.** Removing the spread lands on one draw, and the four
   draws here are 20, 23, 25, 28 — three of the four are below the best. `LOCAL_ANALYZER_SEED`
   shifts nothing about which draw you get.

⚠️ MAP **B37** calls `LOCAL_ANALYZER_SEED` and `LOCAL_ANALYZER_TEMPERATURE` *"the two knobs this
campaign has never touched"*. That framing is **stale**: `arms.json` records both the `avo` and
`thuiv3` arms as built with **`LOCAL_ANALYZER_SEED 20260825` and `TEMPERATURE 0.6`**. The knobs are
set; what has never been measured is whether setting them **removes the spread**.

## What it does NOT say

- It is a **bound on what per-game best-of-k would give**, not a plan. No lever in this harness
  collects it, and this note does not propose one.
- It is **public-set only** (25 games, v10-era chassis). The current chassis is Flash-Next, whose
  runs are not in this fixture — the census was built 2026-08-27/28, before they existed.
- It says nothing about hidden. Hidden is one scalar per submission, so per-game variance there is
  **not measurable with anything banked**.
- The `avo` and `fast` arms (two members each, both declared same-build) and three of the four
  `thuiv3` members are **not in the census fixture**, so the script skips them loudly. The gap is
  measured on one arm, on one chassis.

## The cheapest next reading

**Bank the census rows for the other three `thuiv3` members.** That arm is declared byte-identical
*and* built with the seed pinned at `20260825`, so its spread answers the one question the
refutations above leave open: **does a pinned seed remove the draw, or does the serving stack
re-introduce it anyway?** Continuous batching under vLLM is not bitwise deterministic, so a pinned
seed plausibly does nothing here — but that is a hypothesis, and this arm is the measurement.
It costs no slot and no GPU: the logs for those runs are already on Kaggle.

If the spread survives a pinned seed, then the +39% is not a sampling artefact at all, and the
lever that could collect it is **in-run recovery after a stall** — the agent reaching its own best
depth reliably rather than being given another draw. That has no ticket; the nearest rows are B50
(plateau detection) and B70 (the ACT-NOW breaker).

## Reproduce

```bash
python3 eval/arm_oracle_gap.py
```

No network, no key, no slot — stdlib only, same as `per_level_census.py` and `rank_runs.py`.
