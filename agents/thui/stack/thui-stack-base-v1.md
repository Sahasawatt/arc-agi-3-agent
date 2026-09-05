# thui `stack base v1` — our own copy of the standing-best build, with no arm in it

**Line** thui · **family** stack · **directory** [`thui-stack/`](../../../thui-stack) · **ticket** none — the composition rule for `B61`/`B62` · **status** built, NOT RUN

## The one change

**None, and that is the design.** Built with no `--arms`, `thui-stack` emits the `B48` chassis
(`thuiv3/taaf-thui-v3-0.ipynb` — `thui-v1-1` + yield 180, the build that drew the standing best 2.03)
**byte-identical on cells 1–16**. Only cell 0's markdown differs.

**Why an empty stack is a build at all**: it is exactly what a resubmit of the standing best is, produced
by our own builder rather than by re-pushing someone else's notebook — so the draw-candidate path and the
arm-composition path are the same path, and an empty arm list is the default rather than a special case.

**The composition rule this file exists to enforce**: an arm enters the stack **only after its own paired
public read clears the `B35` floor** — `+1` level in ≥ 6 of 25 games on both draws, against
`eval/fixtures/thuiv3-pool.json`. Until then the stack is a smoke artifact, **never a submission**. On
2026-09-04, when the builder was written, **no arm had read, so the default stack was empty**.

## Where it lives

| what | path |
|---|---|
| builder | `thui-stack/build_notebook.py --full` (no `--arms`) |
| notebook | `thui-stack/taaf-thui-stack-base-v1.ipynb` |
| kernel | **none** — never pushed |

⚠️ `thui-stack/kernel-metadata.json` names `sahasawatt/thui-stack-reflect-rank-v0`, the **other** variant:
the builder rewrites one metadata file, so the tracked copy records whichever build ran last and is not a
per-variant record.

## What it scored

**Nothing. It has never run.** `notes/LEDGER-all-runs.md` has no row and should not gain one until it does.

## Verdict

**None — it is a chassis emitter.** Its value is the invariant it asserts: with no arms it must reproduce
`thui-v3-0` byte-for-byte, which is what makes any *later* stacked build's diff readable as the arms and
nothing else.

## Read next

- [`thui-stack-reflect-rank-v0.md`](thui-stack-reflect-rank-v0.md) — the two-arm variant, and why chaining works
- [`../v3/v3-0.md`](../v3/v3-0.md) — the chassis this emits
