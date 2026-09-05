# thui `avo v0` — Tufa's own AVO agent, run as they ship it, in-band on public

**Line** thui · **family** avo · **directory** [`thui-avo/`](../../../thui-avo) · **ticket** none — evidence for `B60` · **status** ran, public read done, hidden open

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
| kernel | `sahasawatt/thui-avo-v0` |
| cited in | `notes/B60-exploration-prior-design.md` (the evidence list) |

## What it scored

⚠️ **`notes/LEDGER-all-runs.md` has no row for this run.** The public mean and the p-value below are the
reading recorded in `notes/B60-exploration-prior-design.md`; the levels and the run date are from the
commit that added the builder (`482accb`). Per-run columns not derived.

| run | public | levels | benchmark name |
|---|---|---|---|
| `thui-avo-v0`, 2026-09-02 | **4.40** | 23 | `avo-kaggle` |

Against the `B57` pooled `v10` arm (mean 4.28): delta **+0.13**, `p = 0.946`, **NOT-DISTINGUISHABLE**.
Inside the same-build band `[2.82, 5.24]`, so **it ranks nothing on public**.

## Verdict

**In-band, and that is itself the finding this arm contributes.** `B60` reads it as evidence that *the
harness lane is model-bound at our model class* — every 100-RHAE system trains no weights, and the same
AVO harness on Qwen3.8 lands where our own chassis lands.

**The hidden question is open and costs a slot.** Nothing here answers it.

🔴 **Blocked from submission as the kernel currently stands.** `kaggle_submit_gate.py --dry-run` on
`sahasawatt/thui-avo-v0` returned **G2 BLOCKED**: `Tufa Labs` in the solver-credit line sat at char 506,
ahead of our own identity at 669, so the notebook opened as theirs. The tracked notebook was fixed —
the H1 now names Thuitanium first, every credit line unchanged, `scan_branding()` returns `None` with a
positive control firing — but **that fix was never pushed**, because a new kernel version is a GPU run and
the weekly quota was exhausted on that account. Push the rebuilt notebook before any submission.

## Read next

- [`thui-prior-v1.md`](../prior/thui-prior-v1.md) — `B60`, which cites this run as its first piece of evidence
- `docs/` and `scripts/kaggle_submit_gate.py` — G2, the branding-position gate that held here
