# duck `clock2x` — the highest public mean the campaign has produced, and it ships nowhere

**Line** duck · **version** clock2x · **directory** [`clock2x/`](../../../clock2x) · **ticket** `B34` · **status** ran, closed

## The one change

`bm.solver.max_runtime_s_per_game` **7,920 s → 15,840 s**, gated so it can never apply on a real
competition rerun. Nothing else differs from `duckv10`: same anim bundle, same Qwen3.8-27B-FP8,
output uncapped, no KV flag, no upscale change, no patch.

**Why it was worth a slot** (`B33`, `scripts/b27/censoring.py`): every one of the 125 run-games on
record ends **at the wall** — per-game wallclock min 7,920.2 / median 7,920.5 / max 7,970.3 against
a cap of 7,920, **zero** games under 98% of it. No game has ever stopped on its own logic, so the
corpus is **right-censored on depth** and *"finished"* and *"cut"* are indistinguishable in every
score this campaign holds. Inside the observed window the level-up rate does not decay (50.9% /
49.1% across each game's halves).

## Where it lives

| what | path |
|---|---|
| builder | `clock2x/build_notebook.py` |
| notebook | `clock2x/taaf-clock-2x-v1.ipynb` |
| kernel | `clock-2x-v1` |

## What it scored

| run | public | levels | actions | act/lvl | Mtok | wall |
|---|---|---|---|---|---|---|
| `clock2x` | **6.40** | **30** | 2,637 | 87.9 | **4.33** | 4 h 24 m 50 s |

Dated reading from `notes/LEDGER-all-runs.md`, 2026-08-27. The **highest public mean on record**,
and outside the same-build band `[2.82, 5.24]`.

## Verdict

🔴 **It cannot ship.** Hidden is 4 waves × 15,840 s = **17.6 h** against a 9 h budget.

🔴 **And doubling the clock did not buy depth.** Levels went **28 → 30 — +2 across 25 games** at
`p = 0.2761`, **NOT-DISTINGUISHABLE**. The `+1.69` on the mean came from efficiency and luck in six
games. Say **NOT MEASURABLE**, never *zero*: at that p, `+2` and `0` are not separable.

**Where the doubled budget went is the sharper half**: generated tokens **2.03 M → 4.33 M (2.13×)**,
the first run to break the campaign band of 2.02–2.21 M — but it landed in **tok/action
1,272.6 → 1,640.6 (+28.9%)**, higher than every other run, while actions rose only 1.65×. The agent
deliberated harder per decision and cleared no more levels.

Doubling is the strongest form of the lever that can be built, so the answer covers the family —
and it **prices `B36`** (reallocate rather than extend) before anyone builds it: reallocation hands
live games **+30%** actions where doubling handed them **+100%**, so its ceiling is **under one
level per run**.

## What it left behind

The run's `summary.txt` prints `levels=<cleared>/<TOTAL>` per game, so it settled **all 25 game
totals** (sum **183**) — recorded as `eval/fixtures/game-totals.json`. That closed the blocker
`B35` had been sitting on.

## Read next

- `notes/B34-clock2x-result-2026-08-25.md` (in `Knowless-Crew/arc-agi-pub`)
- `notes/wayfinder/MAP.md` `B33` — the censoring measurement that motivated it
