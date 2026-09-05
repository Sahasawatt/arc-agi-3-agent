# thui `rank v0` — the smoke that proved the harness path and never reached the branch it exists for

**Line** thui · **family** rank · **directory** [`thui-rank/`](../../../thui-rank) · **ticket** `B61` · **status** smoked, ticket open

## The one change

The **same online CNN as [`B60`](../prior/thui-prior-v1.md), moved from the yield path to the `step_env`
argument path**. `B61` never issues an action: it only *refuses* ones it predicts inert. Inside the
wrapped `rec_step_env`, a proposal whose `p_change` is below **τ = 0.15**, after **≥ 20 observations**
for that game, is answered with the harness's own invalid-action payload, so the LLM re-picks inside the
same turn. At most 2 vetoes per analysis step; RESET is never vetoed; a batch never empties.

A veto's failure mode costs one tool round-trip, never a scored action — which is the opposite cost
profile from `B60`, and the whole reason the row exists after `B60` closed negative.

⚠️ **Chassis: this arm was rebased onto the `B48` build** (`--base=v3` = `thuiv3/taaf-thui-v3-0.ipynb`)
on 2026-09-04, so its baseline for any paired read is the **`thuiv3` pool** (4.01 / 4.52 / 5.17 / 3.85),
not `thui-v1-1`. Cells changed: 0, 12, 14 (the smoke's 3-game / 900 s filter).

## Where it lives

| what | path |
|---|---|
| builder | `thui-rank/build_notebook.py --owner=yocybercode --base=v3` |
| notebook | `thui-rank/taaf-thui-rank-v0.ipynb` |
| kernel | `yocybercode/thui-rank-v0` — pushed from the mac after the `sahasawatt` weekly GPU quota blocked it |
| design + read | `notes/B61-prior-as-ranker-design.md` |

## What it scored

**Nothing, and it must not be scored.** A 3-game 900 s smoke produces no public number; the ledger has
no row and should not gain one. COMPLETE 2026-09-04 ~10:27Z, wall **1,347 s**, after a **~2h35m queue
wait** — the first measured queue wait on record.

| oracle | result |
|---|---|
| **P3** harness path intact | **PASS** — 3 games finished (`tr87` 3 actions / `sk48` 11 / `sc25` 10, 0 levels), `wrapper error` 0, `observe skipped` 0, no action ever issued by the prior |
| **P2** the prior trains | **PASS** — `thui-rank: update n=25 buf=10 loss=1.8076`, finite |
| **P1** ≥ 1 veto at obs ≥ 20 | **NOT EXERCISED** — `VETO` 0, `BATCH-DROP` 0 |

Read twice and independently — Sahasawat from `kernels output`, Watchara from `kernels logs` — and every
number agrees.

## Verdict

**Not a refutation: the branch never ran.** The veto arms at ≥ 20 observations per game and no game got
past 11 executed actions in 900 s, so the smoke measured the harness path only. `B61` stays **open**.

Next was `thui-rank-v0-1` with the arming threshold lowered to 5 — see below.

## Read next

- [`thui-rank-v0-1.md`](thui-rank-v0-1.md) — the re-smoke at threshold 5, and why it still could not fire
- [`thui-prior-v1-1.md`](../prior/thui-prior-v1-1.md) — `B60`, the same prior as a fallback, closed negative
