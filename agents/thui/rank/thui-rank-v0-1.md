# thui `rank v0.1` — a loss of exactly zero, and what it says about these three games

**Line** thui · **family** rank · **directory** [`thui-rank/`](../../../thui-rank) · **ticket** `B61` · **status** smoked, ticket open

## The one change

`--min-obs=5`: the veto's arming threshold drops from the design's **20 observations per game to 5**.
Smoke-only — `--full` with any non-design threshold is refused by an assert, and cell 0 carries a
"Smoke variant" line. Everything else is [`v0`](thui-rank-v0.md).

It exists to prove the veto **path** — score → the harness's own invalid-action payload → the LLM
re-picks in the same turn — once per game, plus the false-veto proxy. `v0` could not reach it because no
game got past 11 executed actions in 900 s.

## Where it lives

| what | path |
|---|---|
| builder | `thui-rank/build_notebook.py --min-obs=5 --owner=yocybercode --base=v3` |
| notebook | `thui-rank/taaf-thui-rank-v0-1.ipynb` |
| kernel | `yocybercode/thui-rank-v0-1` |
| design + read | `notes/B61-prior-as-ranker-design.md` |

## What it scored

**Nothing — a smoke, as above.** COMPLETE 2026-09-04 ~11:35Z, wall **1,337 s**, queue wait ~20 min (so
the morning's 2h35m was the pool, not a rule).

| oracle | result |
|---|---|
| **P3** harness path intact | **PASS** — 3 games finished (`sc25` 16 actions / `tr87` 18 / `sk48` 8, 0 levels), `wrapper error` 0 |
| **P2** the prior trains | **PASS by letter, and the number is the finding** — `update n=25 buf=11 loss=0.0000`, `update n=50 buf=9 loss=0.0000` |
| **P1** ≥ 1 veto | **STILL NOT EXERCISED** — `VETO` 0, `BATCH-DROP` 0, false-veto proxy 0 |

## Verdict

⚠️ **A loss of exactly zero after 25 steps means every observation carried the same label.** On these
three games, inside 900 s, **every executed action changed the board**, so the buffer holds no inert
example at all. The prior *was* armed this time (8–18 executed actions per game) and still never vetoed,
because `score()` returns `None` for any (board, action) already observed to change, and a net trained on
all-ones predicts change everywhere else.

**What this closes**: the harness path is clean twice over — the wrap lands, the filter fires, the
trainer runs, nothing breaks the turn. That is the whole of what a 900 s smoke can say.

**What it does not**: the veto path has still never executed, and it cannot be forced on games whose
early actions all move the board. Proving it needs either a smoke game with inert early actions or the
full clock.

**Not today's build.** `B60` measured this prior family net negative as a fallback, and `B61`'s only
evidence so far is *does not crash*. Left **open**; the next step is a `--full` run at the design
threshold paired against `eval/fixtures/thuiv3-pool.json`, and only when a slot is not better spent — on
2026-09-04 it was, by [`B62`](../reflect/thui-reflect-v1.md).

## Read next

- [`thui-rank-v0.md`](thui-rank-v0.md) — the first smoke
- `notes/B61-prior-as-ranker-design.md` — the veto rule, the budget, and the pre-registered killers
