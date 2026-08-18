# duckmod build: HUD auto-flag + transition-graph injection into the duck fork

Output: `duckmod/duck_tools.py`, `duckmod/prompt_additions.txt`, `duckmod/taaf-duck-mod.ipynb`,
`duckmod/kernel-metadata.json`. `duck/**` untouched (read-only reference, as instructed).

## 1. The customization hook, verbatim

Cell 12 ("## 6. Customization hook") of the original notebook, in full, is:

```python
# Make one-off changes to `bm`, `bm.games`, or `bm.solver` here before the run starts.
# Example:
# bm.label = f"{bm.label}-debug"
```

That's it — an empty cell with a comment. It runs **after** cell 10 unpickles `bm`/`bm.solver`
(so the bundled repos are already importable and the `HarnessSolver` object already exists) and
**before** cell 14 builds the game list and calls `await bm.run(...)`. So anything done here is
in effect for the entire run and for every game.

**What the hook can reach, concretely:** `bm`, `bm.games`, `bm.solver` are the only names it
documents, and its own example (`bm.label = ...`) only mutates a data attribute on the already-
constructed `HarnessSolver`. It does **not** give you a supported way to add a new callable
into the python-tool sandbox's subprocess namespace or add text to the system prompt — those
live in module-level constants (`python_tool_sandbox._SANDBOX_BOOTSTRAP`,
`inference.agent.prompts.PYTHON_ADDENDUM`, etc.), not on `bm`/`bm.solver` as attributes. So the
hook reaches neither (a) nor (b) as documented; it's a mutation point on the solver object, not
an extension point on the module source. What it **does** give us is the right *place* — the
sequencing (imports done, solver loaded, run not yet started) is exactly where a runtime patch
of those module constants has to land, so injection here means "write ordinary Python in this
cell that reaches into `sys.modules['inference.agent.tool_agent']` /
`sys.modules['inference.agent.python_tool_sandbox']` and edits their globals directly," not
`monkeypatching bm`.

## 2. What the added cell does, step by step

The generated cell 12 (full text in `duckmod/taaf-duck-mod.ipynb`, ~14.4k chars) does four things:

1. **Splice `duck_tools.py`'s source into `python_tool_sandbox._SANDBOX_BOOTSTRAP`.** The
   bootstrap string already has `segment_layer` (from `segmentation.py`) spliced in at *its own*
   module's import time via `.replace("__SEGMENTATION_SOURCE__\n", inspect.getsource(...))`
   (`python_tool_sandbox.py:398`) — but that placeholder is gone by the time our cell runs (it
   was consumed at `python_tool_sandbox.py`'s own import). So the cell finds a different, unique
   anchor that's still present verbatim — `"HOST_STDOUT = sys.stdout\n"` — asserts it occurs
   exactly once (loud failure if the upstream bootstrap changes shape), and inserts our
   stdlib-only source text immediately before it, at the same module level `segment_layer`
   already lives at.
2. **Expose `hud_mask`/`TransitionGraph` as bare callables in `runtime_globals`.** Same pattern
   `action` uses (`python_tool_sandbox.py:369`, `runtime_globals["action"] = action`, inside
   `main()`). Rather than hand-typing the indentation of that line (risky — a future re-indent
   of the bundle would silently break a hardcoded guess), the cell walks the bootstrap
   line-by-line, finds the exact `runtime_globals["action"] = action` line, reads its *own*
   leading whitespace off that line, and inserts two new lines using the same captured indent.
   Asserts the anchor was found.
3. **Document both helpers in the system prompt — patching `tool_agent`, not `prompts`.** This
   is the one non-obvious finding of the build. `tool_agent.py` does
   `from inference.agent.prompts import (PYTHON_ADDENDUM, STRUCTURED_RUNTIME_STATE_ADDENDUM, ...)`
   — a `from X import Y` **copies the reference into `tool_agent`'s own module namespace** at
   import time. `_build_system_prompt` then resolves the bare name `PYTHON_ADDENDUM` as a
   global lookup against `tool_agent.__dict__`, never against `inference.agent.prompts.__dict__`.
   So patching `inference.agent.prompts.PYTHON_ADDENDUM = ...` after `tool_agent` has already
   been imported (which it has, by cell 10's unpickle) would silently do **nothing** — the
   prompt actually sent to the model would be unchanged, with no error anywhere. Verified this
   both ways locally (see §5). The cell patches `tool_agent.PYTHON_ADDENDUM` and
   `tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM` directly instead.
4. **Extend `tool_agent._PYTHON_TOOL_DESCRIPTION`** (the OpenAI function-calling tool's own
   `description` field, a separate, shorter-budget surface from the system message) with a
   compact restatement of both helpers.

Printed at the end: byte counts of what was added to the bootstrap, the system prompt, and the
tool description, so a kernel log line confirms the patch actually ran and by how much, without
needing to inspect the sandbox subprocess.

Timing is safe regardless of exactly when a `ToolAgent`/ `_HarnessGameSession` gets constructed:
that construction happens inside `bm.run()` (cell 14), which is textually and temporally after
our patch cell (cell 12) finishes. Every `ToolAgent` built for the rest of the run reads the
already-patched module globals the first time it calls `_build_system_prompt` or spawns a
sandbox subprocess.

## 3. The two helpers

`duckmod/duck_tools.py` — stdlib-only, no project imports, no `from __future__` import, same
constraint `segmentation.py` states about itself (`segmentation.py:1-6`), no top-level side
effects, no `__main__` guard in the spliced portion (the build script strips everything from
`if __name__ == "__main__":` onward before embedding it in the notebook — segmentation.py has
no such guard at all, for the same reason: this text lands inside a larger script and must not
run anything on import).

- **`hud_mask(history) -> set[(row, col)]`** — flags a cell if it changed on ≥95% of
  frame-to-frame transitions (a ticking clock/budget bar), or if it was, alone, the only cell
  that changed on ≥2 separate transitions (an isolated ticker). Reads only `.frame.ascii` off
  each `history` entry (row/char diffing — the sandbox doesn't expose a raw grid), skips
  transition pairs whose frames have mismatched shapes (a level boundary) rather than
  miscounting them.
- **`TransitionGraph`** — `.record(state, action, next_state)` (state can be anything; hashable
  values pass through, others coerce via `repr`), `.untried(state, valid_actions)`,
  `.path_to_nearest_untried(state, valid_actions)` (BFS over recorded edges only, returns
  `{"target": ..., "path": [...]}` or `None`). Docstring states explicitly that it's a
  hypothesis generator over *observed* transitions only, never an oracle — mirrors this
  campaign's own `ka59` lesson in `CLAUDE.md` ("a static colour-based walk map OVERCOUNTS
  reachability... when a static model and a real router disagree, the model loses").

### Self-test output (`python duckmod/duck_tools.py`)

```
duck_tools self-test OK
```

Asserts covered: the ticking-clock cell gets flagged and the real gameplay cell does not; an
isolated two-tick flip gets flagged; a level-boundary shape mismatch doesn't crash `hud_mask`;
`TransitionGraph.untried` correctly lists never-tried actions; `path_to_nearest_untried` returns
the current state when it itself still has untried actions, and correctly BFS's one hop away
once exhausted; an unhashable state (a `list`) round-trips through the `repr` coercion.

## 4. Prompt additions

`duckmod/prompt_additions.txt` — three sections, `[STRUCTURED_RUNTIME_STATE_ADDENDUM]` (812
chars, documents the return shapes), `[PYTHON_ADDENDUM]` (1,019 chars, documents *when* to
reach for each — subtract `hud_mask` before diffing/keying, use `TransitionGraph` to avoid
repeating actions and navigate to unexplored states), `[PYTHON_TOOL_DESCRIPTION]` (403 chars,
compact restatement for the tool-schema description). Total system-message growth: 1,835 chars
against an existing ~2.6k-char `VISUAL_GAME_ADDENDUM`/`PYTHON_ADDENDUM` block per the study doc
— roughly proportionate, not a budget blowout, and the whole assembled prompt is exempt from
context eviction either way (`tool_agent.py:1682`, always re-prepended).

## 5. Local verification (full output in the build run below)

Ran `duckmod/duck_tools.py` standalone (own venv, no bundle deps needed) — self-test passes
(§3). Then, **against the real `duck/bundle/src/ARC3-Inference` source** (imported directly,
nothing on disk under `duck/` touched):

- `json.load` on both the original and generated notebook: valid JSON, both parse.
- Diffed all 17 cells between original and `taaf-duck-mod.ipynb`: **only cell 12 differs**; the
  other 16 are byte-identical.
- Every code cell in the generated notebook parses with `ast.parse` (0 syntax errors).
- The generated cell-12 source itself parses with `ast.parse` before being embedded.
- Ran the *actual* patch logic (identical code to what's embedded in the notebook cell) against
  the real, imported `inference.agent.tool_agent` / `inference.agent.python_tool_sandbox`
  modules:
  - Both bootstrap anchors (`"HOST_STDOUT = sys.stdout\n"`, `runtime_globals["action"] = action`)
    found exactly once in the real, already-segmentation-spliced bootstrap.
  - Patched `_SANDBOX_BOOTSTRAP`: 19,288 → 27,915 chars, **compiles clean**
    (`compile(..., "exec")`).
  - `exec`'d the bootstrap's module-level code (everything above `def main():`) in a fresh
    namespace: `hud_mask`, `TransitionGraph`, and `segment_layer` all define without error —
    proves the splice doesn't collide with segmentation's own names or break its source.
  - `tool_agent.PYTHON_ADDENDUM` + `tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM`: 7,970 → 9,805
    chars.
  - `tool_agent._PYTHON_TOOL_DESCRIPTION`: 872 → 1,276 chars.
  - Called `tool_agent._build_system_prompt(tool_output_tokens=4000)` **after** patching:
    14,193 chars, contains both `"hud_mask(history)"` and `"TransitionGraph()"` — confirms the
    patch actually reaches the assembled system message, not just the module attribute.
  - As a negative control (not shown as code above but run manually before settling on the
    design): patching `inference.agent.prompts.PYTHON_ADDENDUM` instead of
    `tool_agent.PYTHON_ADDENDUM` leaves `tool_agent._build_system_prompt`'s output **unchanged**
    — confirms the from-import binding finding in §2.3 is real, not a theoretical concern.

**What could NOT be verified locally, and why:** the notebook cannot be executed end-to-end —
it requires the Kaggle GPU environment (vLLM server, the attached model/wheelhouse datasets,
`/kaggle/input` mounts) that doesn't exist in this sandbox. Everything short of an actual model
call was verified against the real source tree: the splice, the patch, the resulting prompt
text, and that the sandboxed subprocess's own module-level code defines cleanly. The one thing
genuinely unverified is runtime behavior inside the isolated `-I -S` subprocess itself (e.g.
whether `SAFE_BUILTINS`/`SAFE_MODULES` restrict anything `hud_mask`/`TransitionGraph` need —
they don't: no imports, no builtins outside plain dict/list/set/str operations, all of which are
in `SAFE_BUILTINS`). **UNVERIFIED**: an actual LLM turn calling `hud_mask`/`TransitionGraph`
inside a live game.

## 6. What the main thread should push

```bash
cd duckmod
KAGGLE_API_TOKEN=$(cat ../.kaggle/access_token) kaggle kernels push -p .
```
(mirrors the existing `kernels push -p duckmod/` instruction — `kernel-metadata.json` inside
`duckmod/` names `id: sahasawatt/taaf-duck-mod`, `code_file: taaf-duck-mod.ipynb`, and copies
`dataset_sources`/`machine_shape`/`docker_image` unchanged from `duck/kernel-metadata.json`, so
no new dataset attachment is needed — everything duckmod needs is embedded in the notebook cell
itself as string literals, not a separate attached file).

Before pushing: `exec` the notebook's cell 12 source once in isolation is what this build already
did (§5) — the equivalent of the repo's own "exec the built bundle before every push" discipline
for the Kaggle bundle pipeline, applied here to a notebook cell instead of `kaggle/my_agent.py`.

## 7. Risk list

- **Anchor drift.** Both splice anchors (`"HOST_STDOUT = sys.stdout\n"`,
  `runtime_globals["action"] = action`) are asserted present-and-unique before use, so an
  upstream bundle change that removes or duplicates them **fails loudly at cell-12 execution**
  (`AssertionError`, run aborts before `bm.run()` starts) rather than silently no-op'ing. Low
  risk of silent failure; nonzero risk of the run not starting at all if the bundle changes
  between when this was built and when it's pushed — re-run the dry-run script in §5 against
  whatever `duck/bundle/` looks like at push time.
- **Prompt-cost risk.** +1,835 chars to the always-resident system message, paid on every
  chat-completion request for the entire run (never evicted). Proportionate to what's already
  there (§4), but it is pure downside if the model never actually calls either helper.
- **`hud_mask` false positives/negatives are cheap by design.** It's advisory text the model can
  ignore (same as the existing prose warning it augments) — a wrong flag doesn't touch action
  semantics. Threshold constants (`HUD_RATIO_THRESHOLD=0.95`, `HUD_ISOLATION_MIN_COUNT=2`) are
  unvalidated against this specific harness/model combination (the campaign's own two HUD
  signatures motivated the numbers, not a sweep on the duck harness itself) — if it flags too
  aggressively on a real board, these are the two knobs to loosen.
- **`TransitionGraph` cost is O(history length) per rebuild**, same risk the study doc already
  flagged for injection #2 in general (`results/taaf-study-20260818.md` §8, injection #2 Risk
  paragraph) — a long game/level could make the LLM's own from-scratch rebuild-and-replay start
  competing with the 30s per-call budget. Nothing in `duck_tools.py` itself does the rebuilding
  (that's left to the model's own code, per the design in the study doc); this is a risk the
  model inherits when it chooses to replay `history` into a fresh `TransitionGraph` each call,
  not a cost this file pays unconditionally.
- **Unlike the baseline fork, this one has never scored on Kaggle.** `sahasawatt/taaf-duck-fork`
  (unmodified) already reproduced the milestone winner's measured 1.25 mean; `taaf-duck-mod` is
  the first run of the modified harness, so its risk profile is "does what the baseline does,
  plus two additive, ignorable helpers" — the failure mode to watch for on the actual run is the
  assertion-abort case above, not a change in play quality, since nothing about action selection,
  scoring, or existing driver logic between fork and mod-fork is touched (this campaign's own
  `compete.py`/driver code is a completely separate codebase from the duck harness and is not
  part of this fork).

## 8. Verification summary (Tested = N)

| Claim | Tested |
|---|---|
| `duck_tools.py` self-test (hud_mask + TransitionGraph) | Yes, `python duckmod/duck_tools.py` → `duck_tools self-test OK` |
| Generated notebook is valid JSON | Yes, `json.load` |
| Only cell 12 differs from the original notebook | Yes, cell-by-cell diff, 16/17 identical |
| Every code cell's Python parses | Yes, `ast.parse` on all 17 |
| Splice anchors exist exactly once in the real bundle | Yes, against `duck/bundle/src/ARC3-Inference` |
| Patched bootstrap compiles | Yes, `compile(..., "exec")` |
| `hud_mask`/`TransitionGraph`/`segment_layer` define cleanly once spliced | Yes, `exec`'d module-level code in a fresh namespace |
| Patched system prompt actually contains the new text | Yes, called `tool_agent._build_system_prompt(...)` post-patch |
| Patching `prompts.X` instead of `tool_agent.X` is a no-op | Yes, negative control run manually |
| Full notebook run on Kaggle (GPU, vLLM, live model) | **UNVERIFIED** — no GPU/Kaggle env available locally |
