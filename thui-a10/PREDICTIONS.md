# thui-a10 G1 smoke — pre-registered 2026-09-19, before push

Design: workspace `notes/DESIGN-textual-world-model-experiment-2026-09-19.md`, arm **A1′(b)**. A1′(a) (thui-a9,
`World model:` line required) was KILLED at G1 twice (see `thui-a9/PREDICTIONS.md`), which closes (a).

**The change vs B81 (`thui-a5-mtp0k7s28-full25-r1`): one.** A cell-9 wrapper on the imported module function
`_format_model_response_meta` (called by `analyze()` on every response, with keyword `reasoning=` / `content=`).
After the original returns, it parses the **reasoning** with the chassis's own `_extract_scientist_note` and
writes a world-model slot **only where the same response's visible content wrote nothing**, capped at **488
chars** with the chassis's own `_normalize_summary_text`. The visible path is untouched: visible values are not
capped, and they still land after the wrapper in the same response. So the cap binds only the new source, which
is why this counts as one change and not the "extract + cap" pair the design warned about.
The meta string the wrapper returns is byte-identical to the original's.

**Arms, pushed together on the same serving profile:**
- `thui-a10-thk-smoke`: the treatment.
- `thui-a10-ctl-smoke`: identical except cell 9 prints a marker and installs no wrapper.

Both run tn36 / vc33 / bp35 at 1,800 s, the a9 smoke set.

## Offline teeth (2026-09-19, before push)
- `test_a10_graft.py` runs the GRAFT exactly as built, against the **real** `inference.agent.tool_agent`
  (localrig copy, the module Step 0 lifted the extractor from). All poles pass:
  - **positive:** filled, capped (1,000 → 511 chars incl. suffix), visible `Plan` left alone, meta string
    identical.
  - **no-self**, **error-swallowed**, **moved** (the assert fires before any install), **control**.
- **Mutation proof:** remove the cap and the visible-wins test → 3 checks RED. Restored notebook is
  byte-identical to the rebuild.
- **Live mechanics, local 8B:** win-dev vLLM Qwen3-8B, `ls20`, 20 actions, through `gpu-guard`.
  - `THUI_A10_GRAFT ok` and `APPLIED first` printed.
  - Final counts: calls 21, no_self 0, errors 0, so the frame-`self` lookup works on a real `analyze()`.
  - Fills 0, because the 8B's thinking carries 0 label lines in 21 sections.
  - The positive path is therefore proven by the teeth only, not live. Step 0 says Flash-Next writes labels in
    thinking in 25/25 games.

## VALID (any failure = VOID, nothing read)
- **V1:** the treatment log has `THUI_A10_GRAFT ok` and `THUI_A10_APPLIED first`, and 0 `THUI_A10_NO_SELF` and 0
  `THUI_A10_ERROR`. The control log has `THUI_A10_GRAFT control`.
- **V2, the lever fires:** at least one `THUI_A10_FILLED` line in the treatment log. Zero means VOID-mechanism,
  not KILL.
- **V3:** both kernels are COMPLETE with 3 games in `benchmark.json`, and no engine death.
- **V4, the cap holds:** no world-model slot value rendered into a treatment user prompt exceeds 488 chars plus
  the `... [N chars omitted]` suffix.

## KILL (any one on the treatment = stop; base stays)
- **K1, cost:** for any smoke game, treatment total actions ÷ control total actions **< 0.50**. That is the B82
  and a9 floor.
- **K2, prompt growth:** median treatment user-prompt chars ÷ median control **> 1.25**. The slots are
  re-injected into every later prompt on a KV-bound server.

## MECHANISM (reported, not gates)
- `THUI_A10_FILLED` counts: responses filled, slots filled, and which slots.
- Median `reasoning_chars` / `content_chars` per response, per arm.
- Levels per game, per arm. At n=1 on 3 games this is **not a result**, and no level read is taken from G1.

## If G1 passes
G2 per §5a option 1:
- `thui-a10-ctl-full25-rN` (A0) and `thui-a10-thk-full25-rN` (A1′(b)) run as same-day interleaved pairs, up to
  k = 8 each.
- The placebo A2 is built and run only after A1′ beats A0.
- A futility look happens at k = 4.

## RESULT — G1 smoke, 2026-09-19 (both COMPLETE by ~16:5xZ): **PASS** on the registered gates
Read: workspace-private `a10_g1_read.py` (extractor teeth: content 145/145 + 84/84, reasoning 228/228 + 216/216).
- VALID:
  - **V1:** the treatment log has `GRAFT ok` and `APPLIED first`, with 0 NO_SELF and 0 ERROR. The control log
    has the marker and no `GRAFT ok`.
  - **V2:** the lever fired.
  - **V3:** 3+3 games.
  - **V4:** the largest rendered slot is 512 chars in the treatment, which is the 488 cap plus its suffix.
    Capped values seen: 511 and 512.
- KILL:
  - **K1:** action ratio T/C is tn36 1.38, vc33 **0.62**, bp35 2.21. All are ≥ 0.50, so ok.
  - **K2:** user-prompt median is 3,372 against 3,103, a ratio of 1.09 ≤ 1.25, so ok.
- MECHANISM (not gates):
  - **Reach is small.** Thinking fills a slot the visible text left empty in **8 of 228** treatment responses
    (3.5%). The same count taken offline on the control is 15/216. The fills went to `world_model`,
    `current_plan` and `cross_level_notes`.
  - Visible content median is T 201 vs C 0. Reasoning median is T 2,208 vs C 1,627.
  - Levels are T 1/1/3 vs C 1/1/3 (bp35/tn36/vc33). At n=1 this is not a result.
- Reading: the lever is safe and cheap, and it touches few responses. Whether a lever that touches ~4% of
  responses can move levels at a detectable size is G2's question, and the power for that is the owner's call
  before spending k full-25 pairs.
