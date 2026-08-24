# R29 — B27 answered: the goal is right, the transition model is not

2026-08-24. B26 framed the bottleneck as *"ปัญหาคือการเลือก action"* and split it into two free
measurements — B27 (is the stated goal correct when a game is stuck?) and B28 (does prompt
pressure move search usage?). This closes B27, from artifacts already on disk. No GPU, no
quota, no new run, and `environment_files/` untouched.

## The instrument, and why it is better than the one B27 planned

B27's method was to pair a stuck run from v18/v19/v21 against a clearing run from v10cal. Every
one of those pairs carries a knob change, so a difference is confounded.

Two runs on disk are a **cleaner pair**: `v10cal` (4.71) and `thui-v1` (3.20). thui-v1 is v10
plus the cell-12 usage probe, which R35 established is inert, and `eval/rank_runs.py` reads the
two as **NOT-DISTINGUISHABLE, p=0.3027**. So per-game differences between them are rollout
variance on one build, not a lever.

They disagree on **11 of 25 games** — a superset of the five B27 enumerated:

| game | stuck | at level | cleared by | of |
|---|---|---|---|---|
| ar25 | v10cal | L3 | thui-v1 (reached L5) | 8 |
| cd82 | thui-v1 | L1 | v10cal (L3) | 6 |
| cn04 | v10cal | L1 | thui-v1 (L2) | 6 |
| dc22 | thui-v1 | L1 | v10cal (L3) | 6 |
| ft09 | thui-v1 | L3 | v10cal (L4) | 6 |
| ka59 | thui-v1 | L1 | v10cal (L2) | 7 |
| lp85 | thui-v1 | L2 | v10cal (L4) | 8 |
| r11l | v10cal | L1 | thui-v1 (L2) | 6 |
| re86 | v10cal | L2 | thui-v1 (L3) | 8 |
| sc25 | thui-v1 | L1 | v10cal (L3) | 6 |
| tu93 | thui-v1 | L2 | v10cal (L3) | 9 |

⚠️ `level` on an action event is 1-indexed and **post-increment**: clearing level *j* is logged
with `level = j+1`. A run with `levels_completed = k` is stuck ON level `k+1`. Verified on
re86 / ft09 / cd82 against `benchmark.json` before any of the above was computed.

## 1. The stuck level is not a time problem

| game | stuck: turns / actions on that level | clearing run: turns / actions |
|---|---|---|
| ar25 | **29 / 45** | 4 / 41 |
| cd82 | **40 / 18** | 30 / 39 |
| cn04 | **29 / 41** | 11 / 23 |
| dc22 | **31 / 51** | 15 / 32 |
| ft09 | 19 / 30 | 19 / 34 |
| ka59 | 24 / 24 | 22 / 35 |
| lp85 | **27 / 14** | 8 / 12 |
| r11l | **19 / 4** | 9 / 3 |
| re86 | 4 / 1 | 23 / 63 |
| sc25 | **33 / 23** | 27 / 35 |
| tu93 | 8 / 16 | 14 / 17 |

**In 9 of 11 pairs the stuck run got at least as many turns on the level as the run that
cleared it**, and in four of them roughly three times as many. The same build solves ar25 L3 in
**4** turns and fails it in **29**; lp85 L2 in **8** and fails it in **27**.

**re86 is the single clock-starved case** and it is the one B27 called sharpest: v10cal arrived
on L2 at action 123 out of the 123 it ever fired, spent 4 turns, and its last words are
*"currently analyzing the new layout in detail"*. That is R1's wall clock, not a wrong goal —
so the sharpest planned pair turns out to measure something else entirely.

## 2. What the stuck run actually believed

Read from the carried world model (the block the user prompt re-injects each turn) and the
agent's own prose. Three cases, quoted:

**lp85 — goal right, decomposition wrong, no search.**
Stuck (thui-v1): *"the board is one big loop … The win is almost certainly 'the floating yellow
block(s) reach the circle(s)'."* The **win condition is correct**. The mechanics are not.
Clearing (v10cal): *"3 overlapping rings, 6 arrow actions … Running BFS on the two yellow cells
(42-cell state space) to the goal {yellow at (26,35) and (35,35)}"* → cleared at action 18.

**cd82 — goal roughly right, action model never formed.**
Stuck (thui-v1), carried unchanged through its last turns: *"purple rectangle is a movable
brush/piece; goal is to paint/cover the white square purple. - Open: do arrows move the purple
piece? … - Plan: probe RIGHT to see if brush+slot move."* Forty turns in, it is still asking
whether the arrows move the piece — and it has spent those 40 turns firing **18** actions.
Clearing (v10cal): *"Full orbit confirmed … stamp top half white, orbit counter-clockwise to
bottom, switch to purple, stamp bottom half."*

**ar25 — a confident, concrete, wrong plan.**
Stuck (v10cal) re-carried the same plan for its last three turns: *"G first: DOWN×5 then LEFT×14
at rows 42-47 → lands exactly on C…"*. Clearing (thui-v1) found what that plan omits — a
reflection axis and a 3-cell step quantum: *"with bar axis at row 28, sprite 1 … covers target 4
and its mirror covers target 1 … Moves needed (all multiples of 3)"*.

**The pattern: the goal is usually right. What is wrong is the transition model — what an action
does to the board.** B27 asked whether the goal is wrong; measured, it mostly is not.

## 3. Search separates clearing turns from stuck turns

Re-running v17's search-construct probe (`bfs|dfs|deque|heapq|itertools.product|def solve|def
search|def plan|visited=|frontier|permutations|product(`) over the paired levels only:

| | turns | with a search construct |
|---|---|---|
| stuck levels | 263 | **0** (0.0%) |
| clearing levels | 182 | **5** (2.7%) |

**Fisher exact, two-sided: p = 0.0111.** The five hits come from three games (lp85 25%, tu93
14.3%, ft09 5.3%).

⚠️ This is an association, not a direction. A run that already understands a level can afford
to search, so search may be a symptom of understanding rather than its cause. Five hits over
three games is a thin sample. What it does establish is that the two populations differ, which
is the premise B28 and B29 both rest on and which nothing had tested.

## 4. Correction: "goal stated 93%" does not reproduce

MAP's B26 line reads *"(no-op 5%, no lock-in, goal stated 93%)"*. Measured over both runs, from
the carried world model:

| | v10cal (974 turns) | thui-v1 (999 turns) |
|---|---|---|
| carried world model **non-empty** | 521 (53.5%) | 447 (44.7%) |
| carries a `Plan:` line | 420 (43.1%) | 384 (38.4%) |
| carries a `World model:` line | 320 (32.9%) | 254 (25.4%) |
| carries an **explicit `Goal model:` line** | **29 (3.0%)** | **0 (0.0%)** |
| carries any goal wording (`goal\|objective\|win condition\|target`) | 193 (19.8%) | 205 (20.5%) |

R24's own figure was *"7 of 104 rendered turns"* read Unknown/empty — i.e. 93% **of the 104
turns that carried the line**, which is ~9% of its 1,062 turns. The denominator was dropped on
the way into MAP, and 9% became 93%. The agent states a goal on roughly **one turn in five**,
and names it `Goal model:` on **three in a hundred or fewer**.

**The carried world model is empty on 46.5% / 55.3% of turns** — R6's Mode 1 state amnesia,
still live two months later, on the best build.

## 5. Two instrument facts found on the way

- **`request_error` on 4.0% (v10cal) / 3.2% (thui-v1) of analysis turns** — `[ANALYZER STATUS]`
  carries `HTTPConnectionPool(host='127.0.0.1', port=1234): Read timed out. (read
  timeout=398.2)`. The turn produces no model output at all. R35 measured 2.5% from the usage
  probe, which by construction only sees requests that returned; this is the same phenomenon
  counted at the turn.
- **The model responds with no assistant prose on ~29-33% of turns** (`MODEL RESPONSE META`
  present, `ASSISTANT` block absent), despite the user prompt's *"BEFORE EXECUTING NEW ACTIONS
  YOU MUST ALWAYS GIVE THE REVISED VERSION OF THE WORLD MODEL"*. Together with the empty carried
  block above, that is where the state goes.

## What this changes

- **B27: closed.** The goal is not usually the thing that is wrong, so B29 is **not**
  disqualified — which was the whole point of running B27 first.
- **B29 should verify the TRANSITION MODEL, not the goal.** *"Check each candidate plan against
  `history`'s recorded transitions"* is already the right verifier; what R29 adds is that the
  belief worth checking is *what an action does*, not *what winning looks like*. lp85 is the
  worked example: a correct win condition, a wrong ring decomposition, and `transitions` on disk
  contained the refutation the whole time.
- **B28's premise is supported but its direction is not.** Prompt pressure moving search usage
  is still worth measuring on v22; §3 says the two populations differ, not that search causes
  clearing.
- **Depth is still the axis (B20), and this is what depth costs.** The failure is not running
  out of clock on a level; it is spending 3× the turns on a level with an unfalsified wrong
  model of what the buttons do.

## Reproduce

Artifacts (events + `benchmark.json` for both runs, 124 MB) copied out of a session scratchpad
to `~/Claude/arc-artifacts/{v10cal,thuiv1}/`. Scripts in the workspace repo under
`scripts/b27/`: `pairs.py` (enumerate stuck/cleared pairs from `benchmark.json`), `dossier.py`
(dump carried model + prose + actions for one pair).

---

# §6 — extension, same day: §3 does not survive it

§3 above reported that search constructs appear on 0 of 263 stuck turns and 5 of 182 clearing
turns, Fisher exact p = 0.0111, and called it "the first test of the premise B28 and B29 rest
on". Widened from the 11 paired levels to all 1,973 turns of both runs, **that result does not
generalise, and the headline is withdrawn.**

## Base rate — the instrument agrees with v17

Search code (`bfs|deque|heapq|itertools.product|permutations|product(|def solve|def search|def
plan|visited=|frontier|queue=[`) inside the tool call's `<parameter=code>`:

**31 of 1,973 turns = 1.6%.** Counting prose mentions too gives **47/1,973 = 2.4%**, against
v17's **19/935 = 2.0%** over a smaller corpus. The probe reproduces; nothing is wrong with it.

## Four designs, three of them null

| # | design | stuck / not-searching | cleared / searching | Fisher p |
|---|---|---|---|---|
| §3 | matched on (game, level), 11 pairs | 0 / 263 | 5 / 182 = 2.7% | **0.0111** |
| (b) | corpus-wide, unstratified | 22 / 1308 = 1.7% | 25 / 665 = 3.8% | 0.0072 |
| (c) | stratified within (run, game) | 17 / 757 = 2.2% | 25 / 665 = 3.8% | **0.1158** |
| (e) | last 3 turns before a clear vs all others | 42 / 1824 = 2.3% | 5 / 149 = 3.4% | 0.397 |
| (f) | **the level as the unit** — searched anywhere on it, did it clear? | 43 cleared / 88 = 48.9% | 7 cleared / 12 = 58.3% | **0.760** |

(b) is confounded and is listed only to be dismissed: a game the run never got past contributes
stuck turns and nothing else, so the split partly measures which games are hard.

**(f) is the test that matters** — it asks the question anyone would act on. Searching somewhere
on a level goes with clearing it **58.3% vs 48.9%**, p=0.76. Nothing.

⚠️ **Power.** (f) has 100 level-attempts, 12 of them with search code. Only an effect of roughly
**27 percentage points or larger** is detectable there. "No effect" means "no large effect".

## The 0/263 is the anomaly, not the explanation

Splitting stuck levels by whether the *sibling run of the same build* cleared that exact level:

| stuck levels | turns with search |
|---|---|
| ones the sibling run provably cleared (§3's arm) | **0 / 263 = 0.0%** |
| every other stuck level | 22 / 1045 = 2.1% |

Fisher p = **0.0128**. So the levels where the failing run searched *least* are precisely the
levels we know are solvable — the opposite shape from "search is what clears levels". Under the
2.1% base rate, 263 turns should carry ~5.5 hits; zero is a 0.4% outcome. §3's significance came
from that hole in one arm, not from an excess in the other.

## What was checked and did not hold

`bfs` appears in prose on 35 turns and in code on 16, which invited the reading *"the agent talks
about search more than it runs it"*. Sampling the 15 prose-only turns refutes it: most are the
agent **reporting a BFS it ran on an adjacent turn** — *"BFS found a 9-move solution: LG, LG,
R35G…"*, *"BFS with 6-cell moves found no path (only 11 reachable states) — so my walkable-set or
move model is wrong"*. Intent-without-execution is not what the gap measures. Claim dropped.

## What still stands

§1 (the stuck level is not a clock problem — 9 of 11 pairs), §2 (the goal is usually right, the
transition model is not) and §4 (the `goal stated 93%` correction) are untouched by this. They
rest on turn counts and on quoted text, not on the search probe.

**§3 is withdrawn**: search usage does not predict clearing a level at any effect size this
corpus can resolve.

## Consequence

- **B28 is unaffected as a question but its prior should be lower.** If v22's addendum lifts
  search usage, that will still be worth knowing — but §6(f) says raising usage from ~2% is not
  on its own a route to more levels, so a usage-up/score-flat outcome should be read as the
  expected one rather than as a surprise.
- **B29's justification narrows to §2 alone**, which is the stronger half anyway: the belief
  worth verifying is what an action does, and `transitions` already holds the refutation. The
  "search separates the populations" argument is no longer available to it.
- The instrument, the four designs and the power note are in `scripts/b27/corpus_search.py`
  (workspace repo) so the next widening — more runs, once v18/v19 events are fetched — reuses
  the same predicate rather than a re-derived one.

---

# §7 — widened to five runs: §1 holds hard, §3 stays dead

2026-08-24, later. §1 and §3 were measured on **one** run pair (v10cal vs thui-v1, 11 games,
1,973 turns). `taaf-duck-v18`, `taaf-duck-v19` and `taaf-duck-v23` outputs were pulled from
Kaggle, giving **five** runs of the same family: v10 base, Qwen3.8-27B dense, anim bundle, each
with one inert-or-small knob (probe · vision upscale · banking graft · grid lines). **v20 is
excluded on purpose** — it is a different model (MoE), so a difference there is a lever, not
rollout variance.

Corpus: **5,052 analysis turns · 125 run-games · 237 level-attempts · 115 stuck/cleared pairs**
over the 10 run pairs.

## §1 widened — 11 pairs became 115, and the effect got stronger

| | 2 runs (§1) | 5 runs (§7) |
|---|---|---|
| stuck run had **more** turns on the level than the run that cleared it | 9 of 11 | **97 of 115 = 84.3%** |
| equal | — | 4 |
| **fewer** — the clock-starved shape | 1 (re86) | 14 = 12.2% |

Two-sided sign test on the 111 non-ties: **p = 1.9e-16**.

Magnitude: median **31** turns for the stuck run against **17** for the one that cleared the
same level, ratio median **1.59×**, p90 **4.0×**, max 25×. **44%** of pairs the stuck run spent
≥2× the turns; **21%** spent ≥3×.

⚠️ **Half of this is true by construction and the note says so**: a run that clears a level
stops spending turns on it, a run that fails keeps going until the game clock ends. The claim
this supports is the narrower one, which is also the one the campaign needs — **the failing run
reached the turn count that sufficed for another run of the same family to clear that exact
level**, so more time on the level is not the missing ingredient. The 12% with fewer turns are
the genuinely clock-starved cases.

Which run appears on which side is itself consistent: `v10cal` is the clearing run **33** times
and the stuck run **14**, the best split of the five; `v23` is the stuck run **30** times, the
worst.

## §3 stays withdrawn, and the point estimate has now flipped sign

| design | 2 runs | 5 runs |
|---|---|---|
| (c) stratified within (run, game) | 2.2% vs 3.8%, p=0.1158 | 2.5% vs 3.9%, **p=0.0176** |
| (e) last 3 turns before a clear | 3.4% vs 2.3%, p=0.397 | 5.4% vs 3.1%, **p=0.0358** |
| (d) provably-solvable stuck levels vs all other stuck levels | 0/263 vs 2.1%, p=0.0128 | 0/263 vs 3.2%, **p=0.00046** |
| **(f) the LEVEL as the unit** | 58.3% vs 48.9%, p=0.760 | **40.6% vs 48.3%, p=0.452** |

**The unit decides the answer, and the two disagree.** (c) and (e) are turn-weighted, so one
level carrying many search turns dominates; (f) gives each level one vote and is the unit a
decision is made in. At five runs the turn-weighted tests reach significance while the
level-weighted test not only stays null but **flips direction** — levels where the run wrote
search code cleared *less* often, 40.6% against 48.3%.

The detectable-effect floor is now computed rather than quoted: **2 s.e. = 19 percentage
points** at 237 level-attempts with 32 searching (it was ~27 at two runs). A real effect
smaller than 19 pp is still invisible here — but nothing in this corpus supports search as a
route to clearing levels, and the point estimate is on the wrong side.

(d) sharpens instead of resolving: the 263 turns of §3's stuck arm still carry **zero** search
against a 3.2% base rate that should have produced ~8.5. Whatever selects those levels is not
explained by this probe.

## §2 is unchanged and remains the load-bearing half

Nothing here touches the reading that the goal is usually right and the transition model is
not. That rests on quoted text, and B29's justification rests on it alone.

## Reproduce

`scripts/b27/widen.py <runs…>` for §1, `scripts/b27/corpus_search.py <runs…>` for §3; both take
run names and default to the original pair. Artifacts under `~/Claude/arc-artifacts/`, pulled
with `kaggle kernels output sahasawatt/taaf-duck-v<n>`.

---

# §8 — §2 widened, and it cannot be: the corpus has no structural trace of a wrong transition model

§6 and §7 widened §1 and §3. §2 was left standing on three hand-picked games (lp85, cd82,
ar25), and §7 closes by naming it *"the load-bearing half … B29's justification rests on it
alone."* §3 flipped sign under exactly this widening, so §2 is the one claim in R29 that has
never faced the corpus. This section faces it. **Result: four structural proxies for §2 are
null, and the corpus cannot resolve the effect they would need to show. §2 is neither
confirmed nor refuted — it remains a three-quote claim, and no instrument short of B29's own
verifier can widen it.**

## The instrument had to be rebuilt, because §Reproduce points at nothing

`scripts/b27/widen.py` and `scripts/b27/corpus_search.py` are **not in this repo** — `git
ls-files` returns zero for `b27` and zero for `widen`, against a control of one tracked file
under `scripts/`. They are not in the main checkout either. So §1's `97 of 115, p=1.9e-16`
and §7's whole table were, until now, unreproducible from master.

Rebuilt at `scripts/b27/{corpus,attempts,wm,widen2}.py` and validated against **six** numbers
this note already published, before it was used for anything new:

| check | R29 | rebuilt |
|---|---|---|
| analysis turns, v10cal+thuiv1 | 1,973 | 1,973 ✓ |
| analysis turns, five runs | 5,052 | 5,052 ✓ |
| run-games | 125 | 125 ✓ |
| level-attempts | 237 | 237 ✓ |
| stuck/cleared pairs | 115 | 115 ✓ |
| §4 carried model absent | 46.5% / 55.3% | 46.5% / 55.3% ✓ |
| §4 `Goal model:` stated | 3.0% / 0.0% | 3.0% / 0.0% ✓ |
| §1 named pairs lp85 / ar25 / cn04 / dc22 | 27v8 / 29v4 / 29v11 / 31v15 | all four ✓ |
| §1 medians | 31 vs 17 | 31 vs 17 ✓ |
| B26 row's no-op share | 5% | 5.0% (398 of 7,938) ✓ |

Two things surfaced while matching them, neither of which changes a conclusion:

- **`level_completed` rides the event for the level being ENTERED, not the one being played.**
  Read naively, level 1 is uncleared in every run and the final stuck level reads as cleared.
  The rule that reproduces every published pair is *an attempt at level L is cleared iff the
  run ever reached a level > L*.
- **§1's `97 of 115` is a strict `>`; the prose beside it says "at least as many", which is
  `>=` and gives `101 of 115` (87.8%).** There are exactly 4 ties. Same class as the
  `0.38 = 25%` slip in LEDGER:120 — the pair is right, the wording and the number disagree.
  Either way the effect is overwhelming.

## What was measured

Unit: the 115 stuck/cleared pairs on the same `(game, level)`, identical to §1. Test: paired
sign-flip permutation, two-sided, 100k draws, seed 20260824. The carried world model is the
block between `Working world model carried from earlier turns:` and the literal
`end of world model.` — **trimming at that second marker is load-bearing**, because the
boilerplate after it names every prefix (`World model:`, `Goal model:`, `Action model:`, …),
so an untrimmed read reports every field on 100% of turns and drives any similarity measure
to ~1.0.

| signal | stuck | cleared | stuck>cleared | p |
|---|---|---|---|---|
| **CONTROL+** turns/attempt (§1's own signal) | 30.97 | 17.45 | **97/115** | 1.0e-05 *(permutation floor)* |
| **CONTROL−** random per attempt | — | — | — | 0.43 |
| carries `Action model:` | 0.026 | 0.061 | 3/115 | 0.34 |
| `Open questions:` rate | 0.217 | 0.167 | 26/115 | 0.27 |
| carried model present at all | 0.542 | 0.593 | 58/115 | 0.27 |
| stasis — consecutive-block similarity | 0.901 | 0.878 | 26/51 | 0.39 |

The positive control reproduces §1 exactly (97/115, same direction), so the machinery works.
⚠️ The negative control was drawn twice on independently seeded noise and returned **p=0.43
and p=0.088** — a single draw of a random control is itself noise and proves little; the
positive control is what carries this table.

## Why the null is weak, and why that is the finding

**The agent almost never writes a transition model down.** `Action model:` — the field the
harness's own prompt offers for exactly this — appears on **1.6% of turns** across five runs
and **0 times in either v10cal or thuiv1**, the two runs §2's three quotes come from. Across
the 230 attempts in the 115 pairs it is non-zero on **10**.

So the floor was computed rather than assumed: plant a lift in the stuck arm and ask when this
test finds it (200 sims, confirmed at both 1.5k and 100k permutations).

| planted lift | detected |
|---|---|
| +5 pp | 0% |
| +10 pp | 18% |
| **+15 pp** | **74%** |
| +20 pp | 97% |

The observed difference is **−3.5 pp** — the wrong direction for §2, on 10 informative pairs.
This corpus resolves nothing below roughly **+15 pp**. That is not evidence against §2; it is
the measurement declining to speak.

## What this means for B29

§2 claims the *content* of a belief is wrong. Every proxy above measures whether a transition
model is **maintained, questioned or revised** — never whether it is **correct**. Nothing in a
transcript marks a belief as false, which is why the null arrives underpowered by
construction rather than by sample size. **The only instrument that can widen §2 is a verifier
that checks stated beliefs against recorded transitions — which is B29's own mechanism.** As
it stands, B29's justification and B29's test are the same object.

**That is fixable for zero slots, and it is the recommended next step.** The corpus already
holds every transition such a verifier needs: **7,938 action events across the five runs, with
`action_name`, `board_ascii` and `board_changed` populated on 100% of them.** Run B29's
verifier offline over that corpus before building anything:

- fires often on stuck attempts and rarely on cleared ones → §2 is confirmed at corpus scale
  and B29 is justified on more than three quotes;
- fires alike on both → §2 does not generalise, and B29 dies before it costs a GPU slot.

Either way it is read-only, costs no submission and no GPU quota, and is the only route that
does not spend a slot to learn what §2 already asserts.

## Reproduce

`python3 scripts/b27/attempts.py` prints the validation table; `python3 scripts/b27/widen2.py`
prints the signal table. Both read `~/Claude/arc-artifacts/{v10cal,thuiv1,v18,v19,v23}`,
pulled with `kaggle kernels output sahasawatt/taaf-duck-v<n>`.

---

# §9 — B29's verifier premise, tested offline: the recorded transition does not predict

🔴 **RETRACTED 2026-08-24 by R31 — this section's conclusion is its own instrument, and every
number below is measured on a key that discards the click.** The action was keyed on
`action_name`, so all 662 distinct click cells in the corpus are one symbol, `ACTION6`: a click
at `(58,35)` and one at `(29,22)` fired from the same board were recorded as the same
`(state, action)` and compared to each other. **135 of the 446 repeats below are clicks, and
122 of those were different actions.** Key the action as the agent itself issues and reads it
(`action_display` = `MOUSE(row=58, col=35)`) and the corpus reproduces the `board_changed` flag
**98.1%** corpus-wide and **311/311 = 100.0%** on keyboard actions, against a majority-class
null of 89.8%. The residual is **6 misses in one game** (`s5i5`).

The tell is in the per-game table below: every game it reports as failing has repeats that are
**100% clicks**, and both games it reports at 100% have **zero**. The swap is surgical, not a
shrink — `action_name` and `action_display` are in bijection for keyboard actions, so the 311
keyboard repeats are byte-identical under both keys and only the click population moves.

**So B29's premise holds and this section does not refute it.** What still bounds B29 is
coverage, which is B19's argument and is untouched: only **9.0%** of decisions are taken from a
board the run had seen before, and 91% of those know exactly one action. Full account, controls
and reproduce line: `notes/R31-transition-key.md`. Kept below unedited — the measurement was
sound and the reading of it was not, and the click column was in the data the whole time.

§8 closed by proposing B29's own verifier be run offline over the corpus before anything is
built, for zero slots. Done. **It does not get as far as grading beliefs, because the premise
underneath it fails first: a recorded transition does not predict the next one from the same
observed state.**

B29 is *"draft k candidate short plans in the sandbox, check each against `history`'s recorded
transitions, execute only the best-verified one, abort on first prediction miss."* Every clause
after "check" assumes that if the agent has seen `(state, action) → outcome` once, seeing the
same `(state, action)` again means the same outcome. That is checkable directly, with no model
in the loop: find every case where a run revisited an exact `(level, board, action)` it had
already fired, and ask whether the outcome reproduced.

**446 such repeats across the five runs.** They reproduce the exact board **58.7%** of the time
and the harness's own `board_changed` flag **77.8%** of the time.

## The aggregate is one game, and it inverts without it

| game | repeats | board reproduced | changed-flag reproduced |
|---|---|---|---|
| cn04 | 260 | 70.4% | **99.6%** |
| ls20 | 32 | **100.0%** | 100.0% |
| s5i5 | 28 | 10.7% | 17.9% |
| sb26 | 26 | 15.4% | 26.9% |
| ft09 | 18 | 50.0% | 50.0% |
| dc22 | 14 | **0.0%** | **0.0%** |
| lp85 | 12 | 25.0% | 33.3% |
| su15 | 12 | 16.7% | 25.0% |
| tu93 | 11 | **100.0%** | 100.0% |
| sc25 | 8 | 62.5% | 62.5% |
| vc33 | 7 | **0.0%** | **0.0%** |
| **ALL** | **446** | **58.7%** | **77.8%** |
| **excluding cn04** | **186** | **42.5%** | **47.3%** |

**cn04 holds 58% of every repeat in the corpus and is the best-behaved game in it** — 99.6% on
the flag. It was propping the aggregate up, not dragging it down, which is the opposite of what
its reputation here (the 454-action outlier) would suggest. Drop it and the corpus reproduces
its own recorded transitions **worse than a coin flip**.

**9 of the 11 games with ≥5 repeats fail to reproduce their own recorded transition more than
10% of the time.** Two — ls20 and tu93 — reproduce it perfectly, so this is a per-game property,
not a blanket statement that the environment is random.

## Three artifacts ruled out in the same run

- **Per-batch board attribution.** `batch_size` is **1 on all 7,938 action events**, so the
  recorded board belongs to one action. (Worth noting separately: the prompt urges batching and
  the event stream contains none.)
- **Mid-animation frames.** The `animation` field is present on 1,841 of 7,938 events. It
  explains the asymmetric cases sharply — when animation presence *flips* between the two
  occurrences, reproduction collapses to 6.2% / 8.3% — but those are 28 of 446. The 349 repeats
  with no animation on either side still reproduce only **58.5%**.
- **Cosmetic drift.** When it fails, the median difference is **1 cell** but the mean is 24.4 and
  the max is 320. ⚠️ No claim is made here about *where* those cells sit: a HUD region was
  guessed at and the guess did not survive its own examples, so it is not reported. The
  heuristic-free half is the `board_changed` column, which is the harness's own flag and
  disagrees with itself on 22.2% of repeats corpus-wide and 52.7% outside cn04.

## What this does and does not settle

**Settles:** a verifier keyed on the **observed board** — which is what `history` gives the agent
— cannot do what B29 asks of it. "Abort on first prediction miss" would fire on roughly half of
all correct repeats in nine of eleven games. Built as specified, the gate rejects good plans at a
rate that has nothing to do with the plans.

**Does not settle:** *why*. Either the environment is genuinely non-deterministic, or the visible
board is not the full state and a better key exists. The animation column is a hint toward the
second — repeats where both sides carry animation reproduce at **81.2%**, well above the 58.5%
where neither does. If the sandbox's `history` carries more than the rendered board (segmentation
objects, internal phase), a verifier keyed on *that* is untested and remains open. Nothing here
measures it, and nothing here should be quoted as if it did.

**For the frame (B26):** §8 found that §2 cannot be widened by any instrument short of B29's own
verifier. §9 finds that verifier's premise does not hold on the observed board. So the transition
model being "wrong" is now joined by a second possibility that the three quotes cannot
distinguish from it — that the transition model is being learned against a state signal which is
itself unreliable in most games. **B26 stays open, and this is the sharper form of its question:
not "is the agent's transition model wrong" but "is a transition model learnable from what the
agent is shown".**

Cost: zero GPU slots, zero submissions, no model calls.

## Reproduce

`python3 scripts/b27/b29_offline.py`.

---

# §10 — B28's designed test is confounded, and the fix is free

B28 asks whether v22's ported BFS instruction moves search usage off its ~2% base rate. As
written the test is one run against a baseline, pooled over turns, Fisher exact. That can
only rank something if runs which were **not** prompted differently agree with each other.
Nobody had measured whether they do. The corpus can answer it for zero slots.

Instrument: §6's exact pattern list, over the five-run corpus. Validated before use — it
reproduces §6's **31/1973 = 1.6%** on v10cal+thuiv1 exactly, and the Fisher implementation
reproduces both a published significant value (§3's `0/263 vs 5/182` → 0.0111) and a
published null (§6(f)'s `43/88 vs 7/12` → 0.760).

## The probe reads one section of the transcript, and the choice nearly doubles the answer

A transcript is `[SYSTEM PROMPT] [USER PROMPT] [THINKING]* [ASSISTANT] [ANALYZER STATUS]`,
and `<parameter=code>` appears in **both** `[THINKING]` and `[ASSISTANT]` — 1,009 blocks
against 1,432 over the pair. §6 says *"inside the tool call's `<parameter=code>`"*, and only
`[ASSISTANT]` is a tool call; `[THINKING]` is code the model drafted and did not run. Joining
both gives **72/1973 = 3.65%** where §6 published 31. That is not a detail:

| run | turns | ran | rate | + drafted | rate |
|---|---|---|---|---|---|
| v10cal | 974 | 19 | 1.95% | 21 | 2.16% |
| thuiv1 | 999 | **12** | **1.20%** | **51** | **5.11%** |
| v18 | 1062 | 30 | 2.82% | 36 | 3.39% |
| v19 | 969 | 19 | 1.96% | 28 | 2.89% |
| v23 | 1048 | 39 | 3.72% | 40 | 3.82% |

**thuiv1 drafts search 4.3× more often than it runs it**, while its same-build twin v10cal
drafts barely more than it runs (2.16% vs 1.95%). So the two channels are not two views of
one quantity — the drafted one carries most of the between-run variation. B28's prompt says
*use BFS*, which is likelier to move drafting than execution, and reading the drafted channel
**after** the executed one shows nothing is a forking path. **Declare the section before the
run.** Everything below is the executed channel.

## Unprompted runs separate 4 times in 10

| pair | rates | Fisher p |
|---|---|---|
| v10cal vs thuiv1 | 1.95% / 1.20% | 0.2070 |
| v10cal vs v18 | 1.95% / 2.82% | 0.2467 |
| v10cal vs v19 | 1.95% / 1.96% | 1.0000 |
| **v10cal vs v23** | 1.95% / 3.72% | **0.0226** |
| **thuiv1 vs v18** | 1.20% / 2.82% | **0.0117** |
| thuiv1 vs v19 | 1.20% / 1.96% | 0.2063 |
| **thuiv1 vs v23** | 1.20% / 3.72% | **0.0003** |
| v18 vs v19 | 2.82% / 1.96% | 0.2469 |
| v18 vs v23 | 2.82% / 3.72% | 0.2715 |
| **v19 vs v23** | 1.96% / 3.72% | **0.0227** |

None of these five runs was prompted to search. **Four of the ten pairs separate at p<0.05**,
the worst at p=0.0003. The whole-corpus spread is 1.20% → 3.72% = **2.52 pp**.

And the test is sensitive enough to be fooled: simulated, one v22-sized run (~1,010 turns)
against the 5,052-turn baseline of **119/5052 = 2.36%** detects a lift of **+2 pp** at 80%
power (measured 0.92). The detectable lift is *smaller than the unprompted spread*. Run B28
as designed and a significant result is not evidence about the prompt.

⚠️ The same-build pair is the reassuring one and it is the misleading one: v10cal vs thuiv1
is 0.75 pp apart, p=0.21. Reading only that pair — the obvious control — says the probe is
stable. It is stable **for that pair**, and the corpus contains three pairs it is not.

## Stratifying on the game removes all four, and the null has a floor

Paired sign-flip permutation on the per-game rate difference, 25 shared games, 100k perms —
the same unit and test family §1 used:

| pair | games | mean diff | p |
|---|---|---|---|
| v10cal vs thuiv1 | 25 | +1.11 pp | 0.2517 |
| v10cal vs v18 | 25 | −0.68 pp | 0.6078 |
| v10cal vs v19 | 25 | −0.09 pp | 0.9329 |
| v10cal vs v23 | 25 | −1.71 pp | 0.1865 |
| thuiv1 vs v18 | 25 | −1.79 pp | 0.1780 |
| thuiv1 vs v19 | 25 | −1.20 pp | 0.1373 |
| thuiv1 vs v23 | 25 | −2.81 pp | 0.1102 |
| v18 vs v19 | 25 | +0.59 pp | 0.6142 |
| v18 vs v23 | 25 | −1.02 pp | 0.6199 |
| v19 vs v23 | 25 | −1.61 pp | 0.4026 |

**0 of 10 stratified against 4 of 10 unstratified.** The confound is entirely the game mix —
the same thing §6 dismissed design (b) for, arriving here as a property of the runs rather
than of the arms.

Floor for the stratified test, by planting a lift into v10cal's per-game rates and measuring
detection: **+3 pp per game at 80% power** (measured 0.88). The largest unprompted stratified
difference is 2.81 pp, just inside it — so this null is narrow, not vacuous, and it is not a
comfortable margin.

## What B28 should do

1. **Stratify on the game.** Paired sign-flip over the 25 shared games, never a pooled Fisher.
   Free, and it is the difference between a test that separates unprompted runs 40% of the
   time and one that separates none of them.
2. **v22 must reach roughly 2.4% → 5.4% to be readable.** A "usage rose from 2% to 3.5%"
   outcome ranks nothing, and 3.5% is already inside the unprompted range.
3. **Fix the transcript section before the run** — `[ASSISTANT]` (executed) is what §6's base
   rate means, and the drafted channel is where the variation lives.

None of this changes B28's prior, which §6 already lowered: even a clean usage lift is not on
its own a route to more levels. It changes what the slot buys.

Cost: zero GPU slots, zero submissions, no model calls.

## Reproduce

`python3 scripts/b27/b28_baseline.py`.
