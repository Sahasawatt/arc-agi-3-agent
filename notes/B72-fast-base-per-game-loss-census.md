# B72 — the fast base, game by game: where every point is lost (`thui-fast-v0`, two draws)

Measured 2026-09-08 from the two draws' own artifacts (`benchmark.json` history + `score.json`), 0 slots, 0 GPU.
Tool: `eval/level_loss_census.py <run_dir>…` (pure read; no model). Base = the `fast` arm (B69, pooled 8.69 public,
hidden 3.21 as 56081325). Question charted: **with this serving as the floor, which games lose score, to what, and
what would one more level on each pay?**

## The score is levels, and deeper levels weigh more

`taaf/game.py::_compute_final_score` (mirrors `arc_agi.scorecard` v0.9.8): level k (1-indexed) has weight k; a cleared
level scores `min(115, (baseline/actions)² × 100)`; the game is capped at `Σ weights of scored levels / Σ all weights × 100`.
Two consequences the census confirms:

- **Efficiency is not where the points are.** Cleared levels score at the cap almost everywhere: mean efficiency loss
  **1.1 of 100 per game**; unreached levels **90.2 of 100**. The quadratic action cost that B70's breaker was built
  around costs this base nothing measurable — any lever that spends actions to reach a level is free on this base.
- **The next level on a deep game pays 2–7× the first level on a zero game.** tr87 at 4/6 → +23.8; ft09 / sc25 at 3/6
  → +19.0; lp85 at 5/8 → +16.7; dc22 / vc33 → +14.3. The three games at 0 in every draw (g50t, sk48, sp80) pay
  +3.6 / +2.8 / +4.8 for their first level. Six deep games' next level together = +107 points = **+4.3 mean** if all
  landed; all three zero games' first level = +11 = +0.45.

## Table (draw 1 / draw 2)

| game | N | levels (d1/d2) | score | unreached | eff-loss | next lvl pays | burned | stuck s | dominant action on the failed level | s/act | tok/act | tclear (last draw) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ar25 | 8 | 2/2 | 8.33/8.33 | 91.7 | 0.0 | 8.3 | 252/75 | 5318/3965 | ACTION1 53% ; ACTION2 28% | 21/51 | 150/593 | [440, 3955] |
| bp35 | 9 | 0/1 | 0.00/0.31 | 98.9 | 1.0 | 4.4 | 25/136 | 7920/5211 | ACTION3 36% ; ACTION6+xy 63% | 317/38 | 3110/194 | [2709] |
| cd82 | 6 | 2/1 | 14.29/4.76 | 90.5 | 0.0 | 9.5 | 92/42 | 5384/3459 | ACTION4 32% ; ACTION4 31% | 57/80 | 796/815 | [4461] |
| cn04 | 6 | 1/1 | 1.19/2.38 | 95.2 | 3.0 | 9.5 | 9/176 | 818/5821 | ACTION4 89% ; ACTION2 41% | 69/26 | 388/220 | [2099] |
| dc22 | 6 | 1/2 | 0.91/13.19 | 90.5 | 2.5 | 14.3 | 16/0 | 1575/134 | ACTION6+xy 44% ; - | 92/0 | 1242/0 | [3850, 7786] |
| ft09 | 6 | 4/3 | 47.62/18.53 | 61.9 | 5.0 | 19.0 | 27/78 | 2793/4209 | ACTION6+xy 100% ; ACTION6+xy 100% | 87/54 | 1165/239 | [320, 512, 3711] |
| g50t | 7 | 0/0 | 0.00/0.00 | 100.0 | 0.0 | 3.6 | 121/84 | 7920/7920 | ACTION2 45% ; ACTION2 38% | 64/90 | 741/1091 | [] |
| ka59 | 7 | 1/2 | 3.57/10.71 | 92.9 | 0.0 | 10.7 | 115/85 | 6241/1799 | ACTION1 31% ; ACTION2 28% | 54/21 | 741/278 | [1431, 6121] |
| lf52 | 10 | 1/1 | 1.82/1.82 | 98.2 | 0.0 | 3.6 | 57/79 | 5499/6637 | ACTION6+xy 42% ; ACTION6+xy 35% | 95/83 | 838/684 | [1283] |
| lp85 | 8 | 3/5 | 16.67/41.67 | 70.8 | 0.0 | 16.7 | 9/28 | 2797/1248 | ACTION6+xy 100% ; ACTION6+xy 100% | 281/28 | 2955/560 | [613, 2205, 3217, 5643, 6672] |
| ls20 | 7 | 1/1 | 3.57/0.75 | 96.4 | 1.4 | 7.1 | 164/17 | 6666/1127 | ACTION2 30% ; ACTION1 35% | 40/33 | 425/184 | [6793] |
| m0r0 | 6 | 1/1 | 4.19/4.76 | 95.2 | 0.3 | 9.5 | 41/74 | 6049/4596 | ACTION2 63% ; ACTION2 36% | 108/61 | 984/467 | [3324] |
| r11l | 6 | 1/1 | 4.76/4.76 | 95.2 | 0.0 | 9.5 | 88/19 | 7374/6386 | ACTION6+xy 97% ; ACTION6+xy 95% | 83/274 | 721/3834 | [1534] |
| re86 | 8 | 3/2 | 9.45/8.33 | 87.5 | 3.6 | 8.3 | 57/28 | 2596/5203 | ACTION3 32% ; ACTION1 68% | 43/119 | 148/693 | [595, 2717] |
| s5i5 | 8 | 1/2 | 1.42/8.33 | 94.4 | 0.7 | 8.3 | 109/114 | 6482/5551 | ACTION6+xy 100% ; ACTION6+xy 100% | 59/47 | 296/461 | [569, 2369] |
| sb26 | 8 | 1/1 | 2.78/2.78 | 97.2 | 0.0 | 5.6 | 61/165 | 7646/7557 | ACTION6+xy 92% ; ACTION6+xy 88% | 112/46 | 1173/492 | [363] |
| sc25 | 6 | 0/3 | 0.00/20.20 | 85.7 | 4.2 | 19.0 | 93/3 | 7920/320 | ACTION6+xy 60% ; ACTION3 33% | 84/102 | 1085/965 | [5907, 6621, 7600] |
| sk48 | 8 | 0/0 | 0.00/0.00 | 100.0 | 0.0 | 2.8 | 92/156 | 7920/7920 | ACTION4 37% ; ACTION4 35% | 85/50 | 641/679 | [] |
| sp80 | 6 | 0/0 | 0.00/0.00 | 100.0 | 0.0 | 4.8 | 434/233 | 7920/7920 | ACTION4 30% ; ACTION4 28% | 18/33 | 162/344 | [] |
| su15 | 9 | 2/1 | 6.67/2.22 | 95.6 | 0.0 | 4.4 | 48/75 | 1851/6780 | ACTION6+xy 98% ; ACTION6+xy 97% | 38/90 | 196/597 | [1140] |
| tn36 | 7 | 1/0 | 0.30/0.00 | 98.2 | 1.6 | 3.6 | 67/251 | 4339/7920 | ACTION6+xy 99% ; ACTION6+xy 98% | 64/31 | 429/382 | [] |
| tr87 | 6 | 4/4 | 47.62/47.62 | 52.4 | 0.0 | 23.8 | 42/31 | 3071/1992 | ACTION1 64% ; ACTION1 55% | 73/61 | 1017/509 | [3089, 4323, 5110, 5928] |
| tu93 | 9 | 2/3 | 4.40/8.15 | 90.0 | 3.7 | 8.9 | 73/46 | 3902/2909 | ACTION1 36% ; ACTION4 46% | 52/60 | 632/311 | [1001, 2813, 5011] |
| vc33 | 7 | 3/3 | 21.19/21.08 | 78.6 | 0.3 | 14.3 | 108/102 | 3975/5186 | ACTION6+xy 98% ; ACTION6+xy 98% | 34/50 | 132/569 | [822, 1668, 2734] |
| wa30 | 9 | 1/1 | 0.93/2.22 | 97.8 | 0.6 | 4.4 | 319/68 | 3674/5651 | ACTION3 28% ; ACTION3 32% | 11/83 | 49/1080 | [2269] |

mean score 8.69; mean loss per game: unreached 90.2, efficiency 1.1 (of 100)
level-clears in the last 1,900 s of the wall: 9 of 77 -> [('cn04', 1, 7102), ('dc22', 1, 6345), ('su15', 2, 6069), ('dc22', 2, 7786), ('ka59', 2, 6121), ('lp85', 5, 6672), ('ls20', 1, 6793), ('sc25', 2, 6621), ('sc25', 3, 7600)]

`unreached` / `eff-loss` are points of 100 lost per game (mean of the two draws); `next lvl pays` is for one more level
on the last draw; `burned` = actions on the level never cleared; `stuck` = seconds of the 7,920 s wall spent on it;
`dominant action` = the most frequent action id on that level and its share (`+xy` = a click with coordinates).

## Reading — four failure shapes

1. **Click-only stall** (`ACTION6+xy` ≥ 88 % of the failed level's actions for ≥ 3,000 s): **s5i5** (100 %, 5,400–6,400 s),
   **sb26** (88–92 %, ~7,500 s), **tn36** (98–99 %), **vc33** (98 %, 3,600–5,100 s at level 4), **ft09** (100 % at level
   4–5), **su15** (97–98 %), **r11l** (95–97 %). The model keeps clicking; either the target is wrong (perception) or the
   level needs a non-click action it never tries (action-space blindness). The transcript (`solver_analysis/*.html` in
   the kernel output) can tell the two apart; this census cannot. → **B73**.
2. **Deep-tail wall** — the level the fast base fails on has NEVER been cleared by any banked run (per-level census +
   every fixture): tr87 L5, ft09 L5, vc33 L4, lp85 L6, sc25 L4. Whether that is a capability wall or a draw/time question
   is unmeasured; 30-odd draws at 0 says wall. → **B74**. Contrast: levels other arms reached that this base does not
   — ar25 L3–5 (thuiv1-1 reached 5; fast sits at 2 both draws, burning 75–252 actions, 4,000–5,300 s), re86 L4 (v18),
   sb26 L4 (thui-prior-v1) — those are reachable and are where the solver (not the serving) still matters.
3. **Wall-bound clears** — 9 of the 77 level-clears across both draws landed in the last 1,900 s (dc22 L2 at 7,786 s,
   sc25 L3 at 7,600 s, cn04 L1 at 7,102 s, ls20 L1 at 6,793 s, lp85 L5 at 6,672 s, sc25 L2, ka59 L2, su15 L2, dc22 L1).
   The draw-to-draw swing on those games (sc25 0 → 3 levels, dc22 1 → 2) is this component; a hidden rerun at 4 waves
   sits on it, and it is what a "favourable draw" looks like from inside. Measured, no ticket — it prices the hidden
   variance, it is not a lever.
4. **Thinking-bound turns** — bp35 d1 (317 s / action, 3,110 tok), r11l d2 (274 s, 3,834 tok), lp85 d1 (281 s, 2,955 tok):
   25–30 actions in a whole game because each turn spends 4–5 min generating. On this serving the reasoning parser is
   on and no per-turn output cap is set (yield 60 governs the analyzer, not the completion). → **B75**.

Zero games (g50t / sk48 / sp80 at 0 in both draws and in every arm that ever ran): 84–434 actions each, 5–7 distinct
action ids, 7,700+ s — exploring, never finding the mechanic. Lowest pay-off on the board (≤ 4.8 each); not charted.

## What this changes on the map

- The lever axis on this base is **levels on the six deep games**, not throughput (B69 bought that) and not action
  efficiency (1.1 points). The three tickets below are the questions, one per failure shape that has a lever.
- B70's premise (actions cost quadratically, so act sooner) is false on this base — closed on its own evidence and now
  also on the score formula.
