# R15 — two rival duck-harness notebooks: v19 and fast-eval

Read-only Kaggle-notebook forensics. Sources: `arc3-duck-v19.ipynb` (thtennant, id
`thtennant/arc3-duck-v19`) and `duck-harness-fast-eval.ipynb` (kunaldesale2408, id
`kunaldesale2408/duck-harness-fast-eval`), both pulled to
`/mnt/c/Users/Vampi/AppData/Local/Temp/rivals/`, plus their `kernel-metadata.json`. Cross-
referenced against our own measured evidence in `R9-stability.md`, `R10-throughput.md`,
`R11-model-intel.md`, `R12-model-swap-trace.md`, `R13-anim-bundle-diff.md`. Cell numbers
below are the notebooks' own `id` attributes (v19: integers `0`-`16`; fast-eval: strings
`cell-0`-`cell-10`).

## Executive summary

- **v19** is Tufa Labs' own public "readable" re-issue of their milestone-winning
  submission, still on `Qwen3.6-27B-FP8` (via the `driessmit1/vrfai-qwen3-6-27b-fp8-hf-
  snapshot` dataset), with one first-party graft cell (`taaf_grafts.composite.install`,
  cell 12) layering `goalkeep` + `hudmask` on top of a "v12 floor". Its interactive
  (non-submission) run is deliberately **cheap**: 3 real games + 1 duplicate (4 games
  total), explicitly to keep a Kaggle "Save & Run" commit short.
- **fast-eval** is a third party's fork of the same lineage, rebased onto the **anim
  bundle** we already analysed in `R13-anim-bundle-diff.md`
  (`jakobbrggen/taaf-kaggle-source-anim-20260807-anim`), swapped onto **Qwen3.8-27B-FP8**
  (repacked Kaggle Model, `foysalemonshanto/qwen3-8-27b-fp8-repacked-v1`), and its
  interactive run is the **full 25 public games × 1 pass** ("Q38 P1"-style), same
  `concurrency=28` / `max_runtime_s_per_game=7920` shape our own `R10-throughput.md`
  measured at ~2h12m wall-clock.
- **The name "fast-eval" is misleading relative to our stated need.** Nothing in the
  visible notebook cells makes a single pass run faster than the ~2.2h envelope R10 already
  measured for this exact game-count/concurrency/clock-cap shape — it is "fast" only in the
  sense of *fast-to-screen* (one pass, not a multi-pass significance campaign), not
  *cheap-in-GPU-hours*. See §4 and §6 item 7 for the direct conflict with R9/R10.

---

## 1. Dataset/model attachments and wiring

### v19

| Kind | Ref | Role |
|---|---|---|
| Dataset | `thtennant/taaf-kaggle-source-share-fork` | index 0 — the TAAF source bundle (own fork of the share dataset) |
| Dataset | `driessmit1/arc3-vllm-h100-wheelhouse-v3` | vLLM wheelhouse |
| Dataset | `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot` | Qwen3.6-27B-FP8 weights, mounted as a plain **dataset**, not a Kaggle Model |
| Competition | `arc-prize-2026-arc-agi-3` | supplies `arc_agi_3_wheels` + offline `environment_files` |

Wiring (cell 6): `_find_bundle_dir()` walks `/kaggle/input` for the marker file
`taaf-kaggle-bundle.json` to locate the source bundle (not index-based); a separate,
index-based loop then builds `TAAF_KAGGLE_INPUT_PATHS` and *assumes* `DATASET_SOURCES[0]`
is the bundle for that map entry. Cell 8 puts every bundled repo's `src/` (or the repo
root) on `sys.path` and writes a `.pth` file so child processes (vLLM server, etc.) see it
too, then runs `setup_commands.json` verbatim — this is where the model actually gets
loaded into vLLM (the command is a rendered heredoc baked at deploy time; see
`R12-model-swap-trace.md` for the full trace of that mechanism, done against our own
bundle). Cell 10 unpickles `deploy_target.pkl` and `benchmark_initial.pkl`.

### fast-eval

| Kind | Ref | Role |
|---|---|---|
| Dataset | `jakobbrggen/taaf-kaggle-source-anim-20260807-anim` | the **anim bundle** — same one `R13-anim-bundle-diff.md` analysed |
| Dataset | `driessmit1/arc3-vllm-h100-wheelhouse-v3` | vLLM wheelhouse (same ref as v19) |
| Kaggle Model | `foysalemonshanto/qwen3-8-27b-fp8-repacked-v1` (`PyTorch/hf-fp8/1`) | Qwen3.8-27B-FP8, attached through Kaggle's separate **Model** system, not a dataset |

Wiring differs from v19 in three ways worth noting:

1. **Bundle discovery is fully marker-based** (cell-2's `_find_taaf_bundle()`): it first
   honours an explicit `TAAF_KAGGLE_BUNDLE_DIR` env var, then walks
   `/kaggle/input/datasets`, `/kaggle/input`, `Path.cwd()` for the marker file — no
   index-into-`DATASET_SOURCES` assumption anywhere.
2. **The model is validated file-by-file before any expensive setup runs** (cell-2):
   asserts the model directory exists, asserts seven named files are present
   (`config.json`, `model.safetensors.index.json`, `tokenizer.json`,
   `tokenizer_config.json`, `outside.safetensors`, `mtp.safetensors`,
   `chat_template.jinja` — note `mtp.safetensors` is present, i.e. this repacked
   checkpoint's MTP head was NOT stripped, which is the exact unresolved risk
   `R11-model-intel.md` §1d/§2a flagged as unverified for the 3.8 FP8 checkpoint), and
   asserts an exact shard count (`16` layer shards, `18` total `.safetensors` files) —
   raising `RuntimeError` with the missing-file list or the wrong counts rather than
   silently proceeding.
3. **The model ref is injected into `TAAF_KAGGLE_INPUT_PATHS` directly**
   (`kaggle_input_paths[QWEN_MODEL_REF] = str(QWEN_MODEL_PATH)`, cell-2) so the bundled
   setup script's generic dataset-resolver mechanism can find it via the same owner/slug
   lookup it uses for datasets — the Kaggle-Model attachment is made to look like just
   another dataset ref to the rest of the pipeline.

`HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1` are also set explicitly and re-asserted
inside the patched setup command (cell-4), which v19 does not do.

---

## 2. Env/config overrides with values

### v19

| Var | Value | Cell | Note |
|---|---|---|---|
| `TAAF_RUN_AS_SUBMISSION` | `"1"`/`"0"` from `KAGGLE_IS_COMPETITION_RERUN` | 2 | |
| `TAAF_MINIMAL_DIAGNOSTICS` | `"1"`/`"0"`, same flag | 2 | disables periodic JSON/HTML diagnostics writes in a real rerun |
| `ONLY_RESET_LEVELS` | `"true"` | 2 | pins `arc_agi`'s cached level-reset-only behaviour before the client is built |
| `MPLBACKEND` | `"Agg"` | 2 | headless plotting |
| `LIBRARY_PATH` | prepends `/usr/local/nvidia/lib64` | 2 | so vLLM/torch can link `libcuda` |
| `ARC_API_KEY` | `"test-key-123"` (submission only) | 14 | |
| `ARC_BASE_URL` | `"http://gateway:8001/"` (submission only) | 14 | |
| `RECORDINGS_DIR` | `WORKING_DIR/server_recording` | 14 | |
| `bm.n_passes` | `1` | 14 | |
| `bm.game_weights` | `None` | 14 | |
| soft deadline | non-submission: `budget - min(600, budget/2)`; submission: start + **11h20m** | 14 | the submission-only hard cap is new relative to "used to run with `soft_end=None`" per its own comment |

### fast-eval

| Var | Value | Cell | Note |
|---|---|---|---|
| `TAAF_RUN_AS_SUBMISSION` | same pattern as v19 | cell-0, cell-6 | computed twice (once early, once again from `KAGGLE_IS_COMPETITION_RERUN` directly) — the second computation is the one actually used downstream |
| `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE` | `"1"` | cell-2, re-asserted cell-4 | not present in v19 at all |
| `ONLY_RESET_LEVELS` | `"true"` | cell-6 | same as v19 |
| `SOFT_DEADLINE_BUFFER_S` | `600.0` (constant) | cell-2 | same 10-minute buffer v19 hardcodes inline |
| `bm.solver.concurrency` | `28` | cell-7, non-submission only | explicit override, "already matches Q38 P1 in the source notebook" per its own comment |
| `bm.solver.max_runtime_s_per_game` | `7920.0` (= **2.2 hours**) | cell-7, non-submission only | same value the task brief's "<< 2.2 GPU-hours" bar is presumably keyed to |
| `bm.n_passes` | `1` | cell-7 (non-submission) and cell-8 (submission) | |
| `bm.game_weights` | `None` | cell-7, cell-8 | |
| `SCHEME`/`HOST`/`PORT`/`OPERATION_MODE`/`ENVIRONMENTS_DIR` | `http`/`gateway`/`8001`/`competition`/`""` | cell-8, submission only | v19 does not set these explicitly (relies on defaults inside `ArcadeSpec`/`Arcade`) |
| soft deadline | `_soft_end_time()`: `None` if submission or `max_runtime_s <= 0`, else `start + (budget - min(600, budget/2))` | cell-5/cell-8 | **fast-eval has no v19-style 11h20m submission-time hard cap** — a real rerun gets `soft_end=None` unconditionally, i.e. it reverted to the *older* behaviour v19's own comment says it "used to" have before the safety-pack change |

Conflict worth flagging: v19's comment at cell 14 explicitly frames the `soft_end=None`
submission behaviour as a **known-bad prior state it patched away** ("a real rerun used
to run with `soft_end=None`... Cap at run start + 11h20m so the solver drains and the
shared scorecard closes before Kaggle's hard kill"). fast-eval's `_soft_end_time()`
reproduces exactly that older, patched-away shape for `run_as_submission=True`. Whether
that is a regression or an intentional divergence cannot be told from this notebook alone
— it is not discussed in any fast-eval cell.

---

## 3. Source patches / monkeypatches in cells

### v19

Only one substantive patch cell, **cell 12** (the "Customization hook"):

```python
from taaf_grafts.composite import install
install(bm, flags={"efficiency": True, "retry_guard": True, "shortcircuit": True,
                    "goalkeep": True, "hudmask": True})
```

Mechanism, from the cell's own comment (this is prose in the notebook, not code we can
verify further without the `taaf-grafts` source, which is not in the pulled artifacts):

- **Composite graft install**, described as "v19 = the v12 floor + goalkeep + hudmask".
- `goalkeep`: stops the agent's carried world model being wiped on every game-over/level
  change. Cited measurement: *"the stock harness carried a non-empty model on only 33 of
  481 turns"*.
- `hudmask`: segments the status/timer band out of the per-action board-change-rate
  signal fed into the digest. Cited mechanism: `board_changed` is a whole-frame diff, so
  on 10 of 25 public games it reads `True` 100% of the time and the rate table carries
  zero bits (example cited: *"tn36's live v18 prompt read 'MOUSE 61/61'"*). The band is
  discovered empirically per-game (a row/column every base action drives at ≥90% is HUD,
  one no action touches is gameplay) and reused for later levels, with earlier evidence
  re-scored retroactively once found. Cited measurement: *"informative action tables 15 ->
  23, and the 17 games where no band exists are bit-identical"*.
- `EfficiencyToolAgent` (`efficiency` flag): budget-aware per-turn note + net-zero waste
  detection, described as report-only (does not change actions taken).
- `RetryGuard` (`retry_guard` flag): described as "a proven pass-through rider" in the
  analyzer chain.
- `shortcircuit`: a "no-op overshoot trimmer".
- The install prints a machine-parseable `TAAF_GRAFTS FEATURES={...} API_VERSION=1`
  banner, described as read by a commit-log gate (not visible in this notebook).
- Failure handling is double-guarded: `install()` itself is described as restoring
  `bm.solver` on any internal error, and the cell wraps the whole call in a bare
  `try/except Exception` that falls back to the stock `HarnessSolver` and prints the
  exception type/message — belt-and-suspenders so even an *import* failure of
  `taaf_grafts.composite` leaves `bm.solver` untouched.
- The comment explicitly notes this is safe against the run cell (14) reassigning
  `bm.games` afterward, because `Benchmark.run` deepcopies whatever solver is present at
  run time and cell 12 never touches `bm.solver` itself.

Second, smaller patch at cell 14 (the "dup-game commit gate", both a games-list mutation
and a monkeypatch-adjacent trick): in a non-submission run it truncates `bm.games` to the
first 3 real games plus a **duplicate** `GameAPI` pointed at `games[0]`'s `env_name`, using
a distinct `external_game_id=f"{first.env_name}-dup"` so `Benchmark`'s unique-`game_id`
check (cited as `benchmark.py:160`) passes, while the shared `arcade_spec` keeps the
duplicate in `games[0]`'s scouting/fingerprint family (cited as `game_api.py:155`) — i.e.
`games[0]` scouts and publishes results, the duplicate replays them. Purpose per comment:
*"keep interactive commit runs short AND make the transfer family store fire"*. Falls back
to plain `bm.games[:4]` truncation on any construction exception.

### fast-eval

No solver/agent-behaviour monkeypatches at all — its only patch is **infrastructural**:
`_patch_qwen38_setup_commands()` (cell-4) regex-rewrites the bundled `setup_commands.json`
heredoc in place, before it is executed:

```python
def _replace_python_assignment(command, variable_name, value):
    pattern = rf"(?m)^{re.escape(variable_name)}\s*=\s*(['\"])[^\r\n]*?\1\s*$"
    replacement = f"{variable_name} = {value!r}"
    return re.subn(pattern, replacement, command, count=1)
```

applied to `MODEL_OWNER`, `MODEL_SLUG`, `SERVED_MODEL_NAME` — the exact three literals
`R12-model-swap-trace.md` independently identified as the load-bearing assignments in our
own bundle's `setup_commands.json`. Two properties this has that our own R12 write-up's
recommended literal-`.replace()` approach does not:

1. **Regex, multiline-anchored, on the assignment statement shape** rather than the
   literal old value string — survives the old value being spelled slightly differently
   (whitespace, quote style) as long as the variable name and statement shape match.
2. **Counts replacements and raises `RuntimeError` naming which assignment(s) went
   missing** if any of the three are not found exactly once — R12's literal-string
   `.replace()` would silently no-op instead (a `.replace()` call that matches nothing just
   returns the string unchanged, with no signal).

It also patches the `vllm_env()` command specifically to inject
`HF_HUB_OFFLINE`/`TRANSFORMERS_OFFLINE` into the child vLLM process's env
(string-splicing after `'VLLM_NO_USAGE_STATS': '1',`), and, after all setup commands run,
asserts the setup actually took effect: `INFERENCE_ANALYZER_MODEL` must equal
`QWEN_SERVED_MODEL_NAME`, else `RuntimeError`. This is a genuine verification step our own
R12 trace stopped short of proposing (R12 recommended the rewrite but not a post-hoc
assertion that it was applied).

---

## 4. What makes fast-eval "fast", and a cheap-eval recipe for our campaign

**Direct finding: nothing in the visible notebook cells makes a single evaluation pass
run faster than the shape we already measured.** Cell-7's override (`Q38_P1_PUBLIC_GAME_IDS`
— all 25 public games, `n_passes=1`, `concurrency=28`, `max_runtime_s_per_game=7920.0`) is
**the identical shape** to the runs `R10-throughput.md` measured directly: `duckv5out` and
`duckmodcal` both ran this exact game-count/concurrency/clock combination end-to-end in
**2h12m42s and 2h12m30s** respectively (`R10-throughput.md` §2). Concurrency 28 already
exceeds the 25-game count, so every game runs in **one wave**, and R10's own §4 shows why
reducing game count alone would not shorten wall-clock at a fixed `max_runtime_s_per_game`:
almost every game **spends its entire clock** regardless of how much it accomplishes (no
early-stop signal; the agent keeps acting until the deadline). The only in-notebook lever
that touches wall-clock is `max_runtime_s_per_game` itself, and fast-eval leaves it at the
same 7920s both v19's and R10's runs used.

So "fast-eval" is fast only relative to a **multi-pass significance campaign** — it is a
single-pass, fixed-25-game "Q38 P1"-style screening run, explicitly named after the
convention `R13-anim-bundle-diff.md` §6 already flagged from the same lineage: *"One-pass
fast evaluation only as screening... suitable for coverage and gross regression detection,
not for a final significance claim."* fast-eval does not reduce the cost of that one
pass; it just standardizes running it (fixed IDs, no catalog dependency, corroborated by
`R13`'s note that the anim bundle removes dataset/tag catalog discovery entirely,
`run.py:117`).

**What a genuinely cheap discriminating recipe would need, built from our own evidence**
(none of this is in either rival notebook — it is what R9+R10 together imply is missing):

1. **Cut `max_runtime_s_per_game`, not game count.** Since concurrency (28) already
   covers all 25 games in one wave, shortening the per-game clock is the only lever that
   shortens wall-clock proportionally. A 900–1800s cap (vs 7920s) is 11–23% of the current
   clock, i.e. roughly **0.25–0.5 GPU-hours** for a full-25-game pass instead of 2.2 —
   comfortably under the `<< 2.2 GPU-hours` bar. This is a hypothesis, not yet measured:
   R10 does not tell us how much of a game's *signal* (score, level completions) accrues
   in the first 15–20% of its clock versus the last.
2. **Subset to the informative games**, per `R9-stability.md`'s classification: 7
   RELIABLE games carry the only score signal that survives identical-code reruns with
   bounded (though not small — up to 1.75×) variance; 8 DEAD games contribute essentially
   nothing (`min((baseline/actions)² × 100, 115)` scored on games that never move off
   zero); the 10 LOTTERY games are exactly the ones R9 shows swing up to **55.39×** between
   identical-code runs and should not be trusted to discriminate two *different* designs
   at n=1 either. A design-ranking pass over the 7 RELIABLE games (+ perhaps 2–3 LOTTERY
   games tracked separately, never averaged in) at a shortened per-game clock is a much
   smaller, much more honest signal than the full-25 single pass fast-eval demonstrates.
3. **Multiple short passes beat one long pass for ranking, not just for total actions.**
   R9's identical-code pairs (DM1/DM2, V5a/V5b) show single-pass 25-game means disagree
   with each other by more than some of the cross-design deltas they were meant to compare
   against (§3 of R9: *"the data does not permit treating cross-design reliable-base
   changes as clean design effects"*). At a 1800s clock, 3 short passes cost roughly the
   same wall-clock as one 7920s×1 pass restricted to the RELIABLE subset (3 × 1800s × 7
   games / 28 concurrency-slack ≈ well under an hour), while giving a spread estimate the
   single fast-eval-style pass cannot.
4. **Free lever, zero additional GPU-hours: rescore existing artifacts.** `R13` §6 flags
   the anim bundle's `traces.py` change — per-level baseline-action counts are read from
   the run artifact itself rather than an external catalog — as something to adopt. If two
   designs' past runs already exist as artifacts, comparing them via rescoring costs
   nothing further; this is the cheapest possible instance of "rank two designs in <<
   2.2 GPU-hours" (it is 0 GPU-hours) whenever prior runs already exist.

None of items 1–3 are demonstrated or even discussed in fast-eval; it runs the expensive
shape and calls it fast relative to a longer campaign it never runs, not relative to the
2.2h floor R10 already measured. Item 4 is the one piece of applicable tooling actually
present in the anim bundle fast-eval is built on.

---

## 5. What v13-v19 changed (from markdown/comments)

**Only one direct hint exists in this notebook**, and it is not a changelog — it is the
single prose comment inside cell 12 (quoted in §3 above): *"Composite graft install (v19 =
the v12 floor + goalkeep + hudmask): the single cell-12 entry point shipped in our..."*.
From this:

- **v12 is named as the floor** — i.e. whatever v12 contained is the baseline v19 builds
  on. Nothing in this notebook says what v12 itself contains beyond "the source-import cell
  above put every bundled repo on `sys.path`" (implying v12 already had the `taaf_grafts`
  package structure and at minimum `efficiency`, `retry_guard`, `shortcircuit` as prior
  flags, since the comment frames only `goalkeep` and `hudmask` as new to v19).
- **v19 = v12 + `goalkeep` + `hudmask`** is the only explicit version delta this notebook
  states. It does not say what, if anything, versions v13–v18 individually changed — there
  is no other version string, changelog cell, or dated comment anywhere else in the
  notebook (checked all 17 cells; only cell 0's markdown intro and cell 12's inline comment
  mention a version number at all).
- The measured numbers attached to `goalkeep` (33/481 non-empty-model turns in the stock
  harness) and `hudmask` (15→23 informative action tables, 17/25 games bit-identical) are
  the only quantified claims about *what changed*, and they describe the **effect being
  fixed**, not a version-by-version history.
- Cross-reference: `R7-v4-postmortem.md` and `R11-model-intel.md` were not re-opened for
  this pass beyond what's cited above; if a fuller v-number history exists, it is not
  visible from this notebook's own text — flag as UNKNOWN / not surfaced here, rather than
  inferring one.

---

## 6. Ranked "worth stealing" list

Ranked by (measured leverage where available) × (absence of a conflict with our own
evidence). Each entry names its conflict status explicitly.

1. **HIGH — Regex-anchored, fail-loud setup-command patching** (fast-eval cell-4,
   `_replace_python_assignment` + `RuntimeError` on missing assignment). Strictly safer
   than the literal-`.replace()` approach `R12-model-swap-trace.md` recommended for our own
   bundle: multiline regex on the assignment *statement shape* survives minor upstream
   reformatting, and it fails loudly instead of silently no-op'ing. **No conflict** — pure
   upgrade to a mechanism R12 already independently derived as necessary.

2. **HIGH — Post-setup identity assertion** (fast-eval cell-4: assert
   `INFERENCE_ANALYZER_MODEL == QWEN_SERVED_MODEL_NAME` after setup commands run, else
   raise). Closes the exact gap R12 left open (R12 verified *how* to rewrite the command,
   not that the rewrite took effect at runtime). **No conflict.**

3. **HIGH (evidence-gathering, not yet a config change) — Free rescoring from existing
   run artifacts** (`R13-anim-bundle-diff.md` §6, `traces.py` change in the anim bundle
   fast-eval is built on). Directly answers "rank two designs in << 2.2 GPU-hours" for
   **zero** additional GPU-hours whenever compatible artifacts already exist. **No
   conflict** — R13 already recommended adopting this independently of fast-eval.

4. **MEDIUM-HIGH, cautioned — Qwen3.8-27B-FP8 model swap itself.** Per
   `R11-model-intel.md` §2a: same architecture/param count as 3.6 (drop-in, no expected
   throughput penalty) with meaningfully higher agentic-benchmark scores (Terminal-Bench
   63.4→73.0, DeepSWE 13.3→42.2, OSWorld-Verified 63.9→84.3). fast-eval's own file-shape
   validation (cell-2: `mtp.safetensors` present, correct 16/18 shard counts) is the first
   concrete evidence we have that a repacked Qwen3.8 FP8 checkpoint's **MTP head survived
   repacking** — R11 §1d/§2a explicitly flagged this as unverified risk for this exact
   checkpoint. **Partial conflict/gap**: fast-eval demonstrates the checkpoint *loads and
   validates*, not that it *scores well on ARC-AGI-3* — no benchmark output from this
   notebook is in our possession, only its config. Adopt the swap as a paired A/B
   candidate, not as an assumed win.

5. **MEDIUM — Marker-file-only bundle discovery + explicit `TAAF_KAGGLE_BUNDLE_DIR`
   override** (fast-eval cell-2 `_find_taaf_bundle()`). Removes the index-into-
   `DATASET_SOURCES` assumption v19 still carries for its `kaggle_input_paths` map entry.
   **No conflict**, modest robustness gain (protects against a future dataset-list
   reordering silently mis-mapping the bundle path).

6. **MEDIUM — Pre-setup file/shape validation of an attached model** (fast-eval cell-2:
   assert required files present, assert exact shard counts, before any GPU/vLLM work
   starts). Fails fast on a bad mount instead of burning GPU time discovering it later.
   **No conflict.**

7. **CONFLICT — do not adopt the "Q38 P1" 25-game × 1-pass shape as our cheap-eval
   recipe.** This is the one place fast-eval's own design choice directly contradicts our
   measured evidence. R10 measured this exact shape at ~2h12m wall-clock (i.e. *at* the
   2.2h ceiling the task explicitly says we must beat, not under it), and R9 measured that
   a single such pass is not reliable enough to attribute a score delta to a design change
   in the first place (up to 55.39× swings between identical-code reruns on individual
   games, 1.75× swing on the reliable-only aggregate). See §4 for the recipe we should use
   instead (shortened clock + RELIABLE-game subset + multiple short passes).

8. **Confirmed non-lever, both rivals share it — `LOCAL_ANALYZER_MAX_OUTPUT` still
   unbounded.** `R13-anim-bundle-diff.md` §1 already found the anim bundle's
   `configs/inference.json` still ships `max_output: 0` (unbounded) with thinking enabled —
   fast-eval is built on that exact bundle and does not override it anywhere in its
   customization cells; v19 does not touch it either. Neither notebook has adopted
   `R10-throughput.md`'s highest-leverage finding (a hard output-token cap, tested at
   768–1024 tokens, as the single biggest lever on actions-per-GPU-hour, r≈0.99 correlation
   between generated tokens/action and seconds/action). Not something to "steal" — it
   confirms our own R10 finding is still ahead of both public forks, and is the first
   thing to layer onto whichever of items 4/7 we end up adopting.
