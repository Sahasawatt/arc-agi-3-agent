# Wayfinder map — "Score 3.00" (created 2026-08-19, label wayfinder:map)

Goal: Kaggle ARC-AGI-3 public leaderboard score >= 3.00 (current us: 1.00, rank 585/2409;
#1 = 3.57 cstl; top5 bar = 2.57). Base = Tufa Duck Harness fork (duck-mod).

## Notes

- Domain: ARC-AGI-3 Kaggle competition. Scoring run = 110 HIDDEN games, no internet,
  RTX Pro 6000 / 96GB / ~9h envelope, 1 submission per UTC day.
- Duck harness = Qwen 3.6 27B FP8 in a Python REPL loop; source vendored at
  `duck/bundle/src/`. Study: `results/taaf-study-20260818.md`.
- ⚠️ CORRECTED by R5: the "σ≈0.4 per game" cited in duckmod-build/duckv3-build/
  next-session-prompt is MISLABELED — 0.4 is Tufa's spread of the AGGREGATE 25-game mean;
  real per-game SD in our data is 2.15-4.88. Single runs cannot rank designs (all three
  pairwise comparisons p > 0.18).
- Standing rules every ticket inherits: NEVER read `environment_files/` · never log the
  Kaggle token · one submission per UTC day, verified builds only · agents = sonnet, no
  background processes inside agents · PYTHONUTF8=1 · cd every bash.

## Decisions so far

- [T0 Tomorrow's slot](../next-session-prompt.md) — resubmit duck-mod v1 at 2026-08-20
  00:00 UTC (second hidden draw; Kaggle keeps best). May be superseded by v4 if its
  commit run lands clean (decide at window with the log read, per B2).
- [B1 duck-mod-v4 built](../../results/duckv4-build-20260819.md) — duckv4/: world-model
  cap 6000 chars/field (tail-keep + marker, patches _extract_labeled_blocks
  tool_agent.py:226-260) + BudgetReallocator (zero-sum-or-negative pool over
  runtime_limit_reached/timing_payload solver.py:212-225, hard caps 600s/game +
  600s system-wide). Verified: py_compile, mock self-tests (main-thread re-run), patch
  targets live in real bundle, negative controls fail loudly, notebook diff = cell 12
  only. Constants THRASH_ACTION_FLOOR=150 / 600s caps are conservative guesses, not
  measured.
- [R1 Where duck-mod loses score](../../results/wayfinder/R1-forensics.md) — ALL 25 games
  cut by the 7,920s per-game wall clock (zero crashes/surrenders); ft09 was 2/28 actions
  into L4 at cutoff. Latency 19-233s/action on identical config. 14 games thrash ≥2×
  baseline (9 of 10 zeros there) = discovery gap; 5 games are purely clock-limited.
- [R2 Harness levers](../../results/wayfinder/R2-levers.md) — no scoring-awareness
  anywhere (flat time budget per game); world-model fields UNCAPPED and re-injected every
  turn (compounding token bloat → the latency curve); soft-deadline is dead code under
  TRUE_SUBMISSION; sandbox lacks memory rlimit. Full lever table with file:line.
- [R3 Competitive intel](../../results/wayfinder/R3-intel.md) — milestone-2 is a
  disclosure blackout; best transferable ideas: context COMPACTION over eviction
  (externally validated 13.3%→38.3%; Tufa self-flags context mgmt as weak) and explicit
  state-graph tracking (hidden-validated twice). Our 2.41→1.00 (~2.4×) vs Duck's own
  ~1.32× shrinkage → smells like harness regression, not overfit. Franzen-style TTT does
  not transfer by construction.
- [R4 Scoring EV](../../results/wayfinder/R4-ev.md) — depth is ~7× cheaper than breadth
  (final level of a 7-level game = 25.0 pts vs fresh L1 = 3.57); efficiency past 1.07×
  pace is worth zero; 1.00→3.00 = ~9 deep games closed vs ~62 new games opened.
- [B3 v5 eval](../../results/duckv5-build-20260820.md) — v5 (state channel) public
  **2.43**, top of band [2.16, 2.41], clean run; digest x1106 + banner x594 live in the
  first 10 games' transcripts. Window 2026-08-20 00:00 UTC submits v5 (Kaggle keeps best;
  higher EV + info than a duck-mod resubmit). n=1 caveat recorded.
- [B2 v4 eval + R7 postmortem](../../results/wayfinder/R7-v4-postmortem.md) — v4 public
  1.73 vs identical-code calibration band [2.16, 2.41] (duck-mod rerun = 2.16) → HOLD.
  Postmortem: binding stop = wall clock only (token hypothesis refuted); reallocator fired
  correctly but pool cap 600s exhausted by ft09 alone; world-model cap could never fire
  (fields OVERWRITTEN per turn, max 3,501 chars; 77.1% of turns write no state) — gap =
  rollout variance on 3 games, not the levers.
- [R6 Thrash forensics](../../results/wayfinder/R6-thrash-forensics.md) — 9 zero-games
  read turn-by-turn: Mode 1 scaffold state amnesia 8/9 (world-model field frozen/empty
  after turn 1-4; real reasoning lives in an uncaptured [THINKING] channel, hypotheses
  re-derived every turn); Mode 2 offered tools used ZERO times 9/9 (confirms the design
  law: an LLM under time pressure does no bookkeeping through callable APIs); Mode 3
  silent GAME_OVER resets erase 75-300 actions of progress 6-7/9; Mode 4 HUD/timer
  misread 3/9 (m0r0 drove TOWARD its own game-over timer as a win target). v5 levers
  ranked in the file — top two are auto-persist + auto-record, i.e. duck-v3's philosophy
  with the missing half (persistence) done server-side.
- [R5 Eval protocol](../../results/wayfinder/R5-eval-protocol.md) — harness ships its own
  `significance.py` (paired t/permutation/Bayes, multi-pass native); notebook hardcodes
  `bm.n_passes=1` in cell 14 AFTER the customization hook (silent trap); a commit-run
  eval costs ~2.2 GPU-h wall regardless of game count; calibration run needed before any
  power budget is real.
- **[D1 Lever class → RESOLVED 2026-08-19]** Build order for the v4 candidate, by
  evidence convergence:
  1. **Context compaction + world-model caps** — one fix hits BOTH failure axes: latency
     (R1's 19-233s spread ← R2's uncapped re-injection) and reasoning quality (R3's
     validated compaction result). Highest confidence.
  2. **Depth-aware time reallocation** — R4's math (marginal 25 pts at depth) + R1's
     clock-cutoff evidence (ft09 mid-L4). Scheduler-level, cheap, orthogonal to 1.
  3. PARKED: more injected tools / v3-style auto-push — two attempts, zero measured
     adoption or lift; revisit only after the eval protocol can actually measure a delta.
  Rationale: R1+R2+R3 form one causal chain (uncapped context → token bloat → latency →
  clock death mid-level) and R4 says the points recovered by finishing deep levels are
  the biggest pool. Both levers attack that chain directly.

## THE v7 PLAN (D3, resolved 2026-08-20 from R9+R10+R11) — "raise the floor, measure what has low variance"

R9 killed score-based iteration on single public runs (reliable base itself swings 75%
between identical-code reruns). The levers that remain are GENERAL (help every game, both
sets) and are verifiable on LOW-VARIANCE metrics (actions/clock, tokens/action) instead of
score. Build order:

- **B5 throughput build** (config+prompt only, on duck-mod base):
  (a) hard output cap `LOCAL_ANALYZER_MAX_OUTPUT` ~768 + bounded thinking (R10 very-high;
  per-request rate is ~9 tok/s so a 1k-token answer costs ~110s);
  (b) slim the 14.5k-char system prompt (dedupe the 6 addenda, target <8k) + compact
  history retention (prefix-cache hit rate falls 70-80% -> 23-34% as histories diverge);
  (c) prompt-push multi-action batching (one LLM turn amortized over 5-15 env actions —
  R10 calls it the strongest empirical determinant of actions/clock).
  SHIP CRITERION: actions/game UP >= 2x on a commit run AND paired 2-pass score
  not-degraded vs duck-mod (harness significance.py — first actual use of R5's protocol).
- **B6 model swap**: Qwen3.8-27B-FP8 (released 2026-08-14; same size/arch = same tok/s
  envelope, large agentic jumps). PRE-CHECK first: our launch args vs the sm_120
  FlashInfer+FP8-KV silent-corruption bug (vLLM #41651) — if our path uses it, add
  TRITON_ATTN workaround regardless of swap.
- **B7 combine + submit**: best of B5/B6/combo gets the next spent slot (cadence is
  on-demand per user 2026-08-20). Judge on the actions KPI + paired eval, never a single
  public mean.
- Parked: spec decoding (throughput-negative at ~25 concurrent), smaller models (no
  3.6/3.8 family below 27B; proxies say net-negative), all prompt features tuned on
  public games (v5/v6 lesson).

## Frontier tickets

| id | type | question | status |
|---|---|---|---|
| B5 | task | Throughput build per D3 (output cap + prompt slim + batching push) on duck-mod base | open |
| B6 | DONE | **duckv8 (Qwen3.8 swap) = 3.31 public, 15/25 scoring, 22 levels** — first run above every prior band; model verified in vLLM log | closed |
| B8 | DONE | duckv9 = **0.22** — the output cap truncates tool calls (finish_reason `length` 704 vs `tool_calls` 68; parser errors 87). R10's cap lever REFUTED; anim bundle still untested (confounded) | closed |
| B9 | task | v8 confirmation rerun (identical) for a band, then recommend submission | open |
| B10 | task | clean anim+3.8 NO-CAP run to test the rebase separately (v9 was confounded) | open |
(B3 closed — see Decisions: v5 = 2.43 top-of-band, features live in transcripts; tonight's slot = v5)

## Blocked tickets

| id | type | question | blocked by |
|---|---|---|---|
(B2 closed — see Decisions: v4 = 1.73, below band, HOLD; postmortem = R7)

- **[B4 v6 eval → HELD 2026-08-20]** public 1.85 out-of-band (band v5 [2.37,2.43]);
  warnings fired 74x/8 games but actions fell 4,000→2,802 (-30%) inside the same clock —
  an intervention that taxes throughput loses under a wall-clock-bound regime; hud hint
  fired 0 times (confidence gate never met on real frames). Lesson: interventions must
  REDIRECT exploration, not tax it; confidence gates need calibration against real-game
  frame statistics before shipping.
- **[Hidden-shrink ledger — the dominant unknown, updated 2026-08-20]** public→hidden:
  duck-mod 2.41→1.00 (2.4x) · v5 2.43→0.84 (2.9x) · Tufa's own reported shrink ~1.32x
  (R3, public→semi-private, dated). Both OUR builds shrink worse than the base reportedly
  did → open hypothesis: our public gains are partly public-specific. Decisive-but-costly
  probe: spend one daily slot on the PURE baseline fork (taaf-duck-fork v1, public 1.25)
  for its hidden draw — if ~0.95 (1.32x), the additions bought nothing hidden-side and v7
  must target general competence (latency, exploration policy), not prompt features tuned
  on the public 25. Candidate for the Aug-22 slot if duck-mod's second draw teaches little.

## Fog

- Whether hidden set rewards the same failure mix as public 25 (only submission deltas
  probe it — 1/day; three data points so far and the gap dominates design differences).
- v7 gating question: is there ANY lever measurable on public that transfers? The R5
  multi-pass protocol (n_passes>1, harness's own significance.py) has never actually been
  used — a paired 2-pass eval of duck-mod vs candidate would at least kill public-side
  noise before spending hidden draws.
- Whether a calibration run (repeat duck-mod commit run unchanged) is worth a slot vs
  spending every run on candidates (Kaggle GPU quota bounds this, not submission quota).
- duck-v3 salvage — parked with D1.3.
- Multi-day submission strategy once a local candidate beats duck-mod's public 2.41.
