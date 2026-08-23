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

- **D-alloc (2026-08-21) — the exchange rate is 2 slots per rankable answer.** R9 says a single
  run cannot rank two designs, and v10's own band took two runs. Quota is 30 GPU-h/week and a
  commit run is ~2h12m, so **13 slots/week = 6 rankable answers/week, maximum**. Running 13
  designs once each yields 13 numbers and zero rankings — the exact mistake R9 exists to prevent.
  Corollary: a candidate whose *losing* branch teaches nothing costs a full rankable answer to
  learn nothing, which is why B13 is held. There is no cheap eval mode — R15 settled that (games
  run concurrently, so 4 games cost the same wall clock as 25). Full reasoning:
  `notes/quota-allocation.md`.

- **D-read (2026-08-21) — read the vLLM log BEFORE the score, pre-registered.** v14's outcome
  space has two independent axes, and the quadrant "score up, mechanism unchanged" is confounded.
  It is only visible if the mechanism is read first; reading the score first makes a confounded
  result indistinguishable from a confirmation.

- **D-pred (2026-08-21) — two of R19's four predictions were not discriminators and were
  rewritten.** "`lf52`/`tr87` execute a non-zero number of actions" fails because `lf52` already
  scored 1.82 in run B — the marker is present in both worlds, so luck satisfies it. Same flaw for
  the `r11l`/`sk48` tok/s outliers (n=1 per game per run). Both replaced with population
  statistics that have many samples per run: the count of game-runs with a >50% dead tail plus the
  total fraction of clock in stuck-yield tails, and the spread of per-game tok/s across all 25
  games. Also measured: vLLM's "prefix cache hit rate" is a **cumulative** average, not a rolling
  window (mean step 0.52 → 0.041 while n grew 14.8×, the 1/n signature), so the endpoint is
  comparable across runs only at equal run length — true here, but by coincidence of config.

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
| B9 | DONE | v8 band = **[2.87, 3.31]** (rerun 2.87: 13/25 scoring, 19 levels) — 0.44 spread on identical code | closed |
| B10 | DONE | **duckv10 (anim bundle + Qwen3.8, uncapped) = 4.55 public, 22 levels from 1,285 actions** — campaign best; anim guards verified live (hard_noop_guard/animation_awareness True), zero truncation | closed |
| B11 | DONE | **v10 band = [4.55, 4.71]** (rerun: 18/25 scoring, 28 levels) — tightest band measured; lottery worry retired (broader floor, different top-3) | closed |
| B12 | DONE | v12 (v10 + brevity prompt) = 3.72, below band → the "cut reasoning" axis is dead in BOTH forms (cap v9 0.22, prompt v12 3.72) | closed |
| B13 | task | v13 (v10 + animation-retrieval discipline) — **HELD**, not queued: prompt axis is 0-for-2 and a loss teaches nothing (see D-alloc) | held |
| B14 | DONE | **duckv10 hidden = 1.70** (ref 55662656), best ever, up from duck-mod's 1.00. Predicted 1.6-1.9 before the number was known and hit; shrink 2.68-2.77x lands mid-band against duck-mod 2.41x and v5 2.89x — 3 points now, still not a law | closed |
| B15 | task | **v14 smoke, 12-minute clock (~0.1 slot)** — does the `--kv-cache-dtype fp8` flag land and does the kernel serve? `kv_cache_dtype` is readable at 5m50s and the first request is served at 6m37s, both measured off v10's own log. Insurance against v7's two ERROR-burned slots. Does NOT measure score or prefix decay | open |
| B16 | task | **v14 paired, 2 slots** — does KV retention change the mechanism, and does that move score? Read the vLLM log BEFORE the score (see D-read). P2/P4 rewritten as population statistics first (see D-pred) | blocked by B15 |
| B17 | task | **v16 (push-the-diff) — build, then paired, 2 slots.** Design done at `notes/v16-push-the-diff.md`; wiring is two edits reusing `_diff_cells`/`_bbox_text`/`_format_changes` and the proven `_build_user_prompt` push channel | open |
| B16 | DONE | **v14 ran = 2.87 public.** Mechanism confirmed on Kaggle's engine (KV 199k→398k tokens, concurrency 11.32x→21.23x, prefix retention 22%→42%, 338→426 tok/s) and the capacity became **more actions (1285→1633) and fewer levels (22→19)**. Throughput axis closed | closed |
| B17 | DONE | **v16 ran = 3.51 public.** Patch installed in-kernel with 4/4 teeth; delivery measured at 90.4% of turns vs 46.6% before. Most games scoring ever (19) and best act/lvl ever (50.8), still below band — breadth does not pay. Push-more-state axis closed | closed |
| B19 | DONE | **v17 (search over a learned transition model) KILLED before build**, three offline measurements: search constructs appear in **2.0%** of code turns today; predicting the changed-cell count from the action is **24.6%**; exact `(state, action)` repeats are **20 of 1,597 = 1.3%** so a learned model has almost no coverage. Details + the delivery-option reasoning: `notes/v17-search-killed.md` | closed |
| B20 | DONE | **The scorer has a second cap and it was missing from working memory.** `completion_cap = 100·Σ(done levels)/W`, recovered from `R4-ev.md:19-20`, verified exactly on 5 games. **7 of 25 games are already at it, 41% of the score is locked there, and the whole efficiency axis ceilings at 5.80 public (~2.1 hidden)** — below the 6.9-7.1 that top-5 needs. Depth is the only axis left: +1 level/game = 12.07 public (×2.56) | closed |
| B21 | DONE | **v10 second draw = 1.32 vs first 1.70 (ref 55694474).** Same build, 0.38 apart — hidden mean ~1.51, shrink ~3.05x, every past hidden comparison inside the noise. Plus the retro pair: v9-lite 0.10/0.10 (byte-identical accidental duplicate) → **variance grows with score**. LEDGER CORRECTION 2 | closed |
| B25 | DONE | **v20 (MoE) = 0.18 — the first result outside the same-build spread [2.82, 4.71], so the first one a single run can rank.** vLLM loaded it, tool calls parsed, the agent fired **7,656 actions (4.7x v10)** and cleared **3 levels vs 28**. act/lvl 57 -> 2,552. Converts R24 from elimination to measurement: throughput was not the bottleneck, reasoning-per-decision is. Does NOT separate architecture from the one-generation gap (3.6 vs 3.8, worth +37% measured the other way). `notes/R25-moe-result.md` | closed |
| B22 | DONE (2nd) | **MoE found AND run.** After the reopen, v20 ran Qwen3.6-35B-A3B-FP8: **0.18**, 3 levels, 7,656 actions — see B25/R25. The axis is closed by measurement, not by availability | closed |
| B23 | run | **v18 = v10 + `MULTIMODAL_UPSCALE` 4→8.** The anim bundle has been sending a PNG of the board every user message all campaign (`tool_agent._build_user_message:1377`) at 256×256 = **~64 vision tokens for 4096 cells, 1 token per 8×8 block**. 8× gives 1 per 4×4 for ~+192 tok/message (≈+24% of 2.03 Mtok). Smoke pushed 2026-08-22 (`-t 900`, version 1). Note: `notes/v18-vision-upscale.md` | open |
| B24 | DECIDED | **Stay on the anim bundle.** The newer bundle (6d8e3dd) offers env-var knobs (moot — cell-8/12 patches work), animation_retrieval default OFF (we do not use it), grid lines (its own flag is broken: sets 'true', reader tests "1"), and vision byte counters (nice, not worth a re-base). Revisit only if a future change needs a seam the string-replace cannot reach | closed |
| B26 | frame | **"ปัญหาคือการเลือก action" — sharpened against evidence 2026-08-24.** Per-pick mechanics are fine (no-op 5%, no lock-in, goal stated 93%); what fails is upstream: (a) whether the stated GOAL MODEL is *correct* — never measured, only its presence — and (b) whether the model ever *searches* over what it believes (2.0% of code turns, v17 note) instead of probing one action at a time. B27/B28 measure the two halves for free; B29 is the build if either confirms | **closed 2026-08-24**: both halves measured. (a) goal model WRONG 4/5 on stuck levels (R28) · (b) search unmovable by prompt and unpaid when induced (B28/v22). The frame held: selection fails upstream, at rule discovery |
| B27 | measure-free | **Is the goal model RIGHT when a game is stuck?** Method that never touches `environment_files/`: take stuck-level transcripts from v18/v19/v21 artifacts on games some OTHER run eventually cleared, and judge the stuck run's `Goal model:` text against the mechanic the clearing run's own actions demonstrate. Deliverable: % wrong-goal on stuck levels, with per-game examples. If high → the bottleneck is rule DISCOVERY and B29's verify-loop is the wrong build. **Pairs enumerated 2026-08-24 (same-model runs only, v20 excluded): cd82 v18-L0/v10cal-L2 · dc22 v18-L0/v10cal-L2 · ft09 v19-L0/v10cal-L3 · lp85 v19-L1/v10cal-L3 · re86 v10cal-L1/v18-L4** — re86 is the sharpest: the BEST build is the stuck one. **CLOSED 2026-08-24 → notes/R28-goal-model-audit.md**: 4/5 stuck levels hold a WRONG or never-formed goal (cd82 rejected the true goal on a false mechanical premise · dc22 enumerated gem positions in a ball-path game · ft09 never discovered clickability · re86 38 turns of pure perception; lp85 the exception: goal right, action model wrong). Bottleneck = rule DISCOVERY; 3/5 clears trace to a probe taken before the theory was finished. (Also corrected: v10cal events were on disk all along at Temp/duckv10cal/artifacts/ — the never-downloaded claim was false when written; v18/v19 events fetched same day, 25+25 files) | **closed** |
| B28 | measure-free | **Does prompt pressure move search usage?** v22's ported addendum carries the rank-21 team's explicit BFS instruction. When v22 lands, re-run the v17 search-construct probe (`def solve/search/plan`, `deque`, `heapq`, ...) over its transcripts. Baseline 19/935 = 2.0%. Usage up + score flat → search isn't the lever; usage still ~2% → prompts cannot move it and only a structural gate (B29) can | **CLOSED 2026-08-24**: v10cal control reproduced exactly (19/935 = 2.0%), v22 = 22/902 = 2.4% — prompts cannot move it. And the two games where it DID spike locally scored WORSE (tu93 10/28 turns, 5.22→0.08; g50t 8/40, 0→0) — search turns bought nothing even where induced, consistent with v17's 1.3% transition-coverage kill. Both pre-registered branches point AWAY from search as the lever |
| B29 | build-candidate | **Verified-plan gate** (R20 #1 + #11 merged, built on OUR stack): when stuck, draft k candidate short plans in the sandbox, check each against `history`'s recorded transitions, execute only the best-verified one, abort on first prediction miss. The free verifier (frame diff) already exists in the sandbox. Blocked by B27/B28 — if the goal model is usually WRONG, verified plans toward a wrong goal are worthless | **closed — REFUTED 2026-08-24**: both blockers landed against it. B28: prompts can't move search usage and induced usage bought nothing. B27: the goal model on stuck levels is wrong 4/5 — verified plans toward a wrong goal are worthless (R28). Not built |
| B31 | build-candidate | **Grid lines on the board PNG — the feature its own author never ran** (notes/R29-grid-lines.md). Newer bundle ships `_render_grid_lined_image` gated on `MULTIMODAL_GRID_LINES == "1"`; its own setup says `'true'` → never fired anywhere. Anim bundle lacks it entirely. Targets R28's failure mode at the perception layer (3/5 wrong goals pivot on a spatial misread) without prompt pressure. v23 = v10 + upscale 8 + ported renderer, patched at `vision_context.frame_to_png_data_url` (in-module call chain verified — no import-by-name trap); **v18 (8, no lines, p=0.508 ≈ v10) is the control arm**, so any out-of-band result attributes to the lines. Costs 1 GPU slot | open |
| B32 | build-candidate | **Untried-ledger nudge** — per-level "never pressed / never clicked" list injected via the proven nudge channel (sk48 obeyed 7/7). Targets ft09's failure exactly, but nearest precedent v16 (state-derived push, 3.51 in-band-worse) and B28 (induced behaviour ≠ score) both lean against. Deferred behind B31 | open |
| B30 | decision | **Where the remaining hidden draws go.** Variance grows with score (v9-lite A/A spread 0.00 vs duck-v10 0.38), so ranking high builds needs 2+ draws each. ~1 submission/day; the week's GPU quota ~7 slots. Decide: spend draws re-measuring v10's mean vs testing one candidate — after v22's public number lands. **Decision-ready 2026-08-24**: v22 landed in-noise (2.84, p=0.0798) and B26/B27/B28/B29 all closed — no candidate build holds positive evidence on any measured axis. The only positive-EV move left is resubmitting v10 for more hidden draws (n=2 spread 0.38; leaderboard keeps the best), i.e. buy samples of the upper tail of the best build. Awaiting the user's call | open |
| B18 | DONE | **v15 (stop-on-surprise) ABANDONED** the day it was drafted — the batch path was already guarded, and a "surprise" has no harness-visible definition because the harness never sees the model's expectation. Full reasoning kept at `notes/v15-stop-on-surprise.md` | closed |
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
