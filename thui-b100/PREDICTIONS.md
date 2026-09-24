# thui-b100 (MAP B100 OutcomeSieve) smoke pair — pre-registered 2026-09-22 before any push

Agreed with Watchara over relay (01M33Q6PPJMJ0KQ7EGY00M43E3 → 01M33QV195GS47NWYFBZKSW2YY → his 2026-09-22T05:02:23Z answer):
build B100 with the REVISED keep rule and re-register the prompt-token kill before push. All times UTC.

## Change vs B81 (`thui-a5-mtp0k7s28-full25-r1`)
One graft at the end of cell 9 (`graft_src.py`; the builder asserts cell 9 ends with exactly these bytes, which the test
executes). Wraps `ToolAgent._chat_completion` (the B92 seam) and sends a COPY of the messages in which the stored
`reasoning` key is removed only from assistant messages of levels the agent has already LEFT, except the level-clearing
message (the last assistant message before a "Current state: step S, level L" marker with a higher level). Every
assistant message of the CURRENT level keeps its reasoning; messages whose level is unknown keep it. Content, tool calls,
tool results, message order and the harness's own list are untouched. Serving profile untouched. Cells [0, 9, 15].
Control = the same notebook with the wrapper in logging-only mode (`--control`, `_THUI_B100_STRIP = False`), so both
arms report prompt tokens on the same instrument.
Arms: `sahasawatt/thui-b100-v0-smoke25` + `sahasawatt/thui-b100-ctl-smoke25`, 25 public games @ 1,800 s, ~0.6 GPU-h each.

## Checks passed, 0 GPU
- `test_b100_graft.py` against the real `_chat_completion` (only HTTP faked): 12/12 — Watchara's teeth (old failure
  stripped, old clear kept, all current-level kept), caller's list/dicts unchanged, content/tool calls byte-identical,
  level 1 strips nothing, unknown level kept, control sends everything but still counts eligibility.
- `--mutants`: 7 red (strip all = B92 shape, strip current level too, in-place edit, clearing mis-associated to the
  segment's first assistant, clearing not protected, wrong marker regex, wrapper not installed).
- `b100_read.py --selftest` 9/9.

## Expected size (0 GPU, `estimate_share.py`, 15,537 post-clear turns over 497 banked game-runs)
Share of history REASONING the rule strips on requests made after the first level clear, by history window W:
W=8 0.154 · W=12 0.221 · W=20 0.315 · W=30 0.392 (the real window is set by the 32k estimate and lies between).
Reasoning is ~54 % of prompt text (decode-bottleneck lane D) → expected post-clear prompt-token drop ≈ 8-21 %,
point guess ~10 %. The whole-run drop is smaller because level 1 strips nothing — hence Watchara's option (a).

## VALID (else VOID)
Both logs: `THUI_B100_GRAFT ok strip=True|False` (matching the arm), `THUI_B100_SMOKE arm=`, ≥ 1 `THUI_B100_STATS`
line (last one read; printed every 50 requests, so a lower bound), 25 games, 25 transcripts. Arm stripped > 0 messages
(B100 validity: wrapper fired). Post-clear requests > 0 in both arms.

**Added 2026-09-24, before the smoke was pushed: `void=0` on the last `THUI_B100_STATS` line of BOTH arms,
and no `THUI_B100_VOID` line anywhere in either log.** `void` counts requests where the payload the wrapper
actually built disagrees with the keep rule: `sent_clear_chars != clear_chars`, i.e. a clearing message the rule
promises to KEEP came back with fewer reasoning chars than it went in with. This reads the SENT list, not the
level decision, which is why it can fail while the code runs. Teeth, proven on the existing mutant suite before
this was registered: the `clearing message not protected` mutant gives `clear_chars=200 sent_clear_chars=0 void=1`,
while the unmutated graft gives `void=0` and the 12 baseline checks stay green. The six other mutants do NOT trip
it and are not claimed to; they stay covered by those 12 checks. `sent_left_chars` and `sent_cur_chars` are also
emitted but are TELEMETRY, not gates: they are derived from the same `levels[i] != current` test as the decision
they would be checking, so they cannot fail while the decision is self-consistent. They exist because nothing in
a live run otherwise records what the wrapper sent -- `prompts/*.log` is written before `_chat_completion`.

## KILL rule at smoke (`b100_read.py`, all must hold to PASS to the full pair)
- **PRIMARY (mechanism), within arm, exact: stripped chars / (stripped + sent) history reasoning on post-clear
  requests ≥ 0.05** (revised from 0.10; predicted ~0.10-0.15). Made primary at Watchara's request (05:44Z).
- DESCRIPTIVE, not a gate: post-clear prompt tokens per request vs control, reference 2 % below (predicted 3-8 %,
  point ~5 %). Measured noise: whole-run prompt tokens/request across six same-family smokes that strip nothing
  (b12x-ctl 17,344 · thui-to 17,475 · thui-ap 17,481 · kv10 17,963 · kv12 18,201 · pc 17,664; vllm-metrics-final)
  sd ≈ 1.9 %, largest pairwise gap 4.9 %; the post-clear subset is noisier still. A pass on tokens alone is not
  evidence; a small miss is not a kill if the primary gate and actions/min pass. Sanity anchor: thui-p3, which
  strips ALL reasoning, reads 11,280 (−35 %).
- actions per minute ≥ 95 % of control (Watchara's gate). Same-family noise: 0.90 vs 0.87 (−3 %) between two smokes.
- L2+ clears not down (Watchara's gate, literal). Noise caveat: the control smoke has only 4 L2+ clears, so this gate
  alone can kill on one draw.
- Our guard: final-level redefinitions per python call ≤ 1.5 × control. Set at 1.5, not 1.1, because two same-family
  smokes differ 1.25× on noise (b12x-ctl 0.241 vs thui-to 0.301).
Full pair (later, not this read): PASS only if ≥ 12/25 games gain a level and ≤ 6 lose one (Watchara's gate).

## Prediction (confidence L)
Mechanism fires (share 0.10-0.15); post-clear prompt drop 3-8 %; actions/min +0-5 %; levels flat within noise. The
smoke gate most likely to decide it is the literal L2+ gate (n ≈ 4), not the mechanism.
With an expected ~5 % token drop, B100's case is CONTEXT QUALITY, not throughput: the full-pair level gate (≥ 12/25
up, ≤ 6 down) is what decides it. (This smoke runs all 25 public games at 1,800 s, not 3.)

## REVISION 2026-09-22, before any push — size re-checked on REAL request payloads (`snapshot_share.py`)
518 last-request snapshots (`kout-*/prompts/*.log`): real history window median 8 assistant turns (p10 5, p90 12), so
estimate_share.py's W = 20/30 rows do not apply; reasoning is 27 % of real input chars (not the 54 % assumed). At W = 8
the rule strips 15.4 % of post-clear history reasoning; scaled by B92's measured −35 % prompt tokens for stripping ALL
reasoning → ≈ 5 %; by chars ≈ 4 %; end-of-game snapshots ≈ 3-4 % (mean strip share 0.106, 77/378 with anything left
to strip). The 5 % bar would kill a working mechanism about half the time, so: prompt drop ≥ 2 %, mechanism ≥ 0.05.
Every other gate unchanged. Told to Watchara by relay before push.
