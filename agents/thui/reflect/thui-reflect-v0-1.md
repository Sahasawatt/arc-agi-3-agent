# thui `reflect v0.1` — the fix that made the smoke pass, and hid a threading defect from it

**Line** thui · **family** reflect · **directory** [`thui-reflect/`](../../../thui-reflect) · **ticket** `B62` · **status** smoked, superseded

## The one change

Three things, all on the memory call and none on the memory itself: **thinking OFF for that call only**
(`_ta._LOCAL_ANALYZER_ENABLE_THINKING` patched inside `_reflect`, restored in `finally`), the output cap
**700 → 1200**, and a fallback that parses the seven lines out of `reasoning_content` when `content` is
still empty. The log line gained `completion=` and `from_reasoning=`. Same smoke, same oracle as
[`v0`](thui-reflect-v0.md).

## Where it lives

| what | path |
|---|---|
| builder | `thui-reflect/build_notebook.py` (v0-1 variant) |
| notebook | `thui-reflect/taaf-thui-reflect-v0-1.ipynb` |
| kernel | `yocybercode/thui-reflect-v0-1` |
| design + read | `notes/B62-reflection-memory-design.md` |

## What it scored

**Nothing — a 3-game 900 s smoke.** COMPLETE 2026-09-04 ~11:38Z, wall **1,421 s**, queue wait ~20 min.

| oracle | result |
|---|---|
| **P1** parsed fields | **PASS** — 5 calls, **every one returned all seven fields** in all three games; `content_chars` 1,123–1,787, `completion=` 298–441 tokens, `from_reasoning=False` every time. Against `v0`: **7 of 7 empty → 0 of 5 empty** |
| **P2** injection | **PASS** — `P2 injected lines=9` on every post-reflection turn (`v0`: 3–4, and those were the model's own prefixes). Nine = the seven fields plus two header lines |
| **P3** COMPLETE | **PASS** — 3 games (`tr87` 12 actions / `sc25` 20 / `sk48` 30, 0 levels), `wrapper error` 0, `call FAILED` 0 |

Latency **8.7–14.7 s, mean 12.1 s** (`v0`: 20.7 s at 700 tokens of pure thinking). Both kill rules —
mean > 30 s, empty ≥ half — clear. The fallback never had to fire: **thinking-off alone was the fix.**

## Verdict

**The design is delivered at smoke width**, and on that reading `B62` was chosen as the build for the
2026-09-04 draw.

🔴 **The same fix carried the defect that ruined the full run.** `_reflect` flipped a **module global**
that all 25 game threads read, and a 3-game smoke rarely has two memory calls in flight — so the global
looked correct here (`v0-1` completion mean 1,152, thinking mostly on) and was catastrophic at 25-game
width. See [`v1`](thui-reflect-v1.md).

⚠️ Two things a smoke of this shape structurally cannot see, both learned the expensive way: a **latency**
cost that is a contention effect, and a **shared-state** bug whose window is the union of concurrent
calls. Either needs full width, or a budget computed against the per-turn yield × 25.

## Read next

- [`thui-reflect-v1.md`](thui-reflect-v1.md) — the full run, and the confounder
- [`thui-reflect-v1-1.md`](thui-reflect-v1-1.md) — the thread-local fix and the paired read
