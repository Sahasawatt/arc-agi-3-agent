# thui `compact v1` — delivered on all 25 games, in-band, on the build with the confound still in it

**Line** thui · **family** compact · **directory** [`thui-compact/`](../../../thui-compact) · **ticket** `B65` · **status** ran, draw 1 of 2 — row open

## The one change

[`v0`](thui-compact-v0.md) at full width: window **30** (the chassis's own `_PERSISTENT_HISTORY_ASSISTANT_TURNS`),
K **10**, 25 games on the inherited clock, cells 0 and 12 only. ⚠️ **Built from `4dbc9ef`, pushed
09:49Z — before #127 (game label) and #128 (the header reword) merged.** Every fire line reads
`game=arti`, and every game carried the header the smoke's model read as the game's title.

## Where it lives

| what | path |
|---|---|
| builder | `thui-compact/build_notebook.py --full --owner=yocybercode` (at `4dbc9ef`) |
| notebook | `thui-compact/taaf-thui-compact-v1.ipynb` — the tracked file is now the #128 build, not the one that ran |
| kernel | `yocybercode/thui-compact-v1`, 2026-09-05 11:54Z start, wall 8,481 s |
| fixture | `eval/fixtures/thui-compact-v1.json` (via `rank_runs.load()`) |
| design + read | `notes/B65-compaction-of-dropped-history-design.md` |

## What it scored

| run | public | hidden | scoring | levels | actions | act/lvl | Mtok |
|---|---|---|---|---|---|---|---|
| `thui-compact-v1` | **4.88** | — | 16 | 25 | 1,381 | 55.2 | 2.15 |

Inside the same-build band `[2.82, 5.24]`. **Not drawn on hidden.**

| comparison | mean | levels | per-game | p |
|---|---|---|---|---|
| vs `thuiv3-pool` (4 runs) | 4.39 → 4.88 (Δ +0.49) | 24.25 → 25 | 13 up / 10 down / 8 flipped | **0.6794 NOT-DISTINGUISHABLE** |

B35 floor (+1 level in at least 6 of 25 on both draws): **2 games** (`ft09`, `tr87`), −1 in 3.

## Verdict

**The lever is delivered and cheap at 25-game width**: 51 fires, labels 5/5 on all 51, P2 landed 51/51,
memento 458–1,191 chars, latency mean **16.8 s** / max 29.5 s = **0.43 %** of the clock, `wrapper error`
0, `call FAILED` 0, breaker never tripped, thinking on for the main analyzer (completion mean 1,916).

**NOT MEASURABLE, never "no worse" — and this is not a clean draw 1.** The oracle asks for two draws
over the B35 floor; this one sits at +0.75 levels, in the noise, on a build whose header the model can
read as game content. That it still landed in-band with levels at or above the pool says the misread was
not catastrophic at full width; it does not say what the fixed build does. **Next read: a second draw on
`576f9e8`**, which closes the row either way and measures #128's effect on actions per request for free.

## Read next

- [`thui-compact-v0.md`](thui-compact-v0.md) — the smoke, and the transcript that found the header defect
- [`../rank/thui-rank-v1.md`](../rank/thui-rank-v1.md) — the other full run of the day, read against the same pool
