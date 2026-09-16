# thui `act v1` — the ACT-NOW breaker on the duck chassis, full 25: public 5.51, in the band

`thui-v3-0` + cell-12 wraps on `ToolAgent.analyze` / `_build_user_prompt` (B70): after 2 dead turns an ACT-NOW
directive opens the next prompt; after 2 more, one simple action is executed for the model. Kernel
`sahasawatt/thui-act-v1` v1, 2026-09-07 08:51–11:12Z, wall 8,458 s. Smoke: `thui-act-v0` v2 (07:03–07:43Z).

## What it scored

| public | levels | scoring | actions | gen tok | act/lvl |
|---|---|---|---|---|---|
| **5.51** | **27** | 17 / 25 | 1,661 | 2.20 M | 61.5 |

`rank_runs.py` vs `thuiv3-pool` (4.39 / 24.25): +1.12, +2.75 levels, 10 up / 12 down, **p = 0.3177,
NOT-DISTINGUISHABLE**. B35 floor 3 / 25 (floor 6).

## Verdict

**Open on stage 2, closed-in-noise on stage 1.** The directive fired 35× with 51 % obedience and left the dead-turn
rate where the chassis already has it (38 % vs 39–41 %); the score sits inside the same-build band like the eleven
prompt-side levers before it. The executed-action stage never armed because the wrapper filtered engine action names
(`ACTION1`…) against model names (`UP`…) — an empty list, silently. A v2 fixes the mapping; whether a forced action
on a 4-dead-turn streak buys a level is the one thing this run did not measure.

Read: `notes/B70-act-now-breaker-on-duck-design.md` (design, smoke record, full-run record).
