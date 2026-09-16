# thui-anim full-25 draw r2 — verdict (2026-09-15)

`sahasawatt/thui-anim-full25-r2` = Jakob Bruggen's `anim-20260807` solver bundle on Keith Tyser's Flash-Next NVFP4 chassis, shipped serving
profile, thui-v3 knobs (seed 20260825, yield 180 s) — the composition of Watchara's `thui-animfast-b71-full25-r1`, rebuilt from
`thui-anim/build_notebook.py` (teeth ALL PASS). Ran 16:30–18:55 local, wall ~8,520 s. Output `kout-sa-thui-anim-full25-r2/`.

## 1. Mechanism — as designed
`THUI_ANIM_GRAFT ok` with the solver resolved under the anim bundle, `bm.label=anim-20260807-anim`, `animation_awareness=True`,
`hard_noop_guard=True`; 36 analysis turns/game median (b71: 35), 208 s/turn (b71: 202) — the anim solver is slower per turn than the
June duck (52 turns at 159 s) by design (animation frames), and this draw matched b71's profile exactly.

New: after `PUBLIC25_AUDIT` Keith's `serving_teardown.py` raised `RuntimeError: vLLM teardown did not reach the bounded terminal gate`
three times (`shutdown_ok: false`, `required_artifacts_preserved: true`, `metrics_preserved: true`). Not present in m0-s20, wm-ctl or
b71. Score and artifacts unaffected; if it recurs on a submission rerun it is a watchdog question for Keith's stack, not the solver.

## 2. Score
**10.56 public / 40 levels / 20 scoring games / 2,557 actions.** ft09 **100.00 = 6/6 levels in 83 actions** — the first full game
clear in the census (32 runs; b71 reached 5/6). lp85 3/8, re86 3/8, tr87 3/6, tu93 3/9, vc33 3/7; tn36 1/7, sp80 1/6, bp35 1/9 as always.

| comparator | mean / levels / actions | delta | p (sign-flip) | verdict |
|---|---|---|---|---|
| animfast-b71 (same composition, draw 1) | 9.56 / 39 / 2,008 | +1.00 | 0.65 | NOT-DISTINGUISHABLE |
| animfast-v1-d2 (same composition, 09-08) | 7.62 / 39 / 2,543 | +2.94 | 0.32 | NOT-DISTINGUISHABLE |
| wm-ctl (June duck, shipped, 09-15) | 8.32 / 36 / 3,517 | +2.24 | 0.47 | NOT-DISTINGUISHABLE |

Families on this chassis (public):
- anim, 4 draws: 6.65 / 7.62 / 9.56 / **10.56** → mean 8.60, sd ~1.5
- June duck (+ inert grafts), 8 ledger draws: 6.96 … 10.93 (l1-v0) → mean 8.51, sd 1.13

## 3. Reading
10.56 is the team's best public draw, and it is a **draw**: inside the anim family's own spread, below the shipped family's max (l1-v0
10.93, itself priced NULL at p=0.369), and every pairwise test reads NOT-DISTINGUISHABLE. The anim harness does not move the family
mean on this chassis (8.60 vs 8.51); what it changes is the action profile — 2,000–2,600 actions instead of 3,100–5,700 for the same
36–40 levels, so each cleared level costs less and RHAE pays it back. That is the direction the m0 result pointed at from the other
side (more actions, same levels, less score): **action-frugality is the axis, not turns**.

The one new fact is ft09 6/6. One draw, one game, 83 actions; b71 had 5/6 on the same game. Across the anim family ft09 climbs draw by draw: v1 22.97 score, v1-d2 46.19, b71 5/6, r2 6/6 — while the
June-duck family never passed 4/6 (census max before b71). ft09 is the one game where the anim harness is a family effect, not a draw.

## 4. What this buys / does not buy
- Does NOT buy a submission on its own: hidden family for this chassis is 3.35 ± 0.34 over 7 draws and public→hidden is not quotable.
  A 10.56 public draw is not evidence about hidden.
- Buys: the anim bundle as the base for the next lever instead of the June duck (fewer actions per level, same levels). The
  search-strategy lever on budget levels (tn36 / sp80 / bp35 still 1/1/1) is unbuilt and is where the levels are.
- anim + MTP-0 (`thui-anim-m0s20`, built): not worth a draw — m0 showed the room becomes actions, and anim's value is fewer actions.

Cost: 1 kernel, ~2.37 GPU-h, 0 slots. Harvested as `thui-anim-full25-r2` (census 32 runs; FLASH list untouched). Nothing submitted.
