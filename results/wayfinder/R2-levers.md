# R2 — Duck harness lever inventory

Extends `results/taaf-study-20260818.md` (read first; not re-derived here). Paths are
relative to `duck/bundle/src/` unless marked otherwise. All `file:line` against the
snapshot in this repo. `duckmod/` and `duckv3/` show which injection points our fork
has already spent (noted per-row) — "unspent" levers are the ones actually available.

Two file locations share short names below:
- **tool_agent.py** = `ARC3-Inference/inference/agent/tool_agent.py` (2063 lines)
- **solver.py** = `ARC3-Inference/inference/framework/solver.py` (1277 lines, the
  `HarnessSolver`/`_HarnessGameSession` file the prior study calls `framework/solver.py`)
- **prompts.py** = `ARC3-Inference/inference/agent/prompts.py`
- **sandbox.py** = `ARC3-Inference/inference/agent/python_tool_sandbox.py`
- **taaf/** = `tufa-arc-agi-framework/src/taaf/`

## New, load-bearing finding not in the prior study: the soft-deadline safety net is DEAD CODE on the real scored run

`taaf/kaggle_run.ipynb` cell (mirrored by the actual `tufa-labs-duck-harness-...ipynb`
cell 14): `soft_end = None if TRUE_SUBMISSION else datetime.now() + (max_runtime_s - buffer)`,
then `await bm.run(soft_end_time=soft_end, ...)`. `taaf/benchmark.py:169` only creates the
cancellation task `_cancel_at(soft_end_time, solver_task)` **if `soft_end_time is not None`**.
So on `TRUE_SUBMISSION` (the actual competition rerun): **no deadline task is ever created**,
`solver.py:922-926`'s `_drain_game_tasks`/`_finish_remaining` graceful-stop path is never
entered, and `HarnessSolver.cancel_drain_timeout_s=120.0` is inert. The *only* things that
can stop the run are (a) each game's own `max_runtime_s_per_game` clock
(`solver.py:213-217`, `_HarnessGameSession.runtime_limit_reached`) and (b) Kaggle's external
hard kill of the whole notebook process — which is ungraceful (no drain, no partial-result
write beyond whatever periodic `write_runtime_state`/`write_viewer_payload` already did).
**The 9h envelope is enforced entirely by `concurrency × ceil(games / concurrency) ×
max_runtime_s_per_game` arithmetic, with no code-level backstop if that arithmetic is
wrong.** Bundle values: `concurrency=28`, `max_runtime_s_per_game=7920.0` → 4 waves over
110 hidden games → `4 × 7920s = 31680s ≈ 8.8h`, suspiciously exact against a ~9h budget.
Any change to `concurrency` or `max_runtime_s_per_game` must be re-derived against the
actual hidden-game count and the true wall clock, not tuned by feel.

## (a) Time / budget allocation

| Lever | file:line | Current | Effect of changing | Cost | Risk |
|---|---|---|---|---|---|
| `HarnessSolver.concurrency` | solver.py:746, bundle value 28 (preamble.txt:2) | games in flight at once via `ThreadPoolExecutor`+`Semaphore` (solver.py:884-887, 896-898) | more parallel games = more waves finish inside the 9h clock, but more GPU contention on the local vLLM server (all 28 share one model) → likely slower per-call, offsetting the gain | config-flip (dataclass field / notebook cell 12 tweak) | **load-bearing** — directly multiplies total wall time; see envelope section above |
| `HarnessSolver.max_runtime_s_per_game` | solver.py:745, bundle value 7920.0 | per-game wall-clock budget (solver.py:213-217, 227-244) | lower = more games get a turn inside 9h but each is cut off shallower (scoring is depth-weighted, so cutting a game off early is expensive); higher = fewer full waves fit | config-flip | **load-bearing**, same envelope math |
| `HarnessSolver.max_actions_per_game` | solver.py:744, **bundle value `None` (unbounded)** | secondary stop condition (`solver.py:256-260`), currently never binds — only the clock does | setting a cap would stop a game that is spinning its wheels (many actions, few levels) before its clock runs out, freeing the wave slot sooner — a cheap "abandon a stuck game" lever the harness doesn't use today | config-flip | low — a too-low cap could cut off a game that's making real but slow progress; needs to be generous |
| `analyzer_timeout` (per-LLM-call ceiling) | solver.py:743, bundle value 900.0; consumed via `ToolAgent.__init__` → `self._timeout` (tool_agent.py:929-930) and `request_timeout_seconds()` (solver.py:227-244, `min(analyzer_timeout, per-game-remaining)`) | ceiling on one chat-completion HTTP call | lowering forces the model to answer faster per call (fewer, cheaper stalls) at the risk of truncating a legitimately slow reasoning turn; raising risks one call eating the whole per-game clock (900s is already 11% of the 7920s game budget) | config-flip | moderate — request_timeout is dynamically clamped by the per-game clock already, so raising it mostly matters when a game is early in its budget |
| `_LOCAL_ANALYZER_TOOL_STEPS` (env `LOCAL_ANALYZER_TOOL_STEPS`) | tool_agent.py:140, default 12; consumed tool_agent.py:932, loop bound tool_agent.py:1783 | max sub-turns (chat-completion round-trips) inside **one** `analyze()` call before giving up without acting | more steps = more chances to investigate before yielding, but each step can itself cost up to `analyzer_timeout` — 12×900s would blow the per-game clock in one `analyze()` call if the model never commits; in practice the per-game deadline still clamps each individual request | config-flip (env var, already exposed) | moderate — this is the knob that trades "investigate longer" against "commit sooner"; interacts multiplicatively with `analyzer_timeout` |
| `_python_timeout` (env `LOCAL_ANALYZER_TOOL_TIMEOUT`) | tool_agent.py:933, `min(30, max(1, env))` — **hard-clamped to 30s in code regardless of env value** | wall-clock budget for one sandboxed Python execution (sandbox.py `run_sandboxed_python`, `timeout_seconds`) | the env var can only ever lower this from 30s, never raise it — raising the sandbox time budget (e.g. for our `TransitionGraph` rebuild over long `history`, flagged as O(history) risk in the prior study §8 design #2) requires a code patch, not a config flip | **small patch** to raise the `min(30, ...)` ceiling | low-moderate — a longer per-call sandbox timeout eats into the same 30s-per-tool-call promise made to the model in `COMPACT_TOOL_SESSION_ADDENDUM` (prompts.py:111), which would need updating in lockstep or the model under/over-estimates its budget |
| `_LOCAL_ANALYZER_YIELD_SECONDS` (env) | tool_agent.py:143, default 0 (disabled); checked `tool_agent.py:1777-1778` `control_yield_reason()` | mid-turn wall-clock budget that makes `analyze()` yield control back to the game loop even mid-investigation | currently unused (0 = disabled) — turning it on gives finer-grained cooperative scheduling than "one whole `analyze()` call" so a slow game can be pre-empted more often, at the cost of resetting the model's sub-turn progress each yield (nothing survives between `python` tool calls anyway, per the prior study §2, so a yield mostly costs one extra round-trip of context) | config-flip | low |
| `cancel_drain_timeout_s` | solver.py:773, bundle 120.0 | grace period for in-flight games to finish after a cancellation | **inert on `TRUE_SUBMISSION`** per the finding above — do not tune this expecting it to matter in the scored run | n/a | n/a (dead code path in the mode that matters) |

## (b) Context management (eviction, world model, system prompt)

| Lever | file:line | Current | Effect of changing | Cost | Risk |
|---|---|---|---|---|---|
| `_LOCAL_ANALYZER_CONTEXT_WINDOW` (env) | tool_agent.py:138, default/bundle 32768 | drives `_context_budget_tokens` (tool_agent.py:945-948), the token budget `_trim_messages_for_context` evicts against | raising it (if the served vLLM model actually supports a longer context) lets more raw history survive before eviction — but `_estimate_tokens` (tool_agent.py:462-467) is `len(json_dump)/3`, a crude heuristic that can under/over-estimate real tokenizer usage, so raising this without headroom risks a real 400/context-length error from the server (there's a recovery path, `_is_context_length_error`/`_force_reduce_messages`, tool_agent.py:1836-1853, but it costs a wasted request) | config-flip, contingent on the vLLM `--max-model-len` actually being raised too (setup_commands.json pin) | moderate — this is coupled to a version-pinned vLLM launch flag, not free-standing |
| `_PERSISTENT_HISTORY_ASSISTANT_TURNS` (const) | tool_agent.py:151, 30 | separate cap (independent of the token trim) on how many assistant turns `_persistent_history_messages` keeps (tool_agent.py:1653-1670) before the token-budget trim even runs | lowering forces earlier reliance on the world-model carryover (§(b) next row) instead of raw history; raising keeps more raw transcript around, which is more literal but competes harder for the token budget | config-flip (currently a hardcoded module const, not env-exposed — would need a small patch to make it an env var, or edit the const directly) | low — the world-model carryover is the actual long-horizon memory (prior study §5b), so raw-history depth mostly affects short-term self-consistency |
| World-model field length | `_extract_labeled_blocks` tool_agent.py:226-260, called with `max_chars=None` at line 257 | **no cap** on any of the 7 labeled-block fields (`World model:`, `Goal model:`, etc.) that get replaced-in-full each turn and re-injected verbatim into every subsequent user prompt (`_summarized_knowledge_lines`, tool_agent.py:1128-1145, inserted at 1236) | a model that writes a long "Recent findings" block once pays that cost on **every** subsequent turn for the rest of the game (or until the next level transition clears it, tool_agent.py:1113-1126) — this is the single biggest uncapped, silently-compounding prompt-bloat surface in the harness | **small patch**: pass a `max_chars` into `_extract_scientist_note`/`_extract_labeled_blocks` per field | low risk to add, and directly reduces token spend per turn for long games — a strong candidate |
| `_TRUNCATE_FIELDS`/tool-output truncation | tool_agent.py:1340 (`self._tool_output_chars`), sized from `_tool_output_tokens` (tool_agent.py:938-939, env `LOCAL_ANALYZER_TOOL_OUTPUT_TOKENS` default 1024) | caps `python` tool stdout/error/result text returned to the model per call | raising lets the model see more of a large `print()` dump (useful for e.g. `TransitionGraph` stats) at direct token cost every tool call, not just once like the world model | config-flip (env var, already exposed) | low |
| System prompt itself | `_build_system_prompt` tool_agent.py:350-359, assembled from prompts.py fragments | ~2.6k+ chars, **exempt from eviction**, paid on every single chat-completion request for the whole run (prior study §3) | any addition here is the highest-frequency-paid prompt surface in the harness — cheaper to add one line here than one line to the per-turn user prompt if the content is truly constant, since the system message is cached/reused whereas building it is not the bottleneck; but every byte is multiplied by request count, which for a 900s-timeout/12-tool-steps game can be in the hundreds per game | config-flip (edit prompts.py) | low-moderate — occupied already: `duckmod/prompt_additions.txt` adds to `STRUCTURED_RUNTIME_STATE_ADDENDUM`/`PYTHON_ADDENDUM`/tool description for the HUD-mask + TransitionGraph helpers |
| `_build_user_prompt` per-turn injection | tool_agent.py:1161-1256 | assembles the per-turn user message: progress recap, state line, world-model carryover, instructions | this is where `duckv3_observer.py` already hooks in (patches this exact method to auto-push a `GameObservation` block) — **occupied** | small patch (already spent by duckv3) | n/a |
| `MULTIMODAL_CONTEXT_ADDENDUM` gate | tool_agent.py:354, `current_grid_image_enabled()` (vision_context.py:38-39, env `MULTIMODAL_CONTEXT=current_grid`) | currently off by default (env unset); when on, attaches a PNG of the current frame to every user turn (vision_context.py:52-71, `current_grid_image_upscale()` default 16x) | turning this on gives the model a second modality alongside `.ascii`/`.segmentation` for free (setup_commands.json already writes `MULTIMODAL_CONTEXT` env per the prior study §1) — but every image is a real multimodal-token cost on top of the already-tight 32768 context window, and there's no evidence in this bundle the harness authors validated it helps vs. hurts | config-flip (env var already wired end-to-end) | moderate — untested lever, and image tokens compete directly with the context budget above |

## (c) Model / sampling params

| Lever | file:line | Current | Effect | Cost | Risk |
|---|---|---|---|---|---|
| `_LOCAL_ANALYZER_TEMPERATURE` (env) | tool_agent.py:145, default 0.6 | sampling temperature, passed straight through `build_chat_payload` (tool_agent.py:1294) | lower = more deterministic/exploitative play (good once a strategy is confirmed), higher = more exploration (good early/when stuck) — currently **static for the whole run**, no adaptive schedule | config-flip | low to try, but a fixed value is a known blunt instrument; an adaptive schedule (lower after a level is understood) is a structural rewrite |
| `_LOCAL_ANALYZER_TOP_P` / `_LOCAL_ANALYZER_TOP_K` (env) | tool_agent.py:146-147, defaults 0.95 / 20 | nucleus/top-k sampling | same shape of lever as temperature | config-flip | low |
| `_LOCAL_ANALYZER_SEED` (env) | tool_agent.py:148, default -1 (random) | request seed | pinning it makes runs reproducible for debugging but is irrelevant to actual score (each game still sees different frames) | config-flip | none |
| `_LOCAL_ANALYZER_ENABLE_THINKING` (env) | tool_agent.py:144, default True | passed as `thinking=` to `build_chat_payload` (tool_agent.py:1297) — controls whether the vLLM Qwen3 reasoning parser is engaged | disabling saves the reasoning-token cost per call (real $/latency win against the 900s-per-call and 32768-context budgets) at the cost of whatever the reasoning trace was buying in play quality — untested trade-off in this bundle | config-flip | moderate — could be a large latency win if reasoning tokens are eating a big chunk of the 900s window, worth measuring before flipping |
| `_LOCAL_ANALYZER_MAX_OUTPUT` (env) | tool_agent.py:137, default 0 → `self._max_output_tokens = None` (tool_agent.py:936, "server default") | caps generated tokens per response | currently unbounded (server default) — setting an explicit cap bounds worst-case latency per call but risks truncating a legitimate long tool-call/reasoning turn | config-flip | low-moderate |
| Served model itself (`LOCAL_ANALYZER_MODEL_ID`, currently `vrfai/Qwen3.6-27B-FP8`) | env, resolved tool_agent.py:492 via `_resolve_analyzer_model` (:481-499); vLLM launch flags hardcoded in `setup_commands.json` (`--tool-call-parser qwen3_coder --reasoning-parser qwen3 --generation-config vllm`) | the model doing all the play | swapping models is the highest-variance lever in the whole harness, but the tool-call/reasoning parser flags are model-family-specific and hardcoded — a non-Qwen3 model breaks tool-call parsing silently (prior study §9, already flagged) | **structural** (new wheelhouse, new parser flags, likely a new context-window/RLIMIT tuning pass) | high — this is the "swap the engine" lever, not a tuning knob |

## (d) Prompt surfaces (recap of what's free vs. occupied)

Per the prior study's injection-point table (§7), every addition funnels through one of:
system prompt fragments (prompts.py), the tool-schema description
(`_PYTHON_TOOL_DESCRIPTION`, tool_agent.py:154-165), or the per-turn user prompt
(`_build_user_prompt`, tool_agent.py:1161-1256). **Already spent by this fork:**
`duckmod/` occupies the HUD-mask + TransitionGraph splice (design #1 + #2 from the prior
study §8) via `prompt_additions.txt` into `STRUCTURED_RUNTIME_STATE_ADDENDUM` /
`PYTHON_ADDENDUM` / the tool description; `duckv3/` occupies the auto-pushed
per-turn-observation hook on `_build_user_prompt` itself. **Still free:** the third
design from the prior study (component-centred click enumeration, ranked #3/riskiest
there) has no code in either `duckmod/` or `duckv3/` yet — it is the one unclaimed
injection slot among the three the study scoped.

**New prompt-surface gap found in this pass, not previously flagged**: nothing in
`prompts.py` or `_build_user_prompt` ever mentions the competition's actual scoring
rule — `min((baseline/actions)² × 100, 115)` per level, averaged **weighted by level
number** (this repo's own `docs/competition-rules.md`/`README.md`, not duck-harness
code). `GAME_OVERVIEW_ADDENDUM` (prompts.py:11-20) tells the model to "optimize for as
few in-game actions as possible" and to solve "the entire game," but never tells it
that level 7 is worth 7× level 1, or that going below ~1.15× the human baseline buys
nothing further. A model that spends its budget polishing an already-fast level 1
instead of pushing deeper is doing exactly what the (silent) prompt asks and exactly
the wrong thing for score. See (h) below — this is the same gap from the scheduling
side.

## (e) Tool / REPL surface (sandbox namespace)

Already fully mapped by the prior study §2/§7 (splice mechanism at sandbox.py:398,
`runtime_globals` dict at sandbox.py:322-369, `FrameView` lazy-attribute pattern at
sandbox.py:127-146). Two items not called out there:

| Lever | file:line | Current | Effect | Cost | Risk |
|---|---|---|---|---|---|
| Sandbox resource limits | sandbox.py:252-266 (`_set_limits`) | `RLIMIT_CPU = timeout+1`, `RLIMIT_FSIZE = 1MB`, `RLIMIT_NOFILE = 32`. **No `RLIMIT_AS`/`RLIMIT_DATA` — no memory cap at all** on the sandboxed subprocess (POSIX-only; `resource` is None on non-POSIX, but the Kaggle host is Linux, so this is live in the actual scored run) | a runaway allocation inside LLM-authored `python` code (e.g. a `TransitionGraph`-style structure grown without bound, or an accidental cartesian-product bug) has no per-call memory ceiling — it can only be stopped by the CPU-time limit eventually killing it, or by exhausting host RAM shared with the other ~27 concurrent games first | **small patch**: add an `RLIMIT_AS`/`RLIMIT_DATA` tuple to the same loop | this is a real gap worth closing defensively, independent of any specific feature we add — any future sandbox helper that builds a large structure (the transition-graph design from the prior study §8 is exactly this shape) inherits this exposure |
| `SAFE_MODULES` allowlist | sandbox.py (prior study :42-57), 13 stdlib modules | fixed list (bisect, collections, copy, fractions, functools, heapq, itertools, json, math, operator, random, re, statistics, string) | adding a module (e.g. `array` for a denser board representation, or `dataclasses` for cleaner state) is a one-line allowlist edit, but every module considered must itself be stdlib-only and side-effect-free at import (same constraint segmentation.py states about itself) | config-flip (add a string to the set) | low, but scope-limited — most useful modules for grid/graph work are already present |

## (f) Concurrency / scheduling across games

Covered under (a) for the numeric knobs. The structural finding: `_run_games`
(solver.py:896-926) schedules every game as an equal-priority `asyncio.Task` gated
only by `Semaphore(concurrency)`, in **list order** (`enumerate(games)`,
solver.py:913). There is no reordering, no priority, and no weighting by anything —
see (h).

## (g) Memory / world-model maintenance

Covered in (b) above (world-model field cap) and in the prior study §5b (mechanism).
One more knob: `_update_summarized_knowledge_from_step_summary` (tool_agent.py:1113-1126)
clears the world model on `level_transition`/`run_complete`/`game_over` — this is a
fixed, non-configurable policy (no env var), so "carry some of the world model across a
level transition" is a **structural rewrite**, not a flip, if it's ever wanted (e.g. to
preserve `Cross-level notes:` deliberately, which the label list already singles out
for exactly this purpose but the clear-on-transition code at :1118-1125 does not
special-case it — it clears `world_model`/`goal_model`/`action_model`/
`recent_findings`/`open_questions`/`current_plan` but **not** `cross_level_notes`,
which is the one field the label taxonomy calls out as meant to survive). This
asymmetry is already correct, not a bug — flagged only because it's easy to misread
the clear-list as clearing everything.

## (h) Scoring-aware behavior — none found

Checked three places a scoring-aware policy could live and found none:

1. **The prompt**: no mention of the depth-weighted scoring formula or the 1.15×
   baseline cap anywhere in `prompts.py` (see (d) above).
2. **Scheduling**: `Benchmark.game_weights` (`taaf/benchmark.py:57`, `:100-107`) exists
   as a field, gets validated, and is threaded through save/load
   (`taaf/benchmark.py:418,451`) — but the actual submission notebook sets
   `bm.game_weights = None` (notebook cell 14) and nothing in `_run_games`
   (solver.py:896-926) or `HarnessSolver` ever reads `game_weights` to bias budget or
   scheduling order. It exists purely for **diagnostics aggregation**, not for
   in-run decision-making.
3. **Per-game budget**: `max_runtime_s_per_game` (solver.py:745) is one flat number
   applied identically to every game regardless of how many levels it has or how
   deep the agent has previously gotten into it — no per-game or per-level-depth
   budget differentiation exists anywhere in this bundle.

So both halves of the question in the task brief are "no": the harness does not know
level weights, and it does not prioritize deep games. This is a real, structural gap,
not a config flip — implementing it means either (a) a prompt addition making the
model self-aware of the scoring rule (cheap, uncertain payoff — depends on the model
actually acting on it), or (b) a scheduling change that gives games already past level
N a priority boost or an extended clock when the wave is about to run out (structural,
touches `_run_games`/`HarnessSolver`, needs per-game level-progress telemetry the
solver already has via `game.game_run` but doesn't currently expose to the scheduler).

## Top 5 by leverage-per-cost

Ranked by (expected score impact) / (cost class + risk), independent of the prior
study's three tool-injection designs (which are a separate, already-scoped decision —
two of three are already spent by this fork).

1. **Cap the world-model field length** (b, tool_agent.py:257/1236) — small patch,
   low risk, directly cuts a silently-compounding per-turn token cost that grows for
   the entire lifetime of a level with no existing bound. Pure win: frees context
   budget for more history/tool-output per turn without touching model behavior.
2. **Tell the model the scoring rule** (d/h, prompts.py `GAME_OVERVIEW_ADDENDUM`) —
   config-flip, low risk (worst case: no behavior change), directly targets the
   documented gap between "optimize actions" (current prompt) and "optimize
   depth-weighted score" (actual rule). Cheapest possible fix to the single
   clearest correctness-of-objective gap found in this pass.
3. **Re-verify / re-tune `concurrency × max_runtime_s_per_game` against real hidden-game
   count and measured wall-clock** (a, solver.py:746/745) — config-flip, but
   load-bearing: given the dead soft-deadline path, this arithmetic is the *only*
   thing standing between the current tuning and either (a) wasted slack (finishing
   early, leaving score on the table from games that never got a turn) or (b) a hard
   kill mid-wave with ungraceful loss. High leverage because it's currently unverified
   against the actual hidden set (110 games is an external, unconfirmed number per the
   prior study §6).
4. **Add a memory rlimit to the sandbox** (e, sandbox.py:252-266) — small patch, purely
   defensive, near-zero risk of regressing anything that currently works, but currently
   the sandbox has a real unguarded resource-exhaustion path that a future large-state
   helper (transition graphs, click-candidate ledgers — both already discussed in the
   prior study §8) makes more likely to trigger, not less.
5. **Toggle `_LOCAL_ANALYZER_ENABLE_THINKING` off and measure** (c, tool_agent.py:144/1297)
   — config-flip, moderate risk only in the sense of unknown play-quality impact, but
   cheap to A/B: if reasoning tokens are consuming a large share of the 900s/32768-token
   budget for marginal play-quality gain, disabling it could free real budget for more
   tool-calling turns per game instead. Needs a measured trial before committing, unlike
   #1/#2/#4 which are safe-by-construction.

## Load-bearing for the 9h envelope — do not touch without re-deriving the arithmetic

- `HarnessSolver.concurrency` (28) and `max_runtime_s_per_game` (7920.0) — their product
  across `ceil(hidden_games / concurrency)` waves is the *entire* enforcement mechanism
  for staying inside the platform's hard kill, because the soft-deadline/graceful-drain
  path (`taaf/benchmark.py:169`, `solver.py:922-926`, `cancel_drain_timeout_s`) is
  **inert on `TRUE_SUBMISSION`** (see the new finding at the top of this document).
- `analyzer_timeout` (900.0) interacting with `_tool_steps` (12) — a game whose model
  never commits to an `action(...)` call could in principle spend up to
  `12 × 900s = 10800s` of request time in a single `analyze()` turn before the
  per-game clock (`request_timeout_seconds()`, solver.py:227-244) clamps each
  individual request down — the clamp is real and does bound this, but it means the
  effective per-`analyze()`-call ceiling is `min(analyzer_timeout, game_time_remaining)`
  repeated up to 12 times, not a flat 900s. Lowering `_tool_steps` or `analyzer_timeout`
  changes this multiplicatively, not additively.
- `_LOCAL_ANALYZER_CONTEXT_WINDOW` (32768) is coupled to the vLLM server's own
  `--max-model-len` launch flag (setup_commands.json, version-pinned per the prior
  study §9) — raising one without the other either wastes headroom or causes live
  400s from the server that the harness has to recover from mid-run (tool_agent.py:
  1836-1853), costing wasted requests inside the same fixed clock.
- Any change to the sandbox timeout ceiling (`min(30, ...)`, tool_agent.py:933) or to
  the resource limits (sandbox.py:252-266) changes worst-case per-tool-call latency,
  which compounds across `_tool_steps × turns-per-game`; both are inside, not outside,
  the per-game clock, so they cannot blow the 9h envelope on their own but can eat a
  game's own budget faster if set generously.
