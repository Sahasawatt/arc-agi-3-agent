# thui `reflect v0` — the cadence fired seven times and every reply came back empty

**Line** thui · **family** reflect · **directory** [`thui-reflect/`](../../../thui-reflect) · **ticket** `B62` · **status** smoked, superseded

## The one change

**One extra tool-free chat call every 10 executed steps** (and after a level completes) rewrites the
seven `_summarized_knowledge` fields duck already injects into every prompt — `world_model`,
`goal_model`, `action_model`, `recent_findings`, `open_questions`, `current_plan`, `cross_level_notes`.
It never issues an action and never edits history.

**Why that slot**: those fields are filled only when the model *volunteers* labelled prefixes, and they
are wiped inside the turn that completes a level. Census over three full runs on disk — 60–64% of turns
carry a world model, so **on roughly two turns in five the agent starts with no memory at all**.

Class-level wrap of `ToolAgent.analyze` (cells 0, 12, 14), `B48` chassis, smoke filter `tr87` / `sk48` /
`sc25` at 900 s each.

## Where it lives

| what | path |
|---|---|
| builder | `thui-reflect/build_notebook.py --owner=yocybercode --base=v3` |
| notebook | `thui-reflect/taaf-thui-reflect-v0.ipynb` |
| kernel | `yocybercode/thui-reflect-v0` — pushed from the mac; the `sahasawatt` weekly GPU quota was the only blocker |
| design + read | `notes/B62-reflection-memory-design.md` |

## What it scored

**Nothing — a 3-game 900 s smoke.** COMPLETE 2026-09-04 ~10:24Z, wall **1,319 s**, queue wait ~2h40m.
Read twice and independently; every number agrees.

| oracle | result |
|---|---|
| **P3** COMPLETE, no errors | **PASS** — 3 games (`tr87` 10 actions / `sk48` 33 / `sc25` 28 with **1 level**), `wrapper error` 0, `call FAILED` 0 |
| **P1** ≥ 1 parsed field in ≥ 2 of 3 games | **FAIL BY MECHANISM** — all 7 calls returned `fields=[] content_chars=0`, ~3.5k tokens billed each |
| **P2** the next turn carries the fields | **vacuous** — the `lines=3-4` injected were the model's own volunteered prefixes, not the reflection's |

The cadence itself worked: **7 calls, 6 `reason=k` and 1 `reason=level`** — the latter exactly on `sc25`'s
clear — latency 19.9–22.1 s, mean 20.7 s.

## Verdict

🔴 **The harness runs every analyzer call with `LOCAL_ANALYZER_ENABLE_THINKING=true`, and
`_chat_completion` reads that module global at call time** (`tool_agent.py:1533`) — so the memory call
inherited thinking and spent its whole 700-token cap inside `<think>`. Latency ≈ 700 tok at ~35 tok/s
confirms it.

⚠️ **The pre-registered `empty ≥ half` kill rule fired on this draw, and it fired on a build defect
rather than on the design's ceiling — `B62` is not closed on it.**

**The lesson generalises past this arm**: thinking is on globally, so any capped side-call inside duck
must switch it off for that call or budget for it. That fix became `v0-1` — and, one run later, the
mechanism of a much worse failure.

## Read next

- [`thui-reflect-v0-1.md`](thui-reflect-v0-1.md) — thinking off for the memory call, and P1/P2/P3 all pass
- [`thui-reflect-v1.md`](thui-reflect-v1.md) — where the same fix poisoned a 25-game run
