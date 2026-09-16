# Wipe-guard full-25 A/B, draw r1 — verdict (2026-09-15)

Two kernels on the shipped chassis, same day, ~15 min apart, both 25/25 `gave_up` at budget_s 7920:
`sahasawatt/thui-wm-v0-full25-r1` (graft) and `sahasawatt/thui-wm-ctl-full25-r1` (identical notebook, no wrapper,
marker `THUI_WM_GRAFT control`). Output dirs `kout-sa-thui-wm-{v0,ctl}-full25-r1/`; both harvested into
`eval/fixtures/per-level-census.json` (controls P 50/50, A audit == own total, I 28 rows byte-identical; fixture 30 runs).

## The pre-registered read (thui-wm/build_notebook.py docstring), applied in order

1. **Compare only via `eval/rank_runs.py`** (the two `benchmark.json`, ctl as baseline):
   `mean 8.32 -> 7.44 (delta -0.88) · levels 36 -> 39 (+3) · per-game 10 up / 8 down / 4 flipped ·
   sign-flip permutation p = 0.6716 · VERDICT: NOT-DISTINGUISHABLE`.
2. **Mechanism check — >= 1 THUI_WM_KEPT on >= 5 games, else VOID**: v0 printed **40 KEPT**; the events show 40 in-level deaths
   on **9 games** (bp35 10, tu93 9, sp80 6, cn04 5, tn36 5, su15 2, r11l 1, sc25 1, wa30 1). ctl: 40 deaths on 12 games, 0 KEPT.
   Not VOID — the lever fired, and the control discriminates.
3. **PASS = v0 >= ctl AND levels gained on the wipe-heavy games (r11l/tu93/sp80/bp35/tn36)**: score v0 < ctl (7.44 vs 8.32), and
   on the five pre-named games: r11l **2 vs 1 (+1)**, tu93 2 = 2, sp80 1 = 1, bp35 1 = 1, tn36 0 = 0. **Not PASS.**
   Rule says: "anything else = pool draw 2 or drop".

## What the per-game table says about the mechanism

Where the guard fired hardest, the level did not move: bp35 (10 KEPT) 1 = 1, tu93 (9) 2 = 2, sp80 (6) 1 = 1, cn04 (5) 1 = 1,
tn36 (5) 0 = 0. The +3 total levels came from games where it barely fired or not at all: cd82 +2 (0 deaths in v0), sc25 +2 (1),
lp85 +1 (0), re86 +1 (0), sk48 +1 (0), tr87 +1 (0), r11l +1 (1). Losses: ft09 -2 (4 -> 2, the 47.6 -> 14.3 that owns most of
the score gap), ar25 -1, dc22 -1, m0r0 -1, s5i5 -1 — all games with 0 deaths in v0. So the games that moved are the games the
graft could not have touched; the movement is draw variance of the size the census already measured (7 Flash draws: 54-60% of
stalls behind the family frontier). Kept knowledge across an in-level death did not convert a single dying level.

One reading that stays open: v0 ran **3,100 actions vs ctl 3,517** (-12%) at identical wall. The kept fields make the next prompt
longer after a death (kept_chars up to ~400 per field), so the graft may cost per-action wall on exactly the games it fires on
(bp35 116 vs 28 actions is the other direction, though — a kept plan that keeps dying). Not separable in one draw.

## Decision offered to the owner

**Recommend DROP**, not pool: the mechanism fired 40 times on 9 games and gained 0 levels on the dying levels themselves; a draw 2
can only move the p-value on a score gap that is already inside noise, it cannot manufacture the missing effect. If pooled anyway,
the pre-registered pooled read is n=2 vs the fast pool via rank_runs, nothing else.

The smoke's r11l 4/6 (2026-09-14) is now a 1-of-9 Flash draws outlier: r11l over 9 full-25 draws = 1,1,1,2,1,1,2,2,1 — never 3.

## Cost / state

2 kernels, ~8 GPU-h, 0 slots. Nothing submitted. Both output dirs + logs on disk; rows in the census; eval FLASH list and
LEDGER_PUBLIC carry both keys (public = each kernel's own final mean score; no LEDGER row written — that is the owner's call).
