# thui `stack reflect+rank v0` — two arms chained on one chassis, and neither has earned its place

**Line** thui · **family** stack · **directory** [`thui-stack/`](../../../thui-stack) · **ticket** none — composes `B62` and `B61` · **status** built, NOT RUN

## The one change

`--arms=reflect,rank`: the [`B62`](../reflect/thui-reflect-v1-1.md) reflection memory and the
[`B61`](../rank/thui-rank-v0.md) ranker/veto cell-12 payloads are **appended in order** on the `B48`
chassis, plus cell 14's 3-game / 900 s smoke filter.

**Chaining is wrapping the wrapper.** Both arms wrap `ToolAgent.analyze` at class level, so the second
arm's `_orig_analyze` is the first arm's wrapper and every kwarg — `step_env` included — passes through;
the outermost wrap is asserted. Each arm's payload is imported **from that arm's own builder**
(`CELL12_SUFFIX`), so there is one source of truth per arm and no copy to drift.

⚠️ **`gemma` (`B64`) is not stackable here** — it swaps the model and wheelhouse in cells 6/8 and must read
alone.

## Where it lives

| what | path |
|---|---|
| builder | `thui-stack/build_notebook.py --arms=reflect,rank` |
| notebook | `thui-stack/taaf-thui-stack-reflect-rank-v0.ipynb` |
| kernel | **none** — never pushed |
| metadata | `thui-stack/kernel-metadata.json` names `sahasawatt/thui-stack-reflect-rank-v0` |

## What it scored

**Nothing. It has never run**, and if it did, a 3-game 900 s smoke produces no score. No ledger row.

## Verdict

🔴 **Not submittable as composed, by the family's own rule.** An arm enters the stack only after its paired
public read clears the `B35` floor against `eval/fixtures/thuiv3-pool.json`, and **neither arm has**:

- **`B62` reflect** — [`v1-1`](../reflect/thui-reflect-v1-1.md) read `p = 0.998` NOT-DISTINGUISHABLE at
  n = 1, and the row's own oracle asks for ≥ 2 runs per arm;
- **`B61` rank** — [`v0-1`](../rank/thui-rank-v0-1.md) never exercised the veto branch at all; the arm's
  only evidence is *does not crash*.

**A stack with an unread arm is a smoke artifact, never a submission.** That is the whole content of this
page, and it is worth a page precisely because the notebook exists and looks ready.

## Read next

- commit `2a552c2` — the empty stack (`thui-stack-base-v1`, no page here) emits the `B48` chassis
  byte-identical, which is what makes a stacked build's diff readable as the arms and nothing else
- [`../reflect/thui-reflect-v1-1.md`](../reflect/thui-reflect-v1-1.md) · [`../rank/thui-rank-v0-1.md`](../rank/thui-rank-v0-1.md) — where each arm actually stands
