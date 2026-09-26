# thui-b101 KeepOnDeath — pre-registered 2026-09-26, before any build, test or run

Base: `thui-a5-mtp0k7s28-full25-r1` (B81), full clock (7,920 s), all 25 public games. Treatment: one cell-9
graft only. `ToolAgent._update_summarized_knowledge_from_step_summary` wipes the six summarized-knowledge slots
(`world_model`, `goal_model`, `action_model`, `recent_findings`, `open_questions`, `current_plan`) whenever the
step summary carries `level_transition` OR `run_complete` OR `game_over`. The arm drops `game_over` from that
condition; the level-transition and run-complete wipes stay. The control carries the SAME graft with the keep flag
off: it wipes exactly as B81 does and prints the same counters. Changed cells must be exactly `[0, 9]` on both.

## Why the old bar is not used

MAP B101's registered KILL gate (levels up on >= 12/25 games, read through `rank_runs`) has ~0 power even at full
clock (peer power check, relay `01M39P1AS55GFNE9642ZYAG6N9`; unverified here): the effect is confined to the 7-10
game-runs with a death after non-empty slots, while 6 games carry same-build score sd > 5. The row says any future
run needs a NEW bar at the mechanism. This is that bar. **Its power is UNMEASURED** — the run is registered as a
mechanism reading, not as a promotion decision.

## VALID / VOID (plumbing, per arm)

VALID only if `THUI_B101_GRAFT ok keep=<True|False>` appears once, and the final `THUI_B101_STATS` line shows
`level_wipes >= 1` and `qualifying_deaths >= 1` (a death with >= 1 of the six slots non-empty just before it). On
the arm, `kept == qualifying_deaths` and `wiped_on_death == 0`; on the control, `kept == 0`. Anything else is VOID
and nothing below is read.

## The bar (mechanism level, per qualifying death)

Unit = a qualifying death: a `THUI_B101_DEATH agent=<id> level=<L> slots=<N>` marker with N >= 1. `agent` is the
ToolAgent's `id()` (the harness object carries no game id). Outcome = a later `THUI_B101_CLEAR` marker on the same
`agent` (the run got out of the level it died on), read from the kernel log alone — no transcript parsing, so the
reading does not depend on prompt wording. Read: clear rate after a KEPT death (arm) vs after a WIPED death
(control).

- **PASS (mechanism works):** arm clear rate exceeds control by >= 15 percentage points AND the arm has >= 15
  qualifying deaths.
- **KILL:** arm clear rate <= control clear rate, with >= 15 qualifying deaths on the arm.
- **INCONCLUSIVE:** anything else, including < 15 qualifying deaths on either arm (peer census predicts ~27
  model-seen deaths per full run, 7-10 qualifying game-runs; the unit here is deaths, not game-runs).

Secondary, descriptive only, never a verdict: per-game levels through `eval/rank_runs.py`, hidden score if
submitted.

## Known confound, carried

A death can REFUTE the model, so keeping slots across it can mislead (the peer's caveat). The prompt already asks
the model to revise on contradiction; this bar measures the net effect and does not separate the two.

## Addendum 2026-09-26 (after the reading) — the verdict clauses overlapped

The text above is left as registered. On the reading (keep 21 qualifying deaths, 1 clear-after; ctl 11,
1 clear-after), KILL fired because it floors only the arm (>= 15). INCONCLUSIVE also fired, because its
floor covers "either arm". A registered bar must be a partition, so a future bar in this family uses:

| arm n >= 15 AND ctl n >= 15 | rate order | verdict |
|---|---|---|
| no | any | INCONCLUSIVE |
| yes | arm - ctl >= 15 pp | PASS |
| yes | arm <= ctl | KILL |
| yes | 0 < arm - ctl < 15 pp | INCONCLUSIVE |

Each sample-size floor sits in one place, and every row names both arms. Under this table, B101's reading
is INCONCLUSIVE on sample size. The row closes on the peer's power read (MAP B101), not on this bar.
