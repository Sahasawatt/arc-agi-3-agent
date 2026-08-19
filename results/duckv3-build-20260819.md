# duckv3 build: auto-push OBSERVATION block, no callable APIs

Output: `duckv3/duckv3_observer.py`, `duckv3/build_notebook.py`,
`duckv3/taaf-duck-v3.ipynb`, `duckv3/kernel-metadata.json`,
`duckv3/verify_against_bundle.py`, `duckv3/verify_notebook.py`,
`duckv3/synthetic_drive.py`. `duck/**` and `duckmod/**` untouched (read-only
reference, as instructed).

## 0. Why this design, in one line

`results/duckmod-transcripts-20260819.md` measured that duckmod's callable
`hud_mask`/`TransitionGraph` API got **0-2 real invocations across 2,001
tool-call turns** — the model essentially never reaches for a tool it has to
remember to call under a 3s-per-turn budget. duckv3 removes that failure
mode structurally: there is nothing to call. The harness computes the same
three signal classes (HUD mask, state novelty, untried actions) itself and
appends them as text to every turn's prompt, so the information reaches the
model on turn 1 with 100% delivery instead of ~0.1%.

## 1. Where the per-turn observation is assembled — and why this changes the mechanism

`ToolAgent._build_user_prompt` (`duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1161-1252`)
is the function that assembles every turn's user-facing message. It is a
plain method taking `current_frame`, `history_entries`, `valid_actions`,
`previous_step_summary` and returning a string; called once per turn from
`analyze()` (`tool_agent.py:1727`), which itself loads `current_frame` and
`history_entries` fresh from `runtime_state.load_runtime_state(state_path)`
at `tool_agent.py:1726` — so both objects are already real `Frame`/
`HistoryEntry` dataclasses (`inference/agent/runtime_state.py:16-44`) with a
**raw numeric grid** (`Frame.grid: tuple[tuple[int,...],...]`), not the
letter-coded ASCII view the sandboxed Python tool sees.

This is the load-bearing difference from duckmod: `_build_user_prompt` runs
in the **harness kernel process**, the same process that has `bm`/
`bm.solver` at notebook cell 12 — never inside the isolated `-I -S` sandbox
subprocess `python_tool_sandbox.run_sandboxed_python` spawns per tool call.
duckmod had to splice source text into `_SANDBOX_BOOTSTRAP` and inject names
into `runtime_globals` because that subprocess has no filesystem access to
project files and no import path back into this repo. duckv3 needs **none
of that machinery** — the observation logic is ordinary importable-shaped
Python that patches a method on the class the harness already imports.
Confirms study doc §7's own injection-points table: "Expose it as a bare
callable in LLM's namespace" is the *sandbox* pattern; this design instead
lands purely on the *system/user-prompt assembly* row, which the study doc
lists as a separate mechanism.

`history_entries` (`framework/solver.py:180`, `_HarnessGameSession`) is
**monotonically append-only for the life of one game session** — confirmed
by grepping every append site (`solver.py:203` seed, `solver.py:693` per
executed action; no `.clear()`/reassignment anywhere in the file) — so a
patch that walks it incrementally never sees it shrink or reset across a
level transition or death, only grow.

## 2. The patch mechanism

`duckv3/duckv3_observer.py` defines `GameObservation` (the per-game state)
and `install_patch(tool_agent_module)`, which monkeypatches
`tool_agent.ToolAgent._build_user_prompt` at the **class** level: wraps the
original method, calls it to get duckmod/duck's own base prompt unchanged,
appends one `GameObservation.render(...)` block, returns the concatenation.
Idempotent (a `_duckv3_patched` marker on the class guards against
re-wrapping if the notebook cell runs twice).

**Per-game state, without a game-id dict.** `HarnessSolver._make_analyzer`
(`framework/solver.py:1181-1206`) constructs a **fresh `ToolAgent()` per
`(game, index)`** inside `_play_one`, one call per game task (the study doc's
own §6: games run concurrently, one `asyncio.Task` per `(game, pass)`, each
on its own thread). So the patched `_build_user_prompt` lazily attaches
`self._duckv3_observation = GameObservation()` as an **instance attribute**
on the `ToolAgent` the very first time it's called — since each `ToolAgent`
instance already *is* one game's analyzer, instance-attribute storage gives
per-game isolation for free, with no dict, no game-id key, and no possible
key collision or leak between the concurrently-running games. This is
narrower than the brief's "instances keyed by game id" suggestion and was
chosen because it removes an entire failure class (wrong/stale key) rather
than adding one; verified directly (§4).

## 3. `GameObservation` — what it computes, and the ratio-detector's cold-start caveat

Three signal classes, all built only from *actually observed* transitions —
same "hypothesis generator, never an oracle" discipline this repo's own
CLAUDE.md states for the ka59 static-walk-map lesson ("when a static model
and a real router disagree, the model loses"):

- **HUD mask** — a cell is flagged if it changed on ≥95% of transitions
  observed so far, or was the *sole* changed cell on ≥2 separate transitions
  (same two signatures as duckmod's `hud_mask`, reused because they're
  already validated against this repo's own `re86`/`ls20` HUD lessons in
  `results/taaf-study-20260818.md` §8 design #1). Tallies (`_change_count`,
  `_isolated_count`, `_total_transitions`) are updated **incrementally**, one
  new transition at a time (O(1) amortized per turn) — not recomputed from
  the whole history every call.
- **State novelty** — `current_frame.grid` masked by the HUD set, looked up
  in a `visit_counts` dict keyed by the masked grid tuple itself (a
  tuple-of-tuples-of-ints is already hashable and its hash is **not**
  affected by Python's per-process hash-randomization, which only salts
  `str`/`bytes`/`datetime` — so no risk of the "hash() of bytes is
  randomised per process" trap this repo's own CLAUDE.md documents). Renders
  `NOVEL` or `SEEN(xN)`.
- **Transition graph / untried actions** — `(masked_prev, action) ->
  masked_cur` edges and a per-state `tried` set, built by walking new
  transitions in `history_entries` exactly once each; `untried here` is
  `valid_actions` (normalized to bare action names, `MOUSE(r,c)` → `MOUSE`)
  minus `tried[current_state]`.
- **Last action** — grid-diff of the last two raw frames in `history_entries`
  (unmasked; this one line is intentionally *not* run through the HUD mask,
  since "did anything at all change" is a different question from "did
  gameplay change").

**Known, disclosed limitation (marked `# ponytail:` in the source,
`duckv3_observer.py:104-115`):** the HUD mask used to key a transition's
visit/edge entry is whatever the ratio detector believes *at that moment*,
not re-applied retroactively once more evidence arrives. A cell recognized
as HUD several turns in leaves *earlier* dict entries keyed under a smaller
mask. This can only under-count `SEEN` (a real revisit briefly reads as an
extra `NOVEL`) — it cannot crash, mis-render, or over-count. Measured
directly in the synthetic drive (§5): the detector converges within ~2-3
transitions on a board with no competing hypothesis, and the two-cell
ambiguity only shows up when two cells both change on the *very first*
observed transition (ordinary cold start). Chosen over a correct-by-
construction full re-mask-every-turn because that alternative is O(history
length) per turn — cheap for one call late in a 2,000-action game (a few
thousand cell compares) but O(N²) summed over the whole game if paid every
turn; the incremental version is O(1) amortized per turn with a graceful,
self-healing failure mode instead.

## 4. Verification against the real bundle (Tested = Yes for every row below)

| Claim | Command | Result |
|---|---|---|
| `duckv3_observer.py` self-test (HUD ratio+isolation, NOVEL→SEEN transition, shape-mismatch safety) | `python duckv3/duckv3_observer.py` | `duckv3_observer self-test OK` |
| Source parses | `ast.parse` | clean |
| `install_patch` applies to the real `tool_agent.ToolAgent`, is idempotent | `duckv3/verify_against_bundle.py` | pass |
| Patched `_build_user_prompt` on a real `ToolAgent` instance, real `Frame`/`HistoryEntry` | same | produces a well-formed 4-line block (see below) |
| Two `ToolAgent` instances hold **independent** `GameObservation` — no cross-game state | same | `agent._duckv3_observation is not agent2._duckv3_observation` |
| Notebook is valid JSON, only cell 12 differs from duckmod's (16/17 cells byte-identical) | `duckv3/verify_notebook.py` | pass |
| Every code cell's Python parses | same | pass |
| The **exact embedded cell-12 source** (not a copy) executes against the real bundle | same | system prompt `+273` chars, patch marker set |
| Real `ToolAgent`'s `_system_prompt` contains the new paragraph; a real turn's user prompt contains the OBSERVATION block | same | pass |

Sample real output (`verify_against_bundle.py`, real `ToolAgent`, real
`Frame`/`HistoryEntry` from `inference.agent.runtime_state`):

```
HUD cells (auto-masked): 1 cells [(0, 0)]
state: NOVEL
untried here: ['ACTION1', 'ACTION2', 'ACTION3', 'ACTION4']
last action: CHANGED_FRAME
```

**What could NOT be verified locally, same reason as duckmod's own build
report:** no Kaggle GPU/vLLM environment available in this sandbox, so no
live LLM turn. Everything short of an actual model call is verified against
the real source tree. **UNVERIFIED**: an actual LLM turn reading the
OBSERVATION block inside a live game.

## 5. Prompt-cost accounting vs duckmod (`duckv3/synthetic_drive.py`)

60-turn synthetic drive over an 8x8 board (a ticking HUD corner, a static
obstacle, an agent cycling through 4 positions so it genuinely revisits
states) — the shape this whole design targets: HUD converges from
"3 cells flagged" at turn 0 (cold start, both the clock and the agent's
first two positions look like candidates) down to **exactly the true clock
cell** by turn 9 and stays there, and `state`/`untried here` behave
correctly (`NOVEL` on first visit, `SEEN(xN)` climbing on revisits,
`untried here` shrinking as actions get tried from a state, reaching `[]`
once a small state has been fully explored):

| | min | avg | max |
|---|---:|---:|---:|
| block size (chars) | 101 | 109.4 | 140 |
| block (tok, chars/4) | 25.2 | 27.3 | 35.0 |
| block (tok, chars/3, harness's own `_estimate_tokens`) | 33.7 | 36.5 | 46.7 |

Both well under the 120-token hard cap in every turn observed.

**Total per-turn cost** (system paragraph, resent every request exactly like
duckmod's addition was, + the block — same accounting method
`duckmod-transcripts-20260819.md` used to arrive at duckmod's own
"~450-500/turn" figure):

| | avg case | worst case seen |
|---|---:|---:|
| chars | 381 | 412 |
| tok (chars/4) | **95.3** | 103.0 |
| tok (chars/3, harness estimator) | 127.1 | 137.3 |

vs. duckmod's measured **~450-500 tokens/turn** (1,835 chars once, no
per-turn dynamic component). By the repo's usual chars/4 estimate duckv3
lands under the `<=150/turn` target with margin (95.3 avg / 103 worst-case);
by the harness's own cruder chars/3 estimator it reads higher (127-137) —
still 3.3-3.9x cheaper than duckmod, but I'm not rounding that second number
down to make the target look cleanly hit. Reporting both rather than
picking the flattering one.

System-prompt paragraph itself (`duckv3/build_notebook.py`'s
`_SYSTEM_PROMPT_ADDITION`, appended once to `STRUCTURED_RUNTIME_STATE_ADDENDUM`):
**272 chars = 68 tok (chars/4) / 90.7 tok (chars/3)** — replaces duckmod's
two long tool-doc blocks (`_HUD_PROMPT_TEXT` 812 chars +
`_PYTHON_ADDENDUM_TEXT` 1,019 chars = 1,831 chars) with one paragraph, a
**6.7x reduction** in the one-time system-prompt addition. duckv3 has no
tool-schema description to extend at all (duckmod's `_TOOL_DESC_TEXT`, 403
chars, doesn't exist here — there's no new tool).

## 6. Risk list

- **Advisory only, same risk class as duckmod's `hud_mask`.** A wrong HUD
  flag or a stale `SEEN`/`untried` reading (§3's disclosed limitation) is
  text the model can weigh against its own reading of the board — it never
  touches action selection, gameplay state, or the sandbox. Worst case it's
  a slightly wrong hint, not a crash or a corrupted game state.
- **Monkeypatch anchor is a whole *method*, not a string anchor inside a
  larger string.** Unlike duckmod's `assert bootstrap.count(anchor) == 1`
  pattern (which fails loudly if upstream text shape drifts), this patch
  replaces `ToolAgent._build_user_prompt` outright — if a future upstream
  bundle renames or restructures that method, the patch would either raise
  `AttributeError` at `install_patch` (loud, safe) or silently miss wrapping
  it if the method still exists under the same name but with a different
  signature (the `**` keyword-only args here mirror the current signature
  exactly, `tool_agent.py:1161-1169`, and `verify_notebook.py` executes the
  patch against the live bundle every time it's run, so any drift is caught
  before push the same way duckmod's build discipline calls for).
- **O(1)-amortized incremental design trades a small, disclosed, self-healing
  accuracy cost (§3) for avoiding an O(N²)-over-the-game cost.** Not
  reconsidered without a measured case where it matters — no such case was
  observed in the 60-turn synthetic drive.
- **Unlike duckmod, this fork has never scored on Kaggle.** Same posture as
  duckmod's own risk list: the change is additive-and-ignorable in the
  sense that no existing action-selection code path is touched (only prompt
  text), so the failure mode to watch on the actual run is an exception
  during `install_patch`/`_build_user_prompt` (which would surface
  immediately, first turn, first game), not a change in play quality from a
  correct patch.
- **Not measured, and flagged rather than guessed at:** whether the model
  actually *reads and uses* the OBSERVATION block more than duckmod's
  callable API was used. This design fixes the *delivery* problem
  (0-2/2001 invocations) by construction; it does not by itself prove the
  *content* changes behavior. That is exactly the ablation
  `duckmod-transcripts-20260819.md` §4 recommended before trusting any
  score delta — same recommendation applies here, more so, since duckv3 has
  not been run at all yet.

## 7. What the main thread should push

```bash
cd duckv3
KAGGLE_API_TOKEN=$(cat ../.kaggle/access_token) kaggle kernels push -p .
```

`duckv3/kernel-metadata.json` names `id: sahasawatt/taaf-duck-v3`,
`code_file: taaf-duck-v3.ipynb`, and copies `dataset_sources`/
`machine_shape`/`docker_image` unchanged from `duck/kernel-metadata.json`
(same as duckmod's) — everything duckv3 needs is embedded in the notebook
cell as a string literal (`duckv3/build_notebook.py` embeds
`duckv3_observer.py`'s source, minus the `__main__` self-test block, exactly
the same stripping convention duckmod used), so no new dataset attachment is
required. Regenerate the notebook after any change to
`duckv3_observer.py` or the system-prompt paragraph with
`python duckv3/build_notebook.py` — it is a build artifact, never hand-edited,
same discipline this repo's CLAUDE.md states for `kaggle/my_agent.py`.
Before pushing: re-run `duckv3/verify_notebook.py` (with `PYTHONPATH`
pointed at the bundle) — it already executes the exact embedded cell-12
source against the real bundle, which is the equivalent check duckmod's own
build performed before its push.

## 8. Verification summary (Tested = N)

| Claim | Tested |
|---|---|
| `duckv3_observer.py` self-test | Yes, `python duckv3/duckv3_observer.py` |
| Generated notebook is valid JSON, only cell 12 differs | Yes, `duckv3/verify_notebook.py` |
| Every code cell's Python parses | Yes, `ast.parse` on all 17 |
| Patch applies + is idempotent against the real `tool_agent.ToolAgent` | Yes, `duckv3/verify_against_bundle.py` |
| Per-game isolation (two `ToolAgent`s, independent state) | Yes, same script |
| Exact embedded cell-12 source executes against the real bundle | Yes, `duckv3/verify_notebook.py` |
| Real system prompt + real per-turn user prompt both contain the new text | Yes, both verify scripts |
| Observation block stays under the 120-token cap | Yes, `duckv3/synthetic_drive.py`, 60-turn synthetic drive (max 46.7 tok by the harness's own estimator) |
| Total per-turn cost lower than duckmod's ~450-500 | Yes, measured 95-137 tok depending on estimator (both well under duckmod's; the stricter chars/3 estimator sits above the 150 stretch target, disclosed not rounded away) |
| An actual LLM turn reads/uses the block inside a live game | **UNVERIFIED** — no GPU/Kaggle env available locally; not run at all yet, unlike duckmod which had a prior scored run to diff against |
