# R29 — B27 answered: the goal is right, the transition model is not

2026-08-24. B26 framed the bottleneck as *"ปัญหาคือการเลือก action"* and split it into two free
measurements — B27 (is the stated goal correct when a game is stuck?) and B28 (does prompt
pressure move search usage?). This closes B27, from artifacts already on disk. No GPU, no
quota, no new run, and `environment_files/` untouched.

## The instrument, and why it is better than the one B27 planned

B27's method was to pair a stuck run from v18/v19/v21 against a clearing run from v10cal. Every
one of those pairs carries a knob change, so a difference is confounded.

Two runs on disk are a **cleaner pair**: `v10cal` (4.71) and `thui-v1` (3.20). thui-v1 is v10
plus the cell-12 usage probe, which R28 established is inert, and `eval/rank_runs.py` reads the
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
  timeout=398.2)`. The turn produces no model output at all. R28 measured 2.5% from the usage
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
