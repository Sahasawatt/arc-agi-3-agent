# thui-b105 ActionOutcome — pre-registered 2026-09-27, before any GPU run

Base: `thui-a5-mtp0k7s28-full25-r1` (B81), full clock (7,920 s), all 25 public games. Treatment: one cell-9 graft
only. `ToolAgent._run_python_tool` (anim bundle `tool_agent.py:1693`) builds the tool response as: `stdout` if the
snippet printed anything, else the snippet's `result`, else — only then — the executed actions' result
(`:1949–1962`, an `if / elif / elif` chain). So a snippet that executes actions AND prints gets back its own printout
and nothing from the harness about what the actions did. The harness does summarise every acting call
(`_summarize_step_sequence`, `:1250`), and the next user prompt reports executed actions, level transition and game
over from that summary (`_build_user_prompt`, `:1391`) — but not `board_changed` or `stop_reason`, and not until the
next `analyze()` call, whereas the model keeps acting inside the current one. `_describe_last_outcome` (`:1300`) is
defined and never called.

The arm: every python tool response whose snippet executed >= 1 action and carries no `result` gains an
`action_outcome` field — the step summary's `start_action_num`, `end_action_num`, `executed_count`, `level`,
`level_transition`, `run_complete`, `game_over`, `board_changed`, `stop_reason`, `animation`. Done by wrapping
`_summarize_step_sequence` (stash the summary, thread-local, owner-checked) and `_render_tool_payload` (consume it on the
very next python render). The control carries the SAME wrappers with the flag off: it detects and counts the same case
and changes nothing. Changed cells must be exactly `[0, 9]` on both. Only the tool-response half of agentfix F2 is
carried; its second half (adding `_describe_last_outcome` to the next prompt) is not, because that prompt already
carries most of the same facts — one change.

Source of the idea: agentfix F2 in the public notebook `scottlegrand/taaf-flashnext-sheetu12b-0922`, whose author
reports that 81% of acting calls returned no action result. **Unverified here** — the control's `missing / acting`
measures it on our chassis.

0-GPU evidence already in hand: `test_b105_graft.py` — a source-level check that the defect exists at this bundle and
that `_run_python_tool` calls summarize then render once each, plus the wrapped methods run on the real `ToolAgent`:
12 checks green. Running `_run_python_tool` itself needs the sandbox subprocess and is NOT exercised; the replay calls
the two real methods in the source's order. Teeth: six graft mutations (never add · add over an existing result · no
owner check · pending not cleared · control adds · render unwired) each turn the suite red; graft restored
byte-identical (`cmp`) after the round.

## VALID / VOID (plumbing, per arm)

VALID only if `THUI_B105_GRAFT ok outcome=<True|False>` appears once and the last `THUI_B105_STATS` line shows
`acting >= 100`. On the arm `added == missing`; on the control `added == 0`. Anything else is VOID. STATS prints on the
1st, 101st, ... acting call, so totals undercount by < 100; ratios are what is read.

## Reach bar (read before any score)

From the control's last STATS line, `reach = missing / acting`.
- **MECHANISM-DEAD** if `reach < 0.20` — on our chassis the model rarely prints while acting, the defect rarely bites,
  and the score is not read as evidence about this lever.

## Outcome bar (one matched pair; power UNMEASURED)

Per-game levels through `eval/rank_runs.py` (arm vs control, `--single-baseline` with this file named as the reason).
- **KILL:** arm total levels `<=` control total levels.
- **PROMOTE to a second pair:** arm total levels `>=` control `+ 3` (a chosen floor, not derived).
- **INCONCLUSIVE:** anything between. No hidden submission on INCONCLUSIVE.
- **PASS** only after the second pair: pooled `rank_runs.py` BETTER at p < 0.05 over both pairs.

Secondary, descriptive only: actions per level, tokens per action, and — from transcripts — whether python calls
following an outcome with `board_changed: false` switch action more often than in the control.

## Known confounds, carried

- The field adds ~60–150 characters to each affected tool response, slightly raising trim pressure.
- It can also be redundant where the model's own printout already reported the outcome; the bar measures the net.
- Not stacked with B103 or B104: each is one change on B81.
