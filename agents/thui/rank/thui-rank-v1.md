# thui `rank v1` — the veto finally fires, and 0.9% reach is the whole result

**Line** thui · **family** rank · **directory** [`thui-rank/`](../../../thui-rank) · **ticket** `B61` · **status** ran, mechanism proven, score not measurable; row left `open`

## The one change

**A frame-change prior that REFUSES actions instead of issuing them.** The same online CNN as `B60`
(trained per game on that run's own executed actions), moved off the yield path and onto the `step_env`
argument path: a proposed action whose predicted change-probability is below **τ = 0.15**, after **≥ 20
observations** of that game, is answered with the harness's own invalid-action payload, so the LLM
re-picks inside the same turn. Capped at **≤ 2 vetoes per step**. It never issues an action — that would
be `B60`, which is already closed null-to-negative.

Both smokes left P1 **NOT EXERCISED**: at 900 s a game produces 3–11 actions, so the prior never reached
its arming threshold, and `v0-1` at `--min-obs=5` found no inert example either. Only the full clock could
answer.

## Where it lives

| what | path |
|---|---|
| builder | `thui-rank/build_notebook.py --full` (base `v3`, i.e. the `B48` chassis; `--min-obs` is refused with `--full`) |
| notebook | `thui-rank/taaf-thui-rank-v1.ipynb` |
| kernel | `yocybercode/thui-rank-v1` v1 — the only push |
| fixture | `eval/fixtures/thui-rank-v1.json` (mean reproduces 3.5692) |
| design | `notes/B61-prior-as-ranker-design.md` |

## What it scored

| run | public | hidden | scoring | levels | actions | act/lvl | Mtok |
|---|---|---|---|---|---|---|---|
| `thui-rank-v1` | **3.57** | — | 13 | 19 | 1,306 | 68.7 | 2.11 |

Run 2026-09-05 14:05:29Z–16:19:58Z, wall 2h 14m 28s = the full per-game clock. **Inside the same-build
band `[2.82, 5.24]`.** **Not drawn on hidden.**

| comparison | mean | levels | per-game | p |
|---|---|---|---|---|
| vs `thuiv3-pool` (4 runs) | 4.39 → 3.57 (Δ −0.82) | 24.25 → 19 (−5.25) | 8 up / 14 down / 9 flipped | **0.3862 NOT-DISTINGUISHABLE** |

B35 floor: **1 game** up (`vc33`), −1 in 5. Dated reading; `notes/LEDGER-all-runs.md` is the authority.

## Verdict

**All three predictions passed, and the one that mattered passed too small to matter.**

- **P1 PASS — 22 vetoes**, at observation counts **22–96**, spread `ACTION3` ×12 · `ACTION6` ×5 ·
  `ACTION5` ×4 · `ACTION1` ×1. Never above the ≤ 2/step cap, never an issued action.
- **P2 PASS** — the online model kept updating and the loss stayed finite.
- **P3 PASS** — no wrapper error and no traceback in the run log.

⚠️ **22 vetoes against roughly 2,400 proposed actions is 0.9% reach.** A lever that speaks on one action
in a hundred cannot move a level count in either direction, so **−5.25 levels is NOT MEASURABLE and must
never be written up as "the veto hurt"** — `p = 0.3862`, and the gap sits inside the campaign's own
same-build spread.

**The row is left `open` on purpose.** Closing `B61` here versus buying a second run — or lowering τ /
arming earlier, which is a different build and a new row — is the owner's call, not this read's.

## Read next

- [`thui-rank-v0.md`](thui-rank-v0.md) and [`thui-rank-v0-1.md`](thui-rank-v0-1.md) — the two smokes where P1 was never exercised
- [`../prior/thui-prior-v1.md`](../prior/thui-prior-v1.md) — `B60`, the same prior on the issuing path, closed null-to-negative
