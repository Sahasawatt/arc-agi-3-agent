# arc-agi-3-agent — working rules

An agent for ARC Prize 2026 (ARC-AGI-3). `README.md` is the findings log and is written to be
read by a stranger; this file is the operating manual for changing the code.

## The one rule that is not negotiable

**Never read, grep, list or derive anything from `environment_files/`.** It is the source code
of the 25 public games — the answer key — and nothing derived from it generalises to the 110
hidden games that are actually scored. Every fact about a game must come from frames the
engine returned. `.gitignore` covers it; **never `git add -A`** anyway (the SDK writes into
that directory, and it has leaked into a staging area before).

## Running it

```bash
uv run python compete.py            # all 17 playable environments, writes results/compete.json
uv run python compete.py ls20       # one game, ~30-90s
uv run python -m pytest -q          # the suite
ARC_ACCT=out.jsonl uv run python compete.py ls20   # + action accounting, one line per action
```

`ARC_ACCT` writes, per executed action, which rung of `choose` emitted it (`{"i","lvl","src"}`)
plus event lines (`slid` / `chg` / `silentdeath` / `gameover`). Its invariants are its
verification: the per-level line counts must sum to the reported per-level actions, and two
runs must be byte-identical. This is how "where do level 4's 178 actions go" is answered
with a table instead of a theory — tune from it, never from a hunch.

⚠️ `rtk` is on PATH and rewrites pytest's output — a run with failures has been reported as
`No tests collected` with **exit code 0**. Redirect to a file and read the file.

## How a change is accepted here

This repo is a measurement log that happens to contain code. The bar for any change:

1. **A full 17-game sweep before and after.** Per-game, not just the mean — the mean hides a
   game losing a level while another gains actions.
2. **No game loses a level.** Eight rules that were correct on paper have each cost a
   different game its own and been reverted; they are written up in `README.md` because the
   measurement is worth more than the code was. Add yours to that list rather than deleting
   the entry.
3. **One change at a time.** Two at once and a revert tells you nothing.
4. **A claim needs the run that produced it.** "It should help" is not a result. If a number
   is in a commit message, a README, or a report, it came from a run you can name.

## Traps that have already cost a session

- **`env.reset()` with zero actions taken since the last transition performs a full GAME
  reset**, back to level 1 — it only scopes to the current level once a real action has been
  taken. Probes that reset immediately are measuring level 1 while reporting level 4.
- **A blocked move IS charged budget** (measured 20/20, with 20 walked presses as a control).
  An earlier README claimed the opposite; what actually shows a refusal is that the piece's
  position does not change.
- **Track ids are reused across a level boundary.** Numbering carries on at a boundary so the
  old model's body ids are never handed out again, but it deliberately restarts on a level
  *reset*, where the same board yields the same ids and that is the right answer.
- **A model rebuilt on a new board knows less than the one it replaces.** Its `dirs`,
  `blocking` and `parts` all come back thin or empty, and it replaces a good model anyway.
  `build_model(prior=...)` exists for this; `test_compete.py` guards all three.
- **`hash()` of bytes is randomised per process.** Anything keyed on it makes every run a
  different experiment — pass the raw bytes.
- **`plates()` reads the whole frame, not the play area.** `ls20` draws its indicator across
  the row where the HUD starts.
- **A learned map of the board can remove routes that exist.** `ls20` level 4 has floor cells
  that carry the piece somewhere else, keyed on the cell a press *aims at* (not the source or
  the action). Six of them learned by accident cut the reachable board from 67 squares to 57
  and hid both glyph-changers. Any such map is used when it finds a way and ignored when it
  does not — and a cell is only believed once it has been **deliberately re-probed**, because
  waiting to trip over it twice never happens: a redirect drops the plan and the next route
  goes elsewhere.

- **A plate the piece is standing on is obscured, not read.** The piece is 5x5 and a goal
  box can be 7x7, so walking in garbles the glyph and then hides it. Read fresh, that looks
  like a display changing under the square the piece is on — which is exactly how a changer
  is recognised, so the square in front of the door gets recorded as one. `Gate.observe`
  ignores any plate under the footprint and keeps its last reading from off it; a plate that
  vanishes while the piece is elsewhere is a refill that has been taken, and is forgotten.
- **The clock's rate belongs to the LEVEL, so measure it over this level's steps only.** The
  same 84-cell bar spends 2 cells an action on `ls20` level 1 and 4 on level 2. A window that
  still holds the previous level's steps reads the most common fall off the wrong board, and
  because `full` is the largest reading ever taken, one bad reading at the boundary stands
  for the whole level — level 5 believed a life was 40 actions long instead of 21.
- **`walked` means an object moved by exactly the action's displacement**, so on a floor that
  carries the piece it is False for every carried step. Guarding changer-credit on it means
  no changer is ever credited on such a board. What the guard is actually for is not
  crediting a death, and a death is what puts the clock UP — ask that instead.
- **Cost a route the way the router walks it.** `stage` costed its legs with plain `bfs` and
  `_after`, so on a carrying board every distance it compared was fiction, and it predicted
  endpoints off the board and costed plans against them.
- **"Never stood on" is permanent for a square the piece can never stand on.** The explorer
  hunts squares nobody has occupied; the inside of a shut goal box is walkable in every
  colour it is painted, so it is picked, walked to, pressed into, refused, and picked again
  — 598 of `ls20` level 5's planning rounds went to one such square. A press the piece did
  not move for is the evidence, and it expires when a display changes, which is exactly when
  a door can open.
- **Find the rung that emitted the action before theorising about it.** Four fixes aimed at
  a livelock from its symptoms were all measured neutral; tagging every `return` in `choose`
  and counting them found the real one in a single run.
- **The warm-up is a worst case, not a price.** Waiting a fixed 24 actions before the model
  is trusted costs `ls20` level 1 sixteen of the thirty-nine it spends on a goal box seven
  steps away. Planning can start as soon as the controls are *coherent* — four displacements
  on two perpendicular axes, opposite in pairs. Not sooner: `ar25` answers ACTION3 with right
  and ACTION4 with left, so a model built from a couple of presses can hold a sign backwards
  and lose the level outright. The convention cannot simply be assumed either — measured over
  nine games, the axis is right 8 times of 9 and the full mapping 7, and every game has its
  own step size.
- **A board marks what it does to the piece; read it instead of walking into it.** `ls20`
  draws a bar one cell thick and one step long beside every carrying cell, and the piece
  entering one is thrown away from the bar until something blocks it — all eight of level 5's
  cells come out of that rule exactly, before the first step. Filed as a first sighting rather
  than as the map: believed outright it costs level 4, because some marker-shaped object on
  those boards is not a carry.
- **A quarter turn states its whole cycle in one press.** Every shape change on `ls20` levels
  1, 2 and 3 is exactly a rotation (7 of 7 on level 2), so one observation gives four states
  and their order. Walked instead, the same cycle costs an entry per edge — and a life is 21
  actions.
- **A glyph match is exact, and the escape hatch that said otherwise is gone.** `matched`
  used to let a rejected display state un-reject every glyph the old lossy comparison might
  have confused it with — reasonable while collapsing runs of identical rows mapped
  `#.#/#.#/###` onto `#.#/###`, and wrong now that the normal form divides by the scale the
  glyph is drawn at. With it, the piece walks into a shut door wearing a glyph that plainly
  does not match.
- **The board says where the controls are, and using that is a separate problem from reading
  it.** Terrain is painted in one colour and so is most of what there is to walk onto; every
  changer on `ls20` is four or five colours packed into a block the size of the piece.
  Scanned on the piece's own lattice and measured against the board's background colour —
  not against `passable`, which grows until it contains the changer's own colours — that
  reads both of level 3's changers exactly and two of level 5's three, from one frame.
  Driving the walk with it costs level 4 (3 of 7), offering it as a guessed changer costs
  levels 3 and 4 (2 of 7), and a third wiring — reordering the discovery candidates so the
  many-coloured blocks go first, before any display has moved — is measured exactly inert
  (every per-level count identical), so none of it is in the code. The reading is sound;
  the wiring is still the open problem, and the cheap wirings are now exhausted.
- **A press executed inside a committed plan books nothing.** The standing-on-the-changer
  rungs call `gate.cycled()` per entry, and that counter is what forgets a changer that has
  stopped paying — the loop-breaker on a board with a wrong guess in the table. Baking the
  off/on pairs into a staged trip bypasses it: `ls20` level 4 looped on one such square for
  864 actions across 102 trips (98% dead within three actions) and lost the level, at every
  widening tried — whole trips and first-leg-with-presses both. A truncated stage commit
  ends at the first hop's route; the entries stay with the rungs that book them. Two fixes
  that were *not* the cause, both measured inert on the same loop (every count identical):
  filtering stage's routes against `refused`, and gating the commit on the legs being known.
  The whole-trip gate that holds is `known` AND a leg needing two or more entries — `known`
  alone re-costs level 3 its 55 actions through single-entry trips, `known` plus an
  interleaved-half requirement never fires (level 5's ink is one leg), and a stood-on check
  is vacuous because a watched edge implies the square was stood on.
- **The piece covers what it stands on, so two far-apart frames cannot tell a moving
  object from a static one the piece visited.** Level 6's crosses were read as patrolling
  from two frames 500 actions apart; they are static, and the "trail" of thirteen changer
  squares is the set of footprint-overlap positions — all real. A collider-attribution
  model built on the patrol reading measured empty (no mover ever detected), and its
  discriminator needed three exclusions (zero shift, lockstep shift, own colours) just to
  stop reading the piece's churn-renamed body parts as movers — the naive version cost
  levels 3-5 in one run. Level 6's real shape: changers IN the corridors, walking is
  pressing, `locked` reads 0 because the panel never holds still — the planner it needs is
  phase-counting BFS (see README), triggered by the corridor signature, never by `locked`.
- **CORRECTION (2026-07-30, measured per-move): level 6's changers DO patrol.** The
  "static crosses" verdict above was the second wrong reading, not the correction. Tracked
  one position per piece-move (`results/l6-circuits.txt`), three small objects walk
  deterministic period-8 tracks, advance exactly one lattice step per PIECE MOVE, and
  freeze while a press is refused. A press is the footprint overlapping a patroller AFTER
  the move — that model predicted every position and panel value of a 23-action scripted
  drive (`results/l6-driveB.txt`, `l6drive.py`). The collider-attribution failure above
  stands (its discriminator was wrong, and it cost levels 3-5); its conclusion does not.
  The full measured model — patrol tracks, ink alphabet `12→9→14→8→12` closing at level 6,
  door B a checked PASSAGE with door A behind it, death resetting the panel to
  `(14, ##./.##/#.#)` (which is what poisoned `Gate.legacy` with a phantom `12→14`) — is
  written up in `results/l6-model.md`. What a "corridor signature" was groping for is
  patrollers; `gate.track`/`mover_period`/`route_moving` are the measured replacements.
- **On a patrolled board the square-changer rungs are not idle — they are how presses
  get watched.** Their trips go to `gate.changers`, which on such a board are
  footprint-overlap positions rather than places, and they took 317 of level 6's 844
  actions; replacing them with "top the tank up instead" reads like removing pure waste
  and **loses level 6 outright** (5/7, 22.446%). The freed rounds went to the
  confirm-probe rung (40 → 329 actions) and bought nothing, because what a stuck round
  is short of is a watched EDGE, not fuel — and walking the corridors for a fictional
  destination still walks the corridors, which is where the presses are. Cutting the
  cost has to come from teaching the alphabet faster, not from stopping the walking.
- **Three traps from building the patrol planner, each measured before it was found.**
  (1) `Gate.observe` reuses `h` as a half index, so code later in the method that thinks
  `h` is the footprint height gets 0 or 1 — the mover crediting silently tested a 5x1
  footprint and every patroller lost its credit until the condition was print-traced.
  (2) The piece's own parts churn track ids past the `model.body` filter; a piece pacing
  back and forth earns its own fragments a patrol period and a press credit, and that
  phantom patroller glued to the piece blocks every BFS transition (the search explored
  ONE state). Exclude movers by footprint overlap, not by id. (3) On a ±step lattice, a
  patroller whose lap is aligned to the piece's own lattice can only ever share a
  square's parity, never its tick — a test board built that way proves the planner
  "broken" when the geometry makes the press physically impossible. Real patrollers sit
  off-lattice; test fixtures must too.
- **The HUD's colour-8 counter is LIVES REMAINING, four cells each, on every level.**
  Starved deliberately three times over: `8: 12` → `8: 8` → `8: 4` → GAME OVER → back to
  `8: 12` (`results/l7-lives.txt`), and it reads 12 at the start of levels 2, 4, 6 and 7,
  so it is the game's counter and not one level's. A life is 22 actions at 4 units of an
  84-unit bar. This matters because **the three deaths are not alike**: the first two put
  the panel back, the third is a game over that also clears `movers`, `mover_edges` and
  `mover_p` — the patrol model and the alphabet. `ls20` reaches one twice per run and the
  agent has never known which death it was about to take.
- **Keeping the alphabet across a game over LOSES level 6** (5/7, 22.419%). It reads like
  free money — the edges are the expensive half, the board is the same one, and the
  tracker reissues the same ids in the same order, which is the repo's own stated reason
  for restarting the numbering there. Measured, edges filed under the old ids plan presses
  that do not happen, and a wrong edge costs more than an absent one. Only `movers`'
  histories are safe to keep-or-drop cheaply; the edges must go with them.
- **`ls20` level 7's frame is a 40x40 WINDOW around the piece, not the board.** Terrain is
  destroyed behind the piece and created ahead of it as it walks, reversibly and with no
  hysteresis — and comparing consecutive frames at every shift, the best match is
  **dx=0, dy=0 at 94-95%**, so the world is not scrolling: what moves is the colour-5
  region, and the non-5 extent is `piece ± (-18, +21)` in both axes, clipped by the screen
  and the world's own walls. Every reader here treats the frame as the whole board, so the
  fog reads as wall, the piece looks boxed in by something that recedes as it walks, and
  every planning round sees a different board — **776 of level 7's 793 actions are `cand`**,
  which is what a board that will not hold still looks like from inside. Because the
  coordinates are fixed the windows STITCH: the fix is to remember every non-5 cell at the
  coordinates it was seen at and treat colour 5 as *unknown* rather than as wall — gated on
  the colour-5 region moving with the piece, because on levels 1-6 colour 5 IS the border.
  Stitched, the level **has a door**: `plates` on the composite finds `(28-34, 49-55)`
  asking `(8, #.#/##./.##)` — door B's exact ask on level 6 — which no window from the
  start can reach, so "no plates at all" was measuring the window and not the level. Built
  into the agent it works (world 1,165 → 2,839 cells, the plate visible in 777 of 789
  rounds) and is still **not in the repo**, for two reasons. `gate.displays` stays 0 — no
  plate is ever seen to change, so nothing is `locked` and the door is just a rarity
  target; the likely indicator is the unframed colour-12 L glyph at x3-8 y55-59, which
  `plates` cannot read. And the LATCH is an `ls20` fact dressed as a general one: keying
  on colour 5 trading terrain both ways costs `cd82`, `m0r0` and `ar25` their only level
  each — measured on one sighting AND on three consecutive — with 1,981 of 2,000 actions
  spent wandering a board painted from the memory of a board redrawn under them. A general
  version has to find the fog colour in the frame instead of being told it is 5.
  Full model, controls and the open questions: `results/l7-model.md`, probe `probe7.py`.
- **A period belongs to the OBJECT and a phase belongs to the LIFE.** A death puts every
  patroller back at the start of its lap, so pre-death entries contradict post-death ones
  at the same phase and `mover_period` returns None for the three laps they take to age
  out — and while it is lost the LEARN planner is out too, so nothing teaches an edge
  deliberately and the alphabet is only picked up by walking. Clearing the histories there
  lost the level (5/7, 22.419%) because a period re-read off a handful of post-respawn
  frames can be wrong. Remembering the period and re-using it is not the same act: it is
  **checked** against this life's frames and never read off them, so they can refute it
  and can never invent one — and the phase map is built from this life's sightings alone,
  an unseen phase answering None exactly as the occluded stretch of a lap already does.
  **844 → 570, 23.528% → 24.85%**, levels 1-5 identical to the action
  (`results/sweep-phase.log`). Deaths 9 → 6, `stage1` 317 → 209.
- **`ARC_RMDBG`'s refusals were not attributed to a level, and reading them as one level's
  cost is how a number gets invented.** `route_moving` is called on every board with a
  tracked object and correctly refuses wherever nothing patrols, so its 588 `no ready
  movers` lines look like level 6's and are mostly levels 2-5. The lines carry `lvl=` now.
  Level 6's own split, measured: **723 refusals — 555 `bfs exhausted`, 168 no-ready-movers**,
  so the search failing is 77% of it and the periods are no longer the binding constraint.
  Both readings of the 555 tried so far are refuted: not fuel (no plan at a tank of 200),
  and not a phase map thinned by reading phases off one life — at the moment those searches
  give up the maps are **full for 83%** of the movers involved (`results/l6-fill.log`).
  189 of the 555 are the LEARN planner giving up, which says the missing edge sits on a
  patroller the tank cannot reach, not that there is nothing left to learn.
- **A stuck round on the patrolled board is never short of FUEL, and the accounting that
  says otherwise is reading a tank size that is wrong.** Level 6's planner is handed a
  median of 19 actions of a 42-action tank against a 72-action recipe, five of its ten
  lives end with the square-changer rungs draining a full tank and starving, and not one
  of its 844 actions goes to a refuel rung — every arrow points at thirst. Asked per
  round instead of inferred — *would this door have a plan at a tank of 200?* — the
  answer is no in **121 of 121** rounds where both patrol planners came back empty
  (`results/l6-fueldbg3.log`), so a refuel rung gated on it never fires and the sweep is
  byte-identical. The earlier "the freed rounds bought nothing because what they are
  short of is an EDGE" was an inference from a lost level; this is the same conclusion
  measured directly, and it retires fuel as a lever on this board. Two things fell out
  of asking: `full` itself reads **21 in 72 of those 121 rounds** on a board whose tank
  is 42 — `drain` takes the most common fall over the last 20 steps and that flips 2↔4
  within the level — so any lever keyed on the tank is reading a number that is wrong
  most of the time; and a hypothesis about a resource is settled by handing the search an
  absurd amount of it, which costs one run and no code.
- **Routing walks around the recorded changer squares is inert — measured three times.**
  On stage hops, and again on probe/sweep walks (with the fallback kept), every per-level
  count came back identical: the shortest paths do not cross the *recorded entry squares*.
  The unmeant [chg] events mid-walk come from NEIGHBOURING positions whose 5x5 footprint
  overlaps the same cluster, which the entry-square set cannot name — an avoid set built
  from entry squares is the wrong shape for the thing being avoided. Widening it to a
  footprint neighbourhood is untried and risks sealing corridors.
- **The ink alphabet is a property of the game; the squares that write it are not.**
  `ls20` runs the same `12 -> 9 -> 14 -> 8` on levels 3 and 5, so ink transitions (ints)
  carry across levels in `Gate.legacy` — consulted only for a square already seen to move
  that half on this board, dropped by the phantom-edge refutation if a game disagrees with
  itself. Shapes must NOT carry: level 5 alone has two shape-changers walking two
  different graphs. Worth 306 -> 292 on level 5.
- **A blind probe budgeted one way is a death, and a death resets the panel the probes
  serve.** Twelve of fourteen lives lost in one accounted run ended `probe → desperate`;
  level 6 spent 65% of 1,708 actions in the probe rung and still did not fall (which also
  measured out doubling BUDGET — the block is structural). A blind probe now has to afford
  the walk back to a known refill. Only the blind ones: demanding it of targeted probes too
  costs level 3 twenty-six actions, spent by the rungs that fill the gap when a short,
  useful probe is refused.
- **On a carrying floor, a repeat-count cannot tell a livelock from an honest walk.** Every
  legitimate walk across such a board is dropped and re-planned several times (a carry moves
  the piece, the plan is rebuilt), so "the same goal planned N times without the display
  moving" is true of the door walk that WINS the level as well as of the loop that loses it
  — benching goals on that count was measured three ways and cost level 4 all three times.
  The discriminator would have to be progress (the route to the goal getting shorter across
  replans), not repetition. Related and also open: `slid` drops the plan on every carried
  step including the shortcuts the plan itself routed through (285 drops, 902 planned
  actions in one level-5 run), but both narrow keep-fixes turned level 4's cheap two-square
  bounces into thirty-step circuits — the bounce and the circuit are the same livelock at
  different plan lengths, and the cure has to attack the livelock, not the plan-dropping.
  Progress-based benching (route stops shortening) and teaching-aware benching (map stopped
  growing) were also measured and also cost level 4: what gets benched there is the goal box
  itself, and the walk that looks like a livelock toward it IS the discovery walk that finds
  the level's changer. No local signal separates the two — the next lever is structural:
  either model deaths inside the order search (make the display-reset a cost it can weigh),
  or execute a staged multi-leg plan as a unit instead of committing one leg and rediscovering
  the rest.

## What the scoring actually rewards

`min((baseline_actions / actions_taken)² × 100, 115)` per level, averaged **weighted by level
number**, and the game total is additionally capped by which levels were completed. Two
consequences worth holding on to:

- **Fast enough beats optimal.** Anything at or under 1.15× the human baseline scores the
  same 115, so shaving actions below that threshold buys nothing.
- **Depth is everything.** Level 1 of a 7-level game is 1/28 of the weight; level 7 is 7/28.
  Exploration is charged at exactly the same rate as play — there is no free discovery phase.

`scoring.py` implements this offline; `docs/competition-rules.md` records the rules with
sources, including a retraction of the "5× human median" action cap that is not a rule.

## Layout, in dependency order

`perception` (frame → objects, HUD, glyph bitmaps) → `identity` (cross-frame tracking) →
`discover` (movement model by acting) → `plan` (BFS routing) / `gate` (locks and the squares
that change them) / `signals` (counters, clock, refills) → `compete` (the rules-legal play
loop). `play.py` is the older rewinding searcher and is **not** rules-legal — its numbers are
upper bounds from a dev mode the competition does not offer.

## Git

Branch `master`, remote `Sahasawatt/arc-agi-3-agent` (public, MIT-0 — the competition requires
open source for prize eligibility). **Ask before every commit**, and stage files by name.
