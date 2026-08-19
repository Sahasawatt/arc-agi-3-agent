# duckv4 build: world-model field cap (D1a) + depth-aware time reallocation (D1b)

Output: `duckv4/duckv4_worldmodel_cap.py`, `duckv4/duckv4_reallocator.py`,
`duckv4/build_notebook.py`, `duckv4/verify_against_bundle.py`,
`duckv4/verify_notebook.py`, `duckv4/taaf-duck-v4.ipynb`,
`duckv4/kernel-metadata.json`. `duck/**`, `duckmod/**`, `duckv3/**` untouched
(read-only reference, as instructed).

## 0. What was built and why this base

Two independent levers, both patched onto the **ORIGINAL** duck notebook
(`duck/tufa-labs-duck-harness-june-30-milestone-winner.ipynb`), not stacked on
duckmod or duckv3:

- **(a) World-model field cap** — R2's #1-ranked lever: every one of the 7
  labeled world-model fields (`World model:`, `Goal model:`, `Action model:`,
  `Recent findings:`, `Open questions:`, `Plan:`, `Cross-level notes:`) is
  extracted with `max_chars=None` (unbounded) and re-injected **verbatim into
  every subsequent turn's prompt** for the rest of a level — "the single
  biggest uncapped, silently-compounding prompt-bloat surface in the
  harness" (`results/wayfinder/R2-levers.md` §(b)).
- **(b) Depth-aware time reallocation** — R1 found all 25 games in the
  measured commit run hit the *same* flat `max_runtime_s_per_game` clock and
  none crashed or won; the run's best game (`ft09`, score 28.57) was 2
  actions into level 4 when its own clock cut it off, while 14 of 25 games
  were "thrashing" (≥2x a human's action budget on their current level, 0
  progress) on the identical clock. R2 §(h) confirms no scoring-aware
  scheduling exists anywhere in the harness.

**Why the original base, not duckmod/duckv3**: ANTI-GOALS parks the
REPL-tool-injection lever (duckmod's `hud_mask`/`TransitionGraph`, measured
0-2 invocations across 2,001 turns per `duckmod-transcripts-20260819.md`).
duckv3's auto-pushed observation block is not a REPL tool, but R5's own
paired t-test found duck-v3 − baseline is **not significant** (p=0.314,
mean Δ −0.44) — stacking two new, independently-uncertain levers under an
already-uncertain third design would make any future single-pass score
delta unattributable to any one change, directly against this repo's own
measurement discipline (`CLAUDE.md`: "One change at a time. Two at once and
a revert tells you nothing."). Building duckv4 as a clean fork of the
original keeps a future A/B (`duck` vs `duckv4`) interpretable.

## 1. Lever (a): world-model field cap

**Patch point**: `tool_agent._extract_labeled_blocks`
(`inference/agent/tool_agent.py:226-260`) — the parser both
`_extract_scientist_note` (`:263-296`, its only caller) invokes. The
unbounded call is the `_normalize_summary_text(..., max_chars=None)` at
`:257`. `_extract_scientist_note`'s result is merged into
`ToolAgent._summarized_knowledge` by
`_update_summarized_knowledge_from_assistant` (`:1105-1111`, full
replace-by-key, not append) and re-rendered into **every** following user
turn by `_summarized_knowledge_lines` (`:1128-1146`), inserted at
`_build_user_prompt:1236`.

**Mechanism**: same-module patch, not a from-import copy. `_extract_labeled_blocks`
and its only caller live directly in `tool_agent.py`, so `_extract_scientist_note`'s
call to it resolves the bare name against `tool_agent.__dict__` at *call time* —
replacing the module attribute (`tool_agent._extract_labeled_blocks = wrapped`)
is picked up by the original, unpatched `_extract_scientist_note` without also
patching that function. Same class of finding duckmod's build report
documents for its splice anchors and R5 documents for
`_LOCAL_ANALYZER_SEED`/`_LOCAL_ANALYZER_TEMPERATURE` — verified directly
against the real bundle (§3), not just asserted.

**Cap chosen**: `FIELD_CAP_CHARS = 6000`, flat across all 7 fields (and the 3
alias labels `Hypothesis`/`History check`/`Next test` `_extract_scientist_note`
falls back to). **Conservative, not measured** — R2 documents the mechanism
but does not cite per-field token/char sizes for this harness family; 6000
chars (~1.5–2k tokens by the harness's own `len/3` estimator,
`tool_agent.py:462-467`) sits mid the brief's suggested 4-8k conservative
range. A flat cap (not per-field) was chosen for surgical minimalism — narrow
per-field only once real transcripts (a future commit run's `benchmark.json`
transcripts) show one field dominating growth.

**Compaction shape**: deterministic **tail-keep** (drop the oldest/leading
text, keep the newest `cap` chars) with a `"[compacted: N chars dropped]"`
marker — the brief's stated fallback, chosen explicitly over an LLM
self-compression call: a compression call would add its own latency to the
*same* per-action-latency problem this lever exists to fix (R1: 19-233s/action
across 25 otherwise-identical games is the harness's #1 measured failure).
`# ponytail:` comment in the source names this tradeoff and its upgrade path.

## 2. Lever (b): depth-aware time reallocation

**Patch points**: `_HarnessGameSession.runtime_limit_reached`
(`inference/framework/solver.py:212-217`) and `.timing_payload`
(`:219-225`). `should_stop` (`:246-261`) calls `runtime_limit_reached`
directly, so patching it alone changes when a game's loop stops.
`request_timeout_seconds` (`:227-244`) calls `self.timing_payload()` for its
own remaining-time candidate — patching `timing_payload` alone is therefore
enough to make the per-LLM-call timeout clamp respect the adjusted deadline
too, without touching `request_timeout_seconds` itself (verified: it is
never referenced by name in `duckv4_reallocator.py`).

`HarnessSolver.max_runtime_s_per_game` (`solver.py:745`) and `.concurrency`
(`:746`) are **read, never written** — R2 flags both as LOAD-BEARING for the
9h envelope (their product across `ceil(games/concurrency)` waves is the
*entire* enforcement mechanism, since the soft-deadline graceful-drain path
is dead code on `TRUE_SUBMISSION`). Instead, each `_HarnessGameSession` gets
an *effective* deadline, `solver.max_runtime_s_per_game + delta`, computed by
a shared `BudgetReallocator`.

### The safety invariant, and why it is the design's centerpiece

`BudgetReallocator` funds every extension from a pool that only shrink
harvests:

1. Every ~120s (`REALLOC_INTERVAL_S`, throttled, thread-safe via a lock,
   registered sessions held in a `weakref.WeakKeyDictionary` so finished
   games don't leak), each tracked session is classified: **thrashing**
   (0 levels completed, ≥150 actions taken — `THRASH_ACTION_FLOOR`) or
   **leveling** (levels-completed count increased since the last tick).
2. Every thrashing session is shrunk by up to 300s (`SHRINK_STEP_S`), never
   below 50% of its *own* original budget (`MIN_BUDGET_FRACTION`); the
   amount actually shrunk is added to a shared pool.
3. Every leveling session is granted up to 300s (`EXTEND_STEP_S`) **funded
   strictly from that pool** — a grant can never exceed what has been
   harvested — subject to two hard ceilings: `MAX_EXTENSION_PER_GAME_S=600`
   per session, and `TOTAL_POOL_CAP_S=600` cumulative across the **entire
   run**, forever.

This makes `sum(all session deltas) <= 0` a *provable* invariant (asserted
directly in the self-test, not just argued): a grant step is always
`min(..., self._pool, ...)`, so the pool never goes negative, so
`total_granted <= total_shrunk` at every instant, so the sum of extensions
can never exceed the sum of shrinks. Individually, no session's deadline can
ever exceed `original + 600s`, and the `TOTAL_POOL_CAP_S=600` ceiling bounds
the *system-wide* worst case regardless of how many games level up in a run —
a deliberately small, conservative number against the ~720s of slack R2
measured between the current 4-wave arithmetic (`4 × 7920s = 31680s`) and the
~9h/32400s Kaggle budget. **This number is chosen, not derived from a real
hidden-game run** — see §5 risks.

**Why extension is capped so conservatively while shrink is comparatively
generous**: in the local single-wave commit-run regime (`concurrency=28 ≥
games=25`), extending one session's deadline directly extends the *whole
run's* wall clock (nothing is queued behind it, so total time = max over all
effective deadlines). In the real hidden-game run's pipelined regime
(`concurrency=28 < games`), delaying one session's finish can, in the worst
case, delay whichever queued game was waiting on its slot, and that delay can
in principle propagate along the scheduler's fill order. Neither this repo
nor the sandbox this build ran in can execute the real scheduler to measure
that propagation, so the design treats "how much total wall-clock delay can
ever be introduced" as a single global knob (`TOTAL_POOL_CAP_S`) capped well
inside the measured local-regime slack, rather than trusting an unverified
scheduling-theory argument about the multi-wave case.

## 3. Verification (all four items, exact output pasted)

### 3.1 Syntax — every `.py` compiles, notebook JSON parses

```
$ ./.venv/Scripts/python.exe -m py_compile duckv4/duckv4_worldmodel_cap.py duckv4/duckv4_reallocator.py duckv4/build_notebook.py duckv4/verify_against_bundle.py duckv4/verify_notebook.py
(no output = success)
```

`verify_notebook.py` additionally `json.loads`'s both notebooks and
`ast.parse`'s every code cell (output in §3.4 below).

### 3.2 Patch-target existence, against the real imported bundle

`duckv4/verify_against_bundle.py` imports `inference.agent.tool_agent` and
`inference.framework.solver` directly from `duck/bundle/src/...` and asserts
each patch target exists with the expected shape before touching anything —
`tool_agent._extract_labeled_blocks`/`_extract_scientist_note` are callable;
`_HarnessGameSession` has `runtime_limit_reached`/`timing_payload`;
`HarnessSolver.__dataclass_fields__` still contains `max_runtime_s_per_game`
(read-only contract, not something this build renames or removes).

Real environment note: `inference.framework.solver` imports `taaf.game`,
whose package `__init__.py` eagerly imports `taaf.diagnostics`, which needs
`imageio`/`scipy` — transitive deps of the harness's own diagnostics
rendering, unrelated to anything duckv4 adds, and not present in this repo's
`.venv` (duckmod/duckv3 never triggered this import chain since neither
touches `solver.py`). Resolved with `uv run --with imageio --with scipy`
(ephemeral, does not modify this repo's `pyproject.toml`/lockfile).

### 3.3 Mock dry-tests (both modules' own `__main__` self-tests)

```
$ ./.venv/Scripts/python.exe duckv4/duckv4_worldmodel_cap.py
duckv4_worldmodel_cap self-test OK

$ ./.venv/Scripts/python.exe duckv4/duckv4_reallocator.py
duckv4_reallocator self-test OK
```

Covered by the world-model self-test: under-cap text passes through
unchanged; exactly-at-cap text is not marked; a field that blows the cap gets
the `"[compacted: N chars dropped]"` marker and keeps the **tail** (not the
head) of the original text, with the dropped-prefix content verifiably
absent; an empty field never crashes or grows a marker; `install_patch`
against a fake module caps a long field and passes a short one through
unchanged; re-applying `install_patch` is idempotent (no double-wrap).

Covered by the reallocator self-test: a fake game-state table with one
leveling session (ft09-shaped: levels 3→4, 44 actions), one thrashing
session (m0r0-shaped: 0 levels, 418 actions) and one untouched fair session —
after a forced tick, the leveling session's delta is `> 0`, the thrashing
session's delta is `< 0`, the fair session's delta is exactly `0`, and
`total_delta() <= 0` (the safety invariant, asserted directly). A ten-tick
stress drive with one repeat-leveling session funded by five thrashing
sessions proves both hard caps (`MAX_EXTENSION_PER_GAME_S`,
`TOTAL_POOL_CAP_S`) actually bind and the invariant holds every single tick,
not just once. A session whose `game`/`action_count` accessors raise
(simulating a mid-transition read) does not crash a tick and does not drift
its own budget — Principle 5 failure-awareness, tested directly.

### 3.4 Negative controls (both modules, twice each — synthetic and real)

Synthetic (inside each module's own self-test): pointing `install_patch` at
an object missing the attribute being patched (`_extract_labeled_blocks` for
the world-model cap; `_HarnessGameSession` for the reallocator) raises
`AttributeError` — proving the "patch applied" assertions elsewhere in the
same self-test are not vacuously true.

Against the real bundle (`verify_against_bundle.py`, stronger than the
synthetic version — shows the *actual* unpatched harness reproduces R2's
finding, not a synthetic stand-in):

```
BEFORE patch: world_model = 85779 chars (unbounded, reproduces R2)
AFTER patch: world_model = 6033 chars (capped)
...
BEFORE patch: timing_payload remaining ~= 7920.0s (flat budget)
AFTER patch: timing_payload still reads ~= 7920.0s (no adjustment yet, correct)
...
negative control: a module missing _HarnessGameSession fails loudly
ALL CHECKS PASSED
```

(A 2,000-line synthetic `World model:` block against the real, **unpatched**
`tool_agent._extract_scientist_note` really does come back at 85,779 chars —
the negative control's precondition holds against the live harness, not just
a mock.)

### 3.5 Notebook build + full end-to-end verification against the real bundle

```
$ ./.venv/Scripts/python.exe duckv4/build_notebook.py
wrote C:\Users\Vampi\Desktop\projects\arc-agi-3-agent\duckv4\taaf-duck-v4.ipynb (48215 bytes)

$ PYTHONPATH="duck/bundle/src/ARC3-Inference;duck/bundle/src/tufa-arc-agi-framework/src" \
    uv run --with imageio --with scipy python duckv4/verify_notebook.py
both notebooks parse as valid JSON, 17 cells
only cell 12 differs from the original notebook (16/17 identical)
every code cell's Python parses (ast.parse)
cell 12 source itself parses (ast.parse)
duckv4: patched tool_agent._extract_labeled_blocks (worldmodel source 6026 chars), patched solver._HarnessGameSession.runtime_limit_reached/timing_payload (reallocator source 13717 chars)
executed embedded cell-12 source against the real bundle: both patches applied
real tool_agent._extract_scientist_note now caps a long field to 6032 chars
real solver._HarnessGameSession.timing_payload reads through the reallocator
ALL CHECKS PASSED
```

This executes the **exact** embedded cell-12 source (as a Kaggle kernel
would run it), not a copy, against the real, imported bundle modules — the
same discipline duckmod's and duckv3's own builds applied.

```
$ PYTHONPATH="duck/bundle/src/ARC3-Inference;duck/bundle/src/tufa-arc-agi-framework/src" \
    uv run --with imageio --with scipy python duckv4/verify_against_bundle.py
duckv4_worldmodel_cap.py parses clean (ast.parse)
patch target tool_agent._extract_labeled_blocks exists (patch-target existence)
BEFORE patch: world_model = 85779 chars (unbounded, reproduces R2)
AFTER patch: world_model = 6033 chars (capped)
install_patch is idempotent against the real tool_agent module
duckv4_reallocator.py parses clean (ast.parse)
patch targets _HarnessGameSession.runtime_limit_reached/timing_payload exist (patch-target existence)
BEFORE patch: timing_payload remaining ~= 7920.0s (flat budget)
AFTER patch: timing_payload still reads ~= 7920.0s (no adjustment yet, correct)
install_patch is idempotent against the real solver module
negative control: a module missing _HarnessGameSession fails loudly
ALL CHECKS PASSED
```

## 4. Survives cell-14's `n_passes` overwrite pattern (R5's stated trap)

R5: `taaf/kaggle_run.ipynb`/the real notebook's cell 14 does `bm.n_passes = 1`
**unconditionally**, immediately before `await bm.run(...)`, clobbering any
`bm.n_passes = N` a customization-hook cell (12) might have set. Neither
duckv4 patch touches `bm.n_passes`, `bm.games`, or `bm.game_weights` at all —
both patches mutate **module globals** (`tool_agent._extract_labeled_blocks`,
`solver._HarnessGameSession.runtime_limit_reached`/`timing_payload`), which
persist on the module object itself regardless of what cell 14 does to `bm`.
Every `ToolAgent`/`_HarnessGameSession` constructed inside `bm.run()` (cell
14, which runs textually and temporally after cell 12) reads the
already-patched module attributes the first time it calls
`_build_system_prompt`/`_extract_scientist_note`/`runtime_limit_reached` —
same ordering argument duckmod's and duckv3's own builds made and verified.

## 5. Risk list / known unknowns (what only a real commit run can prove)

- **The 600s system-wide reallocation cap is a chosen conservative ceiling,
  not a measured one.** It is deliberately well inside the ~720s of slack R2
  computed for the *local, single-wave, 25-game* commit-run regime. Whether
  that same margin holds for the real 110-hidden-game, 4-wave, pipelined
  regime is **UNVERIFIED** — this repo cannot execute that scheduler. If a
  future commit run shows real slack is smaller than assumed, lower
  `TOTAL_POOL_CAP_S`/`MAX_EXTENSION_PER_GAME_S` before raising them.
- **`THRASH_ACTION_FLOOR=150` is a flat, ungrounded-in-per-game-baseline
  threshold**, chosen from R1's own zero-level-game action counts (34-418
  actions) rather than each game's real human baseline
  (`re_arc.dsl.precomputed_actions.metadata_baseline_actions`, found during
  this build at `duck/bundle/src/ARC3-Inference/inference/utils/rearc_baselines.py`
  but deliberately **not** wired in — it needs a `game_id`/`environments_dir`
  this patch would have to thread through from cell 14's game-list
  construction into cell 12's patch, a materially larger and riskier diff
  than "one config dict," and it is untested against the hidden competition
  game IDs). A future iteration could replace the flat floor with a real
  per-game ratio once that plumbing is justified by measured need.
- **`FIELD_CAP_CHARS=6000` is a chosen default, not measured against this
  harness's real per-field growth.** R2 does not cite per-field size
  distributions; the one real number surfaced during this build (§3.4,
  85,779 chars from a synthetic 2,000-line block) is a synthetic stress case,
  not a transcript from an actual scored run.
- **No live LLM turn has exercised either patch.** Same limitation duckmod's
  and duckv3's own build reports state: no Kaggle GPU/vLLM environment is
  available in this sandbox. Everything short of an actual model call is
  verified against the real, imported bundle source (§3); the two things
  genuinely unverified are (a) how the model's own writing behavior responds
  to a field it wrote getting compacted out from under it on a later turn,
  and (b) whether the reallocator's periodic 120s-throttled tick ever
  actually fires meaningfully inside a real ~7920s-budget game, versus being
  dominated entirely by per-action latency the way R1 measured (19-233s/action
  means very few ticks may elapse per game even over a full budget).
- **A `_HarnessGameSession`'s effective deadline can only ever change via
  `runtime_limit_reached()`/`timing_payload()` being CALLED.** Both are
  called from inside the game's own `while not self.should_stop()` loop
  (`solver.py:276`), which only advances between analyzer turns — so a
  session stuck inside one very long `analyze()` call (up to
  `analyzer_timeout=900s` per R2's load-bearing section) will not see a
  reallocation tick land until that call returns. This is a real, disclosed
  gap: the reallocator cannot preempt a call already in flight, only change
  the deadline the *next* loop iteration checks against. Not expected to
  matter given the pool cap is a fraction of one such call's own duration,
  but not measured.
- **Unlike duckmod (had a prior scored run to diff against), duckv4 has never
  scored on Kaggle.** Both patches are additive to the game-loop's own
  termination/timeout arithmetic, not to action selection — the failure mode
  to watch on an actual run is an exception surfacing at cell-12 execution
  (loud, first turn, first game) or the reallocator materially extending a
  wave's wall clock in the real pipelined regime beyond what §2's argument
  bounds (silent until a run either finishes late or gets hard-killed by
  Kaggle — the 0-score outcome Principle 5 explicitly calls out as worse
  than any inefficiency this build is trying to fix).

## 6. What the main thread should push

```bash
cd duckv4
KAGGLE_API_TOKEN=$(cat ../.kaggle/access_token) kaggle kernels push -p .
```

`duckv4/kernel-metadata.json` names `id: sahasawatt/taaf-duck-v4`,
`code_file: taaf-duck-v4.ipynb`, and copies `dataset_sources`/
`machine_shape`/`docker_image` unchanged from `duck/kernel-metadata.json` —
everything duckv4 needs is embedded in the notebook cell as string literals,
so no new dataset attachment is required. Regenerate the notebook after any
change to either module with `python duckv4/build_notebook.py` — it is a
build artifact, never hand-edited. Before pushing: re-run
`duckv4/verify_notebook.py` (with `PYTHONPATH` + `uv run --with imageio
--with scipy` as shown in §3.5) — it already executes the exact embedded
cell-12 source against the real bundle.

Per R5's own recommendation, a single 25-game commit-run pass cannot reliably
rank this design against the baseline (paired-t p=0.19-0.31 on the three
existing pairwise comparisons at n=25 games) — treat one push as a smoke
test for "does it run and does the game-loop terminate correctly," not as a
scored verdict, unless run as part of a real calibration batch (R5 §6).

## 7. Verification summary (Tested = N)

| Claim | Tested |
|---|---|
| Both modules' own self-tests (`_demo()`) | Yes, `python duckv4/duckv4_worldmodel_cap.py` / `duckv4_reallocator.py` |
| Both `.py` files parse (`ast.parse`) and compile (`py_compile`) | Yes |
| Generated notebook is valid JSON, only cell 12 differs from the original | Yes, `duckv4/verify_notebook.py` |
| Every code cell's Python parses | Yes, `ast.parse` on all 17 |
| Patch targets exist in the real, imported bundle before patching | Yes, `duckv4/verify_against_bundle.py` |
| World-model cap: real, unpatched harness reproduces R2's unbounded finding (negative control) | Yes, 85,779 chars measured live |
| World-model cap: patch bounds a real long field, passes a short one through unchanged | Yes |
| Reallocator: patch preserves the flat budget for an unadjusted session (no false-positive adjustment) | Yes |
| Reallocator safety invariant (`sum(deltas) <= 0`) holds across a 10-tick stress drive | Yes, mock dry-test |
| Reallocator per-game and system-wide hard caps actually bind | Yes, mock dry-test |
| Reallocator does not crash or drift on a session with raising accessors | Yes, mock dry-test |
| Negative controls (wrong/missing patch target) fail loudly, both modules, both synthetic and real | Yes |
| Exact embedded cell-12 source executes against the real bundle, both patches apply | Yes, `duckv4/verify_notebook.py` |
| Survives cell-14's `n_passes` overwrite (module-global patch, not a `bm` mutation) | Yes, by construction — verified duckmod/duckv3 use the identical ordering argument |
| An actual LLM turn / real commit run exercises either patch | **UNVERIFIED** — no GPU/Kaggle env available locally, not run at all yet |
| The 600s system-wide reallocation cap is safe under the real 110-game pipelined scheduling regime | **UNVERIFIED** — chosen conservative, not derived from a measurable real run (§5) |
