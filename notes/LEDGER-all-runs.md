# Every run this campaign produced — what it scored and why

Assembled 2026-08-22 from the `summary.txt` and `benchmark.json` of every downloaded run.
Public = the 25-game commit-run mean. Hidden = the 110-game leaderboard draw, only for the
four builds ever submitted.

## The table

| run | public | hidden | scoring | levels | actions | act/lvl | Mtok | bundle | what changed, and why it landed there |
|---|---|---|---|---|---|---|---|---|---|
| **v10cal** | **4.71** | — | 18 | 28 | 1597 | 57.0 | 2.03 | anim | rerun of v10; the campaign's best number |
| **v25** | **3.69** | — | 16 | 22 | 1341 | 61.0 | 1.82 | anim | B37's sampler pin — `LOCAL_ANALYZER_SEED=20260825`, temperature left at the harness default. **P1 and P2 both pass**: wall **2h 12m 30s** (thui-v1 was 2h 12m 35s, so not the silent-worker-death shape) and `taaf_setup_env.json` from the run carries `LOCAL_ANALYZER_SEED: 20260825` with `LOCAL_ANALYZER_TEMPERATURE: 0.6` untouched. `rank_runs.py` vs **v10cal p=0.5046**, vs **clock2x p=0.2919**, both NOT-DISTINGUISHABLE — a fifth in-band sample of the v10 family, which is what P1 predicted. ⚠️ **This run is NOT v10+seed and must not be quoted as one.** The builder read `SRC_NB=duckmod` and never replaced cell 12, so the notebook (**sha256 `1504012d`**) carried duckmod's 14,355-char patch block; the corrected build is **`d5473ba8`** and has never run. **Measured what that leak actually cost**, over 1,105 analysis turns with the R33/R39 section discipline: the patch is **additive only — it does not wrap `action`**, it uses that line as an anchor and injects `hud_mask` + `TransitionGraph` beside it. Adoption is **TransitionGraph 0.0%** and **hud_mask 0.7%** (8 turns across 5 games) against an `action()` positive control at 32.6% and a negative control of 0 — and the probe proves it is not blind, since the SYSTEM PROMPT names `TransitionGraph` in all 1,105 turns. **So the real confound is not the tools, it is the PROMPT**: 16,039 chars against clock2x's 14,204, i.e. **+1,835 = +12.9% every turn** to advertise two tools nobody calls — R6's Mode-2 law and B32's lesson in one run. **P2 is unaffected** (a seed does not travel through the prompt); **P1 is conditional** — 3.69 belongs to a build with a longer prompt than v10. **P3 (spread) is untested and now needs two runs of `d5473ba8`, which is a different build from this one.** Kernel `sahasawatt/taaf-duck-v25` v1, 2026-08-24. `results/v25-summary-20260824.txt` |
| **thui-v1-1** | **5.24** | — | 15 | 25 | 1325 | 53.0 | 2.10 | anim | **B37's sampler pin on the CLEAN arm** — v10 exact + `LOCAL_ANALYZER_SEED=20260825` in `setup_env`, temperature untouched at the harness default. This is the arm `v25` above was meant to be: `thuiv1/` sources its own cell 12, so it cannot carry v25's `SRC_NB` defect, and the v1-0→v1-1 diff is **AST-verified as ONE executable change** (cells `[8, 12]` differ; cell 12 is AST-identical, +9 lines of docstring prose, both dumping to 12,980 chars after stripping bare-string `Expr`; controls cells 0 and 14 byte-equal). **All four gates pass.** **P1**: wall **2h 12m 52s** (v25 2h 12m 30s, thui-v1-0 2h 12m 35s — not the silent-worker-death shape); seed literal 1 hit in the setup echo against a `LOCAL_ANALYZER_TEMPERATURE` control at 1, and the run's own `taaf_setup_env.json` confirms it independently (`SEED=20260825`, `TEMPERATURE=0.6`, `MAX_OUTPUT=0`, `UPSCALE=4`). **P3 adoption = 0 calls in 0 of 25 games with a non-zero control (`segmentation`=369)** — `clock2x`'s shape exactly, so this run really is `v10`+seed and not `duckmod`+seed. Against v25's **hud_mask 0.7% / TransitionGraph 0.0%** that is the contrast the two arms exist to draw. **P4**: 25 of 25 `*_usage.jsonl`. `rank_runs.py` (`--selftest` cleared both poles in the same session first): vs **v10cal p=0.8001**, vs **v25 p=0.3094**, vs **clock2x p=0.5868** — all NOT-DISTINGUISHABLE, a **sixth** in-band sample of the v10 family. ⚠️ **The mean rose while the levels FELL** (4.71→5.24 but 28→25, 8 up / 9 down / 7 flipped) — noise, not a lever; and 5.24 clearing the old `[2.82, 4.71]` band is a **screen, not a verdict**, exactly as clock2x's 6.40 was. ⚠️ **The band is now `[2.82, 5.24]`, and that widening is ARITHMETICALLY TRIVIAL, not evidence against B37** — a band is a min/max over samples, so adding one can only widen it or leave it. **B37 is still run 1 of 2**: the reading it needs is the spread across ≥2 runs of THIS build, and nothing here measures that. The seed is proven **SENT**, never **DETERMINISTIC** — batched vLLM is not bit-reproducible across differing batch compositions and 25 games share one server. **Rode free — P5, the v25 free rider, is answered**: under duckmod's cell 12 `ft09` and `bp35` emitted **0** and **1** actions against a floor of **9** anywhere in 125 game-runs; here they are **86** and **63**, i.e. normal, so that stall belongs to the **duckmod prompt**, not to the harness or the sampler. ⚠️ **`v10cal`'s action total is 1597** — the `1285` that appears in older prose is `v10out`, a different run, and swapping them puts tok/action out by 24%. Kernel `yocybercode/thui-v1-1` v1, 2026-08-25. `eval/fixtures/thuiv1-1.json` |
| **clock2x** | **6.40** | — | 17 | 30 | 2637 | 87.9 | 4.33 | anim | v10 with `max_runtime_s_per_game` 7920→15840 and nothing else (B34). **The highest public number this campaign has produced, and it ranks NOTHING**: `rank_runs.py` vs v10cal p=**0.2761** NOT-DISTINGUISHABLE, 10 up / 6 down / 5 flipped. Read the LEVELS column instead — 28→30, i.e. **+2 for double the clock**, against B34's own pre-written P4 of +1 per GAME. So the depth-by-time axis is answered `no` at its strongest setting, and B36 (reallocating the same budget) is bounded below that. P1 passed: wall **4h 24m 50s**, so `bm.solver` does reach the per-game session — the lever worked and the effect is small, which is the one outcome no probe could have told apart from a broken lever. ⚠️ **Ships nowhere**: hidden = 4 waves × 15840s = 17.6h against a 9h budget, and cell 12 degrades to v10 under `TRUE_SUBMISSION` by design. Its lasting value is a by-product — `summary.txt` gave the per-game TOTAL level counts (sum 183) that closed B35's blocker. Kernel `yocybercode/clock-2x-v1`, 2026-08-24. `results/clock2x-summary-20260824.txt` |
| **v10out** | **4.55** | **1.70** | 14 | 22 | 1285 | 58.4 | 1.87 | anim | anim bundle + Qwen3.8, output uncapped. The rebase onto Tufa's animation-awareness branch is the single largest jump in the campaign |
| **v24** | **3.78** | — | 14 | 20 | 1196 | 59.8 | 2.11 | anim | v10 exact + the B32 untried-ledger nudge (R36): per-level tried/never-tried counting spoken through the hint channel at turns 8/16/24. Rig-verified on an 8B first (fired correctly, model obeyed in 4 actions). On the 27B: **64 fires across 18 games, obedience 30/58 = 52% within 6 actions, with hard refusal streaks** (sb26 ACTION7 named 7x never pressed; tr87 arrows named 9x across 72 turns, untouched) — the channel that carried animation nudges 7/7 carries this one only half the time. `rank_runs.py`: **p=0.304, NOT-DISTINGUISHABLE** (8 up / 9 down / 8 flips). Campaign tally: 11 modifications of v10, 0 above the band. `notes/R36-untried-ledger.md` RESULT |
| **v23** | **3.32** | — | 15 | 20 | 1634 | 81.7 | 2.21 | anim | v10 + upscale 8 + the grid-line renderer NO ONE had ever run (ported from the newer bundle whose own setup arms 'true' against a == "1" reader — R34) + one system-prompt line saying the lattice is a rendering aid. The note exists because the v23 SMOKE caught ka59 reading the lattice as GAME STRUCTURE and burning a 7k-char turn on the image-vs-ascii contradiction; v23.1's smoke showed the note in 111/111 prompts and the confusion gone. Full run: `rank_runs.py` **p=0.4061, NOT-DISTINGUISHABLE** (8 up / 11 down / 7 flips, levels 28→20). Mid-band — B31 closes: coordinate scaffolding at the perception layer does not move score either. `notes/R34-grid-lines.md`. Cross-checks from the run artifacts (Watchara, merged 2026-08-25): vs v18 delta −0.28 p=0.8035, vs v19 +0.50 p=0.7325 — indistinguishable from ALL of v10cal/v18/v19; the lattice leaves NO verbal trace (1 of 1,048 turns mentions grid lines — and v18, which renders none, carries the same single mention in the same game re86, so that hit is not the feature); behavioural outlier cn04: 454 actions / 92 turns / 5 RESETs for 0 levels vs 26–41 actions in every sibling run. (His "not built in this repo" note was true when written — duckv23 landed at 3a77b0b and was pruned at 4a42e0b; builder in history) |
| **thui-v1** | **3.20** | — | 16 | 22 | 1493 | 67.9 | 2.16 | anim | v10 + the per-request usage probe in cell 12 (`thuiv1/request_usage_probe.py`). The instrument is inert by design and the number says so: a **fourth** sample of v10, inside the [2.82, 4.71] band, the same shape v19 has. `rank_runs.py` on this run's own `benchmark.json`: vs **v10cal** delta -1.51, **p=0.3027 NOT-DISTINGUISHABLE**; vs **v19** delta +0.38, **p=0.7579 NOT-DISTINGUISHABLE**. Measured, not inferred. `won: 0`, so a banking graft would still be inert here. What it bought is not the score: 25 `*_usage.jsonl` files carrying `completion_tokens` + `finish_reason` per request, which is the distribution duckv9 was capped without — read, and the answer is **no cap is worth placing**: the distribution has no fat tail, so 8192 saves 0.98% and 12288 saves nothing. It also showed **all 25 games hit `max_runtime_s_per_game=7920`** (min 7920, max 7955), so `gave_up` here is the clock, not the agent, and the score is a throughput number with input:output at 10.7:1. `notes/R35-usage-distribution.md`. Kernel `yocybercode/thui-v1-0`, 2h 12m 35s, 2026-08-23. |
| **v22** | **2.84** | — | 16 | 20 | 1612 | 80.6 | 1.99 | anim | v10 + the rank-21 team's PYTHON_ADDENDUM ported verbatim (AST-extracted, both import bindings patched, teeth in-kernel: `3817 -> 4571 chars`). `rank_runs.py`: **p=0.0798, NOT-DISTINGUISHABLE** — lands at the very bottom of the [2.82, 4.71] same-build band. B28 rode free: search-construct usage **19/935 = 2.0% (v10cal control, reproduced exactly) -> 22/902 = 2.4%** — the explicit BFS instruction moved nothing globally, and the two games where it DID spike locally both collapsed (tu93 36% of turns, score 5.22->0.08; g50t 20%, 0->0). The last attributed lever from the only public artifact above us closes. `notes/R27-git-sweep.md` RESULT |
| v12 | 3.72 | — | 17 | 24 | 1810 | 75.4 | 2.19 | anim | v10 + a "be brief" prompt. Below band → the cut-reasoning axis is dead in its soft form too |
| **v21** | **1.25** | — | 15 | 12 | 2921 | 243.4 | 2.27 | anim | v10 + `reasoning_effort=medium` (the rank-21 team's flag; template default is xhigh). Patch verified in-kernel. Mechanism worked exactly as designed — **tok/action 1271→776 (−39%), actions 1597→2921 (+83%)** — and levels HALVED (28→12). `eval/rank_runs.py`: **p=0.0052, WORSE** — the second result outside the same-build noise, in the opposite direction from the hope. `notes/R26-reasoning-effort.md` |
| **v20** | **0.18** | — | 3 | 3 | 7656 | 2552.0 | — | anim | v10 with the model swapped to **Qwen3.6-35B-A3B-FP8** (MoE, 256 experts / 8 active, ~3B active). vLLM booted it fine and tool calls parsed — the agent fired **7,656 actions, 4.7x v10's 1,597** — and cleared **3 levels against 28**. act/lvl 57 -> 2,552. **The first result of this campaign that lands outside the [2.82, 4.71] same-build spread**, so it is the first single run that can rank anything. `notes/R25-moe-result.md` |
| **v19** | **2.82** | — | 16 | 20 | 1638 | 81.9 | — | anim | v10 + the fork's `banking` graft, armed and verified installed (`solver HarnessSolver -> BankingHarnessSolver (installed=True)`). **It never fired**: banking needs a full-game WIN and all 25 games ended `gave_up` — 0 WINs, 20 of 183 levels. So this is a THIRD sample of v10 with an inert graft, and it is what widened the public band to [2.82, 4.71]. `notes/R23-banking.md` |
| **v18** | **3.60** | — | 15 | 22 | 1576 | 71.6 | — | anim | v10 + `MULTIMODAL_UPSCALE` 4→8. The board PNG went 256×256→512×512 (~64→~256 vision tokens for 4096 cells). Below band, and the shape is v14's exactly: **same 22 levels as v10out for 291 MORE actions** (1285→1576), act/lvl 58.4→71.6. Bigger image did not buy sight; it bought attempts. `notes/v18-vision-upscale.md` |
| v16 | 3.51 | — | **19** | 24 | 1218 | **50.8** | 2.02 | anim | v10 + a change summary pushed into every turn. Delivery doubled (46.6%→90.4% of turns) and the score fell. Most games scoring ever, best efficiency ever, still lost — breadth does not pay |
| v8out | 3.31 | — | 15 | 22 | 1946 | 88.5 | 2.12 | old | model swap to Qwen3.8 on the OLD bundle. Proved the model was worth ~+37% before the bundle was touched |
| v14 | 2.87 | — | 15 | 19 | 1633 | 85.9 | 2.35 | anim | v10 + `--kv-cache-dtype fp8`. Mechanism confirmed (KV 199k→398k tokens, prefix retention 22%→42%, +26% tok/s) and the capacity became **more actions, not more levels** |
| v8cal | 2.87 | — | 13 | 19 | 1586 | 83.5 | 2.19 | old | v8 rerun; band [2.87, 3.31] on identical code — 0.44 wide |
| v5out | 2.43 | **0.84** | 14 | 21 | 4000 | 190.5 | 1.76 | old | state channel (accumulating world model). Hidden draw came in below duck-mod |
| duck-mod | 2.41 | **1.00** | 13 | 17 | 3481 | 204.8 | 1.50 | old | Duck + our hud_mask/TransitionGraph patches. Held the leaderboard slot (rank 585/2409) until 08-22 |
| v5cal | 2.37 | — | 14 | 17 | 3740 | 220.0 | 1.77 | old | v5 rerun |
| duck-mod cal | 2.16 | — | 13 | 19 | 3858 | 203.1 | 1.56 | old | duck-mod rerun; band [2.16, 2.41] |
| v6 | 1.85 | — | 11 | 15 | 2802 | 186.8 | 1.58 | old | new digest; warnings taxed actions |
| v4 | 1.73 | — | 13 | 16 | 3867 | 241.7 | 1.66 | old | several levers at once, all measured inert (R7) |
| duck (stock) | 1.25 | — | 13 | 16 | 4090 | 255.6 | 1.54 | old | the unmodified upstream harness — our starting line |
| v3 | 0.80 | — | 12 | 13 | 4336 | 333.5 | 1.58 | old | early fork |
| **v9** | **0.22** | — | 2 | 2 | 255 | 127.5 | 0.22 | anim | `LOCAL_ANALYZER_MAX_OUTPUT=768`. The cap truncated the tool call that carries the action — `finish_reason=length` 704 times vs `tool_calls` 68 |
| v4out2 | 0.00 | — | 0 | 0 | 0 | — | 0.00 | old | dead run |
| our own agent | — | **0.11** | — | — | — | — | — | — | written from scratch before adopting Duck |

Never ran: **v13** (retrieval-discipline prompt, held — losing axis), **v15** (abandoned at design;
the batch path was already guarded and "surprise" has no harness-visible definition), **v7/v7b**
(ERROR twice on an infra flake).

## What the column that actually explains the score is

Not levels. Not games scoring. **Actions per level.**

```
duck stock  255.6 act/lvl → 1.25
duck-mod    204.8          → 2.41
v5          190.5          → 2.43
v8           88.5          → 3.31
v10          57.0          → 4.71
```

Five builds, monotonic, across two different bundles and two models. Score is
`min((baseline/actions)^2 * 100, 115)` weighted by level number, so halving the actions spent per
level roughly quadruples that level's contribution. Every real gain this campaign made was an
efficiency gain wearing some other name.

### CORRECTION 3 (2026-08-23) — the PUBLIC band was wrong too, and it invalidates every run comparison

v19 armed the banking graft and scored **2.82 public**. Then the check that should have come
before the run: **banking never fired.** `solver_note` on all 25 games contains only
`tokens=NNNNN` — no mention of a replay, a prune, or an abort — and the reason is in the
state column:

```
v19    : states {'gave_up': 25}   games reaching WIN: 0   levels cleared 20 of 183
v10cal : states {'gave_up': 25}   games reaching WIN: 0   levels cleared 28 of 183
```

`banking_solver` fires "once a session's WIN is fully recorded" — a WIN is the whole game,
every level. **This campaign has never won a single game.** Its four engine facts were all
verified correctly and none of them was ever reached.

So v19 is v10 with an inert graft, i.e. a THIRD sample of the same build:

| run | public |
|---|---|
| v10cal | 4.71 |
| v10out | 4.55 |
| **v19 (banking inert)** | **2.82** |

**The band this campaign has used to judge every design is [4.55, 4.71]. The real spread of
the same build is [2.82, 4.71] — 1.89 wide, 40% of the top.** Consequences:

| run | score | verdict recorded | verdict that survives |
|---|---|---|---|
| v12 | 3.72 | "below band, brevity axis dead" | inside v10's own spread |
| v16 | 3.51 | "delivery doubled and it still lost" | inside |
| v18 | 3.60 | "bigger image bought attempts, not sight" | inside |
| v14 | 2.87 | "KV fp8 mechanism works, score didn't move" | inside |

**Four of the eight closed directions were closed on a difference smaller than the noise of
the build they were compared against.** The mechanism findings inside them (v14's KV
retention doubling, v16's delivery going 46.6%→90.4%, v18's image arithmetic) are still real
— those were measured directly, not inferred from the score. What does not survive is the
verdict attached to each: "this axis is dead".

⚠️ v19 is not a clean A/A: `BankingHarnessSolver` swaps `session_class`, so trace recording
runs even when the replay never does. Actions moved 1597 → 1638 (2.6%), which does not
explain a 40% score drop, but the pair is a near-A/A rather than an A/A.

**What this costs going forward:** with n=3 spanning 1.89 on public and n=2 spanning 0.38 on
hidden, a single run cannot rank two designs on either set — R9 said this for public and was
under-believed. Any future claim that a change helped needs paired runs, and the campaign
does not have the quota to buy that for every idea.

**The instrument for this now exists: `eval/rank_runs.py`** — paired per-game sign-flip
permutation over the 25 games, verdict DISTINGUISHABLE only at p<0.05. Calibrated on both
poles in one invocation (`--selftest`): v10cal-vs-v19 (same build) reads NOT-DISTINGUISHABLE
at p=0.21 ✓, v10cal-vs-v20 (26x apart) reads WORSE at p=0.0001 ✓. Re-judging v18 with it:
**p=0.51, NOT-DISTINGUISHABLE** — this table's original "below band" verdict on v18 is now
refuted numerically, not just argued. Per-game fixtures for all four runs: `eval/fixtures/`.

### CORRECTION 2 (2026-08-23) — the hidden number has a ±0.19 spread and every past comparison sat inside it

v10 was resubmitted unchanged (ref 55694474) purely to measure hidden variance. Result:

| draw | hidden |
|---|---|
| 1 (ref 55662656, 2026-08-21) | **1.70** |
| 2 (ref 55694474, 2026-08-22) | **1.32** |

Same parquet, same build, **0.38 apart — 25% of the larger value**. So:

- **v10's hidden mean is ~1.51, not 1.70.** Every plan built on 1.70 was built on the
  luckier of two draws, and 1.70 was the number this campaign quoted all day.
- **Every hidden comparison this campaign ever made is inside the noise.** duck-mod 1.00
  vs v5 0.84 is a 0.16 gap; our own agent's 0.11 is the only number outside it. Two
  builds cannot be ranked on one hidden draw each — the same rule R9 established for
  public runs turns out to hold harder here.
- ⚠️ **CORRECTED 2026-08-24 by R30 — the 3.05x below mixes a MAX with a MEAN, which is the
  error this very correction flags one paragraph up about quoting 1.70.** It divides the
  top TWO public draws by the MEAN of the two hidden ones. `v10cal` 4.71, `v10out` 4.55,
  `thuiv1` 3.20 and `v19` 2.82 are all the same build, so means on both sides are **3.82
  public over 1.51 hidden = 2.53x**. It moves the target the easy way: a candidate needs
  public **7.29** to sit at the 2.88 bar, not 8.83, and B20's 5.80 ceiling is **2.29**
  hidden — still under the bar, so the depth conclusion is unchanged.
- **The shrink is worse than recorded**: public [4.55, 4.71] against a hidden mean of
  ~1.51 is **~3.05x**, not the 2.72x the depth table used. The +0 row of that table
  predicted 1.73 and was scored against 1.70; against the mean it over-predicts.
- **Top-5 needs 2.57 hidden**, so the gap from a mean of 1.51 is **+1.06**, not +0.87.

Two draws is n=2: 0.38 is a range, not a standard deviation, and the true spread could
be wider.

**Addendum 2026-08-24 — a SECOND hidden A/A pair existed all along, and it reads 0.00.**
Submissions 55559497 and 55567678 are a byte-identical accidental duplicate of v9-lite
(recorded contemporaneously in `notes/next-session-prompt.md`: *"Today's quota got spent on
an accidental byte-identical duplicate (55567678, PENDING — expect ~0.10)"* — and it drew
exactly 0.10, as predicted). So:

| build | draw 1 | draw 2 | spread |
|---|---|---|---|
| v9-lite (low score) | 0.10 | 0.10 | **0.00** |
| duck-v10 (high score) | 1.70 | 1.32 | **0.38** |

Hidden variance is not a constant — it **grows with the score**, which is exactly what the
per-game mechanism predicts: the swing lives in deep-level clears, and a 0.10 build has no
deep clears to flip. A single hidden draw is adequate for a weak build and inadequate for
precisely the builds worth ranking. What it already rules out is reading any single hidden number as a build's
value.

⚠️ **NARROWED 2026-08-24 by R30 — the v9-lite row contributes nothing to that conclusion.**
"Grows with the score" is a restatement of **constant CV**, and the CV is now measured
twice: **0.249** over the four same-build public draws and **0.178** over this hidden pair.
At v9-lite's 0.10 that same CV predicts σ = **0.025** — the pair had almost no room to
differ, whatever is true about how variance scales, so its 0.00 is implied by the v10 pair
rather than confirming it. The conclusion stands and rests on **one** pair. The public CV
also gives an INDEPENDENT reading of this build's hidden σ — 0.249 × 1.51 = **0.376**
against this pair's own **0.269**, agreeing within 1.40, which is what makes the B30
decision robust where n=2 alone could not.

### Where the variance comes from — per-game, and the big earners are the unstable ones

Asked "compare the logs of the two v10 runs and find what went wrong". Two limits first,
because they bound the answer:

- **The two HIDDEN runs cannot be compared at all from our side.** Submission uses
  `-k sahasawatt/taaf-duck-v10`, so Kaggle re-runs the kernel against the hidden set;
  both submissions uploaded the *same* `submission.parquet` (md5 `f1f99148da4a`, 2648 B).
  The 1.70 and the 1.32 runs happened on Kaggle, privately.
- **`kernels output <kernel>/<version>` silently ignores the version.** Versions 1, 2 and
  4 (4 may not even exist) all returned a byte-identical `benchmark.json`, md5
  `27b8e13acaa3`. So the 4.55 run's log is not retrievable either.

What IS on disk: v10cal (4.71) and v18 (3.60). Per game:

| game | v10cal | v18 | delta | levels |
|---|---|---|---|---|
| re86 | 0.124 | **27.143** | **+27.0** | 1 → 4 |
| ft09 | 22.966 | 4.762 | −18.2 | 3 → 1 |
| dc22 | 14.286 | **0** | −14.3 | 2 → 0 |
| lp85 | 16.667 | 8.333 | −8.3 | 3 → 2 |
| cd82 | 6.534 | **0** | −6.5 | 2 → 0 |
| ar25 | 8.333 | 2.778 | −5.6 | 2 → 1 |

**7 of 25 games (28%) flip between scoring and zero**, and the run mean moves only
4.71 → 3.60 because swings of ±27 on single games cancel each other out.

That pair is not a clean A/A (v18 also changed the upscale), but a ±27 swing on one game
is far larger than one knob explains — and the ledger already holds a true A/A: **v10out
vs v10cal, identical build, 22 vs 28 levels and 1285 vs 1597 actions.**

**The mechanism is structural, not a bug.** `score = (base/actions)^2 × level weight`, so a
deep level pays enormously (ft09 at level 3 = 22.97) and clearing a deep level is the part
that is a coin flip. **The games that earn the most are the least stable ones**, which is
why a 110-run hidden mean moves 25% between draws of one build.

Consequence for what to build: a lever that raises the *mean* while leaving this coin flip
intact inherits the same spread. `banking` (v19) replays an already-won trace
deterministically, so it should raise the floor on levels already cleared rather than buy
another coin flip — UNVERIFIED until v19 lands, but it is the reason it outranks the rest.

### CORRECTION (same day) — act/lvl is a symptom, and the axis has a hard ceiling

The table above is real but it is not the mechanism, and reading it as one points at the wrong
work. The scorer has **two** caps, and the second was missing from my recall until it was
recovered from `R4-ev.md:19-20` and verified against `benchmark.json`:

```
level_score(i)  = min((base_i / actions_i)^2 * 100, 115)     0 if the level was never completed
raw             = sum(level_score(i) * i) / W                W = 1+2+...+N
completion_cap  = 100 * sum(i for i in DONE levels) / W
game_score      = min(raw, completion_cap)
```

Verified exactly on five games of v10cal (`dc22` 14.286, `ar25` 8.333, `ft09` 22.966, `sc25`
11.759, `vc33` 8.699). The `completion_cap` term is why a formula without it overshot two of
four games by precisely 100/115.

What that changes, measured on v10cal:

| | |
|---|---|
| games already AT the completion cap | **7 of 25** — speed buys them exactly zero |
| share of total score locked at that cap | **41%** (48.3 of 117.8) |
| gain if every remaining game reached its cap | **+1.09 mean → 5.80 public** |

**So the entire efficiency axis has a hard ceiling of 5.80 public (~2.1 hidden).** It cannot reach
the 6.9-7.1 needed for top-5, let alone the ~8.0 that hidden 3.0 implies. Every efficiency win
listed in the table above was real, and the axis is now nearly spent.

Depth, by contrast, is not close to spent — recomputed through the true formula, assuming any
newly cleared level is taken at pace:

| every game clears | public | hidden @2.72x |
|---|---|---|
| +0 (today) | 4.71 | **1.73** (actual draw: **1.70**) |
| **+1 level** | **12.07** | **4.44** |
| +2 levels | 23.10 | 8.49 |
| all levels | 100.0 | — |

One extra level per game multiplies the score by **2.56x**. Hidden 3.0 needs public ~8.0, which
sits between +0 and +1 — about **0.6 extra levels per game**, i.e. one more level in roughly 15 of
the 25 games. That the +0 row predicts 1.73 against an actual 1.70 is the closest thing to
validation the shrink model has.

**Consequence for what to build next: nothing on the efficiency axis can reach the target, and
depth overshoots it. All remaining effort belongs to clearing levels we currently cannot.**

A corollary that killed a lever the same hour: actions burned on a level that is never cleared do
not enter any denominator, so a plateaued game that keeps acting costs **nothing** in score. The
"detect the plateau and stop playing" idea is worthless — it was proposed, measured and dropped
within one exchange.

The two exceptions prove the shape rather than breaking it:

- **v16** got act/lvl to **50.8**, the best ever, and scored 3.51. It spread its efficiency across
  *more games at shallow depth*, and the level-number weighting does not pay for shallow.
- **v14** raised throughput 26% and act/lvl went the wrong way (57.0 → 85.9). Capacity was spent on
  attempts.

### The axis, now measured in both directions (2026-08-23)

Three runs cut *reasoning per decision* three different ways, and depth fell every time:

| run | how thinking was cut | actions | levels | public |
|---|---|---|---|---|
| v14 | not cut — throughput raised 26% | more | 19 | 2.87 |
| **v21** | effort xhigh→medium (−39% tok/action) | ×1.8 | **12** | 1.25 (p=0.0052) |
| **v20** | capability 27B dense → ~3B active | ×4.7 | **3** | 0.18 (p=0.0001) |

**Deliberation per decision is monotonically load-bearing on this task**, and xhigh — the
maximum — is what v10 already runs. The rank-21 team ships `medium` inside a 6-file change
(trimmed prompt + a tried-this checklist); the flag alone, on our stack, is decisively
negative. There is no thinking-dial headroom left upward, no larger dense model on either
Kaggle registry, and the harness axes are closed. That is the evidence-backed shape of why
hidden 3.0 is out of reach with the models this competition makes available.

## What is closed, with the number that closed it

| direction | verdict | evidence |
|---|---|---|
| cap the model's output | dead | v9 = 0.22; 704 `length` finishes vs 68 tool calls |
| ask for brevity in the prompt | dead | v12 = 3.72, below v10's band |
| raise inference throughput | dead | v14 = 2.87 with the mechanism confirmed working |
| push more state into the turn | dead | v16 = 3.51 with delivery doubled |
| fix the "retry spiral" | ~+0.1 | only `lf52`/`tr87` exceed the streak threshold, and scoring games reach 25 |
| a better dense model | exhausted | Qwen3.8-27B-FP8 is the newest on Kaggle |
| a luckier draw | capped | best-of-each-game oracle on v10 = 6.73 public ≈ 2.4-2.5 hidden — under the top-5 bar |

## Where the points actually are (v10cal, the best run)

Top 8 games = **80%** of all points, and every one of them cleared **2-3 levels out of 6-9**.
31 of 51 cleared levels are already at the 115 cap, so efficiency on what we clear is nearly spent.

Six of those eight **plateaued and kept playing**: last level-up at 27-59% of their clock, actions
continuing to 75-95%. `ar25` cleared its last level at **27%** and spent the remaining 51% of the
clock acting without progress.

That is the one harness decision nobody has built: **it cannot tell that a game has stopped making
progress, and it has no move to make when it has.** Every other decision the harness makes — time
per game, yield budget, no-op blocking, animation nudges — is either fixed or already measured.
