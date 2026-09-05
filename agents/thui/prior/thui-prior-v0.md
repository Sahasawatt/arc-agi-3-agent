# thui `prior v0` — the smoke that found the trigger was wrong, not rare

**Line** thui · **family** prior · **directory** [`thui-prior/`](../../../thui-prior) · **ticket** `B60` · **status** smoked ×2, superseded by `v1`

## The one change

The `B60` fallback at smoke width: `thui-v1-1` chassis, cells 0 / 12 / 14, three games at 900 s each —
**`g50t`** (0 levels in 19/19 runs), **`sk48`** (19/20), **`tr87`** (17/19), i.e. the three the census says
die most.

## Where it lives

| what | path |
|---|---|
| builder | `thui-prior/build_notebook.py` |
| notebook | `thui-prior/taaf-thui-prior-v0.ipynb` |
| kernel | `sahasawatt/thui-prior-v0` — v1 is smoke run 1, v2 is smoke run 2 |
| design + read | `notes/B60-exploration-prior-design.md` |

## What it scored

**Nothing, and it must not be scored** — the numbers from a 3-game 900 s smoke are not a score and must
not enter any ledger.

**Run 1** (2026-09-02 08:10 UTC) — COMPLETE in 15m33s, 58 actions over 3 games.

| oracle | result |
|---|---|
| **P2** the prior trains | **PASS** — 100 updates, finite loss, buffer growing |
| **P3** harness path intact | **PASS** — COMPLETE, `summary.txt` prints the 3 games |
| **P1** ≥ 1 fallback fires | **FAIL — 0 fires** |

**Run 2** (2026-09-02 09:38 UTC, the `v2` trigger) — COMPLETE in 15m00s. **P1 / P2 / P3 all PASS**:
**4 fires, all `via=yield`, all `executed=True`, all `changed=True`** (DOWN ×1, UP ×3), 0 level-ups, 6
prior updates, actions **58 → 84** (`g50t` 1 → 8, `tr87` 22 → 42, `sk48` 35 → 34).

## Verdict

🔴 **The wrapper never fired because the trigger was wrong, not because dead turns are rare.** Read from
the event logs: `g50t` step 2 ended `Yielded control to solver: turn_time_budget` and re-entered, again
and again, until `stop_requested` — **7 analysis rows for 1 action in 900 s**. A turn that has not acted
does **not** return `step_executed=False`; the 60 s yield returns `yielded_control=True` and `play()`
re-enters the SAME step. So the no-action signal *is* the yield, and the pre-registered killer #2
("trigger rarity") was a **mis-specified trigger**.

The `v2` trigger that followed: fire on the **K-th consecutive yield since the last executed action**
(K = 2, ≥ 120 s silent), execute one prior action, hand the yield back unchanged. `yields_since_action`
resets on any executed action, the LLM's included.

⚠️ **Two facts corrected in the same read, both wider than this arm.** Games run **in parallel** inside
`bm.run` — total wallclock 2,734 s ≈ 3 × 911 s against a 15m33s duration, so a 25-game run at 7,920 s/game
is **one 2.2 h slice with 25 games sharing one vLLM server**. That also closes the campaign's open
"~56 s/game" item: it was never per-game serial time. And the yield **reason** is not on
`AnalyzerTurnResult` — only the bool — but `session.should_stop()` separates `stop_requested` from
`turn_time_budget`.

⚠️ **The per-game fire split is not readable from run 2's log**: the fire line did not carry the game id.
It was added for `v1`.

## Read next

- [`thui-prior-v1.md`](thui-prior-v1.md) — the full run this gated
- [`../reflect/thui-reflect-v0-1.md`](../reflect/thui-reflect-v0-1.md) — the other smoke that passed and hid a defect only full width could show
