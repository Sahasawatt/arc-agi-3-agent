# R42 — B39 built as `duckv27`, and our bundle has one switch where upstream has two

2026-08-25, offline, 0 slots. Builds the retrieval kill-switch R39 designed. **Not pushed.**

## 1. The seam is narrower than "port the flag", and that is the finding

R39 §7 says gate the append at `solver.py:860`. Reading the surrounding code first turned up
something it does not record: **`step_env` already has a flag on this path, and it is the wrong
one.**

```python
# solver.py:684-690
if str(arguments.get("query") or "").strip() == "animation":
    if not self.solver.animation_awareness:
        return {"executed": False, "query": "animation", "record": None}
    return {..., "record": self.animation_record(arguments.get("action_num"))}
```

Upstream has **two** flags — `animation_retrieval` (default **OFF**, "bought no score") and
`animation_awareness` (default **ON**, carrying the `worth_inspecting` threshold they call *the
one transferable result of the series*). **Our `anim` bundle fuses them into
`animation_awareness` alone.** So the config-shaped move — flip the flag we have — takes the
half upstream deliberately keeps down with the half it deliberately dropped. That is why this
is a patch and not a setting.

Confirmed live rather than assumed: `animation_awareness` reads **True** in `thui-v1-1-r2`'s own
event rows.

## 2. What was built

`duckv27/retrieval_off_patch.py` (cell 12), two edits:

1. **`_HarnessGameSession.animation_record` → always `None`.** `step_env` then returns
   `{"executed": False, "query": "animation", "record": None}` — byte-identical to the shape it
   already returns when awareness is off, so no new response shape reaches the model.
   `payload["animation"] = animation` sits one line **above** the history append
   (`solver.py:857`), so the awareness channel the model reads inline is untouched.
2. **The three `animation()` advertisement lines leave the system prompt.** Upstream documents
   what happens with only edit 1: *"that is how the Experiment 4 control arm ended up still
   advertising `animation()` while the handler was off"* — the model spends turns calling a dead
   tool, which is worse than leaving the feature alone. Prompt shrinks **737 chars**.

Gating the reader rather than the writer is equivalent here, and the rig proves it: outside
`animation_record`, `animation_history` appears at exactly two lines (222, the field
declaration; 860, the append) and **neither reads it**.

## 3. 🔴 The trap this patch is mostly built around

`tool_agent.py:21` imports the addendum **by value**, and `_build_system_prompt` (`:499`) reads
its own module global. So:

```python
prompts.STRUCTURED_RUNTIME_STATE_ADDENDUM = <new text>   # changes NOTHING
```

It raises no error, prints no warning, and ships a run that measures nothing — the prompt half
of a two-edit change silently missing, leaving exactly the arm upstream warns about. The patch
rebinds `tool_agent.STRUCTURED_RUNTIME_STATE_ADDENDUM` and then **reads the built prompt back**
(`assert "animation(" not in _ta._build_system_prompt(...)`) rather than trusting the write.

## 4. Rig: 13 cases against the real vendored source, 6 mutations proved red

`duckv27/prove_teeth.py`. `inference.agent.tool_agent` imports cleanly on this machine, so edit
2 is tested end to end through `_build_system_prompt`; `inference.framework.solver` cannot
(`arcengine`, `taaf`, a plotting stack), so edit 1 is asserted structurally by AST — and the
patch carries the same two asserts at runtime, where the real module is present.

| case | what it holds |
|---|---|
| 0, 1 | **controls**: the stock addendum has exactly 3 advertisement lines, and the stock BUILT prompt carries both halves |
| 5 | **anti-tautology**: rebinding `prompts.X` leaves the built prompt **unchanged** — the trap is real, and it is checked *before* the real patch is applied |
| 2, 3, 4, 6 | 3 lines removed, `animation(` gone from the built prompt, all 3 awareness lines survive, prompt actually shrank |
| 7, 8, 9 | `_HarnessGameSession.animation_record` exists; `animation_history` is only written outside it |
| 10, 11, 12 | the patch performs both edits **as real assignments** and never imports `inference.agent.prompts` |

Mutations, each reddening a different case: comment out edit 1 → 10 · comment out edit 2 → 11 ·
target `prompts` instead of `tool_agent` → 11 · typo one advertisement prefix → 0 · widen a
prefix so it swallows an awareness line → 0 · rewrite an awareness prefix as an advertisement →
4. Control unmutated: green.

**Two defects the mutations caught, both in the rig rather than the patch:**

1. Cases 10-12 were substring tests, so **commenting out edit 1 still scored 13/13** — `#_sess.
   animation_record = _no_retrieval` contains the string being searched for. Now parsed with
   `ast` and matched as a real `Assign` to an `Attribute`.
2. The rig kept **its own copy** of the advertisement prefixes, so a typo in the patch's copy was
   invisible to it — the probe was a second implementation of the thing under test. It now
   AST-extracts `_ADVERT` and `_AWARE` from the patch file itself.

## 5. Versioning: a MAJOR, by the same elimination R41 used

| build | its lever | does B39 refine it |
|---|---|---|
| `duckv24` | untried-ledger nudge | no |
| `duckv25` | sampler seed pin | no |
| `duckv26` | family brake on executed actions | no — that constrains what the model may DO; this removes a thing it may LOOK AT |
| `clock2x` | per-game clock | no |

It refines none, and *one kernel per major* forces the same answer from the other side.
`duckv27/`. The notebook is **v10 with exactly one cell changed** — verified directly against
`duckv10/taaf-duck-v10.ipynb`, differing cells `[12]`, with `duckv26` as the control.

## 6. What this build cannot tell you

- **Upstream's "bought no score" is upstream's measurement on upstream's runs.** A strong prior,
  not our data. A removal still needs a public run to rank (B30).
- **Ten of 25 games never execute `animation()` at all** (R39 §4), so whatever the removal is
  worth, it is worth nothing in those ten — the per-game unevenness B35 is about.
- ⚠️ **What retrieval COSTS us is still unmeasured, and an attempt to close it here failed.**
  `thui-v1-1-r2` has the per-request `*_usage.jsonl` R39 §7 said was missing, and joining it to
  the turns that execute `animation()` gives a ratio — but the instrument does not reconcile:
  summing `completion_tokens` over all 1,306 usage rows gives **2,386,886** against
  `summary.txt`'s **1,944,823**, a **+22.7%** excess that exact-duplicate removal only narrows to
  +14.2%, and `(game, action, req_in_turn)` is not a key (672 collisions). A cost ratio computed
  on a probe that disagrees with the run's own total by a fifth is not a measurement, so R39's
  unknown #1 stays **open**. The likely direction of the error is against the finding — retries
  cluster on slow turns, which is the group being measured.
- `worth_inspecting` is still absent from all 75 files of our bundle. Porting it is the larger
  job (four files including `utils/animation.py`) and is untouched here.

## 7. Not pushed

Building spends nothing; running spends a GPU slot, and `duckv26` is in flight
(`sahasawatt/taaf-duck-v26`, RUNNING as of 2026-08-25). Whether B39 or B38's result gets the next
slot is the campaign owner's call.
