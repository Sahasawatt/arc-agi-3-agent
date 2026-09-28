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

## r2 addendum — 2026-09-28 ~10:5xZ, before any r2 GPU run

**Why r2.** The r1 map arm showed a wrong frontier line in every note. `valid_actions` reaches the prompt with
ENGINE names (`ACTION1`..`ACTION6`, `RESET`) while the recorder stores MODEL names (`UP`, `DOWN`, ..), so the r1
frontier never matched and the note told the model to try actions it had just tried (all 25 r1 map transcripts: every
"NOT tried" line names `ACTIONn`). The r1 test fed model names only, so it passed with the bug. Upstream
(`juliancamilovilla/arc-agi3-animfast-map` cell 14, 05:36Z revision) fixed the same bug the same way. The r1 KILL
(42 -> 39) therefore reads "a map with a wrong frontier line did not help", not "the map does not help".

**Change r1 -> r2 (graft only):** `valid_actions` translated to model names before the frontier comparison
(copy of the bundle's `ENGINE_TO_MODEL_ACTION`); `RESET` excluded from the frontier alongside `MOUSE`. Every other
note line is unchanged. The control is affected only in what it computes and never shows.
Test: two new checks feed engine names; both FAIL on the r1 graft and pass on r2.

**Runs:** `thui-b106-{map,ctl}-b81-full25-r2` on yocybercode; `thui-b106-{map,ctl}-b99-full25-r2` asked of sahasawat
(rebuild with `--owner=`). Each pair stays on one account.

**Bars:** unchanged from above — VALID/VOID, reach (B81 control), and per-pair KILL / PROMOTE at +3 / INCONCLUSIVE,
pairs never pooled, r1 and r2 never pooled. Added VOID: any r2 map-arm note whose "NOT tried" line contains `ACTION`
or `RESET` (read from the run's transcripts).

## r2 amendment — 2026-09-28 ~13:5xZ, AFTER the B81 r2 read, BEFORE the B99 r2 read

**Written after the B81 r2 outcome was seen.** It is a post-hoc ruling, stated as one, and the B81 r2 verdict below
carries that label.

**What triggered it.** The B81 r2 map arm hit the added VOID rule: 274 of 842 "NOT tried" lines contain `ACTION`.
Every hit is `ACTION7`, and there is no `ACTION1`..`ACTION6` or `RESET` hit, so the r2 frontier fix works. The hits
fall in the six games that offer `ACTION7` (ar25, sb26, bp35, sk48, su15, lf52). In all 274 of them, the
`Valid actions right now:` line that precedes the note in the same transcript lists `ACTION7`. The base maps only
`ACTION1`..`ACTION6` and `RESET` (`action_names.py`, see B73/B76), so `ACTION7` is the name the model is actually shown,
in both arms. A frontier line that names it names an action the model was offered. That is not the r1 bug, where
the model was told to try engine names that did not match the names it was using.

**Amended VOID (operator ruling, Watchara, 2026-09-28).** VOID if any r2 map-arm "NOT tried" line contains
`ACTION1`..`ACTION6` or `RESET`. It is also VOID if the line contains `ACTION7` and the preceding
`Valid actions right now:` line in the same transcript does not list `ACTION7`. Applies unchanged to the B99 r2 pair,
which has not been read at the time of writing. Every other bar is unchanged.

**B81 r2 read under the amended rule.** VALID: `THUI_B106_GRAFT ok` once per notebook, 0 FAIL, last STATS map
`prompts=1101 notes=1000 errors=0`, ctl `prompts=1101 notes=990 errors=0`. Reach 990/1101 = 0.90. Levels
arm 44 vs ctl 40 (+4), 10 up / 8 down, score mean 10.33 vs 10.49, `rank_runs.py --single-baseline` p = 0.9629
(NOT-DISTINGUISHABLE). Verdict: **PROMOTE to a second pair** (+4 >= +3), under this post-hoc ruling. Under the rule as
first written it is VOID. Not pre-registered, and not evidence: the 19 non-`ACTION7` games give +5 (36 vs 31) and
the six `ACTION7` games give -1 (8 vs 9).
