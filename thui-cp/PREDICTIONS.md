# thui-cp — B81 on UNSEEN community games (instrument; registered 2026-09-25 before any push or run)

> **Repo copy (2026-09-25): a research record, not runnable from this directory as-is.** The scripts resolve paths
> relative to the scratchpad they were written in: `build_notebook.py` reads the B81 source notebook from
> `../wt-daq/thui-a5/out/thui-a5-mtp0k7s28-full25-r1/` (= `thui-a5/out/...` here), `cp_sets.py` reads
> `../testbed/rand200.jsonl` (round 44 random-agent OUTPUT rows, not in this repo), `test_cp.py` needs the anim taaf
> bundle at `../anim-bundle/` and a local copy of the dataset root at `../testbed/full`, and `clock_match.py` globs
> `kout*/benchmark.json` in its cwd. `cp_sets.json` is the exact A/B/smoke sets the kernels ran. Built notebooks and
> run outputs are not included; every run output folder holds `thui_cp_env/` (copied game source): never read or
> commit it.

Why: rounds 59-63 put every remaining lever on "clear L2+ (and L1) on games the harness never saw"; the public 25
cannot measure that (tuned-on). The MIT pack `poonszesen/arc-interactive-community` is unseen by us and by the harness
authors. Pool 139 (round 44 rules, 3 quarantined official games removed), two disjoint seeded sets A/B of 25
(`cp_sets.json`, seed 20260925), smoke = first 3 of A. Metric: levels cleared (the pack has no human baselines).

## Build state (0 GPU, nothing pushed)
- `build_notebook.py` -> out/thui-cp-smoke, out/thui-cpa-full25-r1, out/thui-cpb-full25-r1: B81 (a5) notebook, cells
  0 and 15 changed only; graft only in cell 15's offline branch (asserted); ids `sahasawatt/<slug>`, private; dataset
  added to `dataset_sources`.
- `test_cp.py` (starter venv, arc-agi 0.9.9 / arcengine 0.9.3, real taaf; imageio/scipy stubbed, diagnostics-only):
  the graft CUT FROM THE BUILT NOTEBOOK loads the 3 smoke games, copies only allow-listed dirs, sets
  base_actions_per_level None, level counts match cp_sets. Mutations RED: no-None wrapper 3/3 (1 asserts on length,
  2 would silently take action ids [1, 2, 3, 4, 6] as human baselines), quarantined id, dataset not mounted, id
  missing from the pack.
- `cp_read.py`: VOID on a public run output (control), VALID on a synthetic allow-list run.
- UNVERIFIED until a smoke: the kernel's arc-agi / arcengine versions (not pinned in the notebook, not in any log we
  hold; the graft prints them) and the dataset's mount path (both layouts handled).

## Smoke (3 games @ 1,800 s, ~0.6-0.7 GPU-h) — VOID unless
THUI_CP_GRAFT ok once with a src path and versions; 3 THUI_CP lines; every game takes >= 1 action; cp_read VALID.

## Full set A (25 @ 7,920 s, ~2.4 GPU-h) — predictions for B81
- P1 levels per game in [0.6, 1.6] (hidden implied 0.7-1.06, round 63; public 1.64).
- P2 P(L1) in [0.5, 0.95]; P(L2+|L1) <= 0.5.
Use: this is a BASELINE, not a verdict. A lever arm runs on the same set A; set B is the split-half check.
Instrument rule: if levels per game >= 1.64 (as easy as public) or <= 0.3 (floor), the pack is not a usable hidden
proxy at this size -> stop spending GPU on it.

## VERIFY (wf_c73b5c08-5c6, 2 sonnet refuters, before any push) and fixes (2026-09-25T11:20:18Z)
- BLOCKING, FIXED: cell 15's post-run audit compared the runs against PUBLIC_GAME_IDS, so every thui-cp run (smoke and
  full) would have raised RuntimeError right after bm.run() (benchmark.json already saved, cell failed). Now compares
  against the allow-list _CP_IDS; the audit print no longer hard-codes runs=25.
- FIXED: the smoke build's blanket '!= 25' rewrite had turned the base's pre-graft guard into
  'len(bm.games) != len(bm.games)' (dead). The graft now goes AFTER that guard and its PUBLIC25_SELECTION print, so
  the guard is untouched (builder asserts exactly one '!= 25' left and the graft sits before bm.n_passes).
- test_cp.py now also executes the SHIPPED audit block: passes on the allow-list, raises on other ids; a mutant with
  the pre-fix comparand fails the test (exit 1).
- Checked, not a defect: base=None flows through final_score (0.0, not None) and the frozen scorer (uses final_score);
  cell 13 settings are not keyed on game ids; animation retrieval is generic; 64x64, win_levels, ONLY_RESET_LEVELS,
  WORKING_DIR and the two dataset mount paths match the base notebook's own conventions.
- ACTION7 is unmapped by the harness (ACTION1-6 + RESET only); cp_actions.py: 0 of the 50 selected games expose
  ACTION7 at level-1 reset (clicks: 15 in A, 10 in B). Later levels unchecked.
- Cost note: the base still loads and validates the 25 public offline games before the graft replaces bm.games
  (a few minutes of setup; the competition dataset stays attached, as in the base metadata).

## SMOKE RESULT (2026-09-25T12:25:25Z) — sahasawatt/thui-cp-smoke v1, COMPLETE 12:23:14Z — VALID
- cp_read: VALID. THUI_CP_GRAFT ok x1, src=/kaggle/input/datasets/poonszesen/arc-interactive-community (the 2nd layout),
  kernel arc-agi=0.9.8 / arcengine=0.9.3 (test venv had 0.9.9 — graft worked on both). 3 THUI_CP game lines, n=5 each;
  smoke clock line printed; PUBLIC25_AUDIT runs=3 (fixed audit passed). Actions 321 / 307 / 101 (all >= 1).
- Levels: dt01 5/5 WON (clears at 682/1203/1267/1356/1398 s), fl01 0/5 gave_up @1784 s, jw01 5/5 WON (375..922 s).
  Per game 3.33, P(L1) 0.67, P(L2+|L1) 1.00 — at the QUARTER clock (1,800 s).
- score.json 0.0 everywhere, as designed (base=None -> final_score 0.0); metric is levels only.
- stderr "vLLM teardown did not reach the bounded terminal gate" after the audit: PRE-EXISTING (54 of 77 earlier kernel
  logs carry it), not the graft.
- cp_read fix: output also holds vllm-openai-server.log; the reader now skips vllm*.log (was glob order luck).
  Control: a public run (thui-ap-full25-r3) still VOIDs.
- READING (smoke, n=3, not a measurement): the pack looks EASIER than public (3.33/5 at 1/4 clock vs public 1.64 at full
  clock; hidden implied 0.7-1.06). Outcomes are bimodal (0 or all 5). Crude: Beta(3,2) on the win rate gives
  P(set A per game < 1.64) ~ 0.11 even before the 4x clock -> the registered stop rule (>= 1.64 = not a usable hidden
  proxy) is LIKELY to fire on full set A. Ceiling risk: a lever that helps on hard unseen games cannot show here.

## QUICK SET A — thui-cpa-q1800-r1 (registered 2026-09-25T12:29:39Z, BEFORE push; user chose option 1 = set A @1,800 s)
Build: build_notebook.py --quick --set A; cell 15 differs from the full-A build ONLY by the 2 short-clock lines;
test_cp.py thui-cpa-q1800-r1 A: GREEN, 25/25 no-None reds, 3 guard reds, audit 2/2.
CORRECTION to the smoke READING above: the smoke was NOT a quarter-compute run. Per-game token rate depends on how
many games share the GPU: 3-game runs ~56-80 tok/s per game, 25-game runs ~13 (clock_match.py over 60+ kernel
outputs). Smoke @1,800 s x 3 games ~ 100k tokens/game ~ a FULL-clock 25-game run. The "4x clock only raises it"
argument is withdrawn, and the >= 1.64 levels/game rule is SUPERSEDED (it compared unmatched compute).
Matched reference, 0 GPU (same anim-20260807-anim bundle, 25 games, clock 1,800 s, 8 runs: ap-v0-smoke25-dl,
b100-ctl-smoke25, b100-v0-smoke25, b12x-ctl, kv10, kv12, pc, to-v0-smoke25-dl): levels/game 0.68-0.76,
P(L1) 13-17/25 = 0.52-0.68, L2+ 2-5 -> P(L2+|L1) 0.12-0.36.
Predictions (pack set A, 25 games @1,800 s):
- Q1 P(L1) in [0.05, 0.60], most likely BELOW public's 0.52-0.68: a 25-game 1,800 s run affords a median ~24 actions
  per game (b100-ctl-smoke25 24, kv12 23; full-clock a5 96), public L1 clears take a median ~22 actions (a5 22, a10-ctl
  26/22, range 4-139), and the 2 smoke pack L1 clears took 46 and 133 (70th / 97th public percentile).
- Q2 P(L2+|L1) >= 0.6 (pack levels reuse one mechanic; smoke 2/2 L1 clears went on to win all 5).
- Q3 levels/game in [0.4, 2.5].
Decision (read with cp_read.py <kout> A, VOID rules unchanged):
- P(L1) >= 0.80 -> ceiling even at L1 -> stop GPU on the pack.  P(L1) <= 0.10 -> floor -> stop.
- Else: usable as an UNSEEN-L1 instrument at this clock; next = set B @1,800 s (split-half), then a lever arm on A.
- If Q2 holds, pack L2+ is not a new-mechanic test: read the pack via P(L1) only; levels/game is inflated.
Cost: ~1 GPU-h (smoke wall 61 min: ~27 min setup incl. public-25 load, 30 min play, teardown).

## QUICK SET A RESULT (2026-09-25T13:36:36Z) — sahasawatt/thui-cpa-q1800-r1 v1, COMPLETE 13:31:22Z (first output fetch 503, refetch OK)
- cp_read: VALID. GRAFT ok x1 (25 games, same mount, arc-agi 0.9.8), short clock line, PUBLIC25_AUDIT runs=25
  actions=2787; teardown RuntimeError x3 = the pre-existing one. Output now also carries thui_cp_env/ (copied game
  dirs = game source): NOT read, never commit.
- Levels 32 -> 1.28/game; P(L1) 11/25 = 0.44; P(L2+|L1) 7/11 = 0.64; won 3 (kb01, st01, tr01). Median 66 actions/game
  (public at this clock 23-24 at the same ~13-14 tok/s per game -> pack actions cost fewer tokens). Actions-to-L1 of
  clears: 11,12,17,22,26,26,31,43,48,77,81.
- Predictions: Q1 [0.05,0.60] HIT (0.44, below public's 13-17/25 range min but NOT distinguishable at n=25);
  Q2 >= 0.6 HIT (0.64 vs public 0.12-0.36); Q3 [0.4,2.5] HIT (1.28). The "~24 actions/game" premise was wrong for the
  pack (66); Q1 hit anyway.
- Decision rule: 0.10 < P(L1) < 0.80 -> usable as an UNSEEN-L1 instrument at this clock; Q2 holds -> read via P(L1)
  only (levels/game inflated). Registered next = set B @1,800 s (split-half), then a lever arm on A.
- Same-game repeat (smoke 3 games vs quick): dt01 5 -> 0 (321 vs 126 actions), jw01 5 -> 0 (101 vs 54; its smoke L1
  came at action 46), fl01 0 -> 0. Compute per game dominates.
- POST-HOC (hypothesis, n=6): the "-v1" family (45 of the 139 pool; A 6, B 7; 5-7 levels) has L1 2/6, L2+|L1 0/2;
  the "63be02fb" family (5 levels) L1 9/19, L2+|L1 7/9. The free-L2+ profile may be one family's, not the pack's.

## QUICK SET B — thui-cpb-q1800-r1 (registered 2026-09-25T13:37:36Z, BEFORE push; user "ok" to set B @1,800 s)
Build: --quick --set B; cell 15 differs from the quick-A build ONLY in the _CP_IDS line; test_cp B: GREEN, 25/25 no-None
reds, 3 guard reds, audit 2/2. B holds 7 "-v1" games, 18 "63be02fb".
- B1 split-half: |P(L1)_B - 0.44| <= 0.20 (P(L1)_B in [0.24, 0.64]). Outside -> set composition dominates at n=25 and
  one set is not an instrument; pool A+B (n=50) before any lever arm.
- B2 P(L2+|L1)_B >= 0.5 overall.
- B3 (CONFIRMATORY for the post-hoc family split in A): "63be02fb" P(L2+|L1) >= 0.6 and "-v1" P(L2+|L1) <= 0.34
  (or no -v1 L1 clears at all). A -v1 rate >= 0.6 refutes the family reading.
Budget risk: week GPU left ~0.6 h est (unverified) vs ~0.85 h for this run; a quota stop mid-run -> no benchmark.json
or a partial one -> VOID by cp_read (games missing).

## QUICK SET B RESULT (2026-09-25T14:32:58Z) — sahasawatt/thui-cpb-q1800-r1 v1, COMPLETE 14:28:08Z — VALID
- cp_read VALID; PUBLIC25_AUDIT runs=25 actions=1956; no traceback at all this time (teardown gate reached). Median
  69 actions/game. Output carries thui_cp_env/ = game source: not read, never commit.
- Levels 54 -> 2.16/game; P(L1) 16/25 = 0.64; P(L2+|L1) 12/16 = 0.75.
- B1 split-half |0.64 - 0.44| = 0.20: ON the registered boundary (<= 0.20 passes, barely). Binomial check: diff SE
  0.141, z 1.42 -> consistent with noise, but it means ONE set of 25 carries ~+-0.14 on P(L1): pool A+B.
- B2 P(L2+|L1) >= 0.5: HIT (0.75).
- B3 family split: REFUTED. "-v1" in B: L1 5/7, L2+|L1 5/5 (1.00); pooled -v1 5/7 = 0.71, "63be02fb" 14/20 = 0.70.
  The free-L2+ profile is pack-wide; A's 0/2 was noise.
- POOLED A+B (n=50, 1,800 s, 25 games per kernel): P(L1) 27/50 = 0.54 [public matched 0.52-0.68 -> SAME range];
  P(L2+|L1) 19/27 = 0.70 [public 0.12-0.36 -> pack L2+ is not a new-mechanic test]; levels/game 1.72 (inflated).
- VERDICT: the pack is an unseen-L1 instrument whose L1 is about as hard as the public L1 at matched compute; it cannot
  measure L2+. Power: a single 25-game set swings +-0.14 on P(L1) between halves, so a lever needs a P(L1) move of
  roughly >= 0.25 on one set (or a paired A+B design) to read as more than noise.
