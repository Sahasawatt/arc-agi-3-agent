# arc-agi-3-agent

An agent for [ARC Prize 2026 — ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3).
Open source from the first commit (MIT-0), which the competition requires for prize
eligibility anyway.

## Where this is

Early, but the loop is closed. **The agent now clears a level with no human in it** — on
`ls20` it discovers how the piece moves, works out what ends the level by trying things, and
finishes level 1 in **13 actions against a human baseline of 22**, which is fewer than the 14
a human needed by hand. That is one game of nine; the mean across the nine is 0.456%.

**Measured so far, on public game `ls20`:**

| Approach | Result |
|---|---|
| random actions, 5 seeds × 200 actions | 0 levels, every seed |
| local LLM (`qwen2.5:7b`) on the raw 64×64 grid, 200 actions | 0 levels |
| local LLM on an object-level scene + movement feedback, 3 × 200 actions | 0 levels, but 25–34 blocked moves vs random's 39–75 (non-overlapping) |
| map read off one frame + BFS + budget-aware routing, driven by hand | level 1 in 14 actions; a level-2 route was recorded but **does not reproduce** — replaying `NOTES-ls20.md`'s sequence reaches the refill and ends 54 actions in with the level still uncleared |

Level 1 caps its per-level score. The level-2 line is why the recorded sequence is worth re-deriving rather than trusting: it was written down from a session, not replayed back.

## The rules, read late

Everything measured below was measured in a mode the competition does not offer, and
[`docs/competition-rules.md`](docs/competition-rules.md) records why with sources.

The load-bearing one: competition mode permits **one `make()` per environment** and turns a
game reset into a **level reset**. The search in `play.py` reaches a state by resetting and
replaying a prefix, thousands of times per level — after level 1 is cleared, that replays
level-1 actions against the level-2 board. It would not fail loudly; it would evaluate
nonsense. **Treat every number in this README as an upper bound from a permissive dev mode,
not as a competition score.**

A correction while we were at it: the "5x human median" action cap we briefly believed in is
from the technical report's own evaluation protocol, not from the competition rules, which
document no action cap at all — only 600 RPM.

## Playing by the rules turned out to be better, not worse

`compete.py` plays the way competition mode actually allows: one `make()`, no rewinding, the
only reset the one the engine forces when a run ends. It was built expecting to score worse
than the search — and it clears **four times as many levels**.

| | levels cleared | mean over 17 environments |
|---|---|---|
| `play.py` — search that resets and replays to evaluate | 1 game (`ls20`) | — |
| **`compete.py` — forward only, rules-legal** | **4 games** (`ar25`, `ls20`, `m0r0`, `cd82`) | **0.120%** |

| game | levels | actions | score |
|---|---|---|---|
| `ls20` | 1 of 7 | 39 (baseline 22) | 1.136% |
| `m0r0` | 1 of 6 | 74 | 0.783% |
| `ar25` | 1 of 8 | 173 | 0.095% |
| `cd82` | 1 of 6 | 812 | 0.022% |

**The rewind was not just illegal, it was harmful.** Evaluating a candidate meant resetting
and replaying a prefix, which threw away every state change the level had accumulated — the
pickups collected, the switches thrown. Games that need progress to accumulate cannot be
solved by a searcher that undoes it between every guess. Forward-only play keeps it, and
that alone is worth three extra games.

The mean is lower than the 0.456% reported elsewhere in this README for three separate
reasons, all of which make it more honest: the completion cap is now applied, the average is
over all 17 playable environments rather than 9, and legal play spends more actions (39
against 13 on `ls20`) because it cannot rehearse.

## Why an algorithmic agent rather than a model

The competition notebook has **no internet**, so a frontier model cannot be called — the
public ARC-AGI-3 leaderboard leader scores 30.2% online while the Kaggle leaderboard leader
scores **1.86%**. Meanwhile the ARC engine runs locally at ~2,000 FPS with no rate limit,
so search is nearly free and only *scored* actions are expensive. Scoring is
`min((baseline_actions / actions_taken)² × 100, cap)` weighted by level index, which rewards
minimal action sequences — what a planner produces and a language model does not.

## Layout

| File | What |
|---|---|
| `perception.py` | frame → connected-component objects, movement events between frames, HUD counters, scale-normalised glyph bitmaps |
| `identity.py` | cross-frame object tracking — the thing that makes any of the rest trustworthy |
| `discover.py` | works out a game's movement mechanics by acting — piece, footprint, step, direction per action, wall colours; `locate()` finds that piece on any later frame |
| `plan.py` | routing from a discovered model: candidate targets, containment-aware goals, BFS |
| `goal_llm.py` | asks a local model which object is the goal — it ranks, the planner routes, the engine judges |
| `signals.py` | finds the game's counters anywhere on the frame and tells a clock from a consequence |
| `trace.py` | frame-by-frame record of what each action did — what vanished, what the status bar did, when a level fell |
| `compete.py` | plays under the real competition rules — one make(), no rewinding, forward only |
| `play.py` | the autonomous loop — discover, search object sequences, tour a kind, sweep every reachable square, keep what clears a level |
| `solver.py` | walkable map from a single frame, BFS, multi-waypoint routing with an action budget |
| `agent.py` | play loop with a swappable policy (`random`, two LLM policies) |
| `scoring.py` | the competition's scoring formula, reimplemented for offline analysis |
| `probe_games.py` | measures, per game, whether the walkable-map assumptions hold at all |
| `walk.py` | replay a prefix then probe — per-step position, budget, glyph match |
| `probe.py` | repeat one action from a reset, to see what it does |
| `capture.py` | run an action list; dump PNGs and print what moved |
| `NOTES-ls20.md` | the reverse-engineered rules of `ls20`, the level-2 solution, and the probe traps that produced confident wrong answers |

## Running it

```bash
uv sync
uv run python solver.py ls20 <prefix-actions> cross,yellow1,goalbox0
uv run python walk.py ls20 <prefix-actions> -- <probe-actions>
```

An anonymous API key is fetched automatically; no account needed for development. The
engine can also run fully offline, which is how the competition notebook will use it.

## How far the approach generalises

`probe_games.py` measures, per game, whether the assumptions behind the solver hold: does
anything move under an action, by a constant step, over separable terrain, in several
directions. Full table in [`results/generalisation-probe.md`](results/generalisation-probe.md).

| verdict | games | |
|---|---|---|
| **MAZE_LIKE** — walkable-map + BFS applies | **9 / 25** | trustworthy; every one is `keyboard`-tagged and `ls20` reproduces its known behaviour |
| NEEDS_POINTER | 9 | 6 confirmed by their `click` tag; `ft09`, `cd82`, `sb26` are likely false negatives |
| NOT_GRID_STEPPED | 6 | suspect — the three worst have 183 / 64 / 56 segmented objects, so the object matcher is probably linking the wrong pair |
| PARTIAL | 1 | |

Every verdict is a **lower bound**: the probe presses each action twice from a single
reset, so a piece that starts against a wall reads as immovable. `ft09` is a proven false
negative — arXiv 2512.24156 Table 1 has a keyboard agent clearing three of its levels.

## Discovering the mechanics without a human

`solver.py` only works because a human read ls20's screen: the piece is colour 12, a move
is 5 cells, colour 4 is the wall. `discover.py` derives all three by acting, and nothing in
it is per-game. Full table in [`results/discovery.md`](results/discovery.md).

| | 9 MAZE_LIKE games |
|---|---|
| piece, footprint, step size, direction per action | **9 / 9** |
| wall colours found | **5 / 9** (`ar25`, `dc22`, `ka59`, `ls20`, `m0r0`) |
| checked against a known-good model | 1 — `ls20` |

On `ls20` the discovered model matches the hand-read one — a two-part 5×5 piece, step 5,
wall colour 4 — `locate()` finds that piece on a board the model was not built from, and
BFS to the goal box returns the same 6 moves `solver.py` finds.

### Identity was upstream of everything

Objects used to be keyed on `(colour, cell_count)` and looked up in a dict, so two objects
sharing that key in one frame collided and one was **silently discarded — 55 objects across
the 9 games at reset alone**, 19 of `dc22`'s 31. Everything downstream was reasoning about a
partial board, which is why inferred directions contradicted each other.

[`identity.py`](identity.py) replaces the key with tracks: each predicts where it should be,
every object is scored against every track on position, colour and area together, and pairs
are taken best-first, so any one attribute can drift without losing the object. Three more
defects surfaced only once that was in place — requiring a part to move with the piece on
*every* action dropped it after one missed frame (a 5×2 box for a 5×5 piece, whose own second
colour then read as a wall); a part that loses its track returns under a new id and splits its
agreement across two (171 and 106 of 278 moves on `ls20`), so agreement is now judged against
the frames each id was visible in; and a model built from track ids is useless on a fresh
board, which `locate()` fixes by recognising the piece from the shape signature of its parts.

### What is left

`cn04`, `re86`, `sc25` and `sp80` still find no wall colour, and it is neither an absence of
walls (committing to one direction gets the piece blocked within 1–15 moves on all nine games)
nor a shortage of evidence (`sc25` collects 119 blocked observations and learns nothing from
them). Their pieces are still mis-identified, just less often than before.

Four earlier readings of this failure were wrong — over-segmented footprints, open boards, too
little exploration, and a stale randomised hash making every run a different experiment. Each
was a guess; each was disproved by measuring.

## Playing without a human

`play.py` closes the loop: discover the mechanics, then find out what ends a level the only
way available — walk onto things and watch `levels_completed`. The engine is local and a
reset is free, so a wrong guess costs wall-clock rather than score, and only the sequence
that worked is kept.

| game | levels cleared | actions | baseline | score |
|---|---|---|---|---|
| `ls20` | 1 of 7 | 13 | 22 | **4.107%** |
| the other eight | 0 | — | — | 0% |

Level 1 caps its per-level score (115 of a possible 115), and level 1 is worth 1/28 of a
seven-level game — which is the whole shape of this competition in one line.

One object is rarely the answer: on `ls20` the piece must touch the marker before the goal
box will accept it, so the six moves straight into the box do nothing. The search is over
*sequences* of objects, shortest total first. Two things had to be right for it to work at
all — reaching a large object means being **inside** it, not clipping its edge; and a wall
colour has to be the *only* unexplained thing in the way, more than once. Taking every
unfamiliar colour in a blocked destination made `dc22` treat the wall's neighbour as solid
and sealed its board down to 9 reachable positions.

### It writes down what happened

Every attempt used to be judged by one bit — did `levels_completed` move — and the rest of
the run was discarded. `trace.py` keeps it: per action, which objects vanished or appeared,
which status counters moved, and whether a level fell. It lands in
`results/traces/<game>.jsonl` and reads back as a log a person can follow:

```
press 3: nothing changed
press 1: nothing changed
press 1: object colour 0 at x21 y31 disappeared; object colour 1 at x20 y32 disappeared;
         object colour 1 at x21 y33 disappeared
```

That is `ls20`'s pickup, visible for the first time. Three filters were needed before the
log said anything, and each removed noise that had been drowning the signal: the piece is
excluded by **colour**, not by exact size, or it reads as vanishing and reappearing on every
step; an object that moves by exactly the action's own displacement **walked**, which catches
the piece parts the body model missed; and a status counter that ticks on nearly every press
is a clock, not a consequence, so it is dropped from the summary. `levels_completed` is a
running total, so a level completion is announced when it *increases* — testing it directly
printed LEVEL COMPLETED on all sixteen lines of a summary for one event.

The same summary is what the local model now reads instead of a still board, so it can be
asked what the rule is rather than what looks important.

**The first thing the capture found: `perception.hud` is looking in the wrong place.** It
reads rows 60 and below, and that is only where `ls20` keeps its status bar. `cn04` moves a
colour-4 marker one cell to the right along **row 0** on every press; `sc25` slides a
colour-14 marker down the **right-hand column** two cells at a time and then turns it another
colour; `re86` runs two counters at once, one climbing 6→7→8 and one falling 58→57→56. None
of those were visible before, which is why the clock-detector finds no clock on three of the
nine games.

That looked like the way out: a marker read wherever it lives would be a **reward signal
between levels**, something to hill-climb on, where `levels_completed` alone is one bit that
flips only at the end. `signals.py` was built to find it and `play.climb` to follow it.

**Measuring killed the idea.** Every counter these games expose is a straight line in the
number of actions taken — `ls20`'s budget 1.000, `re86`'s pair 0.980, `cn04`'s row-0 marker
0.976, `sc25`'s right-hand column 0.956. They are all clocks; they differ in *speed*, not in
kind, and the slower ones are exactly what made them look like progress at first. Not one
waits for an event, so the climb finds no gradient and stalls on its first step in all four
games. Rate is the wrong test and shape is the right one, which is what `signals.classify`
now measures — but on this evidence there is nothing here to climb.

### It remembers

Discovery costs 400 actions and the search costs thousands more, and none of it changes
between runs of the same game, so what was found is written to `results/learned.json` and
reused. The note is not trusted on sight — the stored solution is replayed and checked
against `levels_completed` first, and re-derived if it does not hold. A second run of `ls20`
takes **6 seconds and 0 discovery actions** for the same score. In the scored setting, where
exploration is charged at exactly the same rate as play, the gap between knowing and
re-deriving is most of the score.

### What did not work

"Collect all of one kind" was the obvious rule for the five games that answer a touch, and
it was built: find the kinds that respond, then tour every instance, replanning after each
pickup. **It moved the score not at all.** Along the way it exposed a worse bug in the thing
that chose which kinds to tour — a detector comparing total object counts before and after,
which fired for every candidate including objects on the far side of the board, because the
parser's component list flickers by a couple of entries between frames. Asking instead
whether *the touched object* is gone cut nine games' worth of "everything reacts" down to a
real distribution, and the tour still cleared nothing: on `re86` it collects 4→3→2 and then
strands, and the second kind's count oscillates 3→2→3→2 because the items come back.

Three further adjustments were built and measured, and **none moved the score**: candidate
targets extended to cover region-sized goals (`perception.objects` drops any colour over 400
cells, which left `m0r0` with nothing to aim at); the sequence search taken to six waypoints;
and the reaction detector rewritten. Each is a real improvement to the machinery and the mean
stayed at 0.456%. What the measurements did establish, which is worth more than the attempts:

- **`dc22` is not a maze.** Its piece moves exactly one step in each direction and stops —
  measured against the live game, so the model's 9 reachable cells are correct, not a bug.
  Nine positions in a 3×3 is a selector, not a board to cross.
- **There is no hidden switch.** Across all nine games only `ar25` and `m0r0` have an action
  that never moves the piece, and pressing it changes 1 cell and 0 cells respectively. The
  agent is not missing a door-opening control.
- **The budget is readable.** `ls20`'s HUD carries a counter that falls by exactly 2 per
  action (84 → 68 over eight), so remaining actions can be planned against instead of
  discovered by dying. Nothing uses this yet.
- **Level 2 is reachable and still not solvable.** After the level-1 solution the agent sees
  12 targets, routes to 8 of them, and has 42 actions of budget — depth-6 search over those
  clears nothing, because `ls20` level 2 wants a *glyph match*, not an arrival. That is the
  research problem, not a parameter.

**Standing on every square changes nothing either.** The object list is a hypothesis about
where the goal is; `plan.bfs_all` plus `play.sweep` is the space itself — every reachable
position, nearest first, capped at 600. Boards here have 37 to 1024 reachable positions and
the engine runs locally, so the whole sweep is free. Run across all seventeen playable games
it clears the same single level. **No level here ends by the piece standing anywhere**, which
retires a whole class of hypothesis rather than adding one.

### Two more things that did not work

**A local model choosing the goal changed nothing.** `goal_llm.py` shows qwen2.5:7b the
object list, the piece, the walls and the status bar, and asks for up to four ranked plans;
the planner routes them and `levels_completed` judges. It was consulted for real — 55s per
call, varied board-specific indices, zero request failures — and the mean over the nine games
came back at **0.456%, identical to the digit without it**. Two prompt defects had to be
fixed first and both are worth knowing: an example plan in the prompt (`[[2], [0, 2]]`) was
copied verbatim on boards where it made no sense, and the model pairs each plan with its
reason as `[[6], "reach the small object"]` about as often as it returns the bare list it was
asked for.

**Nine more games clear nothing either.** Of the sixteen games outside the MAZE_LIKE set,
nine expose keyboard actions; discovery gets a working movement model for eight of them
(`ft09` exposes only pointer actions, so there is nothing to drive) — and `cd82`, which the
earlier probe wrote off as NEEDS_POINTER, yields directions, confirming that false negative.
All eight then clear **0 levels**. Across eighteen games measured, exactly one level has been
cleared.

The eight games that clear nothing are not failing on movement — they have pieces,
footprints and directions. Their levels end on something other than walking onto an object,
and that is the next thing to find out.

## Next

1. What ends a level in the eight games where walking onto objects does not.
2. `ls20` level 2 and beyond — later levels carry almost all of the weight.
3. Re-probe the false negatives from more than one starting state.
4. A harness under `OperationMode.COMPETITION` (one `make()` per environment, no resets)
   for a real baseline across all games.

## Testing

```bash
uv run python -m pytest -q
```

⚠️ If `rtk` is on the path it rewrites pytest's output — a run with failures was reported
as `Pytest: No tests collected` with **exit code 0**. Redirect to a file and read that.

## License

MIT-0. See `LICENSE`.
