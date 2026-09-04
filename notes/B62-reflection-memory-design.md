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

## 2026-09-04 — smoke pushed from the mac as `yocybercode/thui-reflect-v0`

Built in a detached worktree at `d3e72ba` with `python3 thui-reflect/build_notebook.py --owner=yocybercode --base=v3`; the
notebook came out **byte-identical to the tracked `taaf-thui-reflect-v0.ipynb`** (only `kernel-metadata.json`'s `id` moved),
cell 12 `ast.parse` clean. `scripts/kaggle_push_kernel.py` (G4: token identity `yocybercode` matches the
id's owner) → `Kernel version 1 successfully pushed`, status `QUEUED` — so the `sahasawatt` weekly quota was the only
blocker and the `yocybercode` account had room. **GPU quota only, no submission slot.** Smoke oracle unchanged (P1 / P2 / P3
above); the read is appended below once the run completes.

### Smoke read (`yocybercode/thui-reflect-v0`, COMPLETE 2026-09-04 ~10:24Z, wall 1,319 s)

Read twice, independently (Sahasawat via `kernels output`, Watchara via `kernels logs`); every number agrees.
Queue wait ~2h40m (pushed 07:20Z, RUNNING ~10:01Z).

- **P3 PASS** — 3 games finished (`tr87` 10 actions / `sk48` 33 / `sc25` 28 with **1 level**), `wrapper error` 0,
  `call FAILED` 0. The cadence fired **7** reflection calls (6 `reason=k`, 1 `reason=level` — exactly on
  `sc25`'s clear), latency 19.9–22.1 s, mean 20.7 s.
- **P1 FAIL BY MECHANISM** — all 7 calls returned `fields=[] content_chars=0` with ~3.5k tokens billed each.
  Cause (read from `setup_commands.json` and `tool_agent.py`): the harness runs every analyzer call with
  `LOCAL_ANALYZER_ENABLE_THINKING=true`; `_chat_completion` reads the module global at call time
  (`tool_agent.py:1533`), so the memory call inherited thinking and spent its whole 700-token cap inside
  `<think>` — latency ≈ 700 tok at ~35 tok/s confirms. **The pre-registered `empty ≥ half` kill rule fires on
  this draw, but it fires on a build defect, not on the design's ceiling — B62 is not closed on it.**
- **P2 vacuous** — `P2 injected lines=3-4` were the model's own volunteered prefixes, not the reflection's.

**Next: `thui-reflect-v0-1`** — thinking OFF for the memory call only (`_ta._LOCAL_ANALYZER_ENABLE_THINKING`
patched inside `_reflect`, restored in `finally`), cap 700 → 1200, and a fallback that parses the seven lines out
of `reasoning_content` when `content` is still empty; the log line now prints `completion=` and
`from_reasoning=`. Same smoke, same oracle. Pushed from the mac 2026-09-04 10:53Z as
`yocybercode/thui-reflect-v0-1`, QUEUED.

**Lesson for every extra LLM call inside duck:** thinking is on globally, so any capped side-call must switch it
off for that call or budget for it.

### Re-smoke read (`yocybercode/thui-reflect-v0-1`, COMPLETE 2026-09-04 ~11:38Z, wall 1,421 s) — **P1 / P2 / P3 PASS**

Queue wait ~20 min (pushed 10:53Z, RUNNING ~11:13Z). Read from `kernels logs` on the mac.

- **P1 PASS** — 5 reflection calls (all `reason=k`; no level cleared this draw), **every one returned all seven
  fields** in all three games (`sk48` ×2, `sc25` ×2, `tr87` ×1): `fields=['action_model', 'cross_level_notes',
  'current_plan', 'goal_model', 'open_questions', 'recent_findings', 'world_model']`, `content_chars` 1,123–1,787,
  `completion=` 298–441 tokens, `from_reasoning=False` every time — the fallback never had to fire, the fix was
  thinking-off alone. Against v0: 7 of 7 empty → 0 of 5 empty.
- **P2 PASS** — `P2 injected lines=9` on every post-reflection turn (v0: 3–4 lines, and those were the model's own
  prefixes). Nine = the seven fields plus the two header lines `_summarized_knowledge_lines()` emits.
- **P3 PASS** — 3 games finished (`tr87` 12 actions / `sc25` 20 / `sk48` 30, 0 levels), `wrapper error` 0,
  `call FAILED` 0. Latency **8.7–14.7 s, mean 12.1 s** (v0: 20.7 s at 700 tokens of pure thinking); kill rules
  (mean > 30 s, empty ≥ half) both clear.

**Decision (Watchara, 2026-09-04): B62 is the final build for today's draw.** `thui-reflect-v1 --full` was built
at `f590d2d` (`cells changed [0, 12]`, smoke filter absent, cell 12 parses, thinking-off + cap 1200 present) and
pushed from the mac at **12:05Z** as `yocybercode/thui-reflect-v1`, RUNNING immediately. Plan: read the public
25-game result when it lands; if the build completes without harness errors it is submitted as the 09-04 hidden
draw through `scripts/kaggle_submit_gate.py`; if it crashes or the reflection errors on the full clock, the slot
goes to a `thui-v3-1` resubmit instead. ⚠️ One public draw ranks nothing against the thuiv3 pool
(`[2.82, 5.24]` band, B35 floor) — the draw is the measurement, the public number is only a sanity gate.

### Full run (`yocybercode/thui-reflect-v1`, 25 games, COMPLETE 2026-09-04 ~14:25Z, wall 8,417 s) — **CLOSED: the memory works and the call is unaffordable at 25-game concurrency**

**Public 1.39 / levels 13 / actions 2613** — below the same-build band `[2.82, 5.24]` and below every member of the
thuiv3 pool (4.01 / 4.52 / 5.17 / 3.85, levels 23–26). Read from `kernels logs` on the mac; every number below is from
that log.

- **The lever was delivered**: 314 reflection calls, **294 returned all seven fields, 0 empty**, 20 `call FAILED`
  (all `ReadTimeout` at the 90 s cap), `wrapper error` 0. Nothing about the memory's CONTENT failed.
- **The bill is throughput.** Latency per reflection call: **12.1 s mean in the 3-game smoke → 59.8 s mean /
  88.9 s max / p90 ≈ 76 s on 25 games.** The 25 games share one vLLM server; a reflection is a full ~2.5k-token
  prompt plus 300–450 completion tokens, and every game issues one per 10 executed steps, so at any moment several games
  are blocked ~1 min each and the analyzer's own requests queue behind them — the main analyzer logged
  **20 `analyzer request failed`** timeouts in this run. Games that score in every pool run ended with almost no
  actions: `tr87` **2**, `tn36` **4**, `ft09` **5**, `sp80` **7** (pool runs: dozens to hundreds).
- **Why the smoke could not see it**: 3 games on one server leave the server idle between calls; the cost is a
  contention effect that only appears at the real concurrency. A smoke with a P-oracle on latency needs to run at
  full width, or budget the call against the per-turn yield (180 s) × 25.

**Verdict.** B62 as built is **closed — null-to-negative on public, mechanism proven, cost measured.** Not drawn on
hidden (the 09-04 slot went to a `thui-v3-1` resubmit, `56014686`). Re-open only with a memory rewrite that does
NOT block the game's turn and does not add a full request to the shared server per 10 steps — e.g. piggy-backing the
seven lines onto the analyzer's existing response (a prompt-side ask, already 0-for-5 on obedience), or an
asynchronous rewrite that lands between turns and is skipped when the server is behind. Sahasawat's pre-registration
for a hidden draw (≥ 2.05 / 1.40–2.00 / < 1.40) was never tested because the draw was not taken.

### Correction, same day (Sahasawat, 2026-09-04 ~15:00Z) — **the v1 number is not a memory result; the closure's mechanism is refuted**

The read above is right about the numbers and wrong about the cause. The run was poisoned by the v0-1 fix itself:

- **Thinking was OFF for the main analyzer, not only for the memory call.** `_reflect` flipped
  `tool_agent._LOCAL_ANALYZER_ENABLE_THINKING` — a module global that `_chat_completion` reads at call time
  (`tool_agent.py:1297`) — and the 25 games are **threads of one process** (`framework/solver.py:805`,
  `ThreadPoolExecutor`). Every game's analyzer request built while any game's memory call was in flight went out
  with `enable_thinking: false`. Union of in-flight windows (294 ok + 20 timed-out calls, mean concurrent 2.2):
  **7,324 s of 7,931 s = 92% of the run.**
- **Same-run control, aligned by the transcript wall-clock** (`| HH:MM:SS |` in every analysis event; the alignment
  puts 92% of events in-window, matching the union independently): `[THINKING` appears in **1% of the 1,451
  in-window analysis events vs 41% of the 122 outside**.
- **Per-request completion**: mean **318 / median 253** (n=3,548) vs **1,839 / 1,297** on `thui-v3-1` (same chassis,
  n=1,291) and 1,152 on the v0-1 smoke (sparse windows). tok/action **280** vs 1,272–1,439 across the family;
  actions +80%, levels halved (13) — **B31/v21's signature exactly** (v21: effort cut, 12 levels).
- **Second defect, the identical-output repeats**: upstream rewrites `_last_step_summary` only when a step
  EXECUTES (`:1583`) and never clears it, so an idle turn re-reads the previous step's `executed_count` and
  `level_transition` — `sp80` fired the level reflection **30 times on 7 actions** (26 byte-identical replies),
  `ar25` 26 on 20 (22 identical). Each one cost the game a minute.
- **The latency reading stands and is the minor half**: 17,636 s of reflection in flight = **8.9%** of the
  25 × 7,920 s game clock. The 20 `ReadTimeout`s and the 60 s mean are contention, as written above.

**Consequences.** `rank_runs.py` vs `thuiv3-pool` reads 4.39 → 1.39, p = 0.0002 WORSE — **confounded; it is not
B62's verdict.** B62 is **unmeasured**, not closed: the arm ran with a second variable the base never had.
`eval/fixtures/thui-reflect-v1.json` is banked and labelled DEFECTIVE (never pool it). MAP row re-opened.

**Fix — `thui-reflect-v1-1`** (`build_notebook.py --full --suffix=-1`), two changes in the wrapper, none in the memory:

1. `_ReflectThinkFlag` replaces the module global: `bool()` reads a **per-thread** override, else the harness value;
   the memory call sets its own thread's override and clears it in `finally`. In-kernel teeth: a worker thread
   turns itself off and reads `False` while the main thread still reads `True`, asserted before the benchmark.
2. A summary object is counted **once** (`st["seen_summ"]`), so an idle turn cannot re-fire on stale flags.

K = 10, cap 1200, timeout 90 s unchanged — the cost question above is real and is answered by the paired read at the
real concurrency, not by guessing a K. What the smoke could not see, again: a 3-game smoke rarely has two memory
calls in flight, so the global flag looked correct there (v0-1: completion mean 1,152, thinking mostly on).

Instrument (Windows box): `kernels_output` with `file_pattern` for `benchmark.json` / `summary.txt` / `.log` /
`_usage.jsonl` / `_p0_events.jsonl`; reflect intervals = `latency=` lines (end − latency) plus 90 s for each
`call FAILED`; events aligned per game by `t_log(first "new memory") − clock(first analysis transcript)`.
