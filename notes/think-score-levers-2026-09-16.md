# think-research ledger — "what would still raise our score?" (2026-09-16, manual route)

FRAME. Question: on the chassis we have (Keith Flash-Next NVFP4 serving + anim duck), which unbuilt lever has the largest *measured*
expected gain in LEVELS per run, given that every lever priced so far is NULL/DEAD? "Learned" = a lever with a 0-GPU oracle ≥ +3
levels/run and a smoke that can read its mechanism. Scope: FRAME → RESEARCH (internal instruments + 5 Kaggle pages) → SYNTHESIZE →
THINK → STRESS → working answer. Toolbox: `eval/oracle_ceiling.py`, `eval/per_level_census.py --family flash`, events of six
full-25 runs, MAP e5d9373, B80 note, the 2026-09-15 top-5 report, Kaggle notebook pages read in the in-app browser (JS-rendered).
Prior runs: none on this topic (`.coord/think-*` empty; B80 2026-09-10 is the nearest and its levers L1/L2/L4 are already priced).

## CLAIMS
- C1 Points are levels: 90.2 of 91.3 lost points are unreached levels (B72); one more level per game is worth +1.05 public even at
  20× the human action count (`oracle_ceiling.py` ladder: l1-v0 10.93 → 11.98 at m=20). — H — eval/oracle_ceiling.py
- C2 The family's per-game best (oracle 62–66 levels / 20.2 public) is ~1.5× the best single run (44 / 10.93); 64 % of stalls are
  BEHIND a sibling draw's frontier (a sibling cleared that level). — H — per_level_census.py FLASH 9 runs
- C3 Throughput does not convert: m0 (1.35× turns, 5,722 actions) stayed at or below the family median on every STARVED-class
  game (ft09 2 vs med 4, tu93 2 vs 3); STARVED is "the shape of the corpse, not the cause" (census's own warning). — H — m0 verdict
- C4 Cleared levels take median 10 analysis turns from level start (p75 17, p90 25; 84 % ≤ 20); the final stalled level burns
  median 32 turns. — H — events of 6 full-25 runs (232 cleared / 150 stalled levels)
- C5 Of stalled levels that burned > 20 turns (101 of 150), 69 % were cleared by some sibling run, and median 18 turns remained
  after the 20th; P(clear ≤ 18 | clearable) = 0.80. Upper bound of a fresh retry at turn 20: +9.1 levels/run. — M — same events;
  "sibling cleared" uses the 32-run family max, an upper bound
- C6 In-prompt facts do not move the policy (wm, db v0, db v1) and harness-acts-for-model is null-to-negative (B60, B70, af VOID);
  the mechanisms that changed behaviour are mechanical refusals (bundle no-op guard, +55 % levels in sonpham's HUD-mask fork). — H —
  notes 09-15, MAP B60/B70, B80
- C7 Public recipes' hidden scores: Tufa June duck 1.25, Jakob anim(3.6-27B) 1.61, "LB-9" 27B-FP8+anim 2.23 (title is stale),
  Keith Flash-Next duck 3.38, wuliao0 = Keith's notebook byte-identical: 1.96 latest / 4.33 best — a 2.4-point hidden spread on
  identical code. Our 3.74 (anim b71) sits at the top of everything public. Ranks 2–5 (8.2–8.7) publish nothing. — H — Kaggle pages
  read 2026-09-16 in-browser; top-5 report
- C8 Sampling seed is a module constant passed per request (`_LOCAL_ANALYZER_SEED`, tool_agent.py:159/1536); history and world
  model are reset only in `_ensure_session` (new game). A same-seed fresh context still diverges because the prompt differs. — H —
  anim bundle source
- C9 A 3-game smoke cannot read timing/queue levers (af VOID) but CAN read a turn-count lever: at 3-way the games reach 33–59
  turns in 1,800 s. — H — af smoke transcripts

## OPEN QUESTIONS
- Q1 P(clear | fresh context at the same level) vs P(clear | fresh RUN) — the 69 % is across runs; within a run the game state is
  the same (deterministic level), only the sampling differs. Smoke answers it directly (restarts that clear vs stale contexts that did not).
- Q2 Does wiping the world model at level N lose knowledge needed later (cross-level mechanics)? Measure: levels cleared after a
  restart vs before, per game.
- Q3 Restart cap and cutoff: K=20 from C4; cap 2 per level; whether K should scale with the game's own cleared-level turn median.
- Q4 Hidden variance: wuliao0's 4.33 vs 1.96 on identical code says one hidden draw cannot rank builds — any lever needs ≥ 2
  hidden draws before a submission decision (never quote public→hidden).

## THINK (diverge, inline)
1. Fresh-context restart at stall (harvest C2's variance inside one run) — cheapest, seam known (`_history_messages`,
   `_summarized_knowledge`, `_last_step_summary`, bump seed), oracle +3…9 levels/run.
2. Two agents per game at half turns each (parallel draws) — same idea, doubles queue load; worse than 1 given m0.
3. Restart + carry a one-line "what failed" note — refuted by C6 (facts don't move policy); keep only the no-op guard (mechanical).
4. Level-aware early stop + reallocate turns to games still clearing (thui-bo built) — attacks STARVED, refuted by C3.
5. Better base model — no public recipe beats Flash-Next on hidden (C7); 27B-FP8 recipes are 1.6–2.2. Not a lever we can price.

## STRESS (converge)
- "Variance across runs is not variance within a run" — partly right: the level is deterministic, so all the variance is the
  model's sampling + history; a restart re-samples both. The residual risk is that a level is hard for THIS prompt/model in a
  way seeds do not fix; C5's 69 % says most stalled levels are not that. Q1 is the smoke's job.
- "The wm result says knowledge matters" — wm said keeping knowledge across deaths changed nothing (p=0.67); losing it at a stall
  is the untested opposite pole, and C4 says fresh contexts clear levels fast.
- "af was VOID at 3-way" — this trigger is a turn count, not wall time; C9.
- "B60/B70 precedent" — those made the harness ACT; this makes the harness FORGET. Different class; no MAP row exists.

## WORKING ANSWER (confidence M)
Build **restart-at-stall** on the anim base: one wrapper on `ToolAgent.analyze` counting analysis turns since the level last
changed; at 20 with no progress, clear `_history_messages`, `_summarized_knowledge` (= `_empty_world_model()`), `_last_step_summary`,
`_last_action_result`, keep the no-op guard, bump `_LOCAL_ANALYZER_SEED`, print `THUI_RS_RESTART level= turns= n=`; cap 2 per level.
Smoke on 4 games where siblings cleared the stalled level and turns are plentiful — sb26 (6/6), g50t (5/5), wa30 (5/5), ka59 (5/5) —
at 1,800 s, v0 vs control; read = (1) ≥ 4 restarts fired, (2) levels cleared AFTER a restart that the pre-restart context did not
clear in 20 turns, vs control's clears on the same games, (3) levels ≥ control. Full-25 only if (2) > 0 on ≥ 2 games. Expected
if it works: +3–9 levels/run = +1–3 public; it is the only unbuilt lever whose 0-GPU oracle is above the family's draw noise.
Not a submission decision (Q4).

## Addendum 2026-09-16 01:10 — built as thui-rs; full-width headroom corrected
Built `thui-rs/` (teeth red on 8 mutations; reader `restart_read.py`). Replaying the rule on anim-r2's events: the rule fires in only
**10 of 25 games** at 25-way (turns 20–38 of ~35), leaving ≤ 15 turns for the fresh context — the ledger's +9 upper bound used 52-turn
June-duck runs. Corrected expectation at full width on anim: **+2..4 levels/run** (10 fires × 0.69 sibling-clearable × P(clear ≤ 10)
≈ 0.5). Still the only unbuilt lever above draw noise; a K = 15 rung follows a PASS. The smoke's control number is the stale
context's own late-clear rate (af-ctl: bp35 L1 and tn36 L2 cleared past turn 20 without any restart), which rule 2 now compares against.
