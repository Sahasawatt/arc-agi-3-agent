# v18 — the grid image was always there, at 1 token per 8x8 cells

2026-08-22. One change on top of v10: `MULTIMODAL_UPSCALE` 4 -> 8.

## What was found first, and it was not the knob

While closing the last UNPROVEN item (MoE), a **newer bundle from the same author**
turned up: `jakobbrggen/taaf-kaggle-source`, updated **2026-08-22 13:29 UTC** — two hours
before we submitted v10's second draw. Branch `feature/explore-experiment`, commit
`6d8e3dd`, **clean** (the anim bundle we run is `9158303`, DIRTY).

**14 of 75 files differ.** The agent core is all of them:

| file | diff |
|---|---|
| `framework/solver.py` | +149 −31 |
| `agent/tool_agent.py` | +89 −109 |
| `agent/vision_context.py` | +55 −9 (82 -> 128 lines) |
| `utils/animation.py` | +47 −38 |
| `agent/prompts.py`, `framework/kaggle.py`, `Makefile`, … | smaller |

Three things read straight off that diff:

1. **The harness has been sending the model a PNG of the current grid all campaign.**
   `setup_commands.json` in the anim bundle already carries
   `'MULTIMODAL_CONTEXT': 'current_grid'` and `'MULTIMODAL_UPSCALE': '4'`, and
   `tool_agent._build_user_message` (:1377) puts `current_grid_image_part(current_frame)`
   into the message `content`. Nobody on this campaign knew the vision channel was live.
2. **Upstream reports our own animation finding back at us.** In the new `solver.py`,
   `animation_retrieval` defaults to **False** with the comment *"across Experiments 3
   and 4 it bought no score, so we do not pay for it by default"* — independent
   agreement with v16's result and with `notes/v17-search-killed.md`.
3. **Everything is env-configurable now** (`ARC3_MODEL_DATASET_SOURCE`,
   `ARC3_SERVED_MODEL_NAME`, `ARC3_TOOL_CALL_PARSER`, …), so the cell-8 string-replace
   patch that killed duckv14 version 1 stops being necessary the moment we rebase.

## A near-miss worth recording

The first grep for the image path searched `frame_to_png_data_url|image_url` and found
**zero hits in the anim bundle's `tool_agent.py`** — which reads exactly like "the image
is never sent", and was about to be written down as the finding of the day. It is wrong:
the call site uses the wrapper `current_grid_image_part`, which the pattern did not
cover. Re-grepping for the wrapper found it at **anim:1378** and **new:1347** — both
bundles send the image, and the new one merely adds byte counters around it.

*An absence found by grep is a claim about the PATTERN before it is a claim about the
code* — and here the wrong reading was the more interesting one, which is what made it
attractive.

## The knob, measured before paying for it

Rendered `frames/dc22/000.png` (a real 64x64 board, native 8px cells) through the
bundle's own render path at each scale, and read the Qwen-VL patch arithmetic
(16px patch, 2x2 merge -> one token per 32x32 px):

| upscale | image | ~vision tokens | resolution the model sees |
|---|---|---|---|
| **4 (v10 today)** | 256x256 | **64** | 1 token per **8x8 cells** |
| **8 (upstream's new default)** | 512x512 | 256 | 1 per 4x4 cells |
| 16 | 1024x1024 | 1024 | 1 per 2x2 cells |

**64 tokens for 4096 cells.** Whatever the model has been doing with that image, it
cannot have been reading individual cells. Cost of the move: ~+192 tokens per user
message, ≈ **+24%** against v10cal's 2.03 Mtok — not free, and the direction v14 warned
about (more capacity spent on attempts rather than levels) applies to context too.

16 was not chosen: +1024 tok/image is ~+2.4M on the run, and it departs from the value
upstream actually ships.

## What v18 is, exactly

v10's notebook with one additional `.replace` in the cell-8 setup loop:
`'MULTIMODAL_UPSCALE': '4'` -> `'8'`. Nothing else. Not stacked with the bundle rebase —
R9 says one run barely ranks two designs.

**Grid lines were deliberately left out.** `grep -c GRID_LINE` on the anim bundle's
`vision_context.py` is **0**: the drawing code exists only in the new bundle, so setting
`MULTIMODAL_GRID_LINES` here would be an inert flag. Worth noting for whoever rebases —
upstream's own new `setup_commands.json` sets it to `'true'` while
`multimodal_grid_lines_enabled()` tests `== "1"`, so **grid lines are off in the new
bundle too, despite being switched on**. Rebasing and fixing that value gets a feature
upstream is not currently running.

## Verification done before the push

- builder `compile()`s every modified cell (the duckv14-v1 lesson)
- the **shipped** loop body was extracted from the built notebook and executed against
  the bundle's **real** `setup_commands.json`: upscale 8 present, 4 gone, vision channel
  intact, output uncapped
- teeth: deleting the upscale `.replace` from that same body raises
  `duckv18: upscale rewrite missed - THE change`

## Also closed today, for free

**MoE is not available on Kaggle.** Every Qwen3.6-35B-A3B dataset is either GGUF or an
ollama blob split (`ollama_weights.part_aa`…); there is no HF/FP8 snapshot vLLM can
load. That was the last untried item on the UNPROVEN list — **seven directions closed**.

## Smoke result (version 1, `-t 900`, 2026-08-22 20:31-20:46 UTC)

Terminal status `CANCEL_ACKNOWLEDGED` — the `-t` cap firing, not a failure. Three things
the smoke was bought to answer, all answered:

1. **The kernel starts and the notebook parses.** No repeat of duckv14 version 1.
2. **The flag reaches the kernel.** `taaf_setup_env.json` in the run output — written by
   the harness itself, not by our loop — records `"MULTIMODAL_UPSCALE": "8"` alongside
   `"MULTIMODAL_CONTEXT": "current_grid"` and `"LOCAL_ANALYZER_MAX_OUTPUT": "0"`.
3. **The image genuinely reaches the model.** vLLM's own log grew an `MM cache hit rate`
   field, `0.0% -> 3.8% -> 44.4% -> 56.9%` over the first minute. A multimodal cache
   cannot move without multimodal input, so this is independent of any reading of the
   source — and it is the control the earlier grep near-miss deserved.

vLLM booted at 20:36:09 (~4m40s), 25 games ran concurrently, and prompts/transcripts/
artifacts were produced for all 25.

**What the smoke could NOT show, and it matters:** the prompt logs record only the text
half of a multimodal message (`"Current grid image:"` appears 5x in `ar25`'s log,
`data:image` **zero** times), so the rendered size is not observable from this run's
artifacts. This bundle has no `vision_image_bytes_total` counter — that is one of the new
bundle's additions. The 512x512 figure remains arithmetic plus the local render, not a
measurement of what the kernel sent.

**An unexpected reading worth carrying into the cost estimate:** MM cache hit rate
reached 56.9% within a minute. If that holds, the board is often unchanged between
messages and the image is served from cache, so the real token cost sits **below** the
+24% computed from a per-message worst case.

⚠️ `LOCAL_ANALYZER_CONTEXT_WINDOW` is **32768** while vLLM's `max_seq_len` is 65536 — the
harness caps itself at half the engine's window. At 4x an image was ~64 tokens of that
32k; at 8x it is ~256. Whether older images stay in the conversation history (four
messages back = 1k tokens instead of 256) was not checked and is the one way this change
could cost depth rather than buy it.

## Full run

Version 2 pushed 2026-08-22 (no `-t`), full clock, same build. B23 stays open until its
number lands.
