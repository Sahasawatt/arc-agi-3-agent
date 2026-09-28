# thui-b106 CognitiveMap — pre-registered 2026-09-28, before any GPU run

Two bases, one change each, full clock (7,920 s), all 25 public games:

| pair | base | arm | control |
|---|---|---|---|
| B81 | `thui-a5-mtp0k7s28-full25-r1` | `thui-b106-map-b81-full25-r1` | `thui-b106-ctl-b81-full25-r1` |
| B99 | `thui-b99-rungpin-full25-r1` (B81 + RungPin) | `thui-b106-map-b99-full25-r1` | `thui-b106-ctl-b99-full25-r1` |

The B99 pair was asked for by the operator (2026-09-28) alongside the B81 pair. B99's own lever (RungPin) was closed
below its gate (8 up / 4 down / 13 tied, `MAP.md` B99), so that pair measures the map *on top of* an unproven lever; only
the B81 pair isolates the map. The two pairs are read separately and never pooled.

Treatment: one cell-9 graft. The host keeps the per-level state graph (node = board signature, edge = action) by
wrapping the anim harness's no-op guard (`ToolAgent._noop_guard`, `inference/agent/noop_guard.py`), so it inherits the
guard's animation correction (an action that returned several frames is not inert even when the final board is
identical). Every user prompt (`ToolAgent._build_user_prompt`) gains a compact note: states visited and revisits,
actions already tried from the current state and whether they did anything, the untried frontier, actions that never
did anything on this level, clicks that did something, and animation-only effects. The control carries the SAME
recorder and computes the SAME note, counts it, and does not show it.

Source: cell 14 of the public notebook `juliancamilovilla/arc-agi3-animfast-map` (Apache-2.0), itself a fork of our
public `thui-animfast-v1`. Ported with the graph logic unchanged. Two deviations, both deliberate:
1. **Prompt-facing strings translated from Spanish to English**, same lines and order; our prompts are English.
2. **Install failure is loud**: the original prints a warning and runs stock, which reads as a valid run of the arm.
   Here the missing `THUI_B106_GRAFT ok` line makes the run VOID.

Neither the original's score nor any evaluation of it is known; its notebook claims none.

## VALID / VOID (plumbing, per notebook)

VALID only if `THUI_B106_GRAFT ok map=<True|False>` appears once, no `THUI_B106_GRAFT FAIL`, and the last
`THUI_B106_STATS` line shows `prompts >= 100` and `errors == 0`. Anything else is VOID. STATS prints on the 1st, 101st,
... prompt call, so totals undercount by < 100; ratios are what is read.

## Reach bar (read before any score)

From each control's last STATS line, `reach = notes / prompts`.
- **MECHANISM-DEAD** if `reach < 0.30` on the B81 control — the graph rarely has anything to say on our chassis, and
  neither pair's score is read as evidence about this lever.
- Descriptive: mean note length `chars / notes` (trim pressure).

## Outcome bar (one matched pair per base; power UNMEASURED)

Per-game levels through `eval/rank_runs.py` (arm vs its own control, `--single-baseline` with this file named as the
reason). Per pair:
- **KILL:** arm total levels `<=` control total levels.
- **PROMOTE to a second pair:** arm total levels `>=` control `+ 3` (a chosen floor, not derived).
- **INCONCLUSIVE:** anything between. No hidden submission on INCONCLUSIVE.
- **PASS** only after the second pair: pooled `rank_runs.py` BETTER at p < 0.05 over both pairs.

If the B81 pair is KILL and the B99 pair PROMOTE, that is read as an interaction to test, not as a map win.

## Known confounds, carried

- The note adds up to ~8 lines per prompt, raising trim pressure; the bar measures the net.
- Board signatures come from the harness's `board_signature`; two visually different states with one signature merge.
- Not stacked with B103, B104 or B105.
