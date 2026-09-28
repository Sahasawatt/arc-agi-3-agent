# think-research: one-change successor to B99 — ledger (2026-09-24)

Question (Step 0): which single change to B99 (`yocybercode/thui-b99-rungpin-full25-r1` v1, hidden 5.36; full harness
source in `anim-bundle/`) has the best evidence of raising the score, is not a closed axis, and can be tested by a
design that decides? Scope: FRAME -> RESEARCH -> SYNTHESIZE -> THINK -> STRESS; no build, no GPU (quota saved to 09-30).
Step 1 raw: `step1_research.json` (wf_16499e7d-16c, 3 sonnet lenses: source / data / map).

## Step 2 — SYNTHESIZE
CLAIMS
- Every game in B99 and both controls ends by the ~7,920 s clock; ~47 turns/game at ~174 s/turn; binder = time per
  turn, not actions — H — data lens (benchmark.json, 75 game-runs; min final_wallclock 7,920 s).
- 46-50 % of the clock is spent after a game's LAST clear with no further progress, the same in B99 (49.0 %), B81 ctl
  r5 (50.1 %), b99apg (45.8 %) — H — data lens; matches B50's 39.8 % dead tail measured on the older chassis.
- The same 5 games (wa30, ls20, r11l, sp80, lf52) are among the top-8 dead-time games in all three runs; sk48 never
  clears L1 in any — H — data lens.
- In a sampled stall (B99 su15) the model re-plans ~19 times in 55 min and still fails; ~50 % of dead-time actions
  repeat the previous (action, x, y) — M — data lens (one game traced; repeat rate over ~2,200 actions/run).
- b99apg (ap only after the first clear) issued more RESETs (40 vs 33) and hit more game_overs (40 vs 21) than B99 and
  cleared the most levels (46) — L (n = 1 each) — data lens.
- Closed around B99: cut/strip reasoning (B8/B12/B31/B92), serving knobs (B75/B76/B86/B87/B91), in-prompt nudges and
  memory (B13/B32/B62/B83/B90), world-model slot variants (B89, B93 parked underpowered, round 38 carry), more context
  (B17/B48/B54/B65/B88), plateau detection (B50), clock reallocation (B36), stuck-level explorers (B84 park, B85 kill,
  B60), tool-step cap (B47/B59), history sieve (B100 killed), pin cap 4096 (round 37 NOT-PASS) — H — MAP rows.
- Still open near B99: pin PLACEMENT (round 36, parked), SUBTASK-level pin (round 33, parked), B98 controller
  hypothesis compile/verify (open, stage 1 is 0 GPU), B97 ctx64 + KV12 (open, serving family), ap-after-first-clear =
  b99apg (built, VALID, public 46, hidden never drawn) — H — map lens.
- Decision constraints: hidden sd 0.53/draw; public ~3 levels/run; rank_runs needs >= 6 movers; power 0.31 at k = 8
  for +1 level on 6 games; within-family public<->hidden r = 0.05 — H — notes rounds 29-31, B93 row.
OPEN QUESTIONS
- Is anything B99-local big enough to see? The dominant loss (dead time on 5 fixed games) is shared by every build.
- Does the pin get used at all (round 36: cited in <= 1 % of later turns)? Placement is the one untested lever on that.
- Will the Milestone-2 chassis (by 09-30) make B99-local work moot, or can a ToolAgent graft be carried over to it?
WORKING ANSWER
- Unsettled — need Step 4 stress on the candidates below.

## Step 3 — THINK (candidates, one change each on B99)
A. Draw b99apg (built): ap switched on only after a game's first clear. Answers "ap costs L1" (the b99ap confound).
B. Pin PLACEMENT: insert the RungPin text into the LAST user message next to "Current state" / the world-model block
   instead of a separate user message after the system prompt (one index change in `_b99_chat`).
C. SUBTASK pin: pin not only on level clears but on each first-time effect inside a level (e.g. first board change
   of an action type), keeping the latest few, capped.
D. B98 stage 1 (0 GPU): can the harness compile the model's stated transition hypothesis into a predictor and falsify
   it against banked transitions on >= 12 games — aimed at the dead-time re-planning loop.
E. Stall-triggered level RESET by the harness after N no-progress turns (b99apg's extra resets hint) — suspected
   duplicate of B50/B36/B84; included so the refuters can kill it on the record.

## Step 4 — STRESS (2026-09-24T04:41Z; wf_786fd5e7-899, 2 sonnet refuters; raw `step4_stress.json`)
| cand | closure lens | mechanism lens | status after stress |
|---|---|---|---|
| A b99apg draw | open-weak (family pooled NOT-PASS p 0.172) | built + VALID; its own hidden never drawn; our registered stop fired on b99ap's 2.92 | DEFERRED — a slot decision, not a build; user skips slots to 09-30 |
| B pin placement | open-weak (round 36: pin cited <= 1 %; in-prompt text rarely acted on) | very portable, one line; no affordable run can decide it | HOLD |
| C subtask pin | closed-duplicate (round 33, parked, not testable offline) | needs new engineering, no local support | DROP |
| D B98 stage 1 | open-supported (B82 failed because verify was optional; B74 = capability-bound tail) | targets the 46-50 % dead time seen in every build; stage 1 = 0 GPU on banked transitions | **PURSUE** |
| E stall RESET | closed-duplicate (B50 dead at every K; B36/B84/B85/B60) | kill | DROP |
Both refuters rank D first (closure: D B A C E; mechanism: D A B C E).

WORKING ANSWER (M)
- Next technical step on B99 = **B98 stage 1, 0 GPU**: a harness-owned compiler that turns the model's stated
  transition hypothesis into a predictor and checks it against transitions already banked; MAP's own kill rule:
  dies unless it validates or falsifies hypotheses on stored transitions in >= 12 games with no state cloning
  (~1 human-day). Stage 2 (~0.5 GPU-h smoke) only after 09-30 and only with a GO.
- Stage 0 before building (minutes, 0 GPU): is there compilable hypothesis text in >= 12 games? Round 38 found the
  "Action model" slot written in only 5-7 % of level ends, so hypotheses may exist only in THINKING prose -- if so
  the compiler needs an LLM step, which is where B82 died (cost). This is the first thing that can kill D.
- Caveats: D is a bigger subsystem (lower portability to a new chassis than a text graft); every in-chassis lever so
  far read inside hidden noise, so a stage-1 PASS buys a smoke, not a claim about hidden score.
OPEN QUESTIONS
- Stage 0 count (above). - Whether Milestone 2 publishes a chassis on which B98 would have to be re-hooked.

## Stage 0 for D (registered 2026-09-24T04:45Z, before any judge output)
Mechanical (`stage0_extract.py`, B99 public run): 8,146 candidate sentences (action token + effect verb) in THINKING/
ASSISTANT, all 25 games; controls: a known hypothesis sentence is extracted, a plain sentence is not, recall of
"<DIR> moved" sentences 188/188. Data: all 4,352 action events carry a full board, so before/after boards exist for
every stored transition without state cloning.
Sample: up to 4 per game (dead-time first) = 96 + 3 seeded negative controls, 4 batches, 2 independent sonnet judges.
**PASS iff >= 12 of 25 games have >= 1 sampled sentence that BOTH judges call checkable with a complete predicate
(action + target + effect), AND both judges call all 3 negative controls not checkable (else the judging is VOID).**
A PASS only licenses building stage 1 (the compiler + checker); it says nothing about score.
**Stage 0 RESULT (2026-09-24T04:47Z; wf_600bee69-8ea, 8 sonnet judges, raw `stage0_judge.json`, read by `stage0_agg.py`): PASS.**
21/25 games have >= 1 sentence both judges call checkable with a complete predicate (bar 12); 33 of 96 sampled
sentences (34 %), 17 of them in dead time; kinds rule 10 / observation 21 / prediction 2; judge agreement on
checkable 93/98 (one item had a single judge); all 3 negative controls rejected by both.
What it does NOT show: the judges did the compiling. In the live harness, text -> predicate needs either an LLM call
(B82's cost failure) or the model writing a structured hypothesis line (in-prompt compliance, B32 obedience ~52 %).
Most checkable sentences are observations (restating one past action); the lever lives in the 10 RULES, the claims a
checker could FALSIFY while the model keeps re-trying them in dead time.

## Stage 1 for D (registered 2026-09-24T04:50Z, before any compile or checker output)
Checker spec: `b98-stage1/SPEC.md` (DSL: action + target colour/region + effect move/recolor/appear/disappear/
no_change/any_change/count_delta; matched on the SAME game and level; stored before/after boards only).
Input: the 33 sentences both stage-0 judges called checkable, compiled to DSL by ONE sonnet compiler pass (the
live-harness compile cost is a separate, later question). Each hypothesis gets a negated twin.
**PASS iff (1) hypotheses reach a decisive verdict (validated or falsified) in >= 12 games (MAP B98 kill rule), AND
(2) teeth: among decisive hypotheses that have a twin, the twin's verdict is NOT the same decisive verdict in >= 80 %.**
Reported, not graded: falsified RULES (the lever's value), how many in dead time, compile failures.
**Stage 1 RESULT (2026-09-24T04:54Z): FAIL on both registered conditions -> D closes at stage 1 (MAP B98 kill rule).**
- Checker (`b98-stage1/checker.py`, written by codex, patch reviewed and applied by hand; `test_checker.py` ALL OK
  run here, incl. 3 mutants red) works: the one fully grounded claim (su15 "clicking (23,61) made M(23,55)
  disappear") is VALIDATED and its twin FALSIFIED.
- The COMPILE step is the wall: only 5 of 33 judged-checkable sentences compile faithfully from text; 22 fail for
  want of a colour ("the piece", "the block"), 2 are compound, 4 other. Decisive verdicts in 3 games (su15
  validated; lp85, ft09 falsified) vs the bar of 12; cn04 untested (0 matching clicks), re86 mixed.
- Teeth 1/3 (bar 80 %): lp85 (move -9) and ft09 (whole-board recolor b->R) are falsified together with their twins —
  the claims are ungrounded (a rotation stated as a translation; "the clicked tiles" compiled as every blue cell),
  not a checker fault.
Reading: the model states transition rules in words that point at objects on the board, not at colours and cells.
Turning them into checkable predicates needs the board in the compiler's hands (an LLM call with the frame per
hypothesis = B82's cost failure) or the model writing grounded hypothesis lines (compliance ~52 %, B32). A stage-1b
with board-grounded compilation would be a NEW registered test, not a re-grade of this one; not run.

## ⚠️ CORRECTION 2026-09-24T06:16Z — this was written against a STALE MAP
`scratchpad/MAP_master.md` was a copy taken 2026-09-22 ~05Z; origin `notes/wayfinder/MAP.md` at b4c6470 (fetched
2026-09-24T06:16Z) differs: **B94 CLOSED 2026-09-22** (Watchara's v2 smoke: Qwen3.5-122B fits, 73.24 GiB, but 1,640 actions /
0 levels vs 211 / 6 — killed on play quality); **B99 CLOSED 2026-09-23** (full-pair gate FAIL, 8 up / 4 down;
public B99 = B81); **B98 kill rule REVISED 2026-09-24** by Watchara before stage 1 (now measures availability on
unseen transitions — our stage-1 read used the old bar); B96 closed 09-24; B97 sequenced behind B100's smoke pair.
Any recommendation above that names B94 as a candidate is void. MAP_master.md is now the origin copy (stale one
kept as MAP_master.md.bak.stale-2026-09-22).
