# thui-af — action floor on the anim harness: built, teeth proven, oracle sized (2026-09-15)

## The gap it targets
anim-r2, the stalled games: tn36 36 turns / 46 actions / 0 deaths / L1 in 2.2 h; 19 of 35 turn ends = `Yielded control to solver:
turn_time_budget` (180 s of python inspection + thinking, no `action(...)`), sp80 17/36, bp35 15/33 no-action turn ends. The model
investigates and does not commit. Prompt-side levers priced NULL four times; the two things that moved behaviour on this harness are
harness-side (the bundle's hard no-op guard; the June milestone runner-up's click heuristic *as a fallback when the model does not act*).

## What was built
`wt-fast2/thui-af/` (builder + `test_af_graft.py`, 4 notebooks: smoke bp35/sp80/tn36 @ 1,800 s + full-25, v0 + control; metadata →
`thui-af-v0`). One wrapper on `ToolAgent.analyze`: after the original returns, a per-game stall counter counts turn ends with no
executed action on the same level (yield or plain); at 2 the wrapper calls the solver's own `step_env` with ONE action — a MOUSE click
on a rare-colour cell the floor has not used on this level (background = modal colour), else a random non-mouse valid action, never
RESET — and prints `THUI_AF_FLOOR`. An executed model action resets the counter; a level change resets counter, cap and used cells;
cap 40 floor actions per level; nothing fires when `should_stop()`; retryable failures are not stalls; the original result is returned
untouched (the solver retries the same analysis step and the model sees the new frame through the runtime state, as it does for its
own actions). No prompt text added. Seed 20260915. Control = same notebook, no wrapper.

## Teeth
`test_af_graft.py` ALL PASS on the bundle's real `runtime_state.py` / `action_names.py` with a stub `analyze`: 13 cases (fires on
the 2nd no-action turn only, rare-colour MOUSE, reset on execute, fires every later no-action turn, no cell repeat, level reset, cap
40, should_stop, retryable ignored, never RESET, non-executed not counted, result identity) + a seam check that the real solver passes
`valid_actions/step_env/should_stop` as kwargs. Teeth red on 7 mutations (never-fire 6 FAIL, no-reset 4, no-cap 2, ignore-stop 2,
allow-reset 3, count-unexec 2, no-level-reset 4).

## Oracle (0 GPU) — how often it would have fired
Replaying the stall rule over the transcripts' `step_executed:` sequence (level from the events):

| run | would-fire, 25 games | smoke subset bp35 / sp80 / tn36 |
|---|---|---|
| anim-full25-r2 | 126 (5 per game; max r11l 11, tn36 10) | 7 / 8 / 10 |
| animfast-b71 | 204 (8 per game; max g50t 16, bp35 15) | 15 / 15 / 3 |

So the floor adds ~5–8 actions per game per 2.2 h — a nudge on the ~100-action games, not a flood — and in a 1,800 s smoke about a
quarter of that (2–3 per game), which is why rule 1 asks for ≥ 3 executed fires in total, not per game. What it buys is not the
actions themselves but the frames they produce for a model that is stuck reading the same board.

## Stated costs / unknowns
- Each floor action is charged by RHAE if the level is later cleared (cap bounds it). On never-cleared levels it is free.
- The model sees the floor's action in its history as an action it "took". v0 accepts this; if a smoke shows confusion in the
  transcript ("I did not do that"), v1 labels the history entry.
- Whether a rare-colour click is a useful probe is game-dependent; on tn36 (mark-states on a grid) any click is information.

## Pre-registered read (in the builder docstring)
Smoke v0 vs ctl: (1) `THUI_AF_GRAFT ok` and ≥ 3 `THUI_AF_FLOOR executed=True` total, else VOID; (2) levels ≥ control on all three,
read against both db controls' spread before calling FAIL; (3) descriptive: actions/game and no-action-turn fraction. PASS buys a
full-25 pair on the anim base. Not pushed; 0 GPU spent.
