# thui `compact v0` — the smoke: every oracle passed, and the transcript showed the header being read as a title

**Line** thui · **family** compact · **directory** [`thui-compact/`](../../../thui-compact) · **ticket** `B65` · **status** smoked, superseded by the #128 build

## The one change

**Cell 12 only, on the `B48` chassis.** A class-level wrap of `ToolAgent._persistent_history_messages` — the
harness's own trimmer — diffs its input against its output, buffers the turns it dropped, and every K
drops issues one tool-free call (thinking off on that thread, cap 600, timeout 90 s, two-strike breaker)
that rewrites a five-label **memento** (Rules / Unknown / No-op-harmful / Hypotheses / Plan) from the
previous memento plus the dropped turns. The memento is folded into the first user message and
stripped again before the next trim, so it is never counted as a turn. Smoke constants: window **8**,
K **4** (the full build keeps 30 / 10), cell 14's 3-game / 900 s filter (`tr87` / `sk48` / `sc25`).

## Where it lives

| what | path |
|---|---|
| builder | `thui-compact/build_notebook.py --owner=yocybercode` (v0 = no `--full`) |
| notebook | `thui-compact/taaf-thui-compact-v0.ipynb` |
| kernel | `yocybercode/thui-compact-v0` — pushed from the mac, COMPLETE 2026-09-05 09:12Z |
| design + read | `notes/B65-compaction-of-dropped-history-design.md` |

## What it scored

**Nothing — a 3-game 900 s smoke.** Read twice, from the relay and independently from the kernel output.

| oracle | result |
|---|---|
| **P1** at least 2 fires per game | **NOT REACHED** — 3 fires total: one `analysis_step` is up to 12 model calls, so window 8 fills inside step 1–2 and 900 s gives one fire per game |
| memento non-empty, labels | **PASS** — 551 → 622 → 654 chars, labels **5/5** on every fire |
| **P2** landed | **PASS** — 3/3 |
| **P3** harness | **PASS** — 3 games finished, `wrapper error` 0, `call FAILED` 0, completion mean 1,451 |
| latency | 4.7 / 5.3 / 4.9 s — no kill rule fired |

## Verdict

**The mechanism works, and the smoke found two defects the oracles could not see.** Every fire line read
`game=arti` — on Kaggle the state files sit flat in `artifacts/`, so the label came from the directory
(fixed in #127, label from the state-path stem). And in `tr87`'s transcript the model, handed the memento
as the **first text of its user turn**, wrote *"The title MEMENTO suggests a memory game"* and spent
the whole turn on that reading — 0 actions, yield on `turn_time_budget`. Actions per request across the
four same-game smokes: compact **0.37** vs reflect-v0 1.18 / reflect-v0-1 0.75 / rank-v0-1 0.74 (n = 1
each). #128 rewords the header (*"[Your own notes from earlier turns of this conversation … Not part of
the game.]"*); a local replay of the exact request on an 8B reproduced the misread **6/9** with the old
header and **0/9** with the new one. The full run (`v1`) was pushed before either fix landed.

## Read next

- [`thui-compact-v1.md`](thui-compact-v1.md) — the full run, on the pre-fix build
- [`../reflect/thui-reflect-v0-1.md`](../reflect/thui-reflect-v0-1.md) — the other smoke that passed and hid a defect only the transcript showed
