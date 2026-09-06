# thui `avo v0` — Tufa's own AVO agent, run as they ship it: two draws, in-band on public, first hidden draw 1.15

**Line** thui · **family** avo · **directory** [`thui-avo/`](../../../thui-avo) · **ticket** none — evidence for `B60` · **status** ran twice, public read done, **hidden 1.15** (`56039729`, resolved 2026-09-06)

## The one change

**The whole upstream bundle.** `thui-v1-1` byte-for-byte except three cells:

- **cell 0** markdown;
- **cell 6** `DATASET_SOURCES[0]` `jakobbrggen/taaf-kaggle-source-anim-20260807-anim` →
  `jakobbrggen/taaf-kaggle-source`, whose live branch is `experiment/avo-v2` @ `74ff3df` and whose
  `deploy_target.pkl` carries **`avo_agent=True`** — i.e. the bundle *is* Tufa's AVO Kaggle run, published
  as they run it. `AvoAgent` subclasses `ToolAgent` with durable memory, inspect/plan/implement/evaluate,
  and a stagnation supervisor;
- **cell 8** relaxes the inherited `v10`-exactness `MULTIMODAL_UPSCALE` tooth to a **print**.

**Why the arm exists**: `duckv10`'s own 2.41 → 4.55 came from adopting a newer upstream bundle and
*deleting* fork patches. This repeats that move on the next bundle.

⚠️ **The live dataset moves under you.** The first push died on that inherited tooth even though the
locally-diffed copy carried `'4'`, because `taaf-kaggle-source` had been re-versioned: the mounted LATEST
sets upscale **8** + grid lines 1 and natively pins the Qwen3.8 snapshot the fork used to swap in by hand.
So the chassis's three model `.replace()` calls become correct **no-ops** — their asserts test the negative
and still hold — and the upscale must not be pinned back to 4 for an as-shipped arm.

## Where it lives

| what | path |
|---|---|
| builder | `thui-avo/build_notebook.py` |
| notebook | `thui-avo/taaf-thui-avo-v0.ipynb` |
| kernels | `sahasawatt/thui-avo-v0` (1st draw) · `yocybercode/thui-avo-v0` v1 (2nd draw, the submitted one) |
| fixtures | `eval/fixtures/thui-avo-v0-sahasawatt.json` · `eval/fixtures/thui-avo-v0-yocybercode.json` · pooled `eval/fixtures/avo-pool.json` |
| arm | declared in `eval/fixtures/arms.json` as `avo` |
| cited in | `notes/B60-exploration-prior-design.md` (the evidence list) |

## What it scored

| run | public | hidden | scoring | levels | actions | act/lvl | Mtok |
|---|---|---|---|---|---|---|---|
| `sahasawatt/thui-avo-v0`, 2026-09-02 | **4.40** | — | 16 | 23 | 1,318 | 57.3 | 2.39 |
| `yocybercode/thui-avo-v0` v1, 2026-09-05 | **4.32** | **1.15** | 15 | 21 | 2,572 | 122.5 | 2.30 |
| pooled (`avo-pool`) | **4.36** | — | — | 22.0 | 1,945 | — | — |

Dated readings; `notes/LEDGER-all-runs.md` is the authority.

**The two draws are the SAME BUILD, and that is a measurement, not a claim about the builder**:
`git_status.txt` shows both submodules at `74ff3df` clean on `experiment/avo-v2` in both runs, and
`effective_flags.json` + `taaf_setup_env.json` are identical field for field (`ARC3_AVO_AGENT=true`,
identical `ARC3_AVO_SETTINGS`, seed 20260825, temperature 0.6, yield 60, upscale 8).

| comparison | mean | levels | per-game | p |
|---|---|---|---|---|
| pooled `v10` arm (4 runs) → `avo-pool` | 4.28 → 4.36 (Δ +0.09) | 24.0 → 22.0 | 11 up / 11 down / 4 flipped | **0.9609 NOT-DISTINGUISHABLE** |
| `thuiv3-pool` (4 runs) → `avo-pool` | 4.39 → 4.36 (Δ −0.02) | 24.25 → 22.0 | 10 up / 10 down / 4 flipped | **0.9851 NOT-DISTINGUISHABLE** |
| draw 1 → draw 2 (`--single-baseline`: the question IS the arm's own spread) | 4.40 → 4.32 (Δ −0.08) | 23 → 21 | 9 up / 6 down / 9 flipped | **0.9318 NOT-DISTINGUISHABLE** |

⚠️ **The two draws differ by 1.95× in ACTIONS on one build** — 1,318 → 2,572, with `ls20` alone going
**41 → 1,245** on the same seed, the AVO supervisor loop spinning. So act/lvl 122.5 is this arm's own
spread rather than a lever, and any future AVO read has to carry that spread.

## Verdict

**In-band on public in both draws, and that is itself the finding this arm contributes.** `B60` reads it
as evidence that *the harness lane is model-bound at our model class* — every 100-RHAE system trains no
weights, and the same AVO harness on Qwen3.8 lands where our own chassis lands. Two draws pooled do not
change that: `p = 0.9609` against the `v10` arm, `p = 0.9851` against the `B48` arm.

**The hidden question is ANSWERED: 1.15.** `yocybercode/thui-avo-v0` v1 took the 2026-09-05 slot at
19:53:45Z as **`56039729`**; it resolved COMPLETE and drew **1.15**, read by hand off
`kaggle competitions submissions -v` on 2026-09-06 05:15Z with the standing-best row (`2.03`) returning
unchanged in the same call as the control. The brackets were pre-registered in that submission's own
description, and the **third one fires**:

| hidden | reading | |
|---|---|---|
| in **[1.26, 2.03]** | keeps `B60`'s "the harness lane is model-bound at our model class" | — |
| **> 2.03** | first evidence AVO moves hidden, above our standing best | — |
| **< 1.26** | AVO's extra actions cost on hidden | ← **fired (1.15)** |

⚠️ **The bracket fires and the effect is NOT MEASURABLE, and both halves have to be carried.** The
pre-registered `< 1.26` floor was set from this ledger's ROWS, and **the ledger is not the whole
population**: the submission record carries **six** draws of the `B48` build — 1.63 / 1.59 / 2.03 / 1.35 /
1.35 / **1.22** — of which the last two (draws 5 and 6, 2026-09-03 and 09-04) have **no ledger row at
all**, being resubmits of one kernel version recorded only in prose. So the family's floor on record is
**1.22**, not 1.26; 1.15 sits **0.07** below it, against a within-build range of **0.81** on that one
build. One draw cannot separate 0.07 from a spread eleven times its size. This is the arm's first hidden
reading, not a demonstration that AVO costs on hidden — and pre-registration is what makes even that
sentence sayable, since the bracket was not chosen after the number arrived.

**Standing best does not move**: 1.15 is below `thui-v3-1`'s **2.03**. Among the **12** rows carrying a
numeric hidden value in `notes/LEDGER-all-runs.md` it is the fourth lowest (after 0.11, 0.84, 1.00), and
it is the lowest of the `thui`/`v10` era on either instrument — below the ledger's 1.26 floor and below
the submission record's 1.22.

⚠️ **Its shrink is 4.32 → 1.15 = 3.76×, outside the campaign's population band of 2.68–2.91×** — inside
the per-build span the same ledger already shows (2.14× `thui-v1-1-r2` to 4.80× `thui-v6-0`), which is the
standing reason a per-build ratio is unusable. Do not read this pair as a new shrink estimate.

⚠️ **Dated record, no longer the blocker it was.** `sahasawatt/thui-avo-v0` was **G2-blocked** for
submission: `Tufa Labs` in the solver-credit line sat at char 506, ahead of our own identity at 669, so
the notebook opened as theirs. That kernel is still unfixed on his account — only its owner can Quick Save
it. What was submitted is a **different kernel**: our own `yocybercode/thui-avo-v0`, built from the
corrected notebook, which passed `kaggle_submit_gate.py` on all five gates (G1 version evidence
`Version 1 of 1`, G2 branding position clean, G3 slot unspent, G4 token identity `yocybercode`, G5 record
read back).

## Read next

- [`../prior/thui-prior-v1.md`](../prior/thui-prior-v1.md) — `B60`, which cites this run as its first piece of evidence
- `scripts/kaggle_submit_gate.py` — G2, the branding-position gate that held here, and G4, which decides the kernel's owner
