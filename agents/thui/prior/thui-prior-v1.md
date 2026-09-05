# thui `prior v1` — the exploration prior fires, learns, changes the board, and loses levels

**Line** thui · **family** prior · **directory** [`thui-prior/`](../../../thui-prior) · **ticket** `B60` · **status** ran, closed

## The one change

**Cell 12 only.** A class-level wrap of `ToolAgent.analyze` gives the harness a fallback for the turns
where the LLM produces no action: a per-game online CNN (4 conv layers, 16-channel one-hot 64×64 →
5 action logits + an ACTION6 coordinate map) trained *during play* on `(state, action) → board_changed`,
proposing **one** action through the session's own `step_env`. The prior never overrides an LLM action.

**The trigger is a yield, not `step_executed=False`** — that is what the two smoke runs settled. A turn
that has not acted returns `yielded_control=True` and `play()` re-enters the same step, so `v1` fires on
the **K-th consecutive yield since the last executed action**, K = 2, and hands the yield back unchanged.
Base chassis is `thui-v1-1`; nothing else differs.

## Where it lives

| what | path |
|---|---|
| builder | `thui-prior/build_notebook.py` |
| notebook | `thui-prior/taaf-thui-prior-v1.ipynb` |
| kernel | `sahasawatt/thui-prior-v1` |
| design + read | `notes/B60-exploration-prior-design.md` |

## What it scored

⚠️ **`notes/LEDGER-all-runs.md` has no row for this run.** Every number here is the reading recorded in
`notes/B60-exploration-prior-design.md`, dated **2026-09-02**, and the per-run columns the ledger carries
for other rows (scoring games, act/lvl, Mtok) are **not derived** — blank, not guessed.

| run | public | levels | actions | tokens |
|---|---|---|---|---|
| `thui-prior-v1` | **3.81** | 20 | 1,607 | 2.35 M |

Inside the same-build band `[2.82, 5.24]`, so it ranks nothing on its own. Against the same-seed base
pool (`thuiv1-1` + `-r2`, mean 4.78): delta **−0.97**, `p = 0.5361`. Against the 4-run `v10` pool (4.28):
delta −0.46, `p = 0.7592`. Both **NOT-DISTINGUISHABLE**.

## Verdict

**The mechanism is proven and so is its cost.** 241 fires in 24 of 25 games, **203 (84%) changed the
board**, one level cleared by a prior action directly — and the arm still lost levels, in the shape
`B60` pre-registered as killer #1.

Per-game levels against the two base draws: **above both in 4** (`cn04` 0→1, `m0r0` 0→1, `wa30` 0→1,
`sb26` 2→4 — every one a game where the base sat at 0–2), **below both in 5** (`ft09` 3→2, `lf52` 1→0,
`r11l` 1→0, `re86` 3→1, `tu93` 2→0 — games where the LLM was already progressing). A fallback that
fires on silence cannot tell *stuck* from *mid-plan*, and in a game with a plan its action is a scored
disruption.

That is the same trade the LoRA arm showed — **gain where the base is dead, loss where the base is
alive** — which is the signature of a lever adding variance rather than depth.

## Read next

- [`thui-prior-v1-r2.md`](thui-prior-v1-r2.md) — the second draw, and the pair verdict
- [`thui-prior-v1-1.md`](thui-prior-v1-1.md) — the progress-gated retry that closed the row
- [`thui-lora-v0.md`](../lora/thui-lora-v0.md) — the other arm with this signature
