# R41 — B38 built as `duckv26`, and the seam is better than R38 predicted

2026-08-25, offline, 0 slots. Builds the family brake R38 designed. **Not pushed.**

## 1. The seam is not what R38 §7 said, and the difference is in our favour

R38 §7 called `_handle_action` *"the only caller of `_step_env_callback`"*. **That is wrong** —
there are three (`tool_agent.py:1812` batch, `:1862` per-action, `:1917` `_handle_animation`),
and `_handle_action` is a nested function, so it cannot be wrapped at all.

What is there instead is better. `:1855-1861` already reads:

```python
if (self._noop_guard is not None and action_sig
        and self._noop_guard.is_known_noop(noop_guard_level, noop_guard_board_sig, action_sig)):
    blocked_actions.append(action_sig)
    continue
```

**B29's brake is deployed and blocking today**, on both paths (`:1779` single, `:1858` batch),
and each already carries the refusal back as `stop_reason: "known_noop"` with a `stop_detail`
naming the actions (`:352-358`, `:1798-1800`). So the family brake needs **no new plumbing at
all**: wrapping `NoopGuard` adds a second block reason to machinery that already exists.

That also settles R38's open worry about disobedience. The action does not happen — this is not
B32's hint channel, which the 27B obeyed 52% of the time.

## 1b. Why it is a MAJOR — by elimination, and the case §Versioning does not cover

The name was chosen before the rule was consulted, which is the wrong order; checked
afterwards it holds, and the checking is worth writing down.

§Versioning: a MINOR *"refines the same lever"* and lives in the SAME dir as its major, one
kernel per major. So the test is: which build does this refine?

| build | its lever | does B38 refine it |
|---|---|---|
| `duckv24` | untried-ledger nudge through the hint channel | no — a hint the model may ignore vs a block it cannot |
| `duckv25` | sampler seed pin | no |
| `clock2x` | per-game clock | no |

It refines none of them, so it is not a minor of anything, and *"one kernel per major"* forces
the same answer from the other side: it needs its own kernel, therefore its own major.

⚠️ **The honest objection, recorded rather than argued away.** R38 §4 calls this *"same idea
one level of abstraction up"* from **B29** — and B29 is a real brake that is **already deployed
in the harness** (`hard_noop_guard`, §1 above). Read that way, B38 is a MINOR of B29.

What breaks that reading is only that B29 is not one of our builds: it arrived with the upstream
bundle, has no `duckvNN` dir to live in and no kernel to share. **So `duckv26` is a major that
refines UPSTREAM's lever rather than one of ours — a case §Versioning does not describe.** If the
convention is ever extended, this is the shape to extend it for; until then the elimination test
above is what the name rests on.

## 2. What was built

`duckv26/brake_patch.py` (cell 12) wraps two `NoopGuard` methods:

- **`observe`** counts every EXECUTED action into a per-level ledger keyed by FAMILY —
  `(MOUSE, row)` for clicks, the action name otherwise. Counting only no-ops would rebuild B29;
  the lock this exists to break is made of actions that mostly *do* move something (vc33's clicks
  repaint a row) and get nowhere.
- **`is_known_noop`** refuses a family that has fired K times since the last level-up. B29 keeps
  priority — an exact known no-op is refused for its own reason first.

A level-up empties the ledger; that is the entire reset rule, and it falls out of the level
argument both methods already receive.

**K = 20 is measured, not chosen** (R38 §3): k=10 and k=15 destroy 5 of 30 real level-ups, k=20
destroys 0 while speaking on 25.9% of decisions. `DUCKV26_BRAKE_K` overrides it.

## 3. Rig, six cases, run against the real vendored `NoopGuard`

| case | result |
|---|---|
| control: stock guard, 30 distinct row-56 clicks that all moved the board | **not blocked** — this is B29 today, and it is why the brake is needed |
| vc33 shape: 30 distinct clicks on row 56 | first blocked at fire **#20** |
| a different row | not blocked |
| the same row after a level-up | not blocked |
| keyboard family (`UP` ×25) | first blocked at **#20** |
| B29 priority: an exact repeat that was a no-op | blocked after **1** fire |
| **margin: `lp85`'s real level-up at family count 19** | **not blocked** |

The last one is the case that matters: R38's whole risk is that the deepest family count at a
genuine level-up is 19 against K=20.

## 4. Two builder defects caught by its own self-check

1. The first cut asserted `'MULTIMODAL_UPSCALE': '4'` and `'LOCAL_ANALYZER_TEMPERATURE': '0.6'`
   in cell 8 — **copied from duckv25's builder, which injects a key there**. duckv10's cell 8
   sets neither: both come from the bundle's `setup_commands.json`. The assert failed correctly.
   Same lesson as R40 §2 — a config's "current" value comes from a run's `taaf_setup_env.json`,
   never from source.
2. The self-check's own **print line** then still claimed "upscale 4, temperature 0.6" after
   those asserts were removed — a reassuring line about something no longer checked, which is
   the exact shape that let duckv25 ship. Corrected to state only what is asserted.

The builder compares cells 6/8 against `duckv10/taaf-duck-v10.ipynb` and cell 12 against the
patch file — never against `SRC_NB` (CLAUDE.md §Versioning).

## 5. 🔴 A boundary was crossed before this, and it is the reason §4 matters

Auditing every `kernel-metadata.json` while fixing duckv26's, the roster reads:

```
duckv25/kernel-metadata.json   sahasawatt/taaf-duck-v25
```

**That kernel was pushed and run on 2026-08-24 from this workspace — onto the team leader's
Kaggle account, not `yocybercode`.** The metadata was generated by copying duckv10's, whose `id`
is his, and nothing printed the owner. This is the failure CLAUDE.md constraint 4 documents
verbatim from the `thui-v1-1` near-miss; it was not a near-miss here.

duckv26's metadata was written the same way and caught before any push: it now reads
`yocybercode/taaf-duck-v26`, private. **Read the `id` out of the generated file before every
push** — `scripts/kaggle_push_kernel.py` asserts it, and a bare `kaggle kernels push -p <dir>`
(which is what was used) never sees that gate.

## 6. What is NOT known

1. **A blocked action is not a better action.** The gate can fire correctly, cheaply and
   structurally, and the agent may lock onto the next family. Nothing here speaks to it; only a
   run does.
2. **n=1.** K=20's margin of one rests on 30 level-ups from a single corpus. The 5-run sweep
   R38 asked for is still unrun (the artifacts are on the Mac).
3. **R40's consequence is unaddressed in this build.** A game that fires no actions at all —
   `v25/ft09`, 108 records of one step — is invisible to a repeat-based brake. This patch would
   not have helped it.
4. Reach was measured on clock2x's transcripts, not on a run with the brake armed; the 25.9%
   is a prediction about behaviour the brake itself changes.

## 7. Reproduce

```bash
python duckv26/build_notebook.py     # self-check asserts cells 6/8 = duckv10, cell 12 = the patch
```

Rig: copy the vendored `inference/` tree beside `brake_patch.py`, import it, and drive
`NoopGuard` directly — no notebook, no engine, no Kaggle.
