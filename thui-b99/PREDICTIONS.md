# thui-b99 RungPin — pre-registered before any build or test run

Base: `thui-a5-mtp0k7s28-full25-r1` (B81). Treatment: one cell-9 graft only. When an observed
`level_completed` result clears a level, the harness replaces one per-game `VERIFIED PREVIOUS RUNG` block
with the assistant reasoning from that clearing turn, the executed action, and its compact result. The block
is at most 2,048 characters and is prepended to later analyzer requests without changing stored history. No
extra model call is made. Full-run changed cells must be exactly `[0, 9]`; smoke may additionally change cell
15 only to select tn36 / vc33 / bp35 and set the clock to 1,800 seconds.

## VALID / VOID

A run is VALID only if the install marker `THUI_B99_GRAFT ok` appears, every parsed level transition has
exactly one corresponding `THUI_B99_PIN game=... level=... chars=...` marker, and every reported character
count is at most 2,048. The pinned block must not appear before a clear, must replace rather than accumulate
on a later clear, must remain isolated per game, and injection must leave raw `_history_messages` unchanged.
The solver profile, context settings, prompt text, game set, and clock must match B81, except that smoke uses
the registered three-game subset and 1,800-second clock. Any violation makes the run VOID and no score or
level comparison is read.

## Kill rules

- Smoke (3 games, 1,800 seconds): kill if prompt tokens rise by more than 10% versus control, or if
  actions/minute is below 85% of control.
- Full matched pair (25 games each): pass only with at least +1 level on at least 12/25 games and no more
  than 6/25 games down. Read the comparison per game, never from the mean; one jackpot game cannot pass it.

