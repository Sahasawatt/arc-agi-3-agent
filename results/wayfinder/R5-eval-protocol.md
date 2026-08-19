# R5 — local-eval protocol: how many passes to trust a design delta

Question: before spending the 1/day submission quota, what is the cheapest LOCAL (25-public-game,
non-submission "commit run") protocol that can actually rank two duck-harness designs, given the
variance we can show is really in our own artifacts — not the σ≈0.4 figure three of our own docs
have been citing.

**Headline correction, stated up front because it changes every number below:** `breadth-recon.md:6539`
sources "σ≈0.4" from Tufa's own writeup describing the spread of their *repeated 25-game submission
mean* (a single number per full run) — "Best official 1.21 (variance 0.77-1.3, σ≈0.4 **on public
games**)". Three later notes (`duckmod-transcripts-20260819.md:21/70`, `breadth-recon.md:6612/6625`)
re-cite it as **"per-game σ≈0.4"** — a relabeling from AGGREGATE-mean spread to PER-GAME spread that
was never re-derived. Section 2 below shows this matters by close to a factor of 5.

## 1. The observation table

All three artifacts are real single-pass (n_passes=1) 25-public-game commit runs, same games, same
GPU shape (`NvidiaRtxPro6000` x1), read from `benchmark.json`/`summary.txt` in
`C:\Users\Vampi\AppData\Local\Temp\{duckout,duckmodout,duckv3out}\` (baseline / duck-mod / duck-v3
respectively — `duckout` was not named in the ticket but exists alongside the other two and is the
baseline `results/breadth-recon.md:6595` cites, so it's included for the pairing).

| game | baseline | duck-mod | duck-v3 | mod−base | v3−base |
|---|---:|---:|---:|---:|---:|
| ar25-0c556536 | 0.00 | 7.73 | 0.24 | +7.73 | +0.24 |
| bp35-0a0ad940 | 0.34 | 0.28 | 0.29 | −0.06 | −0.05 |
| cd82-fb555c5d | 0.91 | 0.00 | 0.00 | −0.91 | −0.91 |
| cn04-2fe56bfb | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| dc22-fdcac232 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ft09-0d8bbf25 | 6.37 | 28.57 | 0.00 | +22.20 | −6.37 |
| g50t-5849a774 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ka59-38d34dbb | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| lf52-271a04aa | 1.82 | 1.82 | 1.82 | 0.00 | 0.00 |
| lp85-305b61c3 | 2.78 | 2.78 | 2.78 | 0.00 | 0.00 |
| ls20-9607627b | 0.02 | 2.06 | 0.00 | +2.04 | −0.02 |
| m0r0-492f87ba | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| r11l-495a7899 | 4.76 | 4.76 | 0.25 | 0.00 | −4.51 |
| re86-8af5384d | 6.56 | 0.89 | 0.63 | −5.67 | −5.93 |
| s5i5-18d95033 | 0.00 | 0.08 | 0.00 | +0.08 | 0.00 |
| sb26-7fbdac44 | 2.78 | 2.78 | 2.78 | 0.00 | 0.00 |
| sc25-635fd71a | 0.00 | 0.00 | 1.04 | 0.00 | +1.04 |
| sk48-d8078629 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sp80-589a99af | 1.36 | 4.76 | 4.76 | +3.40 | +3.40 |
| su15-1944f8ab | 2.22 | 2.22 | 1.12 | 0.00 | −1.10 |
| tn36-ef4dde99 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tr87-cd924810 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| tu93-0768757b | 0.14 | 1.46 | 2.22 | +1.32 | +2.08 |
| vc33-5430563c | 1.11 | 0.00 | 2.16 | −1.11 | +1.05 |
| wa30-ee6fef47 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **mean** | **1.25** | **2.41** | **0.80** | **+1.16** | **−0.45** |
| **median** | 0.02 | 0.08 | 0.00 | | |
| **duration (GPU-hr)** | 2.209h | 2.210h | 2.209h | | |

Sources: `duckout/benchmark.json`, `duckmodout/benchmark.json`, `duckv3out/benchmark.json`
(`game_runs[*].final_score`), cross-checked against each dir's `summary.txt`.

**9 of 25 games score exactly 0.00 in all three runs** (cn04, dc22, g50t, ka59, m0r0, sk48, tn36,
tr87, wa30) and **3 more are byte-identical across all three** (lf52, lp85, sb26) — 12 of 25 games
carry zero observed discrimination for this design family. The remaining 13 games carry the entire
signal in every comparison below.

## 2. σ estimates — real, computed, and what they contradict

We have **zero within-cell replicates anywhere in this repo's artifacts** — every (design, game)
cell above is n=1. That means no true per-game σ can be measured from what exists; the numbers
below are paired *cross-game* statistics (n=25 games, each a single realization), which is a
different and much noisier quantity than a repeated-seed σ, but it is the only thing the data
supports, and it is what the vendored harness's own tooling computes (§4).

Computed with a from-scratch paired t-test (no scipy available locally; regularized-incomplete-beta
implementation cross-checked against the formula used by `taaf/diagnostics.py`'s
`_weighted_paired_t_test`, which the harness ships specifically for this comparison — see §4).
Script: `eval_stats.py` (scratchpad), inputs = the three `benchmark.json` files above.

| comparison | n games | mean Δ | sample SD across games | paired t | df | two-sided p | σ_agg proxy (SD/√25) |
|---|---:|---:|---:|---:|---:|---:|---:|
| duck-mod − baseline | 25 | +1.1615 | 4.8767 | 1.191 | 24 | **0.245** | 0.9753 |
| duck-v3 − baseline | 25 | −0.4426 | 2.1538 | −1.028 | 24 | **0.314** | 0.4308 |
| duck-v3 − duck-mod | 25 | −1.6041 | 5.9171 | −1.355 | 24 | **0.188** | 1.1834 |
| duck-mod − baseline, **excl. ft09 outlier** | 24 | +0.2846 | 2.1817 | — | 23 | — | 0.4453 |

**None of the three pairwise comparisons is significant at α=0.05.** This is the direct, computed
answer to the ticket's premise: a single 25-game pass genuinely cannot rank these designs — not as
a qualitative worry, as a p=0.19–0.31 fact from the actual scores.

**The cross-game SD is 2.15–4.88, not 0.4** — 5-12x the figure our own docs have been calling
"per-game σ". But the σ_agg proxy (cross-game SD / √25, i.e. what the SD of a repeated *aggregate
25-game mean* would be if the 25 games were independent and identically noisy) lands at **0.43–0.98**
— and the low end (v3−baseline, 0.43) sits almost exactly on the doc's "σ≈0.4" figure. This is
consistent with the headline correction: **0.4 is very plausibly the SD of the aggregate mean, not
of an individual game**, and treating it as per-game (as "documented per-game σ≈0.4" in
`duckmod-transcripts-20260819.md:21/70` invites) understates the games needed to resolve a
per-game effect by roughly √25 = 5x.

**These are still upper bounds on true noise, not clean noise estimates** — the mod−baseline pair's
5.7x-inflated SD is dominated by ft09 (+22.20) and ar25 (+7.73), which `duckmod-transcripts-20260819.md`
independently concluded were NOT tool-driven (0 TransitionGraph calls, 2 inconclusive hud_mask calls)
and consistent with "prompt-priming and/or plain run-to-run variance" — i.e. our own prior analysis
already reads this spread as noise-dominated, which is why it's used here as a proxy at all, but it
is confounded with whatever real (if fragile) effect the prompt change has, and a true repeated-seed
run could come back either tighter or looser than 0.43–0.98.

## 3. Power table

Two designs, each estimated from N independent replicate 25-game passes (paired by game). Formula:
`N ≥ 2·(z_{α/2}+z_{power})²·σ_agg²/Δ²` per side, z-approximation (1.96+0.84=2.80 at α=0.05 two-sided,
80% power) — reasonable for planning at the N's below (single-digit-to-double-digit df), get exact
via a t-distribution once real calibration data exists.

GPU-hours use the measured **2.21 GPU-hr/pass** (§5) — identical to 3 decimal places across all
three real runs (2.209h, 2.210h, 2.209h), because the harness runs all 25 games fully concurrently
against one shared vLLM server for a fixed wall-clock session (confirmed in §5), not "until each
game finishes."

| Δ target | N/side @ σ_agg=0.43 (low, v3-base proxy) | N/side @ σ_agg=0.98 (high, mod-base proxy, ft09-confounded) | GPU-hr range (2N total × 2.21) |
|---|---:|---:|---:|
| 0.3 | 33 | 168 | **146 – 743** |
| 0.5 | 12 | 61 | **53 – 270** |
| 1.0 | 3 | 16 | **13 – 71** |

**The two σ estimates differ by 2.3x and the resulting cost estimate by 5x** — this range is the
single most important number in this report: it is too wide to plan a budget from, and it is wide
*because* we have never measured a real repeated-seed σ. Closing it costs one calibration run
(§5), which is far cheaper than either end of this table.

For reference, the *actually observed* deltas so far are +1.16 (mod−base) and −0.45 (v3−base) —
both inside the Δ=1.0 / Δ=0.5 rows respectively, both non-significant per §2. Detecting something the
size of what we already measured would need single-digit-to-low-double-digit N per side; detecting
something Kaggle-hidden-score-relevant (the actual hidden delta for duck-mod turned out to be
1.00−1.25≈flat to slightly negative per `breadth-recon.md:6636` — public 2.41 did not transfer)
is closer to the Δ=0.3 row, which is expensive under either σ estimate.

## 4. The harness already ships the statistical tool for this

`duck/bundle/src/ARC3-Inference/inference/tools/significance.py` + `.../taaf/diagnostics.py`
(`_paired_score_test`, `_paired_permutation_test`, `_weighted_paired_t_test`,
`_weighted_paired_permutation_test`) is a paired, per-game, weighted t-test + sign-flip permutation
test + Bayesian P(Δ>0) + bootstrap CI comparator, built for exactly this baseline-vs-candidate
question, and its score file format (`games: {game_id: {score, trial_scores: {seed: score}}}`)
already supports multiple trials per game. `diagnostics.py:1450` comment: *"per-game pairing wins
when game difficulty correlates across solvers, pass-level wins otherwise"* — it also has a
pass-level Welch's-t alternative (`_welch_ok` requires ≥2 passes/side) for when that assumption is
suspect, and the permutation test is there specifically because our score distribution is heavily
right-skewed (median 0.00–0.08 against means of 0.80–2.41) — the paired-t normality assumption is
shaky, which the harness authors evidently anticipated.

**This tool can be run today, at zero additional Kaggle cost**, against the three existing
`benchmark.json` files (convert `game_runs` → `games:{id:{score, trial_scores:{run_label:score}}}`,
one dict comprehension) to get the harness's own canonical p-value/Bayesian-CI verdict instead of
this report's from-scratch t-test. Not done here (out of scope for read-only analysis, and the
manual t-test above already gives the answer — not significant, any of the three pairs), but it is
the natural next step before trusting any future delta, and it is the tool a calibration run's
output should be fed into once trial_scores exist.

## 5. Where the GPU-hours actually go, and what does/doesn't reduce them

**All 25 games start within 0.6 seconds of each other and each carries `final_wallclock_seconds`
≈ 7,921–7,955s** (verified directly from every `game_runs[*].started_at`/`final_wallclock_seconds`
in `duckmodout/benchmark.json`) **against the same session's ~7,955s total duration.** This means
the harness runs all 25 games in full concurrency against one shared vLLM server for a **fixed
wall-clock budget** (~2.21h, almost certainly `deploy_target.pkl`'s `max_runtime_s` minus a soft-end
margin — `duck/tufa-labs-duck-harness-june-30-milestone-winner.ipynb` cell 14), not "until each game
naturally finishes."

**Consequence, and it reverses an intuitive lever:** restricting to the 13-game high-signal subset
(§1) would **not** proportionally cut GPU-hours per pass under the harness as currently wired — the
session still runs the same fixed duration regardless of how many games are in it, because the
budget is a clock, not a completion condition. It would only concentrate the ANALYSIS on informative
games post-hoc (real value for statistical power per §3, since a game contributing pure zero-noise
either way costs a "degree of freedom" without information) — not reduce the price of a pass.

**Seeding IS exposed, but not through the customization hook the injection builds used.**
`tool_agent.py:145-148`: `_LOCAL_ANALYZER_TEMPERATURE` (env `LOCAL_ANALYZER_TEMPERATURE`, default
**0.6**), `_LOCAL_ANALYZER_SEED` (env `LOCAL_ANALYZER_SEED`, default **-1** = unseeded — passed to
vLLM only `if seed >= 0`, confirmed at `openai_compat.py:69-70`). This is the actual mechanism
behind every score difference in §1: every LLM call samples at T=0.6, top_p=0.95, top_k=20, with no
seed pinned, so no two runs (same design or not) are bound to agree. Both constants are module-level
globals in `tool_agent.py` itself (not `from X import Y` copies into another module, unlike the
`PYTHON_ADDENDUM` trap `duckmod-build-20260818.md` §2.3 documents), so patching
`sys.modules['inference.agent.tool_agent']._LOCAL_ANALYZER_SEED = <int>` from the customization
hook (cell 12) **should** work the same way duckmod's system-prompt patch does — this is untested,
flagged UNVERIFIED, not a launched run.
⚠️ Setting temperature→0 for calibration changes the very policy being scored (the real scored runs
use T=0.6 unseeded) — useful for a cheap negative screen, not a substitute for measuring σ at the
regime actually submitted.

**`n_passes` exists and is exactly the feature wanted — but the Kaggle notebook path hardcodes it
past the point our injection cell can reach.** The framework's own offline CLI
(`inference/framework/run.py`) takes `--n-passes N --concurrent-jobs K --include-tags/--exclude-tags`
(game subsetting) directly — this is the intended calibration interface, and it plus
`significance.py` (§4) is the designed-for combination. But the Kaggle notebook does not call
`run.py`; cell 14 does `bm.n_passes = 1` **unconditionally, immediately before** `await bm.run(...)`
— and cell 14 runs *after* the customization hook (cell 12), so a `bm.n_passes = N` patch placed in
cell 12 (the only cell duckmod/duckv3 touch) gets clobbered by cell 14's own line before `bm.run()`
ever reads it. Getting `n_passes > 1` inside one Kaggle execution requires editing cell 14 itself —
a larger, disclosed diff than the "only cell 12 differs" discipline these two builds hold
themselves to, but a legitimate one for a calibration-only kernel fork that is never submitted.

## 6. Recipe

**Option A — safe default, zero code risk, cost known exactly.** Push the identical already-built
kernel (`duckmod/` or `duckv3/` or plain `duck/`) N more times via `kaggle kernels push -p .`
(each push is a fresh container execution; `LOCAL_ANALYZER_SEED` defaults to -1/unseeded, so each
execution is an independent draw). Collect each run's `benchmark.json`. Cost = **N × 2.21 GPU-hr**,
exactly, because the session length is fixed (§5) regardless of outcome. Recommended N=8 for a
first calibration batch:

```bash
cd duck   # or duckmod/ or duckv3/ — whichever design you're calibrating
for i in $(seq 1 8); do
  KAGGLE_API_TOKEN=$(cat ../.kaggle/access_token) kaggle kernels push -p .
  # wait for COMPLETE (~2.2h) before the next push, or push all 8 back-to-back if
  # Kaggle allows queued kernel executions — UNVERIFIED, check before assuming
done
```
Cost: **8 × 2.21 ≈ 17.7 GPU-hours**, cheaper than any single cell of the power table in §3, and it
converts every number in this report from "our own docs' unverified guess" to "measured."

Then feed the 8 `benchmark.json` files into `significance.py`'s expected shape (per game:
`{"score": mean, "trial_scores": {"run1": s1, ..., "run8": s8}}`) and let the harness's own paired
t-test / permutation test / Bayesian estimator (§4) report the real per-game σ, the real σ_agg, and
recompute §3's power table with actual numbers.

**Option B — cheaper if it works, unverified, requires editing cell 14.** Fork the notebook with
`bm.n_passes = N` (instead of `1`) at cell 14, so one kernel execution runs N replicate passes of
all 25 games **concurrently** against the shared vLLM server, instead of N sequential 2.21h
sessions. If the server has throughput headroom at 25 concurrent games (plausible — nothing in the
artifacts read here measures vLLM utilization), the wall-clock for N=2 or N=3 could be close to the
single-pass 2.21h rather than 2N×2.21h — a large saving. **This is a hypothesis, not a measurement**:
test it at N=2 first (cost ≤ one extra pass beyond a normal run, i.e. worst case ~4.4h vs the ~2.2h
best case) before committing a full calibration batch to it. `bm.concurrent_jobs` (or whatever knob
governs how many of the 25×N game-sessions run truly in parallel vs queued) is baked into the
pickled `bm`/`target` objects at kernel-build time and its exact name/location was not identified in
this pass — check `benchmark_initial.pkl`'s attributes before relying on this option.

## 7. Unknowns a calibration run must close (not guessed at here)

1. **Real per-game σ and real σ_agg**, unconfounded with design effect — the entire point of §6
   Option A. Without it, §3's power table spans a 5x cost range and cannot be trusted for budgeting.
2. **Whether §6 Option B's concurrency-amortization hypothesis holds** — run N=2 once, compare
   wall-clock to the single-pass 2.21h baseline, before assuming it saves anything.
3. **Whether `LOCAL_ANALYZER_SEED`/`LOCAL_ANALYZER_TEMPERATURE` are actually patchable from the
   customization hook** (§5) — the mechanism (module-level global, not a `from X import Y` copy) says
   yes by the same logic duckmod's own build verified for `PYTHON_ADDENDUM`, but it has not been
   exec'd against the real bundle the way duckmod/duckv3's builds did for their own patches.
4. **Kaggle's GPU-hour quota/cap for non-submission commit runs** — not documented anywhere in this
   repo. The daily cap of 1 applies to *submissions*, not commit runs, per `notes/next-session-prompt.md:907`
   and `breadth-recon.md`'s repeated "commit run" vs "submission" distinction, but whether there is a
   separate weekly/session GPU-hour ceiling for the `NvidiaRtxPro6000` machine shape used here is
   unverified — check before scheduling 8+ back-to-back pushes.
5. **Whether restricting to the 13-game high-signal subset (§1) changes anything at all under the
   fixed-wall-clock-budget mechanism (§5)** — the direct GPU-hour saving is very likely zero (the
   session runs the same duration regardless of game count), but whether a smaller `--include-tags`
   subset via Option B's `run.py` path behaves differently (e.g., frees vLLM throughput for more
   concurrent passes at the same wall-clock) is untested.
6. **Whether the 9 always-zero / 4 identical-across-all-three games are genuinely floor/insensitive
   for THIS harness family, or a coincidence of n=1** — worth confirming from the calibration run's
   replicate data before permanently excluding them from any analysis; a game that shows 0.00 in
   3/3 single draws could still have nonzero variance a 4th draw would reveal.
