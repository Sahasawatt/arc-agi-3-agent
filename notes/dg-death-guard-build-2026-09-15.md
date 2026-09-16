# thui-dg — hard death guard on the anim harness: built, teeth proven, oracle says DO NOT PUSH (2026-09-15)

## What was built
`thui-dg/build_notebook.py` (+ `test_dg_graft.py`): the anim composition of `thui-anim-full25-r2` plus a cell-9 tail that subclasses the
bundle's own `NoopGuard` (`inference/agent/noop_guard.py`, "Experiment 2: Known-Noop-Guard") into `_ThuiDeathGuard`: a
`(level, board_before_sig, action)` combo that reached GAME_OVER is filed in `fatal` (never in the no-op table) and `is_known_noop()`
answers True for it, so the agent's existing pre-execution block path fires (`THUI_DG_BLOCK`). The death signal arrives through one
wrapper on `ToolAgent._compact_action_result` (called immediately before `observe()` in both the single and the batch path) that sets
`pending_game_over` = the executed action's display; `observe()` consumes it once, only when the action matches. `tool_agent.NoopGuard`
is rebound so both construction sites (init, `_ensure_session`) build the subclass. Control arm: no wrapper. Smoke arms bp35/sp80/tn36
@ 1,800 s and full-25 arms are built (4 notebooks); metadata → `thui-dg-v0`. **Nothing pushed.**

This is the mechanical form of thui-db: refuse the action instead of telling the model about it — the one pattern that changed
behaviour on this harness (the bundle's own no-op guard write-up: "Experiment 1 only *mentioned* known no-ops ... ~12% no-op repeats
remained").

## Teeth
`test_dg_graft.py` ALL PASS: seam counts + call ORDER on the real bundle `tool_agent.py` (compact precedes observe in both paths,
2 construction sites by name, hard guard default True); the notebook's own cell-9 source executed against the bundle's real
`noop_guard.py` with a stub ToolAgent; 10 cases. Teeth proven red on 5 mutations (no-pending 6 FAIL, no-block 4, file-as-noop 2,
no-rebind 5, no-compact 6); a crashed case reports as FAIL, not as skipped.

## Oracle (0 GPU) — the target barely exists on the anim base
Exact-state repeat deaths `(level, board_before, action)` — what this guard blocks by construction — counted from events:

| run | deaths | exact-state repeats | (level, MOUSE cell) repeats | (level, non-mouse action) repeats |
|---|---|---|---|---|
| anim-full25-r2 | 15 | 1 | 0 | 2 (tu93) |
| animfast-b71 | 9 | 2 | 0 | 4 (tu93) |
| animfast-v1-d2 | 0 | 0 | 0 | 0 |
| wm-ctl (June duck) | 40 | 0 | 1 | 10 |
| db-ctl / db-ctl-r2 / db-v1 (3 games) | 28 / 27 / 36 | 0 / 0 / 1 | 3 / 5 / 13 | 9 / 7 / 9 |

Two facts, both fatal to the lever as specified:
1. **The anim harness already hardly dies**: 0–15 deaths per full-25 run vs 28–40 on the June duck (its hard no-op guard + animation
   awareness remove most of the flailing). On anim-r2 the three death games ran bp35 1 death / 37 actions, sp80 1 / 70, tn36 **0 / 46**.
2. **Where deaths repeat, they repeat by action-at-level, not by exact board** (tn36 in db-v1: 14 deaths, 11 on the same cell, 1 exact-
   state — the model replays its 61-click sequence and dies on the 61st cell). An exact-state key blocks 0–2 deaths per run; a
   level-wide key would ban budget-death cells that are not fatal (the thui-db v0 lesson: "SPACE kills" on sp80 L2) and buys nothing
   on tn36, whose 61st click is fatal whichever cell it is.

## Verdict
**Park without a smoke.** A 3-game smoke would read ≤ 2 blocks and be VOID by its own rule 1. The death-repeat class is a June-duck
problem the anim bundle already solved with its no-op guard; on the anim base the stalled games are **under-acted, not over-died**:
tn36 46 actions / 36 turns / 0 deaths / L1 in 2.2 h (b71: 81 / 38 / 0 / L1) against the June duck's 481 actions / 7 deaths. The
search-strategy gap on anim is throughput of *committed* actions on games that show no progress — a per-turn action floor or a lower
yield on no-progress games (thui-v3 sets `LOCAL_ANALYZER_YIELD_SECONDS=180`, 3× the June default) — not a death ledger. Unbuilt.

Cost: 0 GPU. Kept as a reference implementation of the block-not-tell pattern for any future guard on this harness.
