# thui `rank v1` — the veto finally fired, and the run lost five levels

**Line** thui · **family** rank · **directory** [`thui-rank/`](../../../thui-rank) · **ticket** `B61` · **status** ran, close recommended (owner's call)

## The one change

[`v0`](thui-rank-v0.md)'s payload at the **design threshold** — the veto arms at 20 or more observations
per game, τ = 0.15, at most 2 vetoes per analysis step, RESET never vetoed — with cell 14's smoke filter
dropped: 25 games on the inherited clock, `B48` chassis. Nothing else differs from the smokes.

## Where it lives

| what | path |
|---|---|
| builder | `thui-rank/build_notebook.py --full --owner=yocybercode --base=v3` |
| notebook | `thui-rank/taaf-thui-rank-v1.ipynb` |
| kernel | `yocybercode/thui-rank-v1`, 2026-09-05 14:05Z start, wall 8,500 s |
| fixture | `eval/fixtures/thui-rank-v1.json` (via `rank_runs.load()`) |
| design + read | `notes/B61-prior-as-ranker-design.md` |

## What it scored

| run | public | hidden | scoring | levels | actions | act/lvl | Mtok |
|---|---|---|---|---|---|---|---|
| `thui-rank-v1` | **3.57** | — | 13 | 19 | 1,306 | 68.7 | 2.11 |

Inside the same-build band. **Not drawn on hidden.**

| comparison | mean | levels | per-game | p |
|---|---|---|---|---|
| vs `thuiv3-pool` (4 runs) | 4.39 → 3.57 (Δ −0.82) | 24.25 → **19** (−5.25) | 8 up / 14 down / 9 flipped | **0.3862 NOT-DISTINGUISHABLE** |

B35 floor: +1 in **1 game** (`vc33`); −1 in **5** (`tu93`, `sp80`, `cd82`, `ls20`, `ft09`).

## Verdict

**The branch executed — 22 `VETO` lines, 0 `BATCH-DROP`, 96 prior updates, `wrapper error` 0 — so the
row's killer 2 (*nothing to veto*) is refuted at the full clock.** What it bought is a negative sign:
−5.25 levels with 14 of 25 games down, the same shape `B60`'s prior showed as a fallback on this chassis.
Not distinguishable from noise at n = 1, and by the campaign's rule a within-noise negative first draw
does not earn the second draw the instrument would need while `B65` is unread.

**Killer 1 (false vetoes on latent actions) is unmeasured** — the 22 veto lines have not been matched
against what the re-picked action then did. That reading, not another full draw, is what could re-open
the row. Close recommended; the status column is the owner's.

## Read next

- [`thui-rank-v0-1.md`](thui-rank-v0-1.md) — the re-smoke that could not reach the branch this run reached
- [`../prior/thui-prior-v1-1.md`](../prior/thui-prior-v1-1.md) — the same prior as a fallback, same sign
- [`../compact/thui-compact-v1.md`](../compact/thui-compact-v1.md) — the other full run of the day
