# thui `lora e1` — the held-out eval that closed the arm null

**Line** thui · **family** lora · **directory** [`thui-lora/eval/`](../../../thui-lora/eval) · **ticket** none — the LoRA arm, cited by `B60` · **status** ran ×2, arm closed null

## The one change

`thui-v1-1` with the **trained** adapter mounted and the analyzer bound to it. Three chained
`.replace()` on the runtime `command` string at the cell-8 seam the [`v0` smoke](thui-lora-v0.md) proved:
`--enable-lora --lora-modules thui-lora=/kaggle/working/adapter`, then
`'LOCAL_ANALYZER_MODEL_ID'` and `'INFERENCE_ANALYZER_MODEL'` → `'thui-lora'`.

⚠️ **`SERVED_MODEL_NAME` itself is not touched** — it also names the vLLM base alias and the health
probe's model field, so renaming the base would break both. Only the two analyzer bindings move, and
every agent request then routes through LoRA while the server plumbing stays stock.

**The gate is held-out games.** Cell 14 filters — at the real game-selection seam, after
`bm.games = _offline_games(...)`, asserted `== 6` — to the six games `train_lora.py` excludes:
`ls20`, `ft09`, `ka59`, `cd82`, `su15`, `wa30`.

⚠️ **Deviation from base conditions, stated because the comparison must say so**: 6 games at the full
7,920 s clock is ~13 h and busts the 12 h GPU cap, so the clock is capped at **5,400 s/game**. Base
per-game wall-clock on these six is far below that in every census run, so the cap binds only where the
base also starved.

## Where it lives

| what | path |
|---|---|
| builder | `thui-lora/eval/build_notebook.py` |
| notebook | `thui-lora/eval/taaf-thui-lora-e1.ipynb` |
| kernel | `sahasawatt/thui-lora-e1` |
| cited in | `notes/B60-exploration-prior-design.md` (the evidence list) |

## What it scored

⚠️ **`notes/LEDGER-all-runs.md` has no row for these runs.** The held-out means below are the reading
recorded in `notes/B60-exploration-prior-design.md`; the per-game direction and the base draws are from
the commit that added the family (`e598cbe`). Per-run columns not derived.

| arm | held-out mean (6 games) |
|---|---|
| adapter draw 1 (L4) | **2.45** |
| adapter draw 2 (L5) | **3.69** |
| base draw (L4) | 4.61 |
| base draw (L6) | 6.35 |

Two adapters, two draws. `ft09` **degraded on both** draws; `ka59` **gained on both**; net below base.

## Verdict

**The gate — *not worse than base* — was not cleared. The arm is closed null.**

Its lasting contribution is a **signature**, and `B60` uses it as such: **gain where the base is dead,
loss where the base is alive**. `B60`'s own prior showed exactly the same shape a day later, which is
why two levers now say the public-25 ceiling for *this* model is set by the games it already plays, not
by the ones it never starts.

## Read next

- [`thui-lora-train.md`](thui-lora-train.md) — where the adapters came from
- [`thui-prior-v1.md`](../prior/thui-prior-v1.md) — the second arm with this signature
