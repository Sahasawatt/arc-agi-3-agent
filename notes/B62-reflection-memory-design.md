# B62 — reflection memory every K steps, written into duck's own world-model slot

**Design ticket, 2026-09-03.** Lever 7 of `arc-agi-pub/notes/deep-research-arc3-sota-now-2026-09-03.md`:
Reki (#2, Milestone 1) and forge (#3) — both Gemma-4-31B run locally — refresh a *reflection memory*
roughly every 10 steps beside JSON self-repair and legal-action guards. Nobody has tested that inside the
duck harness. The deep-research verdict for our board position: nine of the top ten teams disclose
nothing, Tufa's disclosure is the harness we run, and our bundle already matches their four disclosed
constants — so the levers left are throughput (prefix caching) and this one.
Status: design → smoke (3 games) → decide.

Proposed MAP row:

> | B62 | build | **Reflection memory: one extra tool-free chat call every 10 executed steps (and after a level completes) rewrites the seven world-model fields duck already injects into every prompt.** Fills the slot the model leaves empty on 36–40 % of turns and repairs the level-transition wipe from evidence. Never issues an action, never edits history. Oracle unchanged: paired levels vs the same-seed base pair. | open |

## What duck already has, measured

`ToolAgent._summarized_knowledge` (`duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py`) holds
seven fields — `world_model / goal_model / action_model / recent_findings / open_questions / current_plan /
cross_level_notes`. They are filled only when the model **volunteers** labelled prefixes in its assistant
text (`_update_summarized_knowledge_from_assistant`, `:1896` / `:1930`), injected into every user prompt
as *"Working world model carried from earlier turns:"* (`_summarized_knowledge_lines`, `:1128`), and
**wiped** inside the turn that completes a level (`_update_summarized_knowledge_from_step_summary`, `:1584`;
`cross_level_notes` survives).

Census over the three full-run sidecar sets already on disk (thui-prior-v1, thui-v3-1, thui-v6-0;
`analysis` events with `action_num > 1`, i.e. turns where a carried model is possible):

| run | turns | carried world model present | absent |
|---|---|---|---|
| thui-prior-v1 | 996 | 639 (64 %) | 36 % |
| thui-v3-1 | 741 | 452 (61 %) | 39 % |
| thui-v6-0 | 735 | 443 (60 %) | 40 % |

So on roughly **two turns in five the agent starts with no memory at all** — after every level transition,
and whenever the model skipped the prefixes. That is the gap B62 fills; it is not a new prompt surface.

## Seam

Class-level wrap of `ToolAgent.analyze` (cell 12, same pattern as B60/B61). **After** the upstream turn
returns: read `self._last_step_summary` (`executed_count`, `level_transition`, `run_complete`,
`game_over`); accumulate executed actions since the last reflection; when the count reaches K=10, or the
turn completed a level, run ONE `self._chat_completion(messages, tools=None, request_timeout_seconds=90)`
with a fixed reflection system prompt and a user message = current `_summarized_knowledge_lines()` + the
last 12 history messages rendered as text (`_normalize_message_content`; tool outputs capped at 700
chars, others at 1,500). Parse the reply with the harness's own `_extract_scientist_note`; write every
non-empty field back into `self._summarized_knowledge`. `_max_output_tokens` is temporarily set to 700
for that call and restored in `finally`. The reflection lands after the `:1584` wipe, so a
level-completion reflection is the repair, not a victim, of the wipe. Skipped when `should_stop()` is
true. Every failure is caught and logged; the harness path is never broken.

Cost model: ~1 extra call per 10 executed actions ≈ +8–12 % of chat calls, each ≤ 700 output tokens and
≤ 90 s. Logged per call: `thui-reflect: game=<id> reason=k|level fields=[…] latency=… tokens=…`.

## Smoke oracle (thui-reflect-v0: tr87 / sk48 / sc25, 900 s each)

- **P1** ≥ 1 reflection call with ≥ 1 parsed field in ≥ 2 of 3 games (`fields=[…]` non-empty).
- **P2** the turn after a reflection carries the fields: `thui-reflect: P2 injected lines=N` with N > 0 on
  every check (the wrapper checks `_summarized_knowledge_lines()` at the start of the next turn).
- **P3** run COMPLETE, 3 games, `wrapper_errors = 0`, `errors = 0`.
- Report: calls / ok / empty / mean latency / tokens per call. Kill the design on sight if mean latency
  > 30 s (it would eat the 180 s yield) or if `empty` ≥ half of calls (the model does not follow the
  seven-line format at temperature 0.6).

## Full-run oracle (thui-reflect-v1)

Paired **levels** vs the same-seed base pair (`thui-v1-1` 28 levels / `thui-v1-1-r2`), ≥ 2 runs per arm,
`eval/pool_runs.py` → `eval/rank_runs.py`. Secondary: turns per game and mean actions per cleared level
(B55: cheaper early levels predict depth). Kill: Δ < +1 level in ≥ 6 games (B35 floor) on both draws.

## Not in scope, deliberately

- Changing the seven labels or the prompt text the model reads — that would confound with the memory itself.
- Reflection *before* the wipe to preserve `action_model` across levels — a second arm if v1 reads positive.
- JSON self-repair / legal-action guards (Reki/forge's other two grafts) — separate arms, separate tickets.

## Status

- 2026-09-03: builder `thui-reflect/build_notebook.py` written; `taaf-thui-reflect-v0.ipynb` built (cells
  0/12/14, `ast.parse` on 12 and 14). Push from `sahasawatt` blocked by the weekly GPU quota at the time
  of writing — see the push record below.

### Push record

- 2026-09-03 16:20Z `scripts/kaggle_push_kernel.py repos/arc-agi-3-agent/thui-reflect` → the gate's
  `AssertionError: … (no url in its output)`; raw `kaggle kernels push -p thui-reflect` says
  `Kernel push error: Maximum weekly GPU quota of 30.00 hours reached.` Same blocker as B61. Unblock:
  weekly reset on `sahasawatt`, or `python3 thui-reflect/build_notebook.py --owner=yocybercode` +
  the gate script from the mac.

## Rebased 2026-09-04 onto the B48 chassis

Builder default is now `--base=v3` = `thuiv3/taaf-thui-v3-0.ipynb` (thui-v1-1 + yield 180: the build that drew the standing best 2.03 and holds the campaign's only 4-run public pool). The cell-12/14 seams are identical in that chassis (anchors asserted once; cell 8 asserted to carry the yield-180 injection twice). **Baseline for the paired read is the `thuiv3` arm** declared in `eval/fixtures/arms.json` (thuiv3-0 4.01 / thuiv3-0-r2 4.52 / thuiv3-1 5.17 / thuiv3-2 3.85; the three new fixtures banked from each run's `benchmark.json`, means reproducing the LEDGER), pooled as `eval/fixtures/thuiv3-pool.json`. Read: `python3 eval/rank_runs.py eval/fixtures/thuiv3-pool.json <candidate-pool>.json`, +1 level in >= 6 of 25 games on both candidate draws. `--base=v1` keeps the thui-v1-1 chassis for a control build only.
