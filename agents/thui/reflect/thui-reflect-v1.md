# thui `reflect v1` — DEFECTIVE: a module-global flag turned thinking off for the whole table

**Line** thui · **family** reflect · **directory** [`thui-reflect/`](../../../thui-reflect) · **ticket** `B62` · **status** ran, DEFECTIVE — do not pool, do not quote as B62's verdict

## The one change

[`v0-1`](thui-reflect-v0-1.md) at full width: cells 0 and 12 only, the smoke filter dropped, 25 games on
the inherited clock. The memory call is unchanged — K = 10, thinking off for that call, cap 1200,
timeout 90 s.

## Where it lives

| what | path |
|---|---|
| builder | `thui-reflect/build_notebook.py --full` (built at `f590d2d`) |
| notebook | `thui-reflect/taaf-thui-reflect-v1.ipynb` |
| kernel | `yocybercode/thui-reflect-v1` v1 |
| fixture | `eval/fixtures/thui-reflect-v1.json` — **banked and labelled DEFECTIVE, never pooled** |
| design + read | `notes/B62-reflection-memory-design.md` |

## What it scored

| run | public | hidden | scoring | levels | actions | act/lvl |
|---|---|---|---|---|---|---|
| `thui-reflect-v1` | **1.39** | — | 12 | 13 | 2,613 | 201.0 |

Dated reading from `notes/LEDGER-all-runs.md`, run 2026-09-04 12:05Z–14:25Z, wall 8,417 s. **Below the
same-build band `[2.82, 5.24]` and below every member of the `thuiv3` pool** (4.01 / 4.52 / 5.17 / 3.85,
levels 23–26). **Not drawn on hidden** — the 09-04 slot went to a `thui-v3-1` resubmit.

## Verdict

🔴 **This number is not a memory result.** The run carried a second variable the base never had, so
`rank_runs.py` vs `thuiv3-pool` reading **4.39 → 1.39, p = 0.0002 WORSE** is **confounded** and is not
`B62`'s verdict. `B62` is *unmeasured* by this run, not closed by it.

**The mechanism** (Sahasawat's correction, same day): `_reflect` flipped
`tool_agent._LOCAL_ANALYZER_ENABLE_THINKING`, a **module global** read at call time (`:1297`), and the 25
games are **threads of one process** (`framework/solver.py:805`). So the MAIN analyzer ran without
thinking whenever any game's memory call was in flight — union of in-flight windows **92% of the run**.

| control | in-window | outside |
|---|---|---|
| `[THINKING` present in analysis events | **1%** (n = 1,451) | **41%** (n = 122) |

Same run, aligned by the transcript wall-clock, and the alignment independently reproduces the 92%.
Per-request completion mean **318 / median 253** (n = 3,548) against **1,839 / 1,297** on `thui-v3-1`
(same chassis); **tok/action 280** against 1,272–1,439 across the family; actions +80%, levels halved.
That is **`B31`/`v21`'s signature exactly** — `v21` cut deliberation and cleared 12 levels.

**Second defect**: upstream rewrites `_last_step_summary` only when a step executes (`:1583`) and never
clears it, so idle turns re-fired the level reflection — `sp80` **30 reflections on 7 actions** (26
byte-identical), `ar25` 26 on 20.

**What did work, and is worth keeping**: 314 reflection calls, **294 returned all seven fields, 0 empty**,
`wrapper error` 0. Nothing about the memory's CONTENT failed.

⚠️ **The latency reading stands and is the minor half.** 60 s mean per call at 25-game concurrency
(12.1 s in the smoke), 20 `ReadTimeout`s, 20 `analyzer request failed` — but 17,636 s of reflection in
flight is **8.9%** of the 25 × 7,920 s game clock.

## Read next

- [`thui-reflect-v1-1.md`](thui-reflect-v1-1.md) — the thread-local fix, and the paired read this run owed
- [`../v4/v4-0.md`](../v4/v4-0.md) — the other run whose headline number turned out to be part defect
