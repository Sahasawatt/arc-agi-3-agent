# thui `compact v1` — the dropped-history seam repaired for 0.43% of the clock, and the score does not move

**Line** thui · **family** compact · **directory** [`thui-compact/`](../../../thui-compact) · **ticket** `B65` · **status** ran, `B65` closed on this read

## The one change

**Summarise what the history window is about to DELETE, and re-inject it ahead of the surviving turns.**

duck loses history at `_PERSISTENT_HISTORY_ASSISTANT_TURNS = 30`, not at the token budget — on
`thui-v3-1` the budget binds on 0.2% of requests while the turn window drops 22.2 turns per game. `B62`
rewrote seven world-model slots from turns still *inside* the window and read `p = 0.9978`; this build
summarises the turns leaving it. One tool-free call per **K = 10** dropped turns (and when a level
completes), cap 600, timeout 90 s, thinking off **per thread** (the `B62` v1 defect, fixed there and
inherited here), the seven `_summarized_knowledge` slots untouched — this is not `B62` stacked.

## Where it lives

| what | path |
|---|---|
| builder | `thui-compact/build_notebook.py --full` (base `v3`, i.e. the `B48` chassis) |
| notebook | `thui-compact/taaf-thui-compact-v1.ipynb` |
| kernel | `yocybercode/thui-compact-v1` v1 — the only push |
| fixture | `eval/fixtures/thui-compact-v1.json` (mean reproduces 4.8788) |
| design + read | `notes/B65-compaction-of-dropped-history-design.md` |

## What it scored

| run | public | hidden | scoring | levels | actions | act/lvl | Mtok |
|---|---|---|---|---|---|---|---|
| `thui-compact-v1` | **4.88** | — | 16 | 25 | 1,381 | 55.2 | 2.15 |

Run 2026-09-05 11:54:11Z–14:08:18Z, wall 2h 14m 07s = the full per-game clock. **Inside the same-build
band `[2.82, 5.24]`.** **Not drawn on hidden** — the 09-05 slot went to the AVO arm (`56039729`).

| comparison | mean | levels | per-game | p |
|---|---|---|---|---|
| vs `thuiv3-pool` (4 runs) | 4.39 → 4.88 (Δ +0.49) | 24.25 → 25 (+0.75) | 13 up / 10 down / 8 flipped | **0.6794 NOT-DISTINGUISHABLE** |

B35 floor (+1 level in ≥ 6 of 25): **2 games** (`ft09`, `tr87`), −1 or worse in 3 (`cd82`, `sc25`,
`sp80`). Dated reading; `notes/LEDGER-all-runs.md` is the authority.

## Verdict

**Mechanism delivered and cheap; score not measurable.** 51 compaction calls fired — **35** on the K = 10
rule and **16** on a level completing — summarising **446** dropped turns, mean 8.7 per call. All **51**
returned the full 5/5 label set with `missing=[]`, and the P2 line read `landed=True` on all 51, so the
memento reached the prompt every time. Latency mean **16.8 s** / max 29.5 s, sum **858 s = 0.43%** of the
25 × 7,920 s clock — a quarter of `B62`'s 1.6%, so the non-blocking worry that closed `B62` v1 does not
arise here.

**`B65` closed on it**, by the row's own rule that either reading closes the more-context family
(`B17` / `B54` / `B48` / `B62` / `B65`). Repairing the seam duck actually loses history at is affordable
and moves nothing — the same shape `B62` read at the other seam.

⚠️ **One defect, in the instrument rather than the mechanism.** Every one of the 51 event lines prints the
constant `game=arti`, so this run's log **cannot say which games compacted**; the 25 `new buffer for
game #N` lines are correctly numbered, so the count is trustworthy and the attribution is not. Fix the
print before any successor run reads per-game.

⚠️ **NOT MEASURABLE at n = 1, never *better*.** +0.49 and +0.75 levels are inside this campaign's own
same-build spread.

## Read next

- [`../reflect/thui-reflect-v1-1.md`](../reflect/thui-reflect-v1-1.md) — `B62`, the same shape at the other seam
- [`../v3/v3-1.md`](../v3/v3-1.md) — the `B48` chassis this is built on
