# thui `prior v1.1` — the progress gate worked exactly as specified and closed the row

**Line** thui · **family** prior · **directory** [`thui-prior/`](../../../thui-prior) · **ticket** `B60` · **status** ran, closed

## The one change

Same cell-12 payload as [`v1`](thui-prior-v1.md), **two constants**: `_PRIOR_YIELD_K` 2 → **3** and
`_PRIOR_QUIET_S` 0 → **300**. A fire now needs both the K-th consecutive yield *and* 300 s since the last
progress, where `last_progress` is reset by a level-up or by a board-changing action **not** issued by the
prior (a `from_prior` flag around the fallback's own `step_env` call).

It was built to keep the dead-game wake-ups (`cn04`/`m0r0`/`wa30` are games where nothing changes for the
whole clock) while removing the mid-plan disruption `v1`'s pair showed on `ft09`, **by construction**. The
builder is parameterised (`--v11`, `--suffix=`), and rebuilding `--full` still emits K = 2 / QUIET = 0
byte-for-byte — that regression is asserted.

## Where it lives

| what | path |
|---|---|
| builder | `thui-prior/build_notebook.py --v11` |
| notebook | `thui-prior/taaf-thui-prior-v1-1.ipynb` |
| kernel | `sahasawatt/thui-prior-v1-1` |
| design + read | `notes/B60-exploration-prior-design.md` |

## What it scored

⚠️ **`notes/LEDGER-all-runs.md` has no row for this run.** Reading recorded in
`notes/B60-exploration-prior-design.md`, dated **2026-09-02**; per-run columns not derived.

| run | public | levels | fires | changed |
|---|---|---|---|---|
| `thui-prior-v1-1` | **3.04** | 20 | 144 in 21 games | 120 |

Against the same-seed base pair: delta **−1.74**, levels 24.0 → 20, `p = 0.1565`
**NOT-DISTINGUISHABLE** — and the arm's worst mean of four runs.

**Every fire happened at quiet ≥ 310 s**, so the gate did what it was specified to do.

## Verdict

**It did not buy the outcome it was built for, and `B60` CLOSES: null-to-negative.**

`ft09` **3 → 2** and `re86` **3 → 2** again — the LLM's plans on those games span silences longer than
300 s, so a silence gate cannot separate *thinking* from *stuck* there either — while the dead-game
wake-ups it was meant to keep were mostly lost (`cn04` 0 → 1 kept; `m0r0` and `wa30` back to 0).

⚠️ **`thui-prior-v1-1-r2` was not needed to decide, and it also never landed.** The oracle is the pair's
levels against the base pair's 24.0; with r1 at 20, r2 would have to clear **≥ 28 levels** for the pair to
reach 24 — more than any 25-game run on this chassis has ever cleared at the standard clock (best 28,
`v10cal` and `thui-v6-0`; `clock2x`'s 30 needed a doubled clock). Its push then failed anyway, most likely
GPU quota after ~25 GPU-h on that account that day, and was not retried. **No page for it: it has a
notebook and a `kernel-metadata` file and no run.**

**No hidden slot was spent on this arm.** A future version needs a trigger keyed on the LLM's own STATE
— its transcript declaring it has no hypothesis — rather than on time; that is a different design and
gets its own row.

## Read next

- [`thui-prior-v1.md`](thui-prior-v1.md) · [`thui-prior-v1-r2.md`](thui-prior-v1-r2.md) — the pair this refines
- [`thui-rank-v0.md`](../rank/thui-rank-v0.md) — `B61`, the same prior moved to a role that spends no action
