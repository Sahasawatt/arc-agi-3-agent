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
  rounds), and **it is in the repo now**. The indicator is the unframed colour-12 L glyph at
  x3-8 y55-59, and **a plate does not need a box around it** — `plates` now also admits a
  shape standing ALONE against ONE background colour that reaches the frame's own edge (a
  shape on the floor is a thing to walk to; a shape in the void is a sign). That reads it as
  `(3-8, 55-60) ink=12 .#./.#./###`, and level 7 stops wandering: `cand` collapses from 853
  actions to 44 while `probe` (231), `stage1` (68), `moving-learn` (40), `turn-fuel` (26)
  and `cycle-last` (16) all start firing — the whole lock machinery, including the patrol
  planner. It costs `cd82` 179 actions (1,034 → 1,213, no level lost) and restricting the
  rule to shapes on the void does not recover them — measured, byte-identical.
  What took two attempts is the LATCH. Keying on colour 5 trading terrain both ways is an
  `ls20` fact dressed as a general one, and costs `cd82`, `m0r0` and `ar25` their only
  level each — measured on one sighting AND on three consecutive — with 1,981 of 2,000
  actions then spent wandering a board painted from the memory of a board redrawn under
  them. The question that separates them is not how MUCH changed but WHERE: the fog is
  everything outside a box around the piece, so the fog SET translates by exactly the
  piece's displacement while the content stays in world coordinates, and a board that
  merely redraws has no reason to agree with the piece's own step. Shift the candidate
  colour's mask by that step and ask whether it predicts the next frame better than leaving
  it put; over colours that reach the frame's edge, latched on two steps running. Measured:
  no game loses a level, levels 1-6 identical to the action, fires only on level 7 — where
  `near-fuel` goes 0 → 280 actions because the agent can finally see refills it is not
  standing next to. It buys **no points yet**, and it is the only route to any.
  **Both halves the level looked to lack were behind the window.** Using the stitched map
  as a stability oracle — a cell that comes back DIFFERENT while not under the piece is the
  board acting, not the window moving — level 7 has a PATROLLER (16 cells at x55-57, a
  five-cell cross of colours 0+1 at y=12/17/22/27/32, the same object as level 6's cross-2;
  "nothing patrols" came from an 18-action probe at the start, where the window reaches x40)
  and an INDICATOR (the colour-12 L glyph at x3-8 y55-60 turns a QUARTER TURN per press,
  four states and back — `turned()` already handles that, but `plates()` cannot see it
  because nothing frames it). Route to the patroller from a standing start, inside one life:
  `1,1,4,4,2,4,2,4,2,4` (the last is a carry) then `4,4,4`, then `1` up x54. Open: the door
  asks `(8, #.#/##./.##)` and the indicator normalises to `.#./###` and its rotations — the
  inks and the shapes both differ, so either a second display is still in the fog or that
  plate is not the lock — and it is NOT: driven to (29,45) and the frame dumped from there,
  x29-34 y50-55 reads colour 5 on the LIVE board with floor either side, so it is a HOLE
  with the colour-8 glyph floating in it, and the refusal measured there is the void, not a
  lock. `plates` saw a plate because on the stitched composite the unexplored interior was
  5 and its ring was 5 as well — **the fog framed itself**, which is a hazard the stitching
  creates and nothing yet guards. The glyph is the level's ask drawn as a picture. The same
  frame shows a **multi-coloured block at x11-12 y41-43 (colours 14, 8, 12)** — four or five
  colours in a piece-sized block is this game's signature for a changer, and standing on it
  at (9,40) **changes the indicator's INK, 12 -> 9, shape untouched** (`hud`'s `12: 6`
  becomes `9: 6`). So level 7 has both halves: the x55 patroller turns the SHAPE a quarter,
  this block walks the INK — along `12 -> 9 -> 14 -> 8 -> 12`, which `Gate.legacy` has held
  since level 3, so three presses reach the ask's ink with nothing new to learn. The SHAPE half is
  the colour-0 object beside it at x20-22 y41-43: from (19,40) the indicator goes
  `.#./.#./###` → `#.#/#.#/###`, five cells to seven, so it walks an ALPHABET rather than
  turning — and it is phase-dependent, so it is a patroller too. **Level 7 is fully
  accounted for and is level 6's machine with the parts further apart than one window.**
  What the agent still lacks is `movers`, which reads 0 for the whole
  level, so `route_moving` never runs. Two causes. **The stitch painted GHOSTS** — it
  remembered moving cells too, so a patroller out of view stayed drawn where it was last
  seen and the tracker followed a copy standing still; 25-61 objects tracked with full
  histories and not one period. Fixed: a cell that comes back DIFFERENT is marked dirty and
  never painted from memory (`withp` 0 → 1-3, every game unchanged). **The rest is
  IDENTITY**: a patroller is out of view most of the time and the tracker issues a new id
  every re-entry, so no id accumulates three laps and `_adopt` cannot help because it needs
  a period first. Keying on a SIGNATURE instead of an id — colour and size, and only where
  unambiguous in the frame — was measured and **costs level 5 a hundred actions and level 6
  eighteen** (40.503% → 36.884%): a signature unique in one frame and not the next flips the
  key back and forth and splits the history it meant to join. What DOES hold is patience —
  `identity.update`'s `max_missed` is 2, so a track dies two frames after the piece walks
  away from it, and on a windowed board out of view is not gone. Raising it to 200 while
  `windowed` takes level 7's `moving-learn` from 40 actions to **90** and its `probe` from
  673 to 317, with every game unchanged. Still not enough to clear it.
- **Learn mode may run on mute patrollers alone ONLY on a windowed board.** The guard
  `if not movers: return None` deadlocks level 7 — 1,034 of its 1,816 refusals had one to
  three period-carrying, never-watched patrollers on the board, and nothing ever presses
  one on purpose, so nothing ever becomes ready. Ungated, letting learn through **costs
  ls20 levels 5 AND 6** (4/7, 20.489%) — measured twice, once with `period` degenerating
  to 1 and once with the mute periods folded into the LCM correctly, identical to the
  digit: on a board with a ready mover coming, a learn trip to a mute one pre-empts the
  rungs that win the level. Gated on `gate.windowed` (set by the fog latch, which levels
  1-6 never trip) it is clean — every game unchanged, and level 7's `moving-learn` rises
  90 → 139. Level 7 still does not fall: 31 deaths in one run and 15 presses, so the trips
  are being planned and starved. The next axis is fuel-awareness of those learn trips, not
  more of them.
- **On a windowed board the refill detector UNLEARNS its refill colour.** `refills()`
  demands `seen_with > seen_without`, and on a board whose frame slides, the ring drops off
  the window's edge on nearly every walk — each exit counts against it, so after the first
  pickup the ratio tips and the tank goes back to empty: measured at `tank=[]` in **384 of
  level 7's 415** planning rounds, every learn trip planned with no fuel to weave. The
  trace now drops, on windowed boards only, `gone` entries whose square is FOG in the raw
  frame (slid out of view, not vanished) and `new` entries whose square was fog a step ago
  (slid in, not appeared) — `tank=[11]` goes 31 → 172 rounds and `fuels>0` 31 → 112, every
  game unchanged. The remaining decay was OCCLUSION — the piece walking past a ring hides
  it for a step with the clock flat, and each of those counted against the colour
  (with=58 vs without=68 by run's end, `ARC_RFDBG` since removed). A second windowed-only
  filter drops `gone` under the piece's own footprint when no draining colour rose (a
  pickup rises, so pickups still count): `tank=[11]` 172 → **196 of 345**, `fuels>0` → 118.
  Level 7 still does not fall — the remaining empty-tank rounds are early-level (before the
  first pickup ever happens) plus post-death windows, and the deaths themselves are what
  starve the learning. Measured next session: the trips DO weave now — `moving-learn` 139
  → 383 actions, presses 15 → 23, deaths 31 → 28 — and the post-death half of the decay is
  gone too: a refill colour is a property of the LEVEL, so `tank_colours` LATCHES it on the
  Gate once earned (windowed boards only; the Gate dies at the level boundary, so nothing
  leaks to the next board, and everywhere else `refills()`'s withdraw-on-doubt still guards
  against a false pickup). Deaths 28 → 22, presses → 31, `probe` 627 → 516, all four games
  unchanged to the digit. Full model: `results/l7-model.md`, probe `probe7.py`.
- **On level 7 a press is never credited to the thing pressed — and the square machinery
  already holds what the mover machinery cannot.** Traced per press (`ARC_CRDBG`): the
  shape changer by x20-22 sits at the SAME box in every sighting, so `mover_period` can
  never earn it a period (a cycle needs two distinct positions), `mover_at` answers None,
  and its `hist` is one tick stale at the press because the piece covers it — 8 of 8
  presses uncredited, `withh=0` in all 1,302 no-ready-mover refusals. The x55-57 patroller
  has a period but its press PHASE is exactly the occluded one, so it goes uncredited too.
  Meanwhile the ink block's fragments flicker size under the footprint's edge, which
  reads as "two positions" and earns a GHOST period — level 7's only mover credits (3 in
  one run, all to that fragment). But the walked presses (18 of 23) land in
  `gate.changers`/`gate.cycles` under their SQUARE — (9,40) ink, (19,40) shape — because
  both of level 7's changers are effectively square-pressable; what keeps that knowledge
  idle is the moving rung swallowing every round (30+ junk tracks keep `gate.movers`
  non-empty). Read back from a run (`ARC_L6=... ARC_L6LVL=6`), the squares hold the whole
  lock: the full ink ring `12→9→14→8→12` under (9,40), a growing shape alphabet under
  (19,40), and the x54 quarter-turn. The rung REORDER is in (windowed boards
  only, three edits in `choose`): the learn trip is stashed instead of returned, the probe
  rung yields whenever `turns_for` knows a square for a wrong half, and the stashed learn
  trip returns after `cycle-last`. Presses 31 → 68, `stage1` 13 → 276, `probe` 516 → 73,
  every other game and level unchanged to the digit — and the square records survive a
  game over, which wipes `mover_edges` twice a run. Level 7 still 6/7; deaths 24.
- **Level 7 is SOLVED by hand — a 71-action line completes it** (`results/l7-solution.txt`,
  run `results/l7-solve.txt`, full write-up in `results/l7-model.md` §SOLVED). The shape
  ring at (19,40) is six states and closed WITHOUT the ask; the exact ask is ring state
  `##./.##/#.#` + TWO quarter turns of the x55 patroller, and the door is the hole,
  entered by `down` from (29,45) once the panel is exactly `(8, #.#/##./.##)`. Load-
  bearing mechanics: presses at both (9,40)/(19,40) are one per RE-ENTRY (not phase-
  dependent — that earlier reading was re-entry semantics); the x55 patroller presses by
  CHASE (piece following it down its y12↔32 lap overlaps every tick, three presses in
  three actions — step off to the x49 column to stop at two); three refills are woven in
  ((14,45), (39,5) on a life's last action, (55-57,51-53)) and two carries used
  ((34,20)→(39,40), (39,35)→(29,30)). The agent still plays 6/7: no planner can compose
  square presses + phase-timed patroller presses + refills in one plan.
- **The composition IS plannable now — the wall is in-run DISCOVERY, one layer at a
  time** (all windowed-gated, every sweep clean, ls20 6/7 40.503% throughout; a first
  ungated version of the credit fix cost level 6 fifty actions — 209 → 259 — before it
  was gated). What was built, and what each unlock measured: `route_moving` folds the
  recorded SQUARE changers into its BFS (press per arrival), lets a marked door whose
  interior is unwalkable void be a goal (the hole — `footprints_touching` filters
  walkable, so its inside was never a gate), and runs with no ready mover when squares
  exist (1,198 rounds died on that guard with halves credited to period-less churned
  ids). The mover credit takes an age-1 sighting inflated a step when the pressed thing
  is covered. Trip marks are not refuted while every display is under fog (`raw5`), so a
  staged east leg can run open-loop. `moving-learn` jumps the square rungs when ANY
  wrong half is `exhausted` (`all` never fires — the ink half is always fixable), and
  before the learn trip a `fog-explore` rung walks to the nearest never-stood position
  bordering colour 5 — the unexplored set IS the fog on a windowed board (before it:
  598 learn-trip actions pressed west ghost fragments while the east stayed unseen).
  Where it stands, measured per run: fog-explore 346-514 actions, east-of-x44 only 22,
  (54,*) never pressed in-run — the east is reachable ONLY through the (34,20) carry,
  which `slides` cannot hypothesise (a +5,+20 warp, not a marked throw) and no route
  can aim at before it is walked once. `l7f.jsonl`
  analysis pattern: per-action rows carry `now`+`chg`, plan rows carry rung+cycles.
- **The discovery cascade, continued (2026-08-01, all windowed-gated, every sweep clean,
  ls20 still 6/7 40.503%).** Landed in order, each unlocking the next measurement:
  `fog-poke` presses the never-poked direction wherever the ROUTABLE map dead-ends
  (`gate.poked`, one action each) — that is what finally teaches the (34,20)→(39,40)
  carry (`redirects` now learns it in-run, slid 8 → 29-33); `fog-fuel` weaves a refill
  when the nearest frontier is beyond the tank (east is 20+ actions out on a 21-action
  life); `observe` keeps icons whose box is UNDER THE FOG (a display that slid out of
  view is not gone — dropping it blanked `state()` and made `exhausted` read
  closed-graph where it should read blind), which immediately exposed two more:
  a colour-5 "plate" (the fog framing itself) kept forever as a display — windowed
  boards now refuse ink-5 plates outright and purge kept ones — and the exhausted-yield
  keyed on `locked[0]`, which is often the refill-ring plate rather than the door
  (`ARC_YDBG` prints the per-round wrong/exhausted/path view that caught both).
  In-run state after all of it: ink ring, shape ring AND the x54 quarter squares all
  recorded live ((54,10..30) with presses at each), carry learned, deaths 31 → 18.
  Exploration-vs-press was then settled the same way the reorder settled probe-vs-stage:
  the yield fires only when `learning_path` is ALSO None (while an unwatched edge is
  reachable, the square rungs keep the round), and **the composition is verified
  plannable offline** — hand a Gate the full six-edge ring plus one x54 rotator and
  `path_for` returns `[((19,40),5), ((54,30),2)]`, the hand solution's exact press plan.
  The best stable state ends at: chg 150/run, stage1 290, deaths 22, still 6/7, ring
  incomplete in-run because presses spread across deaths and the x54 phase no-ops.
- **The union drift is FIXED — a display's off-pixels are state, not fog, and the fix
  is scoped to boxes that have CHANGED** (2026-08-01, sweep clean, every count of all
  four games identical). What three suppressor placements could never catch: the
  garble happens on the PRESS TICK with the box fully in view — paint-back has no
  notion of a window, so a glyph pixel that turned off (non-5 → 5, invisible to the
  dirty test) was repainted from memory in the same frame the press changed the rest
  (reproduced raw-vs-composite, `results/ug-repro.txt`; a box "re-entering reading
  range" is simply not when it happens, which is why the suppressor was byte-identical
  — it keyed on ticks that never coincide). The fix: `stitch(boxes=gate.displays)`
  records in-window 5s inside those boxes as KNOWN 5s, so painting them back is a
  no-op forever; `known`/`dirty` untouched, nothing outside the boxes changes. Two
  refinements are load-bearing: (1) scoping to `icons | displays` FLICKERS — the
  door's static ask-picture is partially fogged from positions the ±18/+21 test calls
  readable (its (32,53) pixel is visible at dx=13 and fogged at dx=18: the window is
  wall-clipped, not square), and recording those as OFF minted 85 phantom edges in one
  run; a STATIC plate is exactly what the paint-back stabilises. (2) A box that
  changes changes its INK before its shape, so it is in `displays` before the first
  union pixel can exist. Measured on level 7: junk shape-edges 85 → 0, `desperate`
  113 → 0, `cand` 182 → 55, deaths 22 → 11 — and the shape ring now assembles CLEAN,
  4 of 6 edges in one run. Still 6/7: the panel parks on `#.#/#.#/###`, a state with
  no outgoing edge in `cycles`, and nothing presses (19,40) again for 800 ticks —
  the next wall is the planner's, not perception's.
- **A transition reported against a stale reading can be a FOLD, and the test for it is
  ENTRIES of the pressed square, not the reading's age** (2026-08-01, the session after
  the one above; all sweeps clean, every game identical). Chain of measurements, each
  breaking the previous repair: (1) a death's panel reset folded into the next booked
  edge gave the ink square a phantom SHAPE edge that CLOSED the ring graph two real
  edges short — `exhausted` then read closed-graph and stopped pressing. A tick-age
  guard has an equality hole (a death on a blocked action leaves `ticks` flat), so the
  guard is `gate._fresh`, boxes read fresh THIS LIFE, cleared at both death sites in
  `compete`. (2) `exhausted` itself now also demands the graph be CLOSED (every seen
  state has an outgoing edge) — a state with none is a walk stopped mid-cycle, blind,
  not exhausted. (3) A walk-through press surfacing squares later folded TWO presses
  into one edge (`#.#/#.#/### -> .#./##./.##`, the `.##` state worn unread between) —
  requiring the old reading be age-1 rejects those but ALSO rejects every bounce whose
  off-square is a wall-clipped blind spot (2 booked edges over 80 bounces); the correct
  discriminator is **arrivals of the pressed square since the display's last fresh
  reading: one is one press however stale, two is a fold** (`_arrivals`/`_foldsafe` in
  `gate.observe`, windowed-gated). (4) On a windowed board a DISPLAY unreadable by
  `plates` is kept in `icons` even where the ±18/+21 geometry says readable — the
  window is wall-clipped, and dropping it emptied `state()` and blinded the lock
  machinery for most rounds (`cand` owned the level). (5) The ring changer is
  phase-gated: continuous oscillation walks the whole six-state ring one state per two
  MOVES with zero no-ops (`results/l7-hashpress.txt`), including changes landing on the
  step-OFF move — "press per re-entry" undercounts it, and a single bounce that no-ops
  is not a dead changer. `cycle-on-turn` commits three bounces while a wrong half is
  unplannable-but-open. Net state after all of it: cycles are finally CLEAN (4 real
  ring edges, zero junk, correct changer attribution) but the ring still does not
  close in-run — the two edges out of `#.#/#.#/###` and `.##/#.#/.#.` need a bounce
  session that persists at the changer, and the fuel rungs (`turn-fuel`/`near-fuel`)
  own those rounds instead. The remaining wall is round-ownership economics, not
  perception.
- **A patroller nobody has watched is INVISIBLE to the planner, not unknown to it.**
  `route_moving` builds its patroller list from movers with a period **and a known half**;
  one with no half contributes nothing to `presses`, so walking over it is not modelled as
  a press and no plan can go and find out what it does. Measured: **183 of the 189** rounds
  level 6's learn planner gave up on had two to seven of them on the board, all carrying
  period 8 — the search was right that nothing it could see was unknown, and what it could
  see was not all of them. In learn mode they ARE the unknown press (read each against its
  own period, so the LCM does not have to cover them; same fuel guard, because a press the
  piece starves on teaches nothing). **570 → 285, 24.85% → 32.144%**, levels 1-5 identical
  to the action (`results/sweep-mute.log`). `stage1` 209 → **3**, `moving-learn` 82 → 154,
  deaths 6 → **1**. The lesson generalises past this board: when a search reports "nothing
  left to learn", ask what it is unable to represent before asking what it cannot afford.
- **Preferring to learn the half the DOOR wants is exactly inert.** The learn search
  returns the NEAREST unwatched press and will as happily walk off to learn a half that is
  already right, so a strict pass over the wanted halves before the general one reads like
  free direction. Every per-level count came back identical: the panel differs from a
  door's ask in **both** halves nearly all the time on this board, so the wanted set is
  every half and the strict pass IS the general one. A preference only steers where the
  thing preferred is sometimes a minority.
- **Identity is the LAP, and a track that churns strands the alphabet under the old id.**
  A patroller is invisible exactly when it is pressed — the piece covers it — so the id
  churns on the tick that matters. Level 6's 285-action run makes 85 presses, gains 51
  edges and ends holding **122 edges under 26 keys for three patrollers**, the gains
  arriving in six-action bursts six times over: the same six edges, relearned. Keeping
  edges across a GAME OVER lost the level (ids land on whatever comes next); within a life
  the lap is evidence — two objects on **two** of the same squares of a deterministic
  circuit are one object, two rather than one because a single shared square is a crossing.
  On earning a period a track inherits the halves and edges of the circuit it matches,
  copied not aliased so no reader changes, and a wrong adoption is refutable like any wrong
  edge. **285 → 265, 32.144% → 33.668%** (`results/sweep-adopt.log`).
  Then **265 → 209, 33.668% → 40.503%** by fixing two words of it: adoption was asked only
  on the reading that EARNS a period — never on the commoner one that inherits it, so a
  board that kills the piece adopted nothing for three laps after every death — and it
  compared a SNAPSHOT of the circuit taken at that instant, which holds whatever few phases
  had been sighted by then and never improved. Ask on every reading, accumulate the lap
  (a death moves a patroller back ALONG its track, not off it, so the union is across lives
  while `mover_at` stays within one). Watch the wrong number and you miss it: keys go only
  24 → 22, while the edges SPREAD, 151 → 221.
  Then **265 → 209, 33.668% → 40.503%** by fixing two words of it: adoption was asked only
  on the reading that EARNS a period — never on the commoner one that inherits it, so a
  board that kills the piece adopted nothing for three laps after every death — and it
  compared a SNAPSHOT of the circuit taken at that instant, which holds whatever few phases
  had been sighted by then and never improved. Ask on every reading, accumulate the lap
  (a death moves a patroller back ALONG its track, not off it, so the union is across lives
  while `mover_at` stays within one). Watch the wrong number and you will miss it: keys only
  go 24 → 22, while the edges SPREAD, 151 → 221.
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
  189 of the 555 are the LEARN planner giving up — and asking each of those rounds what an
  INFINITE tank would do says the opposite of what that looked like: in **159 of the 189**
  it finds no unknown press either, so there is genuinely **nothing left to learn within
  reach**, at any tank size. Only 30 are affordability. So "make the learn trip affordable"
  is not the lever; what those rounds are short of is a panel VALUE they can get to. The
  derivation that followed — that the reachable set is CLOSED, so a death's reset to
  `(14, ##./.##/#.#)` is the only move that crosses the frontier — was written down as a
  hypothesis and is **refuted by the panel trace** (`ARC_L6`, 24 distinct states over the
  level): the level's five deepest shapes are first seen at a=1039, 1040, 1041, 1042, 1043
  — five consecutive actions, so five PRESSES, ending on door A's own glyph — and the
  deaths are at 679, 760, 837, 916, 993 and 1098. A death is not what opens the alphabet.
  What a death does introduce is exactly one state, `(14, ##./.##/#.#)` at the first one.
  So "nothing left to learn within reach" is a LOCAL condition of the piece's position,
  phase and panel value, not a permanent closure — the level walks the alphabet in a burst
  when it finally stands where it can, and what costs the ~400 actions is getting there.
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
