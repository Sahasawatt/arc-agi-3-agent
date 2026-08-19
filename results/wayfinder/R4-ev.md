# R4-EV — where the next 2 points come from (breadth vs depth vs efficiency)

Goal: 3.00 mean over 110 hidden games. Current: hidden 1.00 (duck-mod, submission
55613165), public 2.41 (same artifact, 25 public games), duck baseline public 1.25.
#1 = 3.57.

All numbers below are computed by importing `scoring.py` directly
(`environment_score`, `level_score`) — nothing here is hand-derived arithmetic that
could drift from the offline implementation. Script: scratch dir `sens.py` (not in
repo, per constraints), rerunnable, output pasted inline below each table.

## 0. Formula, verified against the rules doc's own worked examples

`scoring.py` implements:
```
level_score(i)   = min((baseline_actions_i / actions_taken_i)^2 * 100, 115)   [0 if never completed]
weights          = 1+2+...+N   (N = levels in that game)
raw              = sum(level_score(i) * i for i in 1..N) / weights
completion_cap   = 100 * sum(i for i in DONE levels) / weights
game_score       = min(raw, completion_cap)
```
Two cross-checks against `docs/competition-rules.md`'s own worked examples, run
through `scoring.py` directly:

| Worked example (from the doc) | doc's stated value | `scoring.py` output |
|---|---:|---:|
| 4 of 5 levels done at pace, N=5 → completion cap | (1+2+3+4)/(1+2+3+4+5) = 66.7% | **66.667%** |
| Level 1 only, at the 1.15x cap, N=7 → real ceiling (not the naive 4.107%) | 1/28 = 3.571% | **3.571%** (naive uncapped value: 4.107%, confirmed as the wrong number) |

Both match exactly. The offline implementation is trustworthy for everything below.

**One mechanic that isn't stated explicitly anywhere and is load-bearing for §3:**
the completion cap depends only on *which* levels are done, never on their speed.
Verified directly:
```
levels 1-5 of a 7-level game, ALL at exactly pace (score=100 each):        53.571
same, but level 3 pushed to the 115 speed-cap:                            53.571  (unchanged)
same, but ALL five pushed to 115:                                          53.571  (unchanged)
```
So the 1.15x speed bonus can never lift a game's score above what its *completed
levels* already cap it at — it can only compensate for OTHER completed levels that
scored under 100 (i.e. slower than human baseline). Once every completed level is at
or above pace, going faster is pure waste. Corollary, also verified: a game where
**every** level is completed has completion_cap = 100 always (sum(done) = full
weight), so such a game's score is never capped — it just equals the plain weighted
average of its level scores. `ls20` 7/7 measured 43.629% in this campaign's own
local play; `environment_score({i:43.629 for i in 1..7}, 7) = 43.629` exactly,
confirming full-completion games report their raw weighted-average pace directly.

## 1. Sensitivity Table A — breadth: one game, 0 → level 1 cleared only

Δ to that one game's score, and Δ to the 110-game mean (÷110), for a game with N
total levels (N unknown for hidden games; 6/7/8/9 bracket what's actually been
measured across this campaign's public-game roster — ft09=6, ls20/g50t=7,
ar25/re86=8, tu93/bp35=9):

| N | weight W=N(N+1)/2 | score(L1 @ pace) | score(L1 @ 115-cap pace) | score(L1 @ half-pace, 2x actions) | Δ to 110-mean (@pace) |
|---:|---:|---:|---:|---:|---:|
| 6 | 21 | 4.762 | 4.762 | 1.190 | 0.0433 |
| 7 | 28 | 3.571 | 3.571 | 0.893 | 0.0325 |
| 8 | 36 | 2.778 | 2.778 | 0.694 | 0.0253 |
| 9 | 45 | 2.222 | 2.222 | 0.556 | 0.0202 |

Note the L1-@-pace and L1-@-115-cap columns are identical — §0's mechanic already
explains why: with only level 1 done, completion_cap = 100/W, and pace alone (score
100) already hits raw = 100/W = the cap. Going faster than pace on level 1 buys
literally nothing when it's the only level cleared.

## 2. Sensitivity Table B — depth: marginal value of clearing one more level

Levels 1..d-1 already done at pace (100 each), level d newly completed at pace.
Formula, verified against `scoring.py` for every d: **Δ = 100·d / W**.

| N=6 (W=21) | N=7 (W=28) | N=9 (W=45) |
|---|---|---|
| L1: +4.762 | L1: +3.571 | L1: +2.222 |
| L2: +9.524 | L2: +7.143 | L2: +4.444 |
| L3: +14.286 | L3: +10.714 | L3: +6.667 |
| L4: +19.048 | L4: +14.286 | L4: +8.889 |
| L5: +23.810 | L5: +17.857 | L5: +11.111 |
| L6: +28.571 (final) | L6: +21.429 | L6: +13.333 |
| — | L7: +25.000 (final) | L7: +15.556 |
| — | — | L8: +17.778 |
| — | — | L9: +20.000 (final) |

Reading a 7-level game: clearing the **final** level (7th) — having already cleared
the other six — is worth **+25.0 points to that game's score**, vs **+3.571** for
clearing level 1 of a game that has nothing else done. **The last level of a 7-level
game is worth ~7x a first level of a fresh game**, and this is exactly the game's own
docstring statement "weighted by 1-indexed level number" made concrete: the level-d
increment carries weight `d`, so depth compounds — each level is worth more than the
last, purely from where it sits in the sequence, before any efficiency is even
considered. This is also why the ft09/ar25 public deltas (§3) look disproportionate
for "2 games out of 25" — going from 2/6 to 3/6 levels on ft09 (a level-3 clear, weight
3/21) plus finishing faster, and unlocking a level-2 attempt on ar25 (weight 2/36),
are structurally the highest-leverage moves the scoring function offers, not an
accident of variance alone (though §3 shows variance is also plausible).

## 3. Sensitivity Table C — efficiency: does speed matter below the cap?

Single already-*completed* level, score vs pace ratio r = baseline_actions/actions_taken:

| r | actions (x baseline) | level_score |
|---:|---:|---:|
| 0.25 | 4.00x | 6.25 |
| 0.50 | 2.00x | 25.00 |
| 0.60 | 1.67x | 36.00 |
| 0.70 | 1.43x | 49.00 |
| 0.80 | 1.25x | 64.00 |
| 0.90 | 1.11x | 81.00 |
| 0.9324 | 1.073x | 86.94 |
| **1.00** | **1.00x (pace)** | **100.00** |
| 1.0724 | 0.932x | **115.00 (cap reached)** |
| 1.20 – 2.00 | 0.83x – 0.50x | 115.00 (flat, wasted) |

**Yes, efficiency matters, and it matters a lot below pace** — the relationship is
quadratic, so halving actions from 2x-baseline to 1x-baseline (r: 0.5→1.0) is +75
points, not +50. But the return is entirely gone past r≈1.07 (actions ≤ 93% of
baseline): every action shaved beyond that is worth exactly 0, both to that level
(115-cap) and — per §0 — to the *game*, unless some other completed level in the same
game is under pace and the completion_cap has room to absorb the surplus. Efficiency
also **only applies where a level is already being completed at all** — `level_score`
is a hard 0 for `actions_taken=0`, so no amount of efficiency creates score on a level
never reached.

## 4. Reconciliation: 2.41/25 (public) vs 1.00/110 (hidden)

Public per-game duckmod scores, from `results/duckmod-transcripts-20260819.md` §1
(mod column) plus the "≈0 both runs" games:

```
known 9 games sum        = 45.55   (ft09 28.57, ar25 7.73, sp80 4.76, ls20 2.06,
                                     tu93 1.46, s5i5 0.08, cd82 0.00, vc33 0.00, re86 0.89)
public sum (2.41 x 25)   = 60.25
remaining 16 games sum   = 14.70   (avg 0.919 each — small nonzero credit, consistent
                                     with "mostly 0.00 or identical" wording)
top 2 games (ft09+ar25)  = 36.30   =  60.2% of the public sum, from 2/25 = 8% of games
```

The public 2.41 mean is **not a broad lift** — it is dominated by exactly the depth
mechanic in §2: ft09 went 2/6→3/6 levels in *half* the actions (92→44), and ar25 went
from never leaving level 1 to clearing it and reaching level 2. `results/duckmod-
transcripts-20260819.md` independently shows **neither of those two winning games ever
called the new tools** (0 `TransitionGraph()` constructions, 2 inconclusive `hud_mask`
calls total, across 2,001 tool-call turns) — so the public 2.41 reflects two games'
worth of depth-shaped variance, not a general capability gain. That is the direct
explanation for why hidden (110 games, no cherry-picking possible) came back at 1.00,
not ~2.4: the hidden set doesn't happen to contain two games this specific agent gets
2-3 levels deep into.

```
hidden sum (1.00 x 110)  = 110.00
if ALL 110 hidden games cleared L1-at-pace only (N=7 assumption): mean = 3.571
  -> that alone would already clear the 3.00 goal, IF it were universal
  -> the fraction of "L1-at-pace-equivalent" games needed to produce the OBSERVED
     110.00 sum by breadth alone = 110.00 / 3.571 = 30.8 games = 28% of the 110
```
28% of hidden games behaving like a clean, on-pace level-1 clear (and nothing else,
anywhere) is one internally-consistent story for the observed 1.00 — but §5.2 below
shows it's a strictly worse bet than the depth-shaped story the public run already
demonstrated once (a couple of games going 2-3 levels deep on an otherwise near-zero
board), because per-game leverage for depth is ~7x higher than for breadth (§1 vs §2).

## 5. Which axis buys the most — direct comparison

Target: mean 1.00 → 3.00 over 110 games needs **Δ(sum of all 110 game-scores) = 220.0
points** (2.00 x 110).

| Strategy | Unit of work | Value per unit | Units needed for 220 pts | % of the 110-game set |
|---|---|---:|---:|---:|
| **Breadth**: 0 → L1 cleared @ pace (N=7) | 1 game | 3.571 | **61.6 games** | **56%** |
| **Depth**: clear the final (7th) level of an already-6/7 game @ pace | 1 game (already 6 levels in) | 25.000 | **8.8 games** | **8%** |
| **Efficiency**: push an already-completing level from 0.6x-pace to the 1.07x cap | 1 level | 50.94 | 4.3 *levels* (not games) — and only levels that are already scoring | n/a (bounded above by how many levels are already being cleared at all) |

**Depth is ~7x cheaper per unit than breadth** (25.0 vs 3.571 per "unit"), and this
is not a coincidence — it is exactly §2's `Δ=100d/W` formula evaluated at the largest
d available. Breadth requires *content coverage*: getting more than half the entire
110-game set to reliably clear at least one level, on games the agent has never seen,
each potentially needing its own board-reading/driver logic (see CLAUDE.md's own
17-game roster — even *with* 14 hand-built drivers, several public games are still
0-scoring walls). Depth requires the opposite: the agent already has to be inside a
game doing something right, and needs 8-9 more games (not 60+) pushed one level
further. Efficiency is real but bounded: it cannot create score on a 0-scoring game,
and it saturates hard past r≈1.07 per level, so its total addressable ceiling is
capped by how many levels are *already* being completed somewhere below pace — a much
smaller number than 220 points can plausibly come from alone (each level tops out at
+50.9 points to that one game's raw component, and only for levels that already score
something).

## 6. Allocation policy for a fixed effort budget

Not a harness redesign — a statement of where marginal engineering/tuning effort is
worth the most, given the shape of the scoring function measured above:

1. **Depth-first on games the agent already touches, not breadth-first tooling
   across the untouched 90%.** §5's 7x leverage gap means one game pushed from 6/7 to
   7/7 is worth as much as ~7 fresh games each barely clearing level 1. Any signal
   that a game is "in progress" (partial level clear, or — per §4 — a run that looks
   like ft09/ar25's shape) is worth following deeper before spending effort on the
   games currently at a hard 0.
2. **Efficiency tuning is a second-order lever, gated on depth already existing.**
   §3 shows it cannot manufacture score from nothing (0 actions = 0 score, always),
   and its return is quadratic-then-zero, so it only pays off on levels the agent
   is *already* clearing slower than baseline pace (r<1) — tighten those first, but
   don't expect it to move the mean on its own the way completing one more level does.
3. **Breadth still matters as a floor, not a lever.** §4's arithmetic shows even
   "every game clears level 1 at pace" (an unrealistic universal floor) would already
   hit 3.571 — above goal — which is a useful sanity check that the *goal itself* is
   reachable through the scoring function's own arithmetic, not evidence that broad,
   shallow coverage is the efficient way to get there. The 28% breadth-only story in
   §4 needed to explain the *current* 1.00 is itself already a large ask (30+ new
   games clearing something), and buying the *next* 2.00 the same way needs 61.6 more
   — a strictly worse trade than depth's 8.8.
4. **Don't over-read a re-roll.** `results/breadth-recon.md`'s own "Strategic read"
   after the hidden score landed: *"re-rolls of a ~1.0-mean design cannot reach
   2.57 [top-5]... requires a design improvement... not another sample."* This
   sensitivity model agrees for the same structural reason — resubmitting the
   identical duck-mod artifact resamples which games happen to go 2-3 levels deep,
   it doesn't change the per-game depth-vs-breadth economics computed above.

## Verdict

**The next point comes from depth, not breadth or efficiency.** The scoring
function weights level *d* by *d* itself, so completing one more level on a game the
agent already has traction in is worth roughly 7x what getting one new game to a bare
level-1 clear is worth (§1 vs §2, verified via `scoring.py` not estimated), and the
one real public data point available — duckmod's 2.41 public mean — is itself a
depth-shaped effect (two games going 2-3 levels deep, contributing 60% of the public
sum from 8% of the games) that happened to not use either of the injected tools
(`results/duckmod-transcripts-20260819.md`), while the hidden 1.00 confirms that
effect doesn't transfer as a general capability. Efficiency tuning is real but
strictly bounded — it cannot create score where none exists and saturates by
r≈1.07x baseline — so it should follow depth gains, not lead them. Breadth-widening
(getting more of the 110 games to score *anything*) is the most expensive axis per
unit of mean-score (56% of the game set needed for the full 2.00-point gap, vs 8%
for depth), and should be pursued only as a byproduct of making the agent generically
better at reading unfamiliar boards — never as a standalone target.
