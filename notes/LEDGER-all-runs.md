# Every run this campaign produced — what it scored and why

Assembled 2026-08-22 from the `summary.txt` and `benchmark.json` of every downloaded run.
Public = the 25-game commit-run mean. Hidden = the 110-game leaderboard draw, only for the
four builds ever submitted.

## The table

| run | public | hidden | scoring | levels | actions | act/lvl | Mtok | bundle | what changed, and why it landed there |
|---|---|---|---|---|---|---|---|---|---|
| **v10cal** | **4.71** | — | 18 | 28 | 1597 | 57.0 | 2.03 | anim | rerun of v10; the campaign's best number |
| **v10out** | **4.55** | **1.70** | 14 | 22 | 1285 | 58.4 | 1.87 | anim | anim bundle + Qwen3.8, output uncapped. The rebase onto Tufa's animation-awareness branch is the single largest jump in the campaign |
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
- **The shrink is worse than recorded**: public [4.55, 4.71] against a hidden mean of
  ~1.51 is **~3.05x**, not the 2.72x the depth table used. The +0 row of that table
  predicted 1.73 and was scored against 1.70; against the mean it over-predicts.
- **Top-5 needs 2.57 hidden**, so the gap from a mean of 1.51 is **+1.06**, not +0.87.

Two draws is n=2: 0.38 is a range, not a standard deviation, and the true spread could
be wider. What it already rules out is reading any single hidden number as a build's
value.

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
