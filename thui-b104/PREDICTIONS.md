# thui-b104 ContactSheet — pre-registered 2026-09-27, before any GPU run

Base: `thui-a5-mtp0k7s28-full25-r1` (B81), full clock (7,920 s), all 25 public games. Treatment: one cell-9 graft
only. The anim bundle already captures every frame of an animated action (solver `animation_history`, depth 4,
`framework/solver.py:222`, appended at `:860`) and serves it through `step_env({"query": "animation"})`; the model
sees it only as a per-action text summary in `last_action_result['animation']` and, if it writes python, through
`animation()`, a text diff timeline (`utils/animation.py`). It never sees the frames as an IMAGE. The arm wraps
`ToolAgent._build_user_message` (`tool_agent.py:1377`): when the action just before this `analyze()` call animated
(the newest record's `action_num == current_frame.step`, >= 2 frames), its frames are rendered as ONE contact sheet —
<= 8 panels (first and last always kept, the rest evenly spaced), 2× NEAREST upscale, 4 columns, each panel labelled
`k/N` with `final` on the last — and attached before the stock current-grid image, which stays last and unchanged. A
second wrapper on `_trim_messages_for_context` strips the sheet (marker text + its image) from every user message but
the newest one, so at most one sheet is ever sent. The control carries the SAME wrappers with the flag off: it computes
the same eligibility, counts it, and attaches nothing. Changed cells must be exactly `[0, 9]` on both.

This is B71's animation channel moved from TEXT to IMAGE, one change: B71 (anim bundle, text + tool) closed ND on
hidden (3.35 n=3 vs June 3.19 n=6, permutation p = 0.536). Source of the idea: agentfix F19 in the public notebook
`scottlegrand/taaf-flashnext-sheetu12b-0922`, whose author writes that exposing frames moved hidden 3.20 → 3.71 and a
text narration of the same frames did not (2.57). **Those are single author-reported draws, unverified here, and read
as motivation only.** Tufa's own write-up (kaggle discussion 717133) reports the opposite for small models — more
frames or video in context did not help. The two claims conflict; this run is one reading of which holds on our
chassis. Code is our own; the idea, not the implementation, is borrowed.

0-GPU evidence already in hand: `test_b104_graft.py` against the real anim-bundle `ToolAgent` and `vision_context`
(Pillow 12.3.0 locally) — 23 checks green. Measured on a synthetic 64×64 frame set: an 8-panel sheet is 522×284 px,
4,690 base64 chars, **1,567 estimator tokens** against 363 for the stock board, so an attached sheet costs about
4.3× a board in the trim budget (the estimator over-charges images; the real vision-token cost is lower and is not
measured here). Teeth: seven graft mutations (no attach · stale record accepted · board not last · no strip · newest
sheet stripped too · pick drops the last frame · control attaches) each turn the suite red; graft restored
byte-identical (`cmp`) after the round.

## VALID / VOID (plumbing, per arm)

VALID only if `THUI_B104_GRAFT ok sheet=<True|False>` appears once and the last `THUI_B104_STATS` line shows
`eligible >= 50` and `query_errors == 0`. On the arm `attached == eligible` and `render_errors == 0`; on the control
`attached == 0`. Anything else is VOID and nothing below is read. STATS prints on the 1st, 51st, ... eligible build,
so totals undercount by < 50 eligible builds; ratios are what is read.

## Reach bar (read before any score)

From the control's last STATS line, `reach = eligible / builds`.
- **REACH-THIN** if `reach < 0.05` — fewer than one analyze call in twenty follows an animated action; the lever can
  touch too little of the run for a full-width score to say anything, and the score is not read as evidence.

## Outcome bar (one matched pair; power UNMEASURED)

Both arms pushed together. Per-game levels through `eval/rank_runs.py` (arm vs control, `--single-baseline` with this
file named as the reason).
- **KILL:** arm total levels `<=` control total levels.
- **PROMOTE to a second pair:** arm total levels `>=` control `+ 3` (a chosen floor, not derived).
- **INCONCLUSIVE:** anything between. No hidden submission on INCONCLUSIVE.
- **PASS** only after the second pair: pooled `rank_runs.py` BETTER at p < 0.05 over both pairs.

Secondary, descriptive only: levels on the games whose animations hide information (the bundle's own "type 1" set,
`utils/animation.py` docstring: ft09, sb26), `stage2_animation_requests` from the experiment counters (does a sheet
replace the model's own `animation()` calls?), tokens per action.

## Known confounds, carried

- A sheet costs ~4.3× a board in the estimator, so the arm evicts somewhat more text history on turns that follow an
  animation. The bar measures the net of seeing frames and losing history.
- Not stacked with B103: each is one change on B81, so neither result can be read as the other's.

## Addendum 2026-09-27, before r2 — r1 VOID on an import, bar unchanged

r1 (`sahasawatt/thui-b104-sheet-full25-r1` / `-ctl-full25-r1`, pushed 09:16Z) died on BOTH arms in cell 9 at ~09:59Z,
before any game: `from PIL import ImageDraw` → `ImportError: cannot import name '_Ink' from 'PIL._typing'`. Kaggle's
Pillow is a mixed install — `PIL.Image` loads (the stock board is rendered with it), `ImageDraw` does not. The local
test ran on Pillow 12.3.0, where ImageDraw loads, so it could not see this. VOID, nothing read.

r2 changes the RENDER only, not the bar or the eligibility rule: no `ImageDraw`, so no text labels; panels stay in
time order (left to right, top to bottom) and the final panel is framed in `(0, 255, 0)`, a colour outside the ARC
palette; the marker text says so. The test now makes `PIL.ImageDraw` unimportable (`sys.modules[...] = None`) and a
mutation restoring the r1 import crashes the suite the way Kaggle crashed; 25 checks, 9 mutations red.

Measured again on r2's render: an 8-panel sheet is 522×262 px, 1,646 base64 chars, **552 estimator tokens** vs 363
for a board (~1.5×). This **replaces** the 1,567 / ~4.3× figure above, which was the labelled r1 render (text
anti-aliasing inflated the PNG); the confound it describes is correspondingly smaller. Slugs are `-r2`.
