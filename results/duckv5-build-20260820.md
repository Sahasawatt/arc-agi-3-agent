# duckv5 build: accumulating world model + auto-injected transition digest/reset banner

Output: `duckv5/duckv5_worldmodel_accum.py`, `duckv5/duckv5_digest.py`,
`duckv5/build_notebook.py`, `duckv5/verify_against_bundle.py`, `duckv5/verify_notebook.py`,
`duckv5/taaf-duck-v5.ipynb`, `duckv5/kernel-metadata.json` (id `sahasawatt/taaf-duck-v5`).
`duck/**`, `duckmod/**`, `duckv3/**`, `duckv4/**` untouched (read-only reference).
`environment_files/` was not read, grepped, or listed at any point.

v5 = **duckmod's own patch, verbatim, plus three new patches stacked on the same cell** --
not a replacement of duckmod (which is how duckv3/duckv4 built off duckmod's notebook: both
reused only the notebook *shell*, cell 12 fully overwritten). duckv5's cell 12 is duckmod's
generated cell-12 source followed directly by the three new patches below, all against the
same already-imported `tool_agent` module. Nothing from v4 (the world-model char cap and the
budget reallocator) -- R7 measured the cap never fires under the harness's own design and the
reallocator's measurable effect this run bought nothing (`results/wayfinder/R7-v4-postmortem.md`).

## 0. Why this design, in one line each

R7 sec5 measured **why** duckv4's cap never fired: `_update_summarized_knowledge_from_assistant`
(tool_agent.py:1105-1111) **overwrites** each field every turn, so the field the cap protects
never grows past ~3,501 chars in a real 25-game run -- 5x under the 6,000-char cap. Feature 1
patches the merge step itself so growth is real, and now the cap matters.

R6 measured two structural gaps across the 9 worst-thrashing games: **Mode 2** (anti-loop
tooling offered every prompt, called 0/0 times in all 9) and **Mode 3** (a silent GAME_OVER
erasing 75-300 actions of progress, confirmed in 6/9, inferred in a 7th). Features 2 and 3 fix
both the same way duckv3 already fixed "the model doesn't call the HUD/TransitionGraph tool":
the harness computes and shows; nothing new to call.

## 1. Feature 1 -- accumulating world model

**Patch target**: `ToolAgent._update_summarized_knowledge_from_assistant`
(`duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1105-1111`), an **instance
method** (unlike duckv4's target, `_extract_labeled_blocks`, a plain module-level function) --
patched at the class level, the same mechanics duckv3 used for `_build_user_prompt`.

```python
def _update_summarized_knowledge_from_assistant(self, content: str) -> None:
    note = _extract_scientist_note(content)
    if not note:
        return
    for key, value in note.items():
        if value:
            self._summarized_knowledge[key] = value   # <-- overwrite; this is what's replaced
```

The replacement calls the module's own `_extract_scientist_note` (unchanged; still lives at
tool_agent.py:263) and, for every non-empty field, **appends** a turn-stamped paragraph instead
of overwriting: `_accumulate(existing, value, turn_label)`
(`duckv5/duckv5_worldmodel_accum.py:47-59`). Rules, in order:

1. **Exact-duplicate dedup**: if `value` already occurs verbatim anywhere in the field, skip --
   a model re-stating an unchanged finding doesn't grow the field for free.
2. **Turn stamp**: `f"[{turn_label}] {value}"`, `turn_label` from a per-instance counter
   (`self._duckv5_turn`) incremented once per call -- each call corresponds to exactly one model
   turn that wrote assistant prose (the two call sites, tool_agent.py:1896/1930, are mutually
   exclusive per `analyze()` invocation: no-tool-call branch vs. tool-call branch).
3. **Bound + oldest-first trim**: `FIELD_CAP_CHARS = 7000` (mid the brief's 6,000-8,000 range,
   flat across all 7 fields -- same simplification duckv4's cap made, since R2 doesn't cite
   per-field sizes for this harness). Trimming keeps the newest text, drops the oldest, and
   prepends `[compacted: N chars dropped]` -- same tail-keep discipline as
   `duckv4/duckv4_worldmodel_cap.py`.

**Left untouched, on purpose**: `_update_summarized_knowledge_from_step_summary`
(tool_agent.py:1113-1126), which wipes all 6 non-cross-level fields to `""` whenever the last
action sequence hit `level_transition`, `run_complete`, or `game_over`. This is a *different*
call site (fires from inside `_run_python_tool`, tool_agent.py:1584, right after an action
executes -- before the *next* turn's assistant-text merge, never interfering with this turn's).
Leaving it alone means accumulation is scoped to one life/level by the harness's own existing
design, not compounding indefinitely across the whole game -- which also bounds the practical
cost of feature 1 well under the worst case (sec5).

## 2. Feature 2 + 3 -- transition digest and reset banner

**Patch target**: `ToolAgent._build_user_prompt`
(`duck/bundle/src/ARC3-Inference/inference/agent/tool_agent.py:1161-1256`) -- same function,
same class-level monkeypatch mechanics duckv3 used (`results/duckv3-build-20260819.md` sec1-2,
explicitly the closest prior art per the brief). `duckv5/duckv5_digest.py` wraps it: calls the
original to get the base prompt, appends a `TransitionDigest.render(...)` block, returns the
concatenation. One `TransitionDigest` per `ToolAgent` **instance**
(`self._duckv5_digest`, lazily created) -- the same instance-attribute-not-dict pattern duckv3
chose specifically so no state is ever keyed on a session/agent object (`HarnessSolver` builds
one fresh `ToolAgent` per `(game, index)`, per `results/duckv3-build-20260819.md` sec1), which
sidesteps the `_HarnessGameSession`-unhashable trap R7's world-model-cap section warns about --
there is no registry here to key at all.

### 2a. The digest

Walks `history_entries` incrementally (a `_processed_len` pointer, never re-scans from scratch --
same O(1)-amortized design duckv3's `GameObservation._ingest` uses) and classifies each
consecutive `(action, before-frame, after-frame)` transition as `changed` / `noop` / `level_up` /
`reset`. Tracked, all server-side, no callable API:

- **Per-action counts** `tried/changed/noop` (`reset` outcomes fold into the noop bucket for
  this tally -- a documented simplification, `duckv5_digest.py:141`).
- **Level milestones**: `level_first_seen[level] -> action index`, rendered as `L1@a0, L2@a43, ...`
  (capped to the last 6 levels shown).
- **Last 5 actions with outcomes**: `UP:changed, UP:noop, DOWN:changed, ...`.

Rendered as a fixed ~9-15-line block (measured worst case with 8 distinct actions and 4 levels:
**14 lines, 382 chars**), well inside the brief's ~15-25-line / ~25-line budget.

### 2b. The reset banner -- and the design bug this caught before it shipped

The brief said "detect a GAME_OVER / level-regression / score-reset between consecutive
frames." An **explicit level regression** (`cur.level < prev.level`) is checked first and is
always a reset. But R6's own header line is: **"All 9 games in this report were stuck on level
1 for the entire run."** A pure level-regression detector can *never* fire on exactly the 9
games this feature exists to fix, because the level number has nowhere to fall from. R6's own
measured signature, quoted twice verbatim ("reset the board to the exact turn-1 layout"), is
the real signal: **the grid reverts to the state it was in when the current level was first
entered, after having visibly diverged from it.**

`TransitionDigest` records, per level, the grid at the moment that level was first observed
(`level_entry_grid`, alongside the existing `level_first_seen` action-index map). A transition
at the *same* level is a reset if the current grid equals that level's entry grid, the
*previous* grid did not (so this is a genuine reversion, not "never left the start"), and at
least `MIN_ACTIONS_SINCE_LEVEL_ENTRY_FOR_RESET = 3` actions have passed since entering the level
(a floor against a trivial one-move-then-back oscillation reading as a false reset -- R6's real
resets erase 75-300 actions, two orders of magnitude above this floor).

There is no field for "score" anywhere in the harness's `Frame` dataclass
(`inference/agent/runtime_state.py:16-20`: `grid`, `step`, `level` only) -- "score-reset" from
the brief is covered by the level-1-stuck grid-revert signature above, not by a separate score
read, since no score is available at this layer.

**Single-shot banner**: detection happens during `_ingest` (as part of assembling THIS turn's
block); the banner text is buffered (`self._pending_reset`) and consumed-and-cleared the moment
`render()` returns it, so it appears on exactly the observation immediately after the reset was
ingested and never again. Text: `"!!! GAME RESET: level went X->Y, N actions of progress lost;
your position/state assumptions are now invalid !!!"`, `N` = actions taken since the last reset
(or game start).

## 3. Assembly: duckmod + duckv5, one cell, no reallocator, no v4 code

`duckv5/build_notebook.py` reads duckmod's already-generated `taaf-duck-mod.ipynb` cell 12
verbatim, then appends (same cell, both `exec`'d against the already-imported `tool_agent`
name):

1. `duckv5_worldmodel_accum.py`'s source (`exec(..., globals())` -- shares the cell's top-level
   namespace, matching duckv4's pattern for its first patch).
2. `duckv5_digest.py`'s source (`exec(..., _duckv5_digest_ns)` -- **isolated namespace**, because
   both modules define an `install_patch` name; executing into a private dict avoids the name
   collision the same way duckv4's `build_notebook.py` isolated its reallocator's exec from its
   world-model-cap's exec).
3. One short system-prompt addition (356 chars) appended to `tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM`
   -- **not** `inference.agent.prompts.STRUCTURED_RUNTIME_STATE_ADDENDUM` (the from-import trap
   `results/duckmod-build-20260818.md` sec2.3 documents: `tool_agent.py` does
   `from inference.agent.prompts import STRUCTURED_RUNTIME_STATE_ADDENDUM, ...`, copying the
   reference into `tool_agent`'s own module namespace at import time, so `_build_system_prompt`
   resolves the bare name against `tool_agent.__dict__` and patching `prompts.X` after import
   would silently do nothing. Confirmed working end-to-end in sec5 below, not just asserted.)

`compete.py`/cell 14 (game-list construction, `n_passes`, `bm.run(...)`) is untouched by, and
has no ordering interaction with, either patch -- both target only `tool_agent.ToolAgent`
methods, and cell 12 (where both install) runs after `bm`/`bm.solver` are unpickled and strictly
before cell 14 builds the game list, the same timing duckmod/duckv3/duckv4 already established.
No solver/reallocator code exists in v5 at all.

Diffed against duckmod's own notebook: **only cell 12 differs** (16/17 cells byte-identical),
and cell 12 itself is asserted (in `verify_notebook.py`) to `startswith` duckmod's own cell-12
text verbatim before the duckv5 additions -- proving this is a stacked layer, not a silent
replacement, the way duckv3/duckv4 both were relative to their own bases.

## 4. Injected-block token-cost estimate

| Item | Chars | Tok (chars/4) | Tok (chars/3, harness's own `_estimate_tokens`) | Frequency |
|---|---:|---:|---:|---|
| duckv5 system-prompt addition | 356 | 89.0 | 118.7 | once, resident forever (never evicted, tool_agent.py:1682) |
| PROGRESS DIGEST block, worst case measured (8 actions, 4 levels) | 382 | 95.5 | 127.3 | every turn |
| Reset banner (added on top of the digest block) | ~150 | ~37.5 | ~50 | one turn only, right after a reset |
| Accumulated world-model field, per field, hard cap | 7,000 | 1,750 | 2,333 | asymptotic ceiling, one field, one life |
| All 7 fields simultaneously at cap (absolute worst case) | 49,000 | 12,250 | 16,333 | never observed; see below |

The digest+banner numbers are directly comparable to duckv3's own measured **95-137 tok/turn**
(`results/duckv3-build-20260819.md` sec5) -- same order of magnitude, same design discipline.

The world-model cap is a **backstop, not a typical operating point**. R7 measured, across a real
25-game run with the harness's *unpatched* (overwrite) behavior: 692 extracted label blocks
total, **p50 = 99 chars, p99 = 505 chars, max = 3,501 chars** (a single block, one turn), and
**77.1% of all turns wrote zero assistant prose at all**. Under accumulation, a realistic single
life with a dozen prose-bearing turns before the next level-transition/game-over wipe (sec1,
untouched clearing behavior) lands in the low thousands of chars per field for most games --
the 7,000-char cap only bites in the pathological case of a life that both survives a long time
*and* writes substantial new (non-duplicate) prose every turn, which is exactly the failure mode
worth capping. The 49,000-char all-fields-maxed number is a genuine upper bound, never measured,
and is disclosed rather than rounded away -- flagged as an open risk in sec6.

## 5. Verification (Tested = N, `Desktop\arc-agi-3-agent\.venv` has the bundle's `requests`
dependency; PYTHONPATH points at both bundle source roots per this repo's CLAUDE.md)

```bash
PYTHONPATH="duck/bundle/src/ARC3-Inference;duck/bundle/src/tufa-arc-agi-framework/src" \
    ./.venv/Scripts/python.exe duckv5/verify_against_bundle.py
PYTHONPATH="duck/bundle/src/ARC3-Inference;duck/bundle/src/tufa-arc-agi-framework/src" \
    ./.venv/Scripts/python.exe duckv5/verify_notebook.py
```

1. **py_compile + notebook JSON parses + only the customization cell differs.**
   `python -m py_compile` on all 5 `.py` files: clean. `json.load` on both notebooks: valid,
   17 cells each. Cell-by-cell diff: only cell 12 differs (16/17 identical) --
   `verify_notebook.py`. `ast.parse` on every code cell of the generated notebook and on both
   standalone modules: clean.
2. **Patch-target existence asserts against the real bundle.**
   `hasattr(tool_agent.ToolAgent, "_update_summarized_knowledge_from_assistant")`,
   `callable(tool_agent._extract_scientist_note)`, and
   `hasattr(tool_agent.ToolAgent, "_build_user_prompt")` all asserted against the actual imported
   module before either patch installs -- `verify_against_bundle.py`.
3. **Mock dry-tests** (each module's own `_demo()`, run via `python duckv5/duckv5_*.py`):
   - (a) accumulation: three turns of field updates accumulate (all three turn-stamped paragraphs
     present), an exact-duplicate repeat is deduped (field unchanged), and trimming past a small
     test cap drops the oldest finding while the newest survives with a `[compacted: ...]` marker.
   - (b) digest: a fake 60-action/8-action-name/4-level stream renders a block whose per-action
     counts and level milestones are asserted exactly; block length asserted `<= 25` lines in
     every case exercised (worst case measured 14).
   - (c) reset banner, **two shapes**: (c1) an explicit level regression (2->1) fires the banner
     on exactly the next render and never again; (c2) **the motivating case** -- a board that
     stays at level 1 the whole time (matching R6's own "stuck on level 1" finding) diverges from
     its entry grid over 4 actions, then reverts to that exact entry grid -- banner fires with the
     correct action-loss count ("4 actions of progress lost") and, again, exactly once. Two
     false-positive guards are also asserted: a board that never left its entry state is not
     flagged, and an immediate one-move-then-back oscillation (2 actions since entry, under the
     3-action floor) is not flagged either.
4. **Negative control per patch, plus restore**, against the real bundle
   (`verify_against_bundle.py`): a `ToolAgent`-shaped fake class missing the target method raises
   `AttributeError` for both `install_patch` calls (proves the check reads the real attribute
   rather than assuming it exists); immediately after, a fresh real `tool_agent.ToolAgent`
   instance is patched and exercised again, confirming the failed attempt against the unrelated
   fake module left the real module's behavior untouched. Each standalone module's own `_demo()`
   repeats the same negative-control-then-restore shape on a self-contained fake module.
5. **Real-bundle smoke** (`verify_notebook.py`): the *exact embedded* cell-12 source (not the
   standalone modules) is `exec`'d against the real, imported bundle in one call -- applies
   duckmod's own sandbox splice AND both duckv5 patches together, matching what a Kaggle kernel
   actually runs. Asserts: `python_tool_sandbox._SANDBOX_BOOTSTRAP` grows (duckmod's splice still
   ran), `tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM` grows (both additions landed), all three
   patch markers (`_duckv5_accum_patched`, `_duckv5_digest_patched`, and duckmod's own) are set,
   a real `ToolAgent`'s `_system_prompt` contains both duckmod's `hud_mask(history)` doc text and
   duckv5's `PROGRESS DIGEST` paragraph, a real per-turn `_build_user_prompt` call produces a
   synthetic observation containing the digest block with correct level milestones (`L1@a0`,
   `L2@a2` on a fabricated level-up), and the accumulate patch, reached only through the exec'd
   cell (not imported directly), correctly accumulates two turns into one field.

Full transcript of both verify runs, tail:

```
ALL CHECKS PASSED          # verify_against_bundle.py
...
ALL CHECKS PASSED          # verify_notebook.py
```

**What could NOT be verified locally, same reason as every prior build report in this
sequence**: no Kaggle GPU/vLLM environment available in this sandbox, so no live LLM turn.
Everything short of an actual model call is verified against the real source tree.
**UNVERIFIED**: an actual LLM turn reading the accumulated world model, the PROGRESS DIGEST
block, or the reset banner inside a live game; whether the model's behavior actually changes as
a result (same caveat duckv3's build report raised for its own observation block -- this design
fixes *delivery*, R6's Mode 1/2/3, by construction, and does not by itself prove *content*
changes behavior).

## 6. Risk list

- **World-model growth is now real, and its aggregate cost across all 7 fields is unmeasured in
  practice** (sec4). The per-field 7,000-char cap is a backstop sized from the brief's suggested
  range, not from a distribution measured on *accumulating* text (R7's 692-block stats describe
  the old overwrite behavior). If a real run shows one or two fields dominating growth, narrow
  those specifically rather than lowering the flat cap for all seven.
- **Reset detection is advisory, same risk class as every prior duckmod/duckv3/duckv4 addition**:
  a false-positive banner (a legitimate exact revisit to a level's own entry state, without an
  actual reset) is text the model can weigh against its own reading of the board -- it never
  touches action selection or game state. The two documented guards (must have diverged first;
  3-action floor) cut the most obvious false-positive shapes but are heuristic, not exhaustive.
- **`_ensure_session` resets `self._summarized_knowledge` (tool_agent.py:984) but not our own
  `_duckv5_turn`/`_duckv5_digest` instance attributes**, if a single `ToolAgent` were ever reused
  across more than one `state_path` runtime dir. Not a new gap -- duckv3's `_duckv3_observation`
  carries the identical exposure and was accepted on the same grounds
  (`results/duckv3-build-20260819.md` sec1: `HarnessSolver._make_analyzer` constructs a fresh
  `ToolAgent()` per `(game, index)`, so this path is not expected to be hit in practice). The
  digest module does add one defensive guard beyond duckv3's precedent: if `history_entries`
  ever shrinks between calls (a proxy for "this must be a new session"), `TransitionDigest`
  resets all its own counters rather than reporting stale totals against fresh history.
- **Anchor risk is lower than duckmod's own splice, higher than a pure string check.** Both
  patches replace a whole method (`_update_summarized_knowledge_from_assistant`,
  `_build_user_prompt`) rather than splicing into a string anchor -- if a future upstream bundle
  renames either method, `install_patch` raises `AttributeError` immediately (loud, safe,
  verified in sec5 item 4) rather than silently no-op'ing. A signature change that keeps the same
  name would not be caught until `verify_notebook.py`'s real-bundle smoke is re-run before push
  (same caveat duckv3's own risk list states for its identical monkeypatch shape).
- **Unlike duckmod, this fork has never scored on Kaggle.** Same posture as every prior build
  report in this sequence: the change is additive to duckmod's already-scored baseline (nothing
  about action selection, HUD masking, or the callable TransitionGraph tool is touched), so the
  failure mode to watch for on the actual run is an exception during `install_patch`/
  `_build_user_prompt`/`_update_summarized_knowledge_from_assistant` (surfaces immediately, first
  turn, first game), not a change in play quality from a correct patch.
- **Not measured, flagged rather than guessed at**: whether the model actually reads and acts on
  the accumulated world model, the digest, or the reset banner more than it called duckmod's own
  callable tools (0-2/2,001 invocations, per `duckmod-transcripts-20260819.md`). This design
  fixes the *delivery* problem R6 measured (Mode 1: frozen/empty field; Mode 2: 0/0 anti-loop
  calls; Mode 3: silent resets) by construction. It does not by itself prove the *content*
  changes behavior -- an ablation run (v5 vs. duckmod baseline, same 25 games) is the next step
  before attributing any score delta to any one of the three features individually.

## 7. What the main thread should push (NOT done by this build -- ANTI-GOALS)

```bash
cd duckv5
KAGGLE_API_TOKEN=$(cat ../.kaggle/access_token) kaggle kernels push -p .
```

Mirrors duckmod/duckv3/duckv4's own push instructions. `duckv5/kernel-metadata.json` names
`id: sahasawatt/taaf-duck-v5`, `code_file: taaf-duck-v5.ipynb`, and copies
`dataset_sources`/`machine_shape`/`docker_image` unchanged from `duckmod/kernel-metadata.json` --
everything v5 needs is embedded in the notebook cell as string literals, same as every prior
fork in this sequence. Not run as part of this build (explicit anti-goal: no Kaggle/git push).

## 8. Verification summary (Tested = N)

| Claim | Tested |
|---|---|
| `duckv5_worldmodel_accum.py` self-test (accumulate, dedup, trim, negative control + restore) | Yes, `python duckv5/duckv5_worldmodel_accum.py` |
| `duckv5_digest.py` self-test (tallies, level milestones, level-regression reset, stuck-at-L1 grid-revert reset, 2 false-positive guards, action-name normalize, shape-mismatch safety) | Yes, `python duckv5/duckv5_digest.py` |
| Both modules parse (`ast.parse`) and compile (`py_compile`) | Yes |
| Generated notebook is valid JSON, only cell 12 differs from duckmod's | Yes, `duckv5/verify_notebook.py` |
| Cell 12 is duckmod's own cell 12 verbatim, plus duckv5's additions appended (stacked, not replaced) | Yes, `startswith` assertion, `verify_notebook.py` |
| Patch targets exist on the real bundle before patching | Yes, both verify scripts |
| Both patches apply, are idempotent, against the real `tool_agent.ToolAgent` | Yes, `verify_against_bundle.py` |
| Negative control (missing attribute) fails loudly, real module still works after (restore) | Yes, both verify scripts, both patches |
| Per-instance isolation (two `ToolAgent`s, independent digest state) | Yes, `verify_against_bundle.py` |
| The exact embedded cell-12 source executes against the real bundle, all 3 patch markers set | Yes, `verify_notebook.py` |
| Real system prompt contains both duckmod's and duckv5's additions (from-import trap avoided) | Yes, `verify_notebook.py` |
| Real per-turn user prompt contains the digest block; real assistant-text merge accumulates, both reached only through the exec'd cell | Yes, `verify_notebook.py` |
| Digest block stays under ~25 lines | Yes, worst case measured 14 lines / 382 chars |
| An actual LLM turn reads/uses any of the three features inside a live game | **UNVERIFIED** -- no GPU/Kaggle env available locally |
