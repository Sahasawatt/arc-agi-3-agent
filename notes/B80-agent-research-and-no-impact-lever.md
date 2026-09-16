# B80 — what the strong ARC-AGI-3 agents do, and the first lever it points at (no-impact detection)

Opened 2026-09-10. Source: a 26-agent deep-research run (5 search angles → 54 sources → 18 read → 51 falsifiable claims →
**45 survived two refuters, 6 refuted, 0 unverified**), synthesised against our own measured base. Full report with citations:
`notes/research/arc-agi3-agent-deep-research-2026-09-10.md`. Instrument: `eval/no_impact_census.py`.

## What the report established (verified claims only)

- **Tufa's Duck** (11.04 public) is our chassis — agent-writes-code in a python REPL, image + ascii perception, oldest-message
  eviction, no external memory — on **Qwen 3.6 27B FP8 self-hosted**; designed minimal and cheap, "some games never pass L1".
- **sonpham-org/arc-3** (instrumented Tufa fork, 27B): the one lever with a measured level effect is **no-impact detection** —
  refusing to count an action whose only board change is the deterministic HUD / moves-counter band: **+55 % levels (21 vs 15)
  at equal action budget**. His agent-side knobs (ledger, outline renders, 900 s yield) cost 2.2× and he scopes the "tempo
  regime dominates" conclusion to 27B — it does not transfer to our measurements.
- **NVIDIA AVO**: 100 % RHAE on the PUBLIC set (183 levels, ~265 actions/game) with a **supervisor process** that watches the
  trajectory for stagnation and redirects the agent, plus cross-run memory. No hidden number, no supervisor ablation.
- **arXiv 2512.24156**: training-free graph of explored states/transitions + pick the action with the shortest path to an
  untested state-action; median 30/52 levels, Preview LB #3; **open source**.
- Organisers: games test explore / infer goal / build a dynamics model / plan; scoring per level `(baseline/actions)²` capped
  1.15, level-index weighted, **an uncleared level is 0 and caps the game** — the rule form of our census (B72: 90.2 of 91.3
  lost points are unreached levels).

## Levers, ranked for our base (each with the cheapest refuter)

| # | lever | attacks | cost | smoke that kills it |
|---|---|---|---|---|
| L1 | no-impact detection (HUD-band mask) | the 30–50-turn wrong-hypothesis stall | ~1 day + 4.4 GPU-h A/B | count HUD-only actions in our own events — 0 GPU |
| L2 | supervisor stall-detector + redirect | stalls + time on early levels | 2–3 days + 4.4 GPU-h | offline replay on our transcripts — 0 GPU |
| L3 | graph state-tracking + shortest-path-to-untested | hypothesis search | 2–4 days vendor + smoke | 3-game smoke vs `--control` |
| L4 | kernel-path sanity (tok/s MTP on/off, concurrency 1) | time-bound tail | < 1 GPU-h | single-request bench |
| L5 | 27B FP8 serving | — | low priority | only after L4 |

Blocked by constraints: AVO cross-run memory (harness rewrite), NVARC synthetic-data LoRA (no data). Already NULL here, not
reopened: B64 B70 B71 B75 B76 B78. Unknown: any hidden number but ours; AVO wall-clock; Kaggle thread 717133 + x.com/tufalabs
unfetched.

## L1 pre-read (2026-09-10, 0 GPU) — the lever's precondition holds on 8 of 25 games

Pre-registered before the count: L1 is dead if our runs contain ≈0 actions whose only change is a HUD band; the positive
control is a game whose transcript names a timer strip (tn36), the negative control a game with no such strip.

Instrument fix, recorded because it changed the answer: a **per-cell** frequency mask found nothing on any game including the
control (tn36 top cell 14 %) — a counter strip ticks every action but at a **different cell** each time, so the mask has to be
a **row band** (tn36 row 1 and sp80 row 0 are touched by 100 % of board-changing actions). Threshold: row touched on ≥ 90 % of
changing actions, ≤ 4 rows (more = a playfield that redraws; tr87's rows 52–56 at 62–70 % are the cursor area, correctly not
masked — tr87's own timer did not surface at this threshold, one control of two).

`thui-fast-v0` v2 (25 games, 3,553 actions, 3,278 board-changing): **203 no-impact actions = 6.2 % of changing actions, in 8
games** — tn36 47 (all on its never-cleared L1, 18.7 %), bp35 33 (24 on its last level), vc33 30 (22 on the L4 it never cleared,
18.9 %), lf52 29 (31.5 %), sp80 26 (11.2 %), su15 21 (23.9 %), tu93 16, ls20 1. 17 games have no HUD band at all. Replication
on `thui-a7-v1` v2: 199 / 3,223 = **6.2 %**, 6 games — same share, independent draw.

Reading: the precondition holds but narrowly — on the eight HUD games one action in six changes only the counter, and on
three of the stall games (tn36, vc33, bp35) those actions sit on the level that was never cleared. Because the harness reports
them as `board_changed=True`, the model reads a dead click as an effect and builds hypotheses on it — the mechanism sonpham's
+55 % removes. Ceiling here is bounded: 17 games are untouched by construction, so the lever can act on at most the 8.

## L1 built 2026-09-10 (local only, no GPU) — `thui-l1/build_notebook.py`

Three variants off the same builder, cells changed `[0,1,3,5,9,15]` asserted against the vendored upstream:
`--` treatment smoke (`thui-l1-v0`, tn36/vc33/bp35 @1,800 s), `--control` (`thui-l1-ctl`, same games, wrappers NOT installed),
`--full` (`thui-l1-v1`, 25 games). Cell 9 wraps four methods on the IMPORTED harness (solver tree on disk untouched):
`_HarnessGameSession._execute_action` (learn the band, flip `board_changed` to False and set `no_impact`),
`ToolAgent._compact_action_result` (carry it to the model's python), `._summarize_step_sequence` (count per sequence),
`._describe_last_outcome` (tell the model in the next prompt). **Frames are not masked** — the model can still read the counter;
only the harness's verdict on "did this action do anything" changes. Band rule = the census rule (row touched by >= 90 % of
board-changing actions, >= 20 seen, <= 4 rows), learned per game online, RESET and level-completing actions excluded.

Teeth, all run before any GPU:
- in-kernel (cell 9, runs on every launch incl. the control): band learner on synthetic sequences — a ticking row 0 plus a
  wandering row yields band `{0}`; a 6-row redraw yields no band; below 20 changing actions nothing is classified.
- local `thui-l1/test_l1_graft.py`: the four method signatures read out of the REAL source by ast (control (a): a fabricated
  method name must be reported missing; `_execute_action` must keep `(self, action, *, ...)` or `**kw` forwarding breaks), then
  the graft's own cell-9 source executed against stubs — a counter-only action ends `board_changed=False, no_impact=True`,
  reaches the compact result, is counted in the summary, and appears in the prompt text.
  **control (b)**: an action touching a non-band row stays `board_changed=True`. **control (c)**: the class must carry the
  wrapper before any step runs. Control (c) exists because the first version of this file reassigned the class attribute after
  the graft installed itself — the wrapper never ran, everything read as "not flagged", and (b) passed trivially: a
  negative-only control cannot see a dead instrument.

Next (needs OK): push the two smoke arms (~40 min each, 0 slots): `thui-l1-v0` then `thui-l1-ctl`.
PASS = levels on the three games >= the control's on every game, with >= 1 `THUI_L1_NOIMPACT` in the treatment log; FAIL = any
game below the control (the counter was information the model needed) -> close L1. Zero `THUI_L1_NOIMPACT` = the band never
armed inside 1,800 s and the run measured nothing (VOID, not a result).

## L1 smoke RESULT (2026-09-11, 2 arms, 3 games each, ~40 min concurrent) — **FAIL on the pre-registered read**

Arms: `sahasawatt/thui-l1-v0` (treatment) and `sahasawatt/thui-l1-ctl` (control), both v1, both COMPLETE, both
`smoke 3 games @ 1800.0 s`, pushed within 20 s of each other and run concurrently, so the clock and the serving are matched.

The read was written into `scratchpad/CHECKPOINT-2026-09-08.md` before either log was opened: PASS = levels(treatment) >=
levels(control) on ALL THREE games AND >=1 `THUI_L1_NOIMPACT` in the treatment log; zero markers = VOID; levels down on any
game = the counter carried information.

| game | treatment levels | control levels | treatment score | control score | no-impact flagged | learned band |
|---|---|---|---|---|---|---|
| tn36-ef4dde99 | **0** /7 | 2 /7 | 0.00 | 8.63 | 72 | row 1 |
| vc33-5430563c | 3 /7 | 3 /7 | **16.53** | 10.45 | 26 | row 0 |
| bp35-0a0ad940 | **1** /9 | 0 /9 | 1.34 | 0.00 | 107 | row 63 |

**Not VOID: the instrument armed.** 205 `THUI_L1_NOIMPACT` lines in the treatment log, 0 in the control (which carries no
wrapper), one `THUI_L1_GRAFT ok` in each. Every band the kernel learned online is the band the offline census predicted from
a different draw — tn36 row 1, vc33 row 0, bp35 row 63 — so the learner is not the thing that failed.

**FAIL, because the rule required all three and tn36 lost two levels.** tn36 is the strongest case for the lever by the
census (47 HUD-only actions, all on a level it never cleared) and it is where the treatment did worst: 312 actions on level 1
without clearing it, against the control clearing the same level in 30. That is the branch the pre-read named — on tn36 the
counter row is information, or telling the model 72 of its actions were dead stopped it exploring the class that clears L1.

**What this run cannot separate** (the instrument, not a hedge): n=1 draw per arm per game. This stack's within-build spread
is large enough to produce this table with no lever at all — the same build scored hidden 3.32 and 2.68 on two submissions,
and bp35 moved +1 in the treatment's favour on the same single draw. A 3-game 1-draw A/B has no power to price a per-game
effect. So the honest reading is: **L1 did not pass its own gate, and the gate could not have distinguished a real -2 on
tn36 from a draw.** Repeating it to n=3 per arm is ~4 GPU-h for a lever whose ceiling is 8 of 25 games; ranked against L2
(offline replay, 0 GPU) and L4 (<1 GPU-h), L1 goes to the back of the queue rather than to a bigger A/B.

Artifacts: `scratchpad/kout-sahasawatt__thui-l1-{v0,ctl}.log`, builder + teeth in `thui-l1/`.

## L2 pre-registered read (written 2026-09-11 BEFORE the detector was run once) — supervisor stall-detector, 0 GPU

Lever: AVO's supervisor process watches the trajectory for stagnation and redirects the agent. B73 already established
that we stall (30-50 analyzer turns per level, hypothesis search that does not converge). That is NOT the question L2
has to win. The two that are:

  1. can a CAUSAL detector see the stall from what is on the trajectory at the time, and
  2. does it see it while there is still budget to redirect into?

Instrument: `eval/stall_detector.py`. On the level the game is currently on, over a sliding window of the last W
board-changing actions, the fraction that reached a board state this game has NEVER been in before. Below theta, the
agent is re-treading. W=10, theta=0.10, soon=20. Nothing in the fire uses the level's eventual outcome.

Each fire is then classified by what happened after it: **target** (level never cleared), **slow** (cleared more than
`soon` actions later), **false** (cleared within `soon` -- a redirect there would have interrupted a solve).

Controls, both in the same run:
- **positive** — the six level-episodes B73 measured as stalls (s5i5 L3, ft09 L4, sb26 L2, su15 L2, tn36 L1, vc33 L4)
  must fire. A detector that misses them is blind and its zeroes are not evidence.
- **negative** — level-episodes solved within `soon` actions of starting must NOT fire.

**L2 is DEAD if any of:**
 (a) the negative control fails on a third or more of fast solves — the redirect breaks more than it fixes;
 (b) the fires on never-cleared levels arrive late — median remaining wall below 20 % — nothing left to redirect into;
 (c) it fires on almost nothing that is a target, i.e. our losses are not re-treading at all.
**VOID (not a result) if** the positive control misses: the detector, not the lever, is what failed.
**ALIVE if** target fires are early (median >= 20 % wall left), the negative control is clean, and both hold on the
second independent run (`thui-a7-v1` d2) as well as the first (`thui-fast-v0` d2).

## L2 RESULT (2026-09-11, 0 GPU, two independent 25-game runs) — **ALIVE, narrowly**; and one signal measured DEAD

Instrument `eval/stall_detector.py` against the pre-read above. Runs: `thui-fast-v0` d2 (`kout-sa-thui-fast-v0-d2`) and
`thui-a7-v1` d2 — a second draw on a different build, so the counts below are replicated, not sampled once.

### The signal a naive supervisor would watch is DEAD here: our stalls are not state re-treading

The novelty detector (W=10, theta=0.10) fired **twice in 25 games and on 0 of the 6 stalls B73 measured**. That is not a
NULL about the lever, it is the detector being blind, and the direct measurement says why: on the stall levels the
agent reaches a board state it has NEVER been in on **94-97 %** of its board-changing actions — tn36 L1 241/251, vc33 L4
97/103, s5i5 L3 63/65, su15 L2 71/75. Our agent stalls while generating novel states relentlessly. **A supervisor that
watches for revisited states, which is the obvious reading of "stagnation", sees nothing to redirect on this base.**

### Instrument fault fixed on the way, recorded because it inverted every episode

`level_completed` events carry the **NEXT** level in their `level` field (verified on tr87 d2: i=61 `level_field=2`,
prev 1, and three more). Attributing them naively makes every episode read as never-cleared and every clear as costing
0 actions — the first sweep reported `FPclear = 0` at every threshold, a zero that looks like perfect separation and is
an artefact. `level_of()` now subtracts the one, with teeth asserting tr87 has 4 cleared episodes at 62/30/39/29 actions.

### The dwell signal, priced rather than tuned (`--sweep`)

Fire the first time T actions have been spent on the current level without clearing it. At **T = 60**:

| run | target fires | of those, wall left >= 20 % | >= 30 % | fires that interrupted an imminent solve | median wall left |
|---|---|---|---|---|---|
| fast-v0 d2 | 16 | **9** | 6 | 3 | 0.240 |
| a7-v1 d2 | 13 | **9** | 5 | 0 | 0.229 |

**Positive control 6/6** on fast-v0 d2 — every stall B73 measured fires (the control is run-scoped and is not readable on
the a7 run, whose games reach different levels; that run replicates the counts, not the control).
**Negative control**: 17 episodes were solved within 20 actions of starting; 3 fires landed on a level cleared within 20
actions of the fire (fast d2), 0 on a7 d2.

Against the pre-read: (a) the harmful-fire rate is 3 of 22 fires, below the one-third DEAD line; (b) median wall left on
a target fire is 0.240 / 0.229, above the 20 % DEAD line — barely; (c) 16 and 13 target fires, not "almost nothing".
Positive control clean. **So the two questions L2 had to win are won: a causal detector CAN see our stalls, and on about
9 of them per 25-game run it sees them with a fifth to two-thirds of the wall still unspent.**

### The cost, stated in the same breath, because it lands on the game that can least afford it

**tr87 L1 fires as a false positive**: 60 actions in, 2,900 s, and it cleared at action 62. tr87 is B74's worst
time-bound game (5,928 s to reach L5, 1,992 s left, active plan) — the single level where the run most needs its early
seconds back is also the level a T=60 supervisor would interrupt two actions before it lands. dc22 L2 and ft09 L3 are
the other two. A dwell rule alone cannot tell "60 actions and about to solve" from "60 actions and lost".

### What this does NOT establish

**That a redirect helps.** Nothing here tests an intervention — the detector answers *seen, and in time*, and stops
there. The content of the redirect is unspecified and AVO's is a supervisor LLM we have not costed. Seven of the 16
fast-d2 target fires sit under 16 % wall left, and those are late because the game only REACHED that level late: a
supervisor cannot buy time that was already spent on the levels before. That is B74's finding arriving again from a
different instrument, and it bounds L2 to roughly the 9 fires that are early, not to the 16 that exist.

Next, in cost order: (i) 0 GPU — add a progress guard to the fire rule (do not fire while the last N actions are still
changing the board in new ways) and re-price the same table; the target is the 3 false fires, tr87 L1 above all.
(ii) GPU — a redirect arm is a real A/B, and the L1 smoke just measured what a 3-game 1-draw A/B can and cannot say, so
the cost of a credible one is n=3 per arm, ~4 GPU-h. Not started; needs the owner's OK.

Artifacts: `../l2_fast_d2_dwell60.json`, `../l2_a7_d2_dwell60.json`.

## L2 progress guard (2026-09-11, 0 GPU) — **no cheap causal progress signal exists here**; the fix is the threshold, and it is not free

The T=60 rule cost three fires into solves that were about to land, tr87 L1 the worst of them (fired at action 60,
cleared at 62, on B74's most time-starved game). Two candidate progress signals were named and measured BEFORE any was
wired, each with a stated mechanism, on the 30 actions preceding every fire in both runs:

| signal | mechanism it assumes | the three harmful fires | the target fires | separates? |
|---|---|---|---|---|
| actions per analyzer turn | a converging agent batches a plan; a lost one probes one click per turn | tr87 15.0, ft09 7.5, dc22 6.0 | 2.0 - 10.0 | **no** — targets sit at 10.0 (ar25, cn04, ka59, lf52, ls20, re86) |
| distinct click cells / 30 | zeroing in on a target vs wandering | 0, 23, 4 | 0 - 27 | **no** — the range is identical |

A threshold catching tr87 alone (>12 actions/turn) is a fit on the single point it is meant to fix, on an n of one, so
it is not written into the tool. A third candidate died before that: `reward` is non-zero **only on the clearing action
itself** (41 positive rewards for 41 cleared episodes) — there is no partial credit on this engine to read progress from.

### What does work is the dwell threshold, and the trade is one-for-one

`--min-left F` was added as a BUDGET guard (refuse to fire with less than F of the wall left). It is definitional, not
fitted — a fire with no wall left cannot be redirected into anything. It does **not** fix the harmful fires: tr87 L1 and
ft09 L3 both fire early, with 63 % and 56 % of the wall still unspent. Only raising T removes them.

| operating point | positive control (of 6) | target fires fast / a7 | harmful fires fast / a7 | median wall left fast / a7 |
|---|---|---|---|---|
| T=60 | **6/6** | 16 / 13 | **3** / 0 | 0.240 / 0.229 |
| T=90 | 4/6 | 8 / 10 | **0** / 0 | 0.435 / 0.202 |
| T=90 + min-left 0.25 | 2/6 | 5 / 6 | 0 / 0 | 0.478 / 0.438 |

**Every step that removes harm removes stalls the detector was validated on.** At T=90 the two lost controls are su15
L2 (75 actions on that level) and ft09 L4 (78) — real stalls that simply never reach 90 actions. There is no setting
that is both clean and complete; the guard buys safety by giving up reach, one for one, and saying otherwise would be
reading the harmful-fire column alone.

**Chosen operating point for any redirect arm: T = 90, no budget guard** — 0 harmful fires in either run, 8 + 10 target
fires, and the five with real budget on fast d2 are a concrete list: sb26 L2 (54 % wall left), sk48 L1 (49 %), tn36 L1
(48 %), sp80 L1 (44 %), cn04 L2 (25 %). The budget guard stays in the tool as an option, off by default, because at 0.25
it halves the reach for a harm count that is already zero.

Bound that did not move: this still says only *seen, and in time*. No intervention has been tested, and the a7 run's
median wall left at 0.202 says half its fires arrive with a fifth of the wall — the redirect would have to be worth
about 1,600 s to matter there.

Artifacts: `../l2_fast_d2_dwell90.json`, `../l2_a7_d2_dwell90.json`.

## L4 pre-read (written 2026-09-11 BEFORE any bench arm was pushed) — is MTP-3 paying on the shipped profile?

### The 0-GPU half, already measured

Three findings from our own artifacts, no GPU spent:

1. **vLLM warns on every one of our starts**: `speculative.py:1010 Enabling num_speculative_tokens > 1 will run
   multiple times of forward on same MTP layer, which may result in lower acceptance rate`. Our profile sets MTP=3.
2. **Two knobs the serving author provides are unset in the shipped profile** `kv5-bf16-mtp3-c8-cg32`
   (cell 3 of the upstream notebook, commented "Apply the measured vLLM winner"):
   `TAAF_VLLM_MTP_INDEX_SHARE_FOR_ITERATION` -> `index_share_for_mtp_iteration`, which addresses exactly the
   repeated-layer path in (1) (`serving_setup.py:2365-2366`), and `TAAF_VLLM_MTP_DYNAMIC_BATCH_SCHEDULE` ->
   `num_speculative_tokens_per_batch_size` (`:2367-2369`), so speculation can shrink as the batch fills. We serve at
   `--max-num-seqs 8` against solver concurrency 28, i.e. a permanently saturated batch, where speculation pays least.
3. **B78 (MTP OFF, full width) produced MORE actions, not fewer**: 4,049 against our two-draw pool's 3,739 mean, ratio
   1.083. Our own draws span 3,553-3,925, so 4,049 sits just above our max — suggestive, not decisive, and neither side
   recorded a throughput number.

A mechanism I chased and **refuted before using it**: `speculator.py:178` also warns the drafter is text-only and gets
no multimodal embeddings. That is inert for us — `MULTIMODAL_CONTEXT` is unset and 0 of 52 analyzer transcripts on a
sampled game carry an image, so we send text only and the drafter loses nothing.

Observed aggregate output rate on the real runs, for the bench's consistency check: **231.4 tok/s** (fast v2,
1,832,988 tokens over a 7,920 s wall shared by 25 games) and **235.4 tok/s** (a7 v2). Caveat stated up front: the
harness's `tokens=` counter is not necessarily generation-only, so this bounds the bench rather than equalling it.

### The GPU half: `thui-l4/build_notebook.py`, one arm per push, no games

Cells 0-14 untouched, so the server starts under the real profile. Cell 15 replays **three real analyzer prompts** from
our own transcripts (tn36 / vc33 / sk48, 21-24 k chars each) at the harness's own sampling — `temperature=0.6`,
`top_p=0.95`, `max_tokens` = server default (`tool_agent.py:145-146,1293-1295`) — at concurrency 1 and 8, reading
vLLM's `/metrics` speculative counters around each phase. Arms: **a** shipped (control), **b** + index-share,
**d** MTP=0.

Pre-registered read:
1. **CONTROL first**: arm a must report `draft_tokens > 0` and arm d `== 0`. Three outcomes, not two — a counter NAME
   this vLLM build does not publish reads as 0 drafts, which is the same number MTP-off gives, so the bench also
   reports `spec_metric_lines`; 0 lines with MTP on prints `METRIC_NAMES_UNKNOWN` (acceptance unreadable, tok/s still
   valid), never `VOID`.
2. **PRIMARY**: aggregate output tok/s at concurrency 8 — the operating point we ship. Secondary: median per-request
   tok/s at concurrency 1, and acceptance = accepted / draft.
3. **DEAD** if no arm beats arm a by more than 10 % on the primary. The knobs are then correctly off and MTP-3 is not
   the tail's problem.
4. **ALIVE** if an arm beats a by more than 10 % at concurrency 8 — and that justifies only a full-width A/B
   (2.4 GPU-h per draw), which is not part of L4.
5. **What no outcome here can say**: nothing in this bench is a score. Every solver-side lever on this base has priced
   NULL, so a throughput win is a hypothesis about levels, not a measurement of them.

Local teeth, 0 GPU (`thui-l4/test_l4_arms.py`, ALL TEETH PASS — 2 seams + 2 controls): the arm env is fed through the
REAL `resolve_vllm_tuning` from `serving_setup.py` and each arm changes exactly its own field (a: mtp=3
index_share=False; b: index_share=True; d: mtp=0); the notebook's own `_spec` is executed against a Prometheus body
with the counters present and against one with them absent, the second being the control that proves an unknown metric
name is distinguishable from zero drafts.
