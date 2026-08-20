# Tanaka Ai24 "LB117 Safety V1" notebook — what it actually does

Source: `arc3-qwen3-6-duck-lb117-safety-v1.ipynb` (10 cells total, public, id
`tanakaai24/arc3-qwen3-6-duck-lb117-safety-v1`), `kernel-metadata.json` in the same
bundle. Compared against our `duckmod/taaf-duck-mod.ipynb` (17 cells, same TAAF
lineage — both unpickle `deploy_target.pkl`/`benchmark_initial.pkl` from a
`jeroencottaar/taaf-kaggle-source*` dataset and call `bm.run(...)`).

Every claim below cites the cell it comes from. Cell numbers are 0-indexed as
returned by `json.load(...)['cells']` on the `.ipynb` (markdown cell 0 counts).

## 0. Headline finding: there is no sampling/runtime config override in this notebook

Grepped the full extracted source for `temperature`, `top_p`, `top_k`, `MAX_OUTPUT`,
`max_output`, `32768`, `LOCAL_ANALYZER`, `YIELD`, `TOOL_STEPS` — **none of
temperature/top_p/top_k/MAX_OUTPUT/context-length appear anywhere in the notebook**.
The only two numeric solver values touched at all are `bm.solver.concurrency` and
`bm.solver.max_runtime_s_per_game`, and both are only **asserted**, not set:

```python
assert bm.solver.concurrency == 28
assert bm.solver.max_runtime_s_per_game == 7920
```
(cell 8, inside the `RUN_AS_SUBMISSION` branch, immediately before the AGI_8 patch
is installed)

That means: **temperature 0.6 / top_p 0.95 / top_k 20 / MAX_OUTPUT 0 / context 32768
/ concurrency 28 / per-game clock 7920 all still come from the pickled
`benchmark_initial.pkl` baked into the `jeroencottaar/taaf-kaggle-source` bundle
dataset, unmodified by this notebook.** Our own `duckmod` notebook is in the same
position — neither notebook sets any of these values directly; both inherit them
from the same upstream bundle-build step outside the notebook (confirmed by
grepping `duckmod/taaf-duck-mod.ipynb` for the same keywords: 0 hits on all of
temperature/top_p/top_k/MAX_OUTPUT/concurrency/32768/7920).

The two `assert` lines are themselves a technique worth noting (§4): Tanaka fails
loudly if the upstream bundle's defaults ever drift instead of silently running a
runtime patch against changed assumptions. See §4 item 1.

**Everything Tanaka's "safety" actually consists of is two runtime monkeypatches
installed conditionally in cell 8**, described in §2, plus a `RUN_AS_SUBMISSION`
gate that is boilerplate shared with our own notebook (§3).

## 1. Env vars / config set (with values)

All in cell 1 and cell 7 (unconditional — same whether or not the run actually
plays games):

| Var | Value | Cell | Same as duckmod? |
|---|---|---|---|
| `TAAF_RUN_AS_SUBMISSION` | `"1"` if `RUN_AS_SUBMISSION` else `"0"` | 1 | Yes (duckmod cell 2, identical logic) |
| `MPLBACKEND` | `"Agg"` (via `setdefault`) | 1 | Yes (duckmod cell 2: hard-set, not `setdefault`) |
| `LIBRARY_PATH` | prepends `/usr/local/nvidia/lib64` | 1 | Yes, byte-for-byte same CUDA path |
| `ONLY_RESET_LEVELS` | `"true"` | 7 | Yes (duckmod cell 2) |
| `TAAF_MINIMAL_DIAGNOSTICS` | `"1"` if `run_as_submission` else `"0"` | 7 | Yes (duckmod cell 2) |
| `ARC_API_KEY` | `"test-key-123"` (setdefault, live-rerun only) | 9 | Yes (duckmod cell 14) |
| `ARC_BASE_URL` | `"http://gateway:8001/"` (setdefault, live-rerun only) | 9 | Yes |
| `SCHEME`/`HOST`/`PORT` | `"http"` / `"gateway"` / `"8001"` (setdefault, live-rerun only) | 9 | **Not present in duckmod** — duckmod's `_competition_games()` builds the `ArcadeSpec` straight from `os.environ["ARC_BASE_URL"]` and never sets these three (duckmod cell 14). Harmless extra defaults, not obviously load-bearing. |
| `RECORDINGS_DIR` | `WORKING_DIR / "server_recording"` (setdefault) | 9 | Yes (duckmod cell 14) |
| `OPERATION_MODE` / `ENVIRONMENTS_DIR` | `"competition"` / `""` (setdefault, live-rerun only) | 9 | **Not present in duckmod** — duckmod passes `operation_mode`/`environments_dir` as explicit constructor args to `ArcadeSpec`/`Arcade` instead of via env (duckmod cell 14 comment: *"ArcadeSpec carries neither [env var]; operation mode, environments dir, and base url are all passed explicitly via the spec, so no env is needed"*). Cosmetically different, functionally redundant with what the spec already receives explicitly. |

`SOFT_DEADLINE_BUFFER_S = 600.0` (cell 3) is a named constant version of the same
`min(600.0, budget/2)` duckmod inlines directly in its own soft-deadline calc
(duckmod cell 14) — same buffer cap, just refactored into a name. Not a behavior
difference.

**No temperature/top_p/top_k/MAX_OUTPUT/context/concurrency override exists in
this notebook** — see §0.

## 2. Source patches / monkeypatches (cell 8 — this is the entire "safety" payload)

Both patches are gated behind `if RUN_AS_SUBMISSION:` (cell 8) and only apply when
the run is a real or emulated submission — never during the fast registration path.

### AGI_8 — batch-level "repeated no-effect direction" guard

Monkeypatches `inference.framework.solver._HarnessGameSession.step_env`
(cell 8, saved as `_agi8_original_step_env` but the original is never called —
the whole method is replaced). Mechanically:

- Iterates a **batch** of requested actions (`requested_actions`) one at a time,
  same as the original harness presumably does.
- After executing each action, if the result's `board_changed` is `False`, the
  action's direction is one of `{UP, DOWN, LEFT, RIGHT}`, **and the next queued
  action in the same batch is the identical direction**, it stops the batch early:
  `stop_reason = "repeated_no_effect"`, with a message telling the model to
  re-observe before retrying (cell 8, lines building `stop_detail`).
- Every other stop condition (`run_complete`, `game_over`, `level_completed`,
  action errors, an invalid action, `should_stop()`) is preserved from what reads
  as the pre-existing batch-execution loop.
- Returns a payload annotated with `stop_reason`/`stop_detail`, `batched`,
  `requested_count`, `executed_count`, `stopped_early`, etc. — richer bookkeeping
  than a bare action result, presumably surfaced back to the model in its next
  turn's context.

Net effect: **if the model queues a batch like `[UP, UP, UP]` and the first `UP`
does not move the board, the second/third `UP` never execute** — the batch is
cut short and control returns to the model instead of burning the rest of the
batch on a move already known to be a no-op.

### AGI_9 — analyzer yield-budget extension

Monkeypatches a module-level constant, `inference.agent.tool_agent._LOCAL_ANALYZER_YIELD_SECONDS`,
from `60.0` to `90.0` (cell 8), with an `assert` on the original value first
(`assert _agi9_original_yield_seconds == 60.0`). Comment: *"give inspection-heavy
turns one additional model/tool cycle before yielding back to the solver."*

This is the same constant our own R10-throughput.md documents as
`LOCAL_ANALYZER_YIELD_SECONDS` (R10 cites `taaf-*.log:257` showing runs set it to
`60` and `tool_agent.py:1767-1785` for where it's checked) — **see §5 for why this
is flagged, not simply copied.**

## 3. What "safety" means in their design

Nothing in this notebook adds a timeout, retry, or crash guard in the
error-handling sense. "Safety" here means: **do not let the model waste actions
or turns doing something the harness can already tell is unproductive.**

- AGI_8 stops a doomed batched action *before* it burns further budget, instead
  of waiting for the model to notice on its own next turn.
- AGI_9 gives "inspection-heavy" turns (i.e., ones spending time on tool calls
  rather than emitting actions) more wall-clock before the harness forcibly
  yields control back to the solver loop, on the theory that cutting an
  inspection turn off too early produces a worse decision.
- The markdown title cell (cell 0) frames the whole notebook as "the public
  LB-1.17 AGI-8/AGI-9 rerun is preserved" — i.e., this notebook's job is to
  reproduce a specific historical scored run, not to explore new settings. The
  registration-mode gate (§3 next) exists so that ordinary Kaggle "Save & Run
  All" pings never accidentally re-spend GPU time or re-play the public games;
  only an actual submission rerun (or `TAAF_RUN_AS_SUBMISSION=1` set externally)
  triggers cells 5's setup commands and cell 8's patches at all.

There is no retry logic, no additional exception handling beyond what's already
present in the batch loop (`try/except Exception as exc` around
`self._execute_action`, cell 8 — this appears to be inherited scaffolding, not new
"safety" work), and no new timeout. The env-readiness poll in cell 9
(`while time.monotonic() < deadline: ... time.sleep(5)` against
`http://gateway:8001/api/games`, 600s deadline) is boilerplate identical in
shape to duckmod's `_wait_for_gateway` (duckmod cell 14) — not new.

## 4. Eval/benchmark override block

Cell 9, only inside `if true_submission:` (i.e. only for a *real* Kaggle
competition rerun, not a `TAAF_RUN_AS_SUBMISSION=1` local/offline validation run):

```python
bm.games = _competition_games()
bm.n_passes = 1
bm.game_weights = None
```

Compare with duckmod cell 14, where the identical two lines
(`bm.n_passes = 1; bm.game_weights = None`) are set **unconditionally**, right
after building the game list, whether that list came from the live gateway or
from `_offline_games(...)`.

**Consequence: Tanaka's notebook has no offline/local validation path at all.**
Unlike duckmod (which has an explicit `_offline_games(env_dir)` branch playing
the bundled competition environment files with no gateway, cell 14), Tanaka's
cell 9 `else` branch (when `run_as_submission` is true but `true_submission` is
false — i.e., manually forcing `TAAF_RUN_AS_SUBMISSION=1` without being inside an
actual Kaggle rerun) just calls `await bm.run(...)` against whatever `bm.games`
the pickle already carries, with no `n_passes`/`game_weights` override in that
branch. This is consistent with the title's claim that this notebook exists
specifically to **replay/preserve** a previously-scored AGI-8/AGI-9 configuration
rather than to run fresh experiments — there is no code path here for iterating
on new games or weights offline.

## 5. Ranked "worth stealing" list

### 1. AGI_8 batch early-stop on repeated no-effect direction — steal, high confidence, no evidence conflict

Directly reduces wasted actions: a batched multi-step plan that starts with a
no-op direction stops before repeating that exact no-op, instead of spending N
more actions confirming what the first one already showed. This is a pure
efficiency win that costs nothing extra in tokens or turns (it's decided from
data already returned by the harness, not an extra model call) and doesn't
contradict anything measured in R9/R10/v6.

One thing to note before porting: it only fires when the model has queued a
**batch** with the *exact same displayed action* twice in a row — our own harness
(`compete.py`) does not batch actions through an LLM tool call the same way (our
agent decides actions programmatically, not via a Qwen tool-calling loop), so
this specific mechanism doesn't transplant directly; the *principle* — stop a
plan early the instant it's proven a no-op, rather than exhausting a
pre-committed plan — is exactly the lesson our own CLAUDE.md traps section
already independently converged on for `ls20`/`wa30`-class livelocks ("a
transition reported against a stale reading" family, and the general
"a blocked move IS charged budget" finding). The applicable takeaway is: any
place in our own planner that commits to a multi-step plan should re-check the
first step's actual effect before blindly executing step 2, not: copy this code.

### 2. Defensive `assert`s before applying a runtime patch — steal, high confidence, cheap

`assert bm.solver.concurrency == 28`, `assert bm.solver.max_runtime_s_per_game == 7920`,
`assert _agi9_original_yield_seconds == 60.0` (all cell 8) — fail loudly if the
upstream bundle's baked-in defaults ever drift instead of silently monkeypatching
against stale assumptions. Cheap, general, and directly protects against exactly
the kind of "we forgot to rebuild the bundle" class of bug our own README already
paid for once (`kaggle/my_agent.py` shipping a stale `mirror.py`, 2026-08-16 entry
in CLAUDE.md). Any future runtime monkeypatch we write against a pickled/bundled
object should assert its starting state first.

### 3. AGI_9 yield-budget extension (60s → 90s) — FLAGGED, contradicts our own R10 measurement

**This is the one to be suspicious of.** R10-throughput.md measured this exact
constant (there called `LOCAL_ANALYZER_YIELD_SECONDS`, confirmed via
`taaf-*.log:257` as set to `60` in the runs it forensically analyzed) and
concluded:

> "Turn yield budget | Runs set `LOCAL_ANALYZER_YIELD_SECONDS=60`... The code
> checks it only between requests/tool iterations... **Low as implemented.** It
> cannot interrupt an in-flight 100–200-second completion, so it does not
> enforce a real 60-second turn ceiling."

Two problems with extending it to 90s given that finding:

- If the R10 reading is right that this knob only gates *between* completions
  and not mid-completion, then raising it from 60→90 mostly just permits **more
  tool/inspection cycles per turn before a forced yield** — i.e., it moves in
  the *opposite* direction from R10's own highest-leverage recommendation, which
  is to hard-cap `LOCAL_ANALYZER_MAX_OUTPUT` (currently `0` = unbounded, per
  R10's evidence chain) because generated-tokens-per-action is the dominant
  driver of seconds/action (r=0.984–0.987 correlation, R10 §1A). Tanaka's
  notebook does not touch `MAX_OUTPUT` at all (confirmed §0) — they're *widening*
  the time budget for expensive turns rather than *capping* the token cost that
  R10 measured as the actual bottleneck.
- More time per turn without a token cap plausibly means **more tokens
  generated per action-producing turn**, which R10's regression says predicts
  *more* seconds/action, not fewer — i.e., a throughput cost, not a throughput
  win, on the metric R10 says is the one to optimize (**total valid actions
  across all games per total job wall-clock**, R10 §3–4).

- **The v6 lesson also cuts against this.** v6-spec-ledger.md's working answer
  explicitly chose "intervention warnings" as digest-layer **advisory text**
  rather than a hard behavioral gate, with the stated reasoning: *"Does Qwen
  comply with 'acknowledge warning before similar batch' prompting? Unknown
  until a commit run; phrase as instruction, do not build a hard gate."*
  AGI_9 is not advisory — it's a hard runtime change to how long the harness
  lets a turn run before forcing control back, applied without (as far as this
  notebook shows) a measured before/after eval run isolating its effect from
  AGI_8's. AGI_8 by contrast doesn't cost extra time/tokens — it only ever
  *removes* wasted work — so it doesn't trip the same v6 caution.

Net: AGI_9 is plausibly a genuine improvement if in-flight completions really
can be interrupted at intermediate checkpoints in ways R10 didn't see evidence
of, but as read against our own R10 forensics it looks more likely to be a
turn-budget widening that increases tokens/action with no compensating cap —
exactly the direction R10 says *not* to move. Do not port this one without
running our own before/after sweep on it first (per this repo's own "no game
loses a level, one change at a time" rule — R14 §0/CLAUDE.md).

### 4. `RUN_AS_SUBMISSION` fast-registration gate — no action needed, already have equivalent

Boilerplate shared with our own duckmod notebook's `TRUE_SUBMISSION` gate (cell
2/7 here vs duckmod cell 2/10) — not something new to adopt, just confirms both
notebooks come from the same TAAF lineage as stated in the task brief.

### 5. `SCHEME`/`HOST`/`PORT`/`OPERATION_MODE`/`ENVIRONMENTS_DIR` env-var setdefaults (cell 9) — skip, redundant

These four env vars aren't read anywhere else in the visible notebook (the
`ArcadeSpec`/`Arcade` constructors take the equivalent values as explicit
keyword args in both notebooks — cell 6 here, cell 14 in duckmod). They look
like leftover scaffolding from an older version of the TAAF launcher rather than
a deliberate safety mechanism. Not worth copying; likely dead code in both
notebooks equally.

## Summary table

| # | Item | Cell(s) | Verdict |
|---|---|---|---|
| 1 | AGI_8 batch early-stop on repeated no-effect direction | 8 | Steal the *principle* (plan re-verification), not the code — no batched-tool-call harness on our side |
| 2 | Defensive asserts before monkeypatching | 8 | Steal directly — cheap, general, matches our own stale-bundle lesson |
| 3 | AGI_9 yield 60s→90s | 8 | **Flagged** — contradicts R10 (widens turn budget with no token cap, R10's own highest-leverage fix is the opposite direction) and v6 (hard gate, not advisory, unvalidated in isolation) |
| 4 | `RUN_AS_SUBMISSION` fast-registration gate | 1, 5, 7, 9 | Already have the equivalent (`TRUE_SUBMISSION`) |
| 5 | Extra `SCHEME`/`HOST`/`PORT`/etc setdefaults | 9 | Skip — likely dead code |
| — | temperature/top_p/top_k/MAX_OUTPUT/context/concurrency/clock | *(not present)* | Confirmed unmodified from the TAAF bundle defaults — Tanaka's "LB117" edge is not a sampling-config trick |
