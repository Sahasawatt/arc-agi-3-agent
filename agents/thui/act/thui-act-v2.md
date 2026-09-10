# thui `act v2` — the breaker with the name mapping fixed, full 25: public 2.47, B70 CLOSED

`thui-act-v1` + the v2 fix (engine action names mapped through `to_model_action` before filtering; withheld case
logged). Kernel `sahasawatt/thui-act-v2` v1, 2026-09-07 09:31–11:45Z, wall 8,480 s.

## What it scored

| public | levels | scoring | actions | gen tok | act/lvl |
|---|---|---|---|---|---|
| **2.47** | **19** | 16 / 25 | 1,249 | 2.31 M | 65.7 |

`rank_runs.py` `thuiv3-pool` (4.39 / 24.25) → v2: −1.92, −5.25 levels, 8 up / 15 down, **p = 0.0309, WORSE**.
v1 → v2 p = 0.0924. B35 floor 1 / 25.

## Verdict

**Closed.** Stage 1 fired 20× at 43 % obedience with the dead-turn rate at 42 % (chassis 39–41 %). Stage 2 armed in
one game (ls20, 37 dead turns of 42), fired three times, and every fire logged `executed=False` — the `step_env`
payload carries no `executed` key, so the wrapper's execution seam is unproven in the direction that matters. A
third draw would measure the same wrapper; reading the harness's real `step_env` return shape is the prerequisite,
and with B69 clearing the rule the same day it is not priced.

Read: `notes/B70-act-now-breaker-on-duck-design.md` (design, smoke, v1 and v2 full-run records).
