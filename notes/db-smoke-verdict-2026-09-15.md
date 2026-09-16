# thui-db (death blacklist) smoke — verdict (2026-09-15, bp35 / sp80 / tn36 @ 1,800 s, v0 vs ctl same hour)

`sahasawatt/thui-db-v0` (graft) and `sahasawatt/thui-db-ctl` (identical, no wrapper), output dirs `kout-sa-thui-db-{v0,ctl}/`.
Oracle: `thui-db/repeat_fatal_read.py --games bp35,sp80,tn36` over both event sets. Pre-registered read in
`thui-db/build_notebook.py`, applied in order.

## 1. Mechanism — not VOID
v0: `THUI_DB_GRAFT ok`, 21 `THUI_DB_RECORD`, 192 `THUI_DB_INJECT`, 0 wrapper errors; budget=61 detected on tn36 L2 and the budget
line injected for 9 lives. ctl: `control`, 0 / 0.

## 2. Repeat-fatal — v0 lower
| | deaths | budget deaths | repeat-fatal |
|---|---|---|---|
| ctl | 28 | 7 (tn36 L2 = 61/life) | **12** — bp35 L2 `MOUSE(33,21)` x3 + RIGHT x1; sp80 L1 SPACE x3, DOWN x2, LEFT/UP/RIGHT x1 |
| v0 | 21 | 9 (tn36 L2 = 61/life) | **6** — sp80 L2 SPACE x3, LEFT x2, RIGHT x1 |

bp35 is the clean case: ctl died 7 times on L2, four of them repeating the same click; v0 died **once** (at a different cell) and
never repeated. That is the mechanism the graft was built for, on the game it was built from (10 deaths / 7 repeats in wm-v0).

## 3. Levels >= control on all three — FAIL on tn36
| game | ctl | v0 |
|---|---|---|
| sp80 | 0/6 (427 actions, 14 deaths on L1) | 1/6 (477; L1 in 13 actions, then 10 deaths on L2) |
| bp35 | 1/9 | 1/9 |
| tn36 | **2/7** (L2 cleared after 7 lives, 35 actions into L3) | 1/7 (9 lives on L2, not cleared) |

tn36 L2 is a 61-action budget level in both arms. ctl cleared it on its 8th life; v0 had 9 lives and did not. Whether the budget
line ("plan within 61 actions of a reset and do not spend lives on exploration") changed the model's play, or this is the same
draw variance the census shows (tn36 level 2 cleared in 3 of 9 full-25 draws), cannot be told from one smoke — and the rule was
written so that it does not have to be: any game below control = FAIL. **Smoke verdict: FAIL** (rules 1-2 pass, rule 3 fails).

## What the smoke also measured, beyond the rule

- **sp80 L2 has two budgets, and the graft mis-taught one of them.** Per-life counts on L2 across db-v0, b78 and wm-v0: b78 died on
  the 5th-6th SPACE in 7/7 lives (a **5-shot budget**); db-v0 died at **exactly 45 actions** in 7/10 lives (a move budget). The
  gap detector saw mixed gaps (45 / 32 / 23), returned budget=None, and the prompt listed `SPACE` as fatal; the model then fired
  1-2 shots per life instead of 5 and died on the move budget instead. If shooting is how the level is won, the blacklist made
  sp80 L2 worse in the way that matters. A per-ACTION-TYPE budget (count of one action per life constant at death -> "N shots per
  life") is the refinement; it is mechanical and 0 GPU.
- **A budget line does not change tn36.** The model already knew "61 ticks" on its own (transcript, 2026-09-15 diagnosis) and kept
  enumerating; being told again did not stop it. The lever for tn36 is the goal model, not the death ledger.
- **bp35 is the one signal**, and it is n=1 on a 3-game smoke.

## Decision offered

Do NOT push the full-25 as built (rule 3). Two honest options: (a) **refine to v1** — per-action-type budgets, drop the "do not
spend lives on exploration" clause from the budget line (it was written for tn36, where it did nothing, and it may suppress the
shooting sp80 needs), keep the fatal list — and re-smoke once (~40 min x 2, 0 slots); (b) park it beside wm as "mechanism fires,
no level effect shown". The bp35 result is exactly the predicted mechanism, so (a) is defensible; (b) costs nothing.
Cost so far: 2 smoke kernels, ~1.3 GPU-h, 0 slots. Nothing submitted, nothing harvested (3-game smokes are not census rows).

---

# v1 re-smoke (same day, ~11:11-11:50) — verdict: the model reads the line and plays the same; PARK

Refinement (a) was built and run: per-life counting, ACTION budget + per-TYPE budget ("N safe uses per life, keep using it"),
exploration clause dropped, type-budget rule tightened to >= 3 agreeing lives after 2-of-3 produced false budgets on real draws.
`sahasawatt/thui-db-v1` vs a second control `thui-db-ctl-r2` (same morning; the first control stays as draw 1).

## Mechanism — fires exactly as designed
36 RECORD / 122 INJECT / 0 errors. The ledger found **sp80 L1 = 30 actions/life at death 3** and **tn36 L1 = 61 actions/life
(+ 61 MOUSE/life)**, and injected the budget line for every later life (INJECT `budget_actions=30` x22, `61` x30). bp35 L2 got the
fatal list with `MOUSE(row=33, col=21)` from its first death onward (lines=1, distinct 1..3).

## Behaviour — unchanged, or worse
| | ctl (draw 1) | ctl-r2 (draw 2) | v0 | **v1** |
|---|---|---|---|---|
| bp35 | 1/9 | 1/9 | 1/9 | 1/9 |
| sp80 | 0/6 | 1/6 | 1/6 | 1/6 (L1 cleared at action 409 of 419) |
| tn36 | 2/7 | 0/7 | 1/7 | **0/7** (868 actions on L1, 14 lives) |
| deaths / budget deaths | 28 / 7 | 27 / 9 | 21 / 12 | **36 / 27** |
| repeat-fatal (non-budget) | 12 | 7 | 3 | 3 |

- Told "this level has a 30-action budget, make them count", the model died on sp80 L1 **13 times** at exactly 30 (ctl: 14, 11).
- Told "61 per life", it died on tn36 L1 **14 times** at exactly 61 (ctl: 7, 9) — more lives burned, not fewer.
- Told "MOUSE(33,21) ended the game, do not repeat", it clicked (33,21) **twice more** on bp35 L2 (v0 had not; ctl draw 1 had 3x).
- Levels: equal to control draw 2 on all three, below control draw 1 on tn36 (which the controls' own 2-vs-0 spread already
  shows is noise). Repeat-fatal 3 vs 7/12 is the only number in the graft's favour and it sits on 8 eligible deaths.

## Reading
The ledger is correct and the prompt carries it; the policy does not move. This is the same shape as the frontier-5 diagnosis
recorded before the graft existed: the model on tn36 *already knew* "61 ticks" from its own analysis and enumerated anyway. Adding
the fact a second time, in the harness's voice, changed nothing; adding a fatal action to avoid was ignored on the one game built
to test it. Two smokes, two controls, four arms: no level effect, no death-count effect, mechanism proven. **Park thui-db (v0 and
v1) beside thui-wm** — same class of result: in-prompt knowledge about deaths does not convert on this model/harness. What the
death games need is a change in *what the model does with the budget* (search strategy), which prompt lines about the budget do
not supply. Total cost of the lever: 4 smoke kernels, ~2.6 GPU-h, 0 slots. Nothing pushed further; nothing harvested.
