# thui `prior v1-r2` — the second draw, and the four per-game moves that survive both

**Line** thui · **family** prior · **directory** [`thui-prior/`](../../../thui-prior) · **ticket** `B60` · **status** ran, closed

## The one change

**None.** `v1-r2` is the **same build** as [`v1`](thui-prior-v1.md) — the yield-triggered prior at K = 2,
no progress gate — run a second time. `B60`'s oracle asks for ≥ 2 runs per arm because `B37` measured
that the seed does not reproduce, so a single draw is not the arm.

## Where it lives

| what | path |
|---|---|
| builder | `thui-prior/build_notebook.py` — unchanged from `v1` |
| notebook | `thui-prior/taaf-thui-prior-v1-r2.ipynb` |
| kernel | `sahasawatt/thui-prior-v1-r2` |
| design + read | `notes/B60-exploration-prior-design.md` |

## What it scored

⚠️ **`notes/LEDGER-all-runs.md` has no row for this run.** Reading recorded in
`notes/B60-exploration-prior-design.md`, dated **2026-09-02**; per-run columns not derived.

| run | public | levels | actions |
|---|---|---|---|
| `thui-prior-v1-r2` | **3.92** | 21 | 1,510 |

223 fires, 185 (83%) changed the board — the same rates as run 1.

### The pair, read under the `B57` baseline rule

| baseline pool | mean | levels | delta | p |
|---|---|---|---|---|
| same-seed base (`thuiv1-1` + `-r2`) | 4.78 → **3.87** | 24.0 → **20.5** | −0.92 | **0.4605** NOT-DISTINGUISHABLE |
| 4-run `v10` arm | 4.28 → 3.87 | 24.0 → 20.5 | −0.41 | 0.6171 NOT-DISTINGUISHABLE |

## Verdict

**NOT BETTER, and the sign is negative on both draws.** The arm nets **−3.5 levels per run** against the
base pair.

The second draw is what separates signal from noise in the per-game table. **Consistent across both
prior draws**: `cn04`, `m0r0`, `wa30` go **0 → 1 in 2 of 2** (the base is 0 in 2 of 2), and `ft09` goes
**3 → 2 in 2 of 2**. Everything else flips between draws — `sb26` 4 then 1, `re86` 1 then 3, `lp85` 1
then 3 — so the single-draw per-game reading in [`v1`](thui-prior-v1.md) is mostly noise, and only these
four moves are the arm's.

## Read next

- [`thui-prior-v1.md`](thui-prior-v1.md) — the first draw and the mechanism
- [`thui-prior-v1-1.md`](thui-prior-v1-1.md) — the progress gate built to keep the wake-ups and drop `ft09`
