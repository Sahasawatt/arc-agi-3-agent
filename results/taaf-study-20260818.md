# The Duck harness: map, injection points, tool designs

Study of `duck/bundle/**` (read-only, not edited). All claims below are `file:line`
against that snapshot; anything not confirmed in the snapshot is labeled `NOT FOUND`.
Paths below are relative to `duck/bundle/`.

## 1. Entry-point flow

```
tufa-labs-duck-harness-june-30-milestone-winner.ipynb   (infra + diagnostics ONLY —
    cell 0 says so explicitly: "You will only find infrastructure and diagnostics in
    this notebook; the actual solver code is in an attached dataset.")
  1. env/submission-mode flags (cell 2)
  2. pip-install `arc-agi` from offline wheelhouse (cell 4)
  3. locate + mount the source bundle by its marker file `taaf-kaggle-bundle.json`
     (cell 6, DATASET_SOURCES[0] = "jeroencottaar/taaf-kaggle-source-share")
  4. sys.path-insert the bundled repos, then run `setup_commands.json` (cell 8)
       -> installs the vLLM wheelhouse, starts a local vLLM OpenAI server, smoke-tests it,
          writes env (LOCAL_ANALYZER_*, MULTIMODAL_CONTEXT, ...) to TAAF_KAGGLE_SETUP_ENV
          (setup_commands.json, single embedded PYSETUP heredoc)
  5. unpickle `deploy_target.pkl` + `benchmark_initial.pkl` -> `bm` (cell 10)
       -> bm.solver is a pickled `HarnessSolver(...)` instance (its repr is in
          preamble.txt line 2 / taaf-kaggle-bundle.json's benchmark.solver)
  6. optional one-off tweak to `bm`/`bm.games`/`bm.solver` (cell 12, empty by default)
  7. build the game list (competition Arcade if TRUE_SUBMISSION, else the offline
     bundled environment files) and `await bm.run(...)` (cell 14)
       -> bm.run() (taaf, benchmark.py, NOT read in this pass) drives
          `HarnessSolver._run_games(games)` (see §Solver below)
  8. teardown_commands.json runs in a `finally:` regardless of outcome (cell 14)
  9. render diagnostics.html inline (cell 16)
```

`preamble.txt` is **not** the LLM's system prompt — it is a benchmark-run header
(`benchmark.label`, `bm.solver`'s repr, pass/game counts, git status of the three
pinned repos) printed once at cell-14 start for the *notebook's own* diagnostics
(`print((BUNDLE_DIR / "preamble.txt").read_text())`, notebook cell 14). The actual
LLM system prompt is assembled entirely in code — see §3.

## 2. Where the REPL tools are defined

There is **exactly one** OpenAI-facing tool, `python`, declared once:

- `inference/agent/tool_agent.py:1258-1280` (`ToolAgent._tools`) — the function-calling
  schema: `{"name": "python", "description": _PYTHON_TOOL_DESCRIPTION, "parameters":
  {"code": <string>}}`. One string parameter, nothing else.
- Dispatch is hard-coded to that one name: `tool_agent.py:1590-1594`
  (`_dispatch_tool`) — any other tool name returns `{"error": "Unknown tool: ..."}`.

So "the tools the LLM can call" are **not** individual function-calling tools — they are
Python names available inside the single `python` tool's execution namespace. That
namespace is built in a completely separate file, `inference/agent/python_tool_sandbox.py`,
because the code runs in an **isolated subprocess**, not in-process:

- `python_tool_sandbox.py:448-577` (`run_sandboxed_python`) spawns
  `python -I -S -c <bootstrap>` (`:458-468`) — `-I` isolated, `-S` no site
  packages — and talks to it over a stdin/stdout JSON-line protocol. Because the child
  has no site-packages and cannot import this project, `_SANDBOX_BOOTSTRAP`
  (`:21-397`) is a **plain string** of Python source, `exec()`'d whole inside that
  subprocess (`:373-375`, inside the bootstrap's own `main()`).
- The bootstrap defines a `runtime_globals` dict that becomes the `exec()` globals
  for the LLM's code (`:322-329`, then populated by `_refresh_state`, `:331-354`, and
  `action`, `:369`). The names placed there are exactly what the LLM sees:
  `current_frame`, `latest_frame`, `history`, `transitions`, `last_transition`,
  `previous_frame`, `last_action_frame`, `last_action`, `valid_actions`,
  `last_action_result`, `result` (initialised `None`), and the callable `action(actions)`.
- Import surface inside the sandbox is an allowlist, not a blocklist:
  `SAFE_MODULES` (`:42-57`, 13 stdlib modules: bisect, collections, copy, fractions,
  functools, heapq, itertools, json, math, operator, random, re, statistics, string)
  and `SAFE_BUILTINS` (`:58-112`, ~45 builtins — no `open`, no `__import__` beyond the
  gated `_safe_import`, `:245-249`, no `eval`/`exec` in the allowed builtin set).
- `action(actions)` (`:356-369`) sends `{"type": "action", "actions": [...]}` over the
  pipe, blocks on `_recv()`, and on reply refreshes every runtime global via
  `_refresh_state` before returning the raw `action_result` dict to the LLM's code.
  Host-side, that message is caught by `run_sandboxed_python`'s main loop
  (`:536-560`) and routed to the `action_handler` callback passed in from
  `tool_agent.py:_run_python_tool` (`:1495-1545`, closure `_handle_action`), which
  calls `self._step_env_callback` (`:1529`) — the actual environment step, wired from
  `HarnessSolver`/`_HarnessGameSession` (`framework/solver.py:588` `step_env`,
  `:667-738` `_execute_action`, which is where TAAF's `Game.execute_action` is
  ultimately invoked — that call chain into `taaf.game.Game` was not read in this pass,
  `taaf/game.py` `NOT read`).
- **The `python` tool call is stateless between calls by design**: `runtime_globals`
  is rebuilt fresh in a brand-new subprocess every single call
  (`run_sandboxed_python` opens a new `Popen` each invocation, `:458`); nothing the
  LLM defines in one call survives to the next except what got written back through
  `action(...)`'s refreshed state or through the labeled-block "world model" the
  *prompt* re-injects (see §5). `COMPACT_TOOL_SESSION_ADDENDUM` states this
  explicitly to the model (`inference/agent/prompts.py:107`, "not saved between calls").

### The segmentation tool

`inference/utils/segmentation.py` (203 lines) is the one non-trivial capability spliced
into the sandbox. Its own docstring states the constraint that governs any future
addition: **"standard library only, no project imports, no `from __future__` import --
so its source can be spliced verbatim into the Python-tool sandbox bootstrap"**
(`segmentation.py:1-6`). Mechanism: `python_tool_sandbox.py:398` —
`.replace("__SEGMENTATION_SOURCE__\n", inspect.getsource(_segmentation))` — literally
pastes the module's source text into the bootstrap string at build time (module import
time, not per-call). `segment_layer(layer, color_chars)` (`segmentation.py:76-203`) does:
4-connected flood-fill into components (reading-order scan, so component `id` is
already top-most-left-most, `:113-130`); a Moore-neighbour contour trace reduced to
direction-change corners for `boundary` (`:16-62`); border-flood-fill-based containment
to build `children` (any component the border flood-fill never reaches is enclosed,
`:150-183`); and a translation-invariant `hash` — sha1 of `(color, cells normalized to
bbox-origin)` (`:65-73`) so the same object/shape can be matched across frames or
frame positions. Exposed to the LLM as the lazy property `FrameView.segmentation`
(sandbox bootstrap `:136-140`, computed once per FrameView instance, cached).
Not exposed: raw numeric grid (`PYTHON_ADDENDUM`/`STRUCTURED_RUNTIME_STATE_ADDENDUM`
both say so explicitly — deliberate design choice, not an omission).

## 3. Where the system prompt lives

`_build_system_prompt(*, tool_output_tokens)` — `tool_agent.py:350-359` — concatenates,
in order, six prompt fragments all defined in `inference/agent/prompts.py`:

1. `"You are a coding agent solving a grid-based puzzle game."` (literal, `:351`)
2. `GAME_OVERVIEW_ADDENDUM` (`prompts.py:11-20`) — one-observe-plan-act-cycle framing,
   64x64 boards, ARC color legend.
3. `STRUCTURED_RUNTIME_STATE_ADDENDUM` (`prompts.py:37-67`) — the full documented API
   surface: every runtime global, its shape, and the gotchas (`history[-1].frame`
   *is* the current frame, not the previous one; `last_action_result` persists across
   inspection-only calls; etc).
4. `MULTIMODAL_CONTEXT_ADDENDUM` (`prompts.py:69-74`), **only if**
   `current_grid_image_enabled()` (`tool_agent.py:354`, from
   `inference/agent/vision_context.py`, `NOT read in full this pass`) — tells the model
   a rendered image of the current grid is attached to user turns.
5. `VISUAL_GAME_ADDENDUM` (`prompts.py:22-35`) — object/HUD-bar heuristics, explicitly
   warns against "a segmented edge bar" being mistaken for clickable pieces (`:29`,
   "DON'T DO THIS!") — this is a *documented* known failure mode, directly relevant to
   injection #1 below.
6. `PYTHON_ADDENDUM` (`prompts.py:76-101`) — coding-style guidance: BFS/pathfinding
   recommendation (`:86`), never print full boards (`:90`), verify HUD-vs-gameplay
   change (`:95`).
7. `COMPACT_TOOL_SESSION_ADDENDUM.format(tool_output_tokens=...)` (`prompts.py:103-114`)
   — "exactly one tool", 30s-per-call limit, output-token cap, tool state not persisted.

This whole assembled string is `messages[0]`, the system message, and is **exempt from
context eviction** (`_trim_messages_for_context`, `tool_agent.py:1682` binds
`system_message = messages[0]` and always re-prepends it, `:1690`). So anything added
to prompts.py is paid on **every** chat-completion request for the entire run, never
evicted — this is the concrete cost surface for "prompt bloat" (see §4 risk notes).

A second, independent documentation surface is `_PYTHON_TOOL_DESCRIPTION`
(`tool_agent.py:154-165`) — the OpenAI function-calling tool's own `description`
field, a compact restatement of the available globals. It is also always-present
(part of every `_tools()` call, `:1258`), separate from the system message, and must
stay short (it competes for the same per-request budget).

## 4. Where actions get executed

Sandbox `action(actions)` (`python_tool_sandbox.py:356-369`) -> pipe message ->
`tool_agent.py:_run_python_tool`'s `_handle_action` closure (`:1495-1545`) ->
`self._step_env_callback(...)` (`:1529`, callback injected into `ToolAgent`, wiring
point `NOT read` in this pass — lives in `framework/solver.py`'s construction of the
analyzer, `_make_analyzer` `:1181-1207`) -> `_HarnessGameSession.step_env`
(`framework/solver.py:588-663`) -> `_execute_action` (`:667-738`) -> TAAF's
`Game.execute_action` (`taaf/game.py`, `NOT read this pass`). `_normalize_actions`
(`solver.py:491-544`) is where model-facing action names (`UP`/`MOUSE(row,col)`, from
`inference/agent/action_names.py:7-15`) get mapped back to engine action names
(`ACTION1..6`) before hitting the real API.

## 5. Context eviction

Two independent mechanisms, not one:

**(a) Token-budget sliding window over raw chat messages.**
`_trim_messages_for_context` (`tool_agent.py:1672-1690`) repeatedly calls
`_drop_oldest_history_block` (`:1608-1622`, pops the oldest message and any
immediately-following `tool`-role messages, i.e. drops in whole assistant/tool-call
units, never mid-unit) while
`_estimate_request_input_tokens(...) > budget_tokens`. Token estimate is a crude
`len(json.dumps(...)) / 3` heuristic (`_estimate_tokens`, `:462-467`), not a real
tokenizer. `budget_tokens = _context_budget_tokens - extra_safety_tokens`, and
`self._context_budget_tokens` (`:945-947`, `NOT fully read` — computed from
`_LOCAL_ANALYZER_CONTEXT_WINDOW` (env `LOCAL_ANALYZER_CONTEXT_WINDOW`, default 32768,
`:138`; the Kaggle setup script sets it to 32768 explicitly,
`setup_commands.json` `ANALYZER_CONTEXT_WINDOW = 32768`) minus reply-reserve and
request-safety-margin tokens (`_REQUEST_SAFETY_MARGIN_TOKENS = 512`, `:149`). System
message is always kept (`:1682-1690`).

**(b) A self-maintained "world model" that survives (a) entirely.**
The prompt asks the model to prefix its answer with labeled sections — `World model:`,
`Goal model:`, `Action model:`, `Recent findings:`, `Open questions:`, `Plan:`,
`Cross-level notes:` (`_build_user_prompt`, `tool_agent.py:1250`, and
`_extract_scientist_note`'s label list, `:263-296`). Every assistant turn is
regex-parsed for these labels (`_extract_labeled_blocks`, `:226-260`) and merged into
`self._summarized_knowledge` (`_update_summarized_knowledge_from_assistant`,
`:1105-1111`). That dict is re-rendered into **every** subsequent user turn verbatim
(`_summarized_knowledge_lines`, `:1128-1146`, inserted by `_build_user_prompt`,
`:1236`) — independent of whether the raw messages that produced it are still in the
context window. It is the actual mechanism carrying long-horizon state (goal, plan,
open questions) across an arbitrarily long game, cheaper than re-summarizing message
history with another LLM call. It self-clears on level transition / game-over /
run-complete (`_update_summarized_knowledge_from_step_summary`, `:1113-1126`) so a
stale plan from the previous level doesn't leak forward.
`_PERSISTENT_HISTORY_ASSISTANT_TURNS = 30` (`:151`) additionally caps how many
assistant turns `_persistent_history_messages` (`:1653-1670`) will try to keep before
(a)'s token trim even runs.

## 6. Per-game time-budget allocation

`HarnessSolver` is a TAAF `Solver` subclass (`framework/solver.py:738-...`) with fields
`analyzer_timeout` (float, seconds per LLM call — default 120.0 at `:743`, actual
Kaggle-bundle value 900.0 per `preamble.txt:2`), `max_runtime_s_per_game` (default
`None`/unbounded at `:745`, actual bundle value 7920.0s ≈ 2.2h), and `concurrency`
(default 16 at `:746`, actual bundle value 28).

All games in a benchmark run **concurrently**, not round-robin: `_run_games`
(`:896-...`) creates one `asyncio.Task` per `(game, pass)` guarded by
`asyncio.Semaphore(concurrency)` (`:898`, `:903-910`), each running on a dedicated
`ThreadPoolExecutor(max_workers=concurrency)` (`:884-887`) — with a code comment
explaining *why* a custom pool: `asyncio.to_thread`'s default executor caps at
`min(32, cpu+4)`, which would silently throttle real concurrency below the configured
value (`:802-805`). So "9h / 110 games" is not a per-game round-robin slice; it's
`concurrency` games in flight at once, each independently budgeted by
`max_runtime_s_per_game`, until the pool drains. **The 110-hidden-games/9h figure
itself is `NOT FOUND` in this bundle** — the bundle's own `benchmark.games: 25`
(`taaf-kaggle-bundle.json:4`, and the harness's own `ARC3-Inference/README.md:253`
says "16 public games") is the public validation set, not the hidden set; the 9h/110
split is an external competition fact this study cannot verify from the code.

Per-LLM-call timeout is **dynamic**, not the flat `analyzer_timeout`:
`_HarnessGameSession.request_timeout_seconds()` (`solver.py:227-244`) takes
`min(analyzer._timeout, per-game time remaining, solver.soft_time_remaining_seconds())`
— so as either this game's own clock or the whole-run soft deadline
(`HarnessSolver.soft_time_remaining_seconds`, `:1164-1173`, `NOT fully read`) closes
in, individual LLM calls get truncated automatically rather than the run blowing its
deadline on one slow call. `_tool_steps` (env `LOCAL_ANALYZER_TOOL_STEPS`, default 12,
`tool_agent.py:140`) is a separate cap — presumably max tool calls per analyzer turn,
consumed at `:932`; its exact use inside `analyze()` (`:1706-...`) was `NOT read` in
this pass (time-boxed).

## 7. Injection points — summary

| What | File : line | Mechanism |
|---|---|---|
| New pure-Python helper callable from LLM code | `inference/utils/<name>.py` (new, stdlib-only, no imports — same constraint as `segmentation.py:1-6`) + splice site `python_tool_sandbox.py:398` (generalize the single `.replace(...)` into N splices, or concatenate multiple `__X_SOURCE__` placeholders) | Source-text splice into an isolated subprocess; cannot be a normal import |
| Expose it as a bare callable in LLM's namespace | `python_tool_sandbox.py:322-369` (`runtime_globals` dict / `_refresh_state`) | Same pattern as `action` (`:369`) |
| Expose it as a lazy attribute on the frame view | `python_tool_sandbox.py:127-146` (`FrameView` class) | Same pattern as `.segmentation` (`:136-140`) |
| Document the new capability's data shape | `inference/agent/prompts.py`, `STRUCTURED_RUNTIME_STATE_ADDENDUM` (`:37-67`) | Always-resident system-prompt text (never evicted) |
| Document *when to reach for it* | `inference/agent/prompts.py`, `PYTHON_ADDENDUM` (`:76-101`) | Same — this is where the existing BFS recommendation lives (`:86`) |
| Update the OpenAI tool-schema description | `inference/agent/tool_agent.py:154-165` (`_PYTHON_TOOL_DESCRIPTION`) | Also always-resident, shorter budget |

Nothing about `_tools()` (`tool_agent.py:1258`) or `_dispatch_tool` (`:1590`) needs to
change for any of the three designs below — the OpenAI-facing tool surface stays fixed
at one `python` function; only the sandbox's Python namespace and the prompt text change.

## 8. Three ranked tool-injection designs

Ranked by **expected score impact vs risk**, using our own campaign's measured
results as the evidence base (this repo's `README.md`/`CLAUDE.md`, not the duck
harness's own history — the duck harness has no comparable per-game measurement log
in this bundle).

### #1 — HUD / budget-bar auto-flagging (highest impact : risk ratio)

**What it does:** a pure function over one `segmentation()` result that flags
candidate HUD/timer objects: a thin (1-2 cell wide/tall) strip of same-color blocks
flush against a board edge, especially if its `pixels`-to-bbox-perimeter ratio and
position match a "repeated small-block strip" pattern. Returns an annotation, not an
action — it never touches gameplay, only labels which segmentation nodes are likely
HUD so the LLM's own reasoning can down-weight them.

**Signature:** `flag_hud_candidates(segmentation) -> list[{"node_id": int, "reason": str}]`,
called as `current_frame.segmentation` already is, e.g.
`hud = flag_hud_candidates(current_frame.segmentation)`.

**Backing evidence:** this is not a hypothesis — the harness's *own* prompt already
names this exact failure mode as a known trap: `VISUAL_GAME_ADDENDUM`
(`prompts.py:28-29`) warns "A common failure mode is to mistake a segmented edge bar
for clickable puzzle pieces... DON'T DO THIS!" — i.e. the harness authors already
know their LLM gets this wrong *from prose alone*. Our own campaign hit the identical
class of bug repeatedly and mechanically, not from misreading prose: `re86`'s
100-action-per-level colour-15 bottom row (README "re86's bottom row is a
100-ACTION-PER-LEVEL BUDGET"), `ls20`'s clock bar mis-scoped to the HUD region
(`plates() reads the whole frame, not the play area`), and the clock-rate-per-level
lesson (`"The clock's rate belongs to the LEVEL"`). A deterministic geometric flag
converts a fuzzy prose instruction ("don't do this") into a computed fact the model
can condition on, which is exactly the class of fix our own campaign found effective
(HUD/budget-bar auto-masking is literally one of our named differentiators).

**Risk:** low. Pure annotation, no new persistent state, no change to action
semantics — a wrong flag just means the LLM sees one extra unreliable hint among many
(it is already told to verify hypotheses, `VISUAL_GAME_ADDENDUM:27`). Prompt cost is
one short paragraph in `PYTHON_ADDENDUM` plus one line in
`STRUCTURED_RUNTIME_STATE_ADDENDUM` describing the return shape — cheap relative to
the existing ~2.6k-char `VISUAL_GAME_ADDENDUM`/`PYTHON_ADDENDUM` blocks it augments.
Computation cost: negligible (single pass over already-computed segmentation nodes).

### #2 — Online transition-graph builder over `history`/`transitions`

**What it does:** rebuilds a lightweight state-transition graph each call from the
*already-persisted* `history`/`transitions` runtime globals (not from anything the
tool needs to remember itself, since nothing survives between calls — see §2) —
nodes keyed by a caller-supplied state signature (e.g. `current_frame.segmentation`
hash or a caller-provided key function), edges = observed `(state, action) -> state'`
transitions with counts, plus a `frontier(known_states, all_actions)` helper listing
untried `(state, action)` pairs. This generalizes what `PYTHON_ADDENDUM` already tells
the model to do by hand every turn ("write an explicit search algorithm such as BFS",
`:86`) into a reusable library instead of re-derived ad hoc code every single call.

**Signature:** `build_transition_graph(history, key_fn=None) -> {"nodes": [...],
"edges": [...]}` plus `frontier_actions(graph, current_key, valid_actions) -> list[str]`.

**Backing evidence:** this is the single most load-bearing pattern across our whole
campaign — the entire `ls20` level-7 saga is a hand-built, hand-maintained version of
exactly this (gate/mover/period graphs, `route_moving`'s BFS over recorded square
presses), and the sharpest negative lesson is the same shape: `ka59`'s "A static
colour-based walk map OVERCOUNTS reachability... when a static model and a real
router disagree, the model loses" — i.e. a graph built from *actually observed*
transitions beats a guessed/static one, which is precisely what rebuilding from
`history` every call guarantees (it can never assert a transition that was not
actually observed). `cd82`'s roller ("same-action-twice is a NO-OP... hidden state")
is the other side of the same coin: online graphs surface hidden-state effects a
static frame-diff heuristic cannot.

**Risk:** moderate. `history`/`transitions` length grows over a long game/level, so
graph-rebuild cost is `O(history length)` per tool call, inside the existing 30s
per-call budget (`_python_timeout`, `tool_agent.py:933`, min-clamped to 30) — for a
level with thousands of actions this could itself start dominating the 30s budget;
would need a cheap incremental or a windowed rebuild once measured. It also does not
change *what* action gets chosen, only what information is available, so it is
lower-risk to the model's decision quality than #3, but it must be documented
carefully in `STRUCTURED_RUNTIME_STATE_ADDENDUM` to avoid the model treating
`frontier_actions` output as a plan rather than as one input among several (mirroring
the ka59 lesson that a graph is "a hypothesis generator, never an oracle").

### #3 — Component-centred click-candidate enumeration

**What it does:** for click/`MOUSE` games, enumerate one candidate click point per
unprobed `segmentation` component (e.g. its centroid or top-left cell), track a
per-node "cells changed by clicking here" ledger across calls (persisted the only way
anything can persist here — via labeled `Recent findings:`/`Open questions:` text in
the world-model carryover, §5b, since Python state itself does not survive calls),
and surface the smallest never-clicked component first.

**Signature:** `enumerate_click_candidates(segmentation, tried_node_hashes) ->
list[{"node_id": int, "row": int, "col": int}]`.

**Backing evidence:** `dc22`'s "63 single clicks all eventually answer zero changed
cells" and the eventual `poke-click` design (click the smallest unprobed object
instead of pacing) is a direct measured win pattern, and `cn04`'s claw-docking rung
also identifies its targets by component motion/shape. But this is also where the
evidence *cuts both ways*, which is why it ranks #3 not #1: `ka59`'s `ferry` driver
shows the aimed click is a **swap onto a specific cell**, not a component centroid,
and `sb26`'s click targets are specific machine-slot cells, not component centroids
either — component-centroid enumeration is a good *default candidate generator*, not
a universally correct model of what a click does in every game.

**Risk:** highest of the three. Unlike #1 and #2, this one encodes a specific
strategic bias (click component centroids) that can actively mislead the model on
games whose click semantics differ (ka59, sb26 above), so it must be framed in the
prompt as *one candidate source among several*, never as the default click strategy,
and its "tried" bookkeeping depends entirely on the world-model text surviving the
labeled-block carryover faithfully (§5b) — a parsing failure there (e.g. the model
not echoing `Open questions:` back verbatim) silently loses the "already tried"
memory and the model could re-click the same dead node forever, the same shape of
livelock our own README documents for BFS/goal-repetition on carrying floors
("On a carrying floor, a repeat-count cannot tell a livelock from an honest walk").

## 9. Operational notes for the fork

- **Submission vs. commit (offline/interactive) mode**: a single flag,
  `TRUE_SUBMISSION = os.environ.get("KAGGLE_IS_COMPETITION_RERUN", "").strip().lower()
  in {"1", "true"}` (notebook cell 2). `TRUE_SUBMISSION` gates: diagnostics
  verbosity (`TAAF_MINIMAL_DIAGNOSTICS` env, cell 2), which game list gets built
  (`_competition_games()` against the live gateway vs `_offline_games()` against
  bundled environment files, cell 14), whether the notebook waits on the Kaggle
  gateway (`_wait_for_gateway`, cell 14), and whether a synthetic
  `submission.parquet` gets written for a non-scored offline run (cell 14, the
  `if not TRUE_SUBMISSION:` branch). It is **not** something `bm`/`HarnessSolver`
  decide — it is entirely the notebook's own environment check, done before the
  benchmark object is even touched.
- **Where scores/diagnostics land**: everything under `WORKING_DIR =
  Path("/kaggle/working")` (notebook cell 2) — `run_config.json`, `benchmark.json`,
  `diagnostics.html`, `artifacts/*_viewer_data.json` / `*_events.jsonl`, per-game
  transcript HTML/text, and (offline runs only) `diagnostics.html` rendered inline in
  the notebook (cell 16). This matches `ARC3-Inference/README.md`'s "Run Artifacts"
  section verbatim — confirmed present, not just documented, via
  `_write_transcript_html`/`write_viewer_payload` in `framework/solver.py:147-166,
  442-490`.
- **Version pins that could break a modified fork**:
  - `pyproject.toml:13` — `requires-python = "==3.12.12"` exact pin (not `>=`).
  - `pyproject.toml:16-22` — `arcengine==0.9.3`, `matplotlib==3.10.6`,
    `python-dotenv==1.2.2`, `requests==2.32.5` exact pins; `tufa-arc-agi-framework`
    dependency has a **TEMP local editable override** in `[tool.uv.sources]`
    (`:59-60`) with a comment saying to revert before committing — and
    `bundle/git_status.txt` confirms `ARC3-Inference` is currently `DIRTY` on branch
    `add-kaggle-share-flag`, i.e. this snapshot is mid-change, not a clean release.
  - `setup_commands.json`'s embedded Python pins the vLLM wheelhouse install to an
    exact stamp text `'vllm==0.19.0 torch==2.10.0 flashinfer==0.6.6\n'`
    (`STAMP_TEXT`) — `cached_install_is_usable()` compares this byte-for-byte before
    reusing a cached install, so bumping any of those three versions forces a full
    reinstall from the wheelhouse dataset (offline, no internet on Kaggle — so the
    wheelhouse dataset itself would need to be rebuilt to bump them).
  - The vLLM server is started with model-specific flags hardcoded in
    `setup_commands.json`: `--tool-call-parser qwen3_coder`, `--reasoning-parser
    qwen3`, `--generation-config vllm`. Swapping the served model (currently
    `vrfai/Qwen3.6-27B-FP8`, `SERVED_MODEL_NAME`) to a non-Qwen3 model would need
    matching parser flags or tool-call parsing breaks silently.
  - `configs/inference.json`'s `analyzer.*` section (mentioned in
    `ARC3-Inference/README.md:119-120` as "still named `analyzer` for
    compatibility") backs the `LOCAL_ANALYZER_*` env vars read throughout
    `tool_agent.py` — a config key rename there without updating the env-var
    plumbing in `setup_commands.json` would silently fall back to the hardcoded
    defaults in `tool_agent.py:137-148` rather than erroring.

## Areas not read this pass (time-boxed at 45 min)

`taaf/game.py` (688 lines, actual `Game.execute_action`/state machine),
`taaf/benchmark.py` (`bm.run()` itself), `taaf/game_api.py` (`GameAPI`/`ArcadeSpec`),
`inference/agent/vision_context.py` beyond its two imported names,
`inference/framework/run.py` (CLI entry point / deployment-target construction,
1422 lines), `inference/framework/kaggle.py` (432 lines, the Kaggle deployment
packaging referenced by `HarnessSolver.kaggle_*` properties), `inference/agent/
tool_agent.py`'s `analyze()` method body (`:1706-...`, the actual per-turn loop
calling `_chat_completion`/`_dispatch_tool` in sequence and consuming
`_tool_steps`) — all `NOT read`, flagged rather than guessed at.
