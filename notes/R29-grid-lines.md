# R29 — the feature its own author never ran: grid lines

2026-08-24. think-research pass over "what lever is still unclosed after B26-B29", toolbox =
local corpus (bundle sources in scratchpad `bundlecmp/`, events on disk). Web deliberately
not used — the deciding evidence is all on this machine.

## The finding

The newer TAAF bundle (`bundlecmp/new`, post-anim upstream) ships a grid-line renderer for
the board PNG — `_render_grid_lined_image` in `inference/agent/vision_context.py`: canvas
filled with `GRID_LINE_COLOR = (128,128,128)`, each cell painted `(scale-1)`px shy, so a
1px gray lattice separates every cell. Gate: `MULTIMODAL_GRID_LINES == "1"`,
`GRID_LINE_MIN_CELL_PX = 4`.

**Their own `setup_commands.json` sets `'MULTIMODAL_GRID_LINES': 'true'` — and the reader
tests `== "1"`. The feature has never run, anywhere, including for its author.** (R26 spotted
this in passing; now verified against source.) Our anim bundle predates the feature entirely:
no `GRID_LINE` token in any of its 28 inference files.

## Why this targets R28's failure mode

R28's wrong-goal audit: 4/5 stuck levels hold a wrong goal, and at least three of the five
cases pivot on a SPATIAL misread feeding the goal:

- cd82 (v18): "the 90° stamps never overlap the canvas" — a coordinate-arithmetic claim,
  false, promoted to "the goal is definitively NOT canvas==panel".
- lp85 (v19): modeled one global ring where the board has per-row rotations — a structure
  misread.
- re86 (v10cal): 38 turns of segmentation inventories that never stabilized into shapes.

A cell lattice on the PNG is coordinate scaffolding at the perception layer — the layer the
errors originate in. It is NOT prompt pressure (the dead lane): nothing tells the model to
behave differently; the input becomes less ambiguous.

## Attribution design (v23)

v23 = v10 + upscale 8 + grid lines armed. Two changes vs v10, but **v18 already measured
upscale 8 alone: 3.60, p=0.508, NOT-DISTINGUISHABLE** — so v18 is the no-lines control arm
and any out-of-band result attributes to the lines. 8 also matches the author's intended
pairing (their setup: UPSCALE '8' + GRID_LINES on) and gives 7×7px cells + 1px line vs the
cramped 3×3+1 at scale 4.

Patch seam (verified in anim source): `tool_agent` imports `current_grid_image_part` only,
and that function calls `frame_to_png_data_url(frame)` by bare name in-module — so patching
`vision_context.frame_to_png_data_url` (module attribute) lands on every render, and the
v21/v22 import-by-name trap does not apply. Teeth must still assert
`not hasattr(tool_agent, "frame_to_png_data_url")` in-kernel to keep that true.

## The other two levers surfaced, and why they rank below

- **Harness-side auto-probe battery at level entry** (execute K actions blind, feed diffs to
  the model): rejected. Probes MUTATE state irreversibly (cd82's stamps paint the canvas;
  RESET refunds nothing — measured, v17 tally), so a blind battery can corrupt the board the
  model then learns from; and structure on the action path is the v9 shape (0.22). The
  harness has no existing probe machinery to extend (the `experiment` event is
  animation-awareness counters only — checked).
- **Untried-ledger nudge** ("you have never clicked any square", derived from history):
  targets ft09's exact failure, uses the proven nudge channel (sk48 obeyed 7/7 animation
  nudges) — but its nearest measured precedent is v16's state-derived info push (3.51,
  in-band-worse), and B28 just showed induced behaviour does not convert to score. Filed as
  a ticket (B32), not built.

## UNVERIFIED

- Whether Qwen3.8's vision reads the lattice at all. v18 says more pixels alone did nothing;
  lines are structure, not pixels — that is the hypothesis v23 exists to test, not a claim.
- Legibility at scale 4 (3×3px cells) untested; v23 does not test it either (runs at 8).
- The three "spatial misread" attributions in R28 are one reader's judgment (n=3 of 5).
