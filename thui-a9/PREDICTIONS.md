# thui-a9 G1 smoke — pre-registered 2026-09-19, before push

Design: workspace `notes/DESIGN-textual-world-model-experiment-2026-09-19.md` (main `81c15be`). Arm A1′(a),
option 1 of §5a, chosen by the owner 2026-09-19 ("go 1").

**The change vs B81 (`thui-a5-mtp0k7s28-full25-r1`): one.** A cell-9 wrapper on the imported
`ToolAgent._build_user_prompt` swaps one element of the per-turn prompt:
- **Before:** *"If you include assistant text … Helpful optional prefixes are `World model:` …"*
- **After:** a `World model:` first line is **required every turn**. The other six prefixes stay optional.

The retry prompt inside `analyze()` (`tool_agent.py:2302` @ `01e36e6`) is not touched.

**Arms, pushed together on the same serving profile:**
- `thui-a9-wmreq-smoke`: the treatment.
- `thui-a9-ctl-smoke`: byte-identical except cell 9 prints a marker and installs no wrapper.

Both run games tn36 / vc33 / bp35 at 1,800 s. At batch cap 2, the two occupy both sessions.

## Offline teeth (2026-09-19, before push)
- The old element is present verbatim in B81's own transcripts: **1,087 of 1,087** user prompts, 25/25 games.
  The control phrase counts 1,087 too.
- `test_a9_graft.py` runs the GRAFT exactly as it sits in the built notebook, against stubs. It passes all
  4 poles:
  - **positive:** the element is swapped, applied=1.
  - **miss:** the text is unchanged, miss=1, and `THUI_A9_MISS` prints.
  - **moved:** the cell-9 source assert fires before any wrapper is installed.
  - **control:** the marker is present and no wrapper is installed.
- The builder asserts the cells changed are exactly [0, 9, 15] and that the id is `yocybercode/…`.

## VALID (any failure = VOID, nothing read)
- **V1:** the treatment log has `THUI_A9_GRAFT ok` and `THUI_A9_APPLIED first`, and 0 `THUI_A9_MISS`. The
  control log has `THUI_A9_GRAFT control`.
- **V2:** in the treatment transcripts, the count of user prompts carrying the new element equals the count
  carrying the control phrase *"When ready, call `action(actions)` from inside the `python` tool"*. The old
  element count is 0. In the control transcripts, the new element count is 0.
- **V3:** both kernels are COMPLETE with 3 games in `benchmark.json`, and no engine death.

## KILL (any one on the treatment = stop; base stays)
Thresholds are the owner-adopted ones from the design, §7 G1.
- **K1, cost:** for any smoke game, treatment total actions ÷ control total actions **< 0.50**. That is
  B82's floor, on the same clock.
- **K2, compliance:** fewer than **90%** of treatment responses carry a parsed `World model:` value in their
  VISIBLE content. The parse uses the chassis extractor on `content` stripped at `\n[TOOL CALL`, the same
  method as `a1_step0_v2.py`.
- **K3, length:** the median treatment `World model` value is **> 488 chars**, 2× B81's voluntary 244, which
  breaks P2's cost model.

## MECHANISM (reported, not gates)
- The `World model` write count per arm; the control is expected near B81's rate of about 12% of responses.
- Median `reasoning_chars` and `content_chars` per response, treatment vs control. This is the "does a
  required line lengthen thinking" question the design says only a smoke can see.
- Responses with no tool call (retry path), per arm.
- Levels per game, per arm. At n=1 on 3 games this is **not a result**, and no level read is taken from G1.

## If G1 passes
G2 per §5a option 1:
- `thui-a9-ctl-full25-rN` (A0) and `thui-a9-wmreq-full25-rN` (A1′) run as same-day interleaved pairs, up to
  k = 8 each.
- The placebo A2 is built and run only after A1′ beats A0.
- A futility look happens at k = 4.
- The G2 predictions get their own pre-registration before the first full-25 push.
