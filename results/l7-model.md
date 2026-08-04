# ls20 level 7: the frame is a WINDOW, not the board (2026-07-30)

Replay `results/prefix-l7.txt` (1,207 actions, the level-6-clearing run cut at the level
boundary) with `probe7.py`, which prints a board census per step instead of the plates
`probe6.py` looks for — this level has none.

    uv run python probe7.py ls20 results/prefix-l7.txt 1,1,4,4,2,4,2

## The controls

`1` up, `2` down, `3` left, `4` right, five cells a step, piece 5x5 (colour 12 over
colour 9). The clock spends **4 units an action** against a full 84, so a life is 21
actions — half of level 6's, on a board that is much bigger.

## What moves when the piece moves

One step up, measured cell by cell (`results/l7-shrink.txt`):

| change | n | where |
|---|---|---|
| floor 3 -> 5 | 98 | x9-40 y20-36 |
| wall 4 -> 5 | 86 | x4-40 y16-36 |
| 5 -> wall 4 | 38 | x4-39 y0-6 |
| 5 -> floor 3 | 8 | x39-40 y5-12 |
| 5 -> 11 | 1 | (40, 8) |
| 1 -> 5 | 1 | (40, 19) |

Terrain is destroyed behind the piece and created ahead of it, a refill ring grows a cell
and a marker loses one. Stepping back restores **every count exactly** — 606 floor cells,
16 of colour 11, 2 of colour 1, both on the way out and on the way back, in both axes. So
the board is a pure function of the piece's position, with no hysteresis.

## It is not a scrolling world: the frame is a clipped window in FIXED coordinates

Comparing two consecutive frames at every shift from -8 to +8 in both axes, the best
match is **dx=0, dy=0 at 94-95%** (the remainder is the piece itself and the border). The
world does not move under the camera; what moves is the colour-5 region.

Measured across ten positions, the non-5 region is

    piece_x - 18  ..  piece_x + 21        piece_y - 18  ..  piece_y + 21

clipped by the screen and by the world's own walls — a **40x40 window around the piece**,
with everything outside it painted colour 5. Every count that looked like a shrinking
arena is that window sliding: going up "loses" the bottom because the window's bottom
edge came up, and the extra colour-11 cell is a third refill ring coming into view at the
top, not a ring growing.

## What this means for the agent

Every reader in the repo treats the frame as the whole board, and on this level it is a
viewport. So:

- `walkable` reads the fog as impassable, and the piece looks boxed in by a wall that
  recedes as it walks;
- every planning round sees a different board, so targets appear and vanish and the
  route is rebuilt constantly — level 7's accounting is **776 of 793 actions in `cand`**,
  the rarity router, which is what a board that will not hold still looks like from
  inside;
- `plates()` finds nothing because whatever the level asks for is outside the window
  almost always.

The shape of the fix follows from the dx=dy=0 result: because world coordinates are
fixed, the windows **stitch** — remember every non-5 cell ever seen at the coordinates it
was seen at, and treat colour 5 as *unknown* rather than as wall.

## Stitched, the level HAS a door — and still no display

Stitching the windows offline (`probe7.py … -map`) and handing the composite to the
agent's own `plates` reader finds one:

    plate (x28-34, y49-55)   ink=8   #.#/##./.##

which is door B's exact ask on level 6 — the game reuses its alphabet. It sits at y49-55
and **no window from the start reaches it**, which is what "no plates at all" in
`l7-first-look.md` was actually measuring. Level 7 is the level 2-6 lock after all.

Built into the agent it does what it says: `windowed` latches on the second action of
the level, the world map grows 1,165 → 2,839 cells, and the plate is visible in **777 of
789 planning rounds** (a refill ring reads as a second plate, `(14-18, 45-49) ink=11
###/#.#/###`). What is still missing is a **display**: `gate.displays` stays 0 for the
whole level, because no plate is ever seen to CHANGE, so nothing is `locked`, the door is
just another rarity target, and the agent walks to it as `cand`. The likely indicator is
the big colour-12 L glyph at x3-8 y55-59 — normal form `.#./###`, which is not the door's
ask — and `plates` cannot read it because it has no frame around it.

**The detector is the open problem, and it is not a small one.** Latching on colour 5
trading terrain both ways is an `ls20` fact dressed as a general one. Measured twice —
on one sighting, and on three consecutive — `cd82`, `m0r0` and `ar25` all latch too and
lose their only level each, spending 1,981 of 2,000 actions wandering a board painted
from the memory of a board that had been redrawn under them. A general version has to
identify the fog colour from the frame rather than being told it is 5, which is its own
problem. The stitching code is therefore NOT in the repo; this file is what it measured.

## It IS the level 2-6 machine: a patroller, a rotating indicator, and a door

Both halves the level looked to be missing were behind the window.

**A patroller.** Using the stitched world as a stability oracle — any cell that comes back
DIFFERENT from what was remembered, while not under the piece, is the board acting rather
than the window moving — a 40-action walk turns up exactly **16 such cells, all at x55-57**,
flipping between floor and colours 0 and 1 at y = 12, 17, 22, 27 and 32, five apart, which
is the lattice step. Per site the shape is `(56,y-1)=0, (55,y)=1, (56,y)=0, (57,y)=0,
(56,y+1)=1` — a five-cell cross of colours 0 and 1, the same object as level 6's cross-2.
The first look concluded "nothing patrols" from an 18-action oscillation at the start
position, where the window reaches x40 and the patroller is at x55: it was never on screen.

**An indicator.** Driven along the right-hand corridor at x54, the big colour-12 L glyph at
x3-8 y55-60 turns a **quarter turn per press**, four states and back to the first:

    ..##../..##../..##../..##../######/######      hud 12: 6
    ##..../##..../######/######/##..../##....      hud 12: 2
    ######/######/..##../..##../..##../..##..      hud 12: 2
    ....##/....##/######/######/....##/....##      hud 12: 2
    ..##../..##../..##../..##../######/######      back to the first

`turned()` already knows what to do with a quarter turn — one observation gives four states
and their order. What `plates()` cannot do is SEE it: the glyph has no frame around it, and
a plate is defined here as a region with its own colour all the way round.

**A route.** From the start, `1,1,4,4,2,4,2,4,2,4` reaches (39,40) in ten actions — the
last of those is the carrying cell — then `4,4,4` walks the row-40 corridor to (54,40) and
`1` repeated climbs x54 through the patroller's track. Nineteen actions from a standing
start, inside one 21-action life.

**CORRECTION (same session, from beside it): the "plate" is a HOLE, and the refusal is
the void.** Driven to (29, 45) and the frame dumped from there — well inside the window,
which reaches x11-50 and y27-66 from that square — the region x29-34 y50-55 reads as
**colour 5 on the live board**, floor at x28 and x35 on either side of it. It is a hole
with the colour-8 glyph floating in it at x31-33 y51-53, not a box the piece may enter
when it wears the right thing. `plates` read it as a plate because on the STITCHED
composite the unexplored interior was 5 and its ring was 5 too, so the fog framed itself.

So the glyph is the level's ASK drawn as a picture, exactly as `l7-first-look.md` guessed
of the L glyph, and the paragraphs below are wrong in their conclusion though right in
their measurement. What they measured stands: the piece IS refused there. What it means
does not: that is the void refusing it, the way every border does.

The same frame shows something the earlier maps never reached: a **multi-coloured block at
x11-12 y41-43, colours 14, 8 and 12**, with colour-0 cells beside it at x20-22. Four or
five colours packed into a block the size of the piece is this game's signature for a
CHANGER, and this one contains colour 8 — the ask's own ink. That is the thread to pull.

**The measurement the correction is built on.** Driven into it — `3,3,2,2,4,4,4,4,2,2,2,2`
walks left, down the x9 column, right along row 25 (open from x9 to x43) and down the x29
column to (29, 45), which is one step above the inside position (29, 50) — the thirteenth
action, `down`, **does not happen**: the piece is still at (29, 45). That is the level 2-6
refusal exactly, the move simply not occurring, so the level does end at a door after all.

**Nothing changes near it.** Running the stability oracle over a 26-action walk around the
door region turns up **zero** contradicted cells. The only changer on this board that has
been found is the patroller at x55-57, twelve actions away from the door in the other
direction, on a level whose life is 21 actions — so the choreography needs a refill, and
there is a ring at x55-57 y51-53 beside the patroller itself.

**What still does not add up** is the match. The door asks `(8, #.#/##./.##)`; the indicator
is colour 12 and its four states normalise to `.#./###` and its rotations. The inks differ
and the shapes differ, and the glyph stays colour 12 through every rotation (a change of ink
would move `hud`'s colour-8 count, which is the lives counter and does not move). So either
a second display is still in the fog, or what this door checks is not an (ink, shape) pair
compared the way levels 2-6 compare theirs.

## Testing the rotations by hand does not converge

The obvious next experiment — press the patroller n times, walk to the door, try to enter,
for n = 0..3 — was scripted as a 38-action drive with two refills (`results/l7-try1.txt`).
It failed, twice over, and both failures are the level telling you something.

**The glyph never turned.** The drive stood at (54, 35) and (54, 30), the same squares that
turned it a quarter each on the earlier run, and nothing moved. The patroller advances one
step per PIECE MOVE, as level 6's do, so arriving at the same square on a different tick
arrives somewhere it is not. Pressing here is a timing problem, not a routing one.

**And the map is not enough to route on.** At step 27 a plain `up` from (39, 35) landed the
piece at **(29, 30)** — five up and ten left, a carrying cell nobody had mapped, and the
second one found on this board. The drive was lost from there and starved at (19, 25).

Which is the argument for doing it the agent's way rather than by hand: `route_moving`
plans over position x patrol phase x panel and already solves exactly this, and it is
`redirects` that learns a carry. Neither can run here until the frame stops being a window,
so the general fog detector is not a nice-to-have — it is the whole gate.

## A plate does not need a box around it

`plates` defined a plate as a region with its own colour all the way round, which is what
made `gate.displays` read 0 here for the whole level: the indicator is a bare glyph on the
void. Widening it to admit a shape standing ALONE against ONE background colour reads it
straight away —

    plate (3-8, 55-60)   ink=12   .#./.#./###

— and the level stops wandering. `cand` collapses from **853 actions to 44** while `probe`
(231), `stage1` (68), `moving-learn` (40), `turn-fuel` (26) and `cycle-last` (16) all begin
to fire: the door reads as `locked`, and the patrol planner runs here for the first time.

The price is 179 actions on `cd82` (1,034 → 1,213, no level lost), and narrowing the rule
to shapes drawn on the VOID — the colour that reaches the frame's own edge, on the argument
that a shape on the floor is a thing to walk to while a shape in the void is a sign — is
byte-identical, so whatever `cd82` newly admits is in its void too.

## The indicator cannot produce the door's ask, and there is no second display

With the bare-glyph reader in place, the stitched world holds exactly **two** plates:

    (3-8, 55-59)    ink=12   the indicator, a T that turns a quarter per press
    (28-34, 49-55)  ink=8    the door, #.#/##./.##

and nothing else, over every walk run so far. So the ink mismatch is not a matter of not
having looked hard enough — there is no colour-8 display anywhere that has been seen.

Worse for the obvious reading, the two are **structurally incompatible**: the indicator's
normal form `.#./.#./###` has five cells and the door's `#.#/##./.##` has six, so no
rotation of one is the other and no sequence of quarter turns can produce the ask. Level
6's door B asked for exactly this glyph and its board could produce it, because a
shape-changer there walked an alphabet that contained it; level 7's only changer rotates.

Which leaves three readings, and the session has not separated them:

- a second changer exists further out in the fog, one that does something other than rotate;
- the door plate is not the goal at all, and the refusal measured at (29, 45) is ordinary
  terrain — the interior x28-34 y49-55 is still unmapped, so it may simply be walled from
  above and entered from elsewhere;
- the ink half is not compared on this level.

The cheapest of the three to settle is the second: map the plate's interior by approaching
it from the other sides, which the agent can now do for itself.

### Two things the live run shows that the offline stitch could not

Read from the agent's own `Gate` across a full level-7 run rather than from a hand-driven
probe: `displays` is **1** from early on, so the indicator does work as a display and the
door does read as locked — the machinery is engaged and the blocker is the shape.

Two loose ends came with it, neither yet chased:

- **`movers` is 0 for the whole level.** The patrol tracking never earns a period for the
  patroller at x55-57, so `route_moving` — the planner this board needs — cannot run here
  at all. Whether `track()` is skipping it or the piece simply never gets near enough for
  long enough is unmeasured.
- **Plates with ink 9 and ink 14 appear two or three times.** Colour 9 is the piece's own
  lower half, and the bare-shape reader admits a shape alone against one background — so
  the piece may be reading as a plate at moments when its colour-12 half is off the window.
  A risk the sweep did not catch and nothing yet rules out.

## The thread to pull next: a changer, read

With the window shifted left (piece at (29, 40)) the block at x11-12 y41-43 reads:

    (11,41)=14  (12,41)=14
    (11,42)= 0  (12,42)= 8
    (11,43)=12  (12,43)= 8

Four colours in a block the size of the piece, which is this game's signature for a
changer on every level that has one — and one of those colours is **8**, the ink the level
asks for. It sits at x11, which is exactly the window's left edge from (29, 40), so it may
run further left than this.

Beside it, a small colour-0 object at x20-22 y41-43: colour 0 is what level 6's crosses
are made of, so this board may have a second patroller down here as well as the one at
x55.

Getting to it: `left` from (29, 40) is blocked — row 40 is wall at x24-28 — so the
approach is from above, down the x19 column, which is floor at rows 35-44. What to do
there is the obvious thing: overlap it, and see whether the indicator becomes something
with six cells in it.

## It IS the ink changer, and the game already knows its alphabet

Standing at (9, 40) — the piece's 5x5 covering x9-13 y40-44, which overlaps the block —
the indicator changes **ink**, shape untouched:

    plate (3-8, 55-60)   ink=12   .#./.#./###      before
    plate (3-8, 55-60)   ink=9    .#./.#./###      standing on the block

`hud` agrees: the `12: 6` entry disappears and `9: 6` takes its place. (An earlier probe
reported the glyph as "none" here, which was the probe's own reader looking for colour 12
and finding a colour-9 glyph.)

So level 7 has both halves after all — the patroller at x55 turns the SHAPE a quarter, the
block at x11-12 y41-43 walks the INK — and the ink it walks is the one this game has used
since level 3: `Gate.legacy` already holds `12 -> 9 -> 14 -> 8 -> 12`, so three presses of
this block reach **8**, the ask's own ink, with nothing new to learn.

## And the shape changer walks an ALPHABET

The colour-0 object beside the ink block — x20-22 y41-43, the colour level 6's crosses are
made of — is the other half. Standing at (19, 40), whose 5x5 covers x19-23 y40-44:

    ink=9   .#./.#./###      before
    ink=9   #.#/#.#/###      after

Five cells to seven, so it is not a quarter turn: this one walks an alphabet, exactly as
level 6's cross-1 does. And it is phase-dependent — the first arrival at (19, 40) changed
nothing and the second did — so it is a PATROLLER, like everything else that presses on
these boards.

So level 7 is fully accounted for, and it is the same machine as level 6 with the parts
further apart than one window:

| part | where | what it does |
|---|---|---|
| indicator | x3-8 y55-60, unframed | reports (ink, shape) |
| ink changer | x11-12 y41-43, four colours, static | walks `12 -> 9 -> 14 -> 8 -> 12` |
| shape changer | colour-0 patroller by x20-22 y41-43 | walks a shape alphabet |
| shape changer | colour-0/1 patroller at x55-57 | a quarter turn |
| the ask | colour-8 glyph in a hole at x31-33 y51-53 | `(8, #.#/##./.##)` |

The ink half is free — `Gate.legacy` has carried that alphabet since level 3, so three
presses of the block reach the ask's ink with nothing to learn. The shape half is a walk
along an alphabet the agent already knows how to learn, by the rung that learns level 6's.

## What still stops it: a ghost, and then identity

`movers` reads 0 for the whole level, so `route_moving` — the planner that times a press
against a patrol — never runs. Two things are behind it, and only the first is fixed.

**The stitch was painting ghosts.** Remembering every non-fog cell remembers the moving
ones too, so a patroller that left the window stayed drawn at the last place it was seen,
and the tracker followed a copy of it standing still. Level 7 tracked 25 to 61 objects with
full 48-entry histories and **not one ever earned a period**. The fix is to notice: a cell
that comes back DIFFERENT is not terrain, so it is marked dirty and never painted from
memory again. With it, `withp` goes from 0 to one to three — real, and nowhere near enough.

**The rest is identity.** A patroller here is out of view most of the time, because the
piece roams a world far bigger than its window, and the tracker hands out a NEW id every
time one comes back. `mover_period` needs three laps of one id; `_adopt` can carry a lap
from an old id to a new one, but only once a period has been earned, and none ever is. The
chain is stuck at its first link.

The shape of the fix is a signature rather than an id: on both boards the patrollers are
distinguishable by what they are made of — level 6's are a 9/14/8/0/12 cluster, a four-cell
colour-0 cross and a six-cell colour-0-and-1 cross; level 7's are a colour-0 cross and a
colour-0-and-1 cross. Keying `movers` on (colours, size) instead of the track id would merge
every sighting of one object into one history. It is also a change that touches level 6,
which is where the score is, so it wants a session with room to measure it.

## The press credit never reaches the movers — and the squares already hold it (2026-07-31)

Traced per press with `ARC_CRDBG` (prints, at every display change, each nearby track's
last sighting, period and `mover_at` answer):

- **Shape presses at (19,40)** — 8 in one run (ticks 13, 83, 85, 410, 447, 544, 581, 678).
  The changer's fragments (`(20,41,1,1)`, `(21,42,2,2)`) sit at the SAME box in every
  sighting, so `mover_period` can never earn them a period (a cycle needs >1 distinct
  positions), `mover_at` answers None, and `hist[-1]` is one tick stale at the press
  because the piece covers the object. Credit lands 0 of 8 times. So "it is a patroller"
  in the section above is wrong in its mechanism half: the thing is SPATIALLY STATIC and
  phase-dependent in its RESPONSE — some arrivals change nothing — which is a different
  animal from level 6's walking crosses.
- **Right-patroller press at (54,25)** — track has period 4, but the press phase is
  exactly the occluded one (`mover_at` None), so it is uncredited too.
- **Ink presses at (9,40)** — the block's fragments flicker box SIZE under the footprint's
  edge (1x2 ↔ 1x1), which `mover_period` reads as two positions and earns a GHOST period;
  those were level 7's only three mover credits.

Consequence, measured: `withh=0` in **all 1,302** `no ready movers` refusals — the moving
planner can never plan a press here. But the WALKED presses (18 of 23) all land in
`gate.changers` / `gate.cycles` under their square — (9,40) ink, (19,40) shape — because
both changers are effectively square-pressable. What keeps that idle is the moving rung
swallowing every round: 30+ junk tracks keep `gate.movers` non-empty, so `choose` never
falls through to the square machinery that won levels 2-5. The lever is rung order on
windowed boards, not mover identity.

Fuel, same session: the learn trips DO weave refills now (139 → 383 `moving-learn`,
presses 15 → 23, deaths 31 → 28), and latching the refill colour on the Gate for the
level (`tank_colours`, windowed only) removes the post-death empty-tank windows too —
deaths 22, presses 31, `probe` 627 → 516, every other game unchanged to the digit.

Acting on the rung-order lever (same session): on windowed boards `choose` now stashes
the learn trip, lets the probe rung yield whenever `turns_for` knows a square for a
wrong half, and returns the stashed trip only after every square rung has passed.
Presses 31 → **68**, `stage1` 13 → 276, `turn-walk` 9 → 115, `probe` 516 → 73,
`moving-learn` 475 → 106; deaths 24. Sweep clean — every other game and level identical
to the digit. The square records (`changers`/`cycles`) also SURVIVE a game over, which
wipes `mover_edges` twice a run — the alphabet now accumulates across all three lives.
Still 6/7: what the 68 presses have and have not reached is the next read
(`ARC_L6=... ARC_L6LVL=6` dumps the panel and cycles per round).

## The shape ring is SIX states, closed, and the ask is not in it (2026-07-31, driven)

Hand-driven with `probe7.py` after the rung reorder found the stall (`results/l7-ring.txt`,
prefix + `3,3,2,2,2,2,2,1,2,1,2,4,2,1,4,1,2,...`): pressing the left changer walks

    .#./.#./### -> #.#/#.#/### -> .##/#.#/.#. -> .#./##./.## -> ###/..#/#.# -> ##./.##/#.# -> (closes)

one press per re-entry at (19,40) — and the `##./.##/#.# -> .#./.#./###` edge the agent had
recorded near the start squares is REAL, so the ring closes at six and **the ask
`#.#/##./.##` is not among them**. The ink walk `12 -> 9 -> 14 -> 8` at (9,40) is three
re-entries, exactly as `legacy` says (one press per entry, no phase dependence observed).
The "phase-dependent" reading earlier was press-per-ENTRY: standing still and pressing
again does nothing; every off/on re-entry pressed, in every drive this session.

**The nearest the indicator gets is `##./.##/#.#`, which is the ask rotated 180°** — and
worn with the ask's own ink, the hole still refuses (`results/l7-holetry.txt`: full
choreography ink→8 then shape→`##./.##/#.#` with a mid-sequence refill at (14,45),
arriving (29,45) at action 36 wearing `(8, ##./.##/#.#)`; the `down` does not happen).
Also measured on the way: `(12, ##./.##/#.#)` refused too; from (29,45) `right` is
refused twice (no eastern approach from there); starving out confirms the death
mechanics — lives `8: 16 -> 8`, piece back to (19,15), panel back to `(12, .#./.#./###)`.

**What can still produce the exact ask: composition.** The x55-57 patroller is a quarter-
turn changer (its recorded cycles at (54,30)/(54,10)/(54,15) are the pure rotation orbit),
and two quarter turns are 180° — so `##./.##/#.#` plus TWO presses of the x55 patroller is
`#.#/##./.##` exactly. Untested: the drive needs the (39,40) corridor (reached via the
carry, east of (29,45) is walled), the x55 presses are phase-timed (the earlier 38-action
drive stood on the turning squares and nothing moved), and the ring beside the patroller
(x55-57 y51-53) is the only refill on that side. The route skeleton that works for the
left half — ink, then shape with the (14,45) refill woven mid-walk — is in
`results/l7-holetry.txt` and fits one life with three actions spare.

**Agent gap this exposes:** the square machinery holds the (54,*) squares as rotators
(`gate.rotates`), but their cycles only contain the five-cell T orbit that was walked —
`path_for` cannot extrapolate a quarter turn to a value it has never seen there, so no
square plan can compose ring + rotation to reach the ask. Extending rotator squares to
answer `turned()` on ANY value (the way `_mover_step` already does for movers) is the
cheapest route to making the composition plannable.

## SOLVED: the level falls to ink + ring + two quarter turns (2026-07-31)

`results/l7-solution.txt` is a 71-action line from the level-7 start that completes the
level (`results/l7-solve.txt`, final line `lvl=7`); replay it with

    uv run python probe7.py ls20 results/prefix-l7.txt "$(cat results/l7-solution.txt)"

The composition hypothesis held exactly: the ask `(8, #.#/##./.##)` is the ring state
`##./.##/#.#` plus TWO quarter turns of the x55-57 patroller, and the door is the hole at
x28-34 y49-55, entered from the north — `down` from (29,45), which had refused every
wrong panel, simply happens when the panel is right.

The line, by phase (every segment verified in isolation first):

| acts | what | detail |
|---|---|---|
| 1-11 | ink `12→9→14→8` | three re-entries of (9,40) via the x9 column |
| 12-23 | shape ring ×5 to `##./.##/#.#` | re-entries of (19,40); **refill (14,45) woven in at act 19** — the ring walk does not fit one life |
| 24-40 | north loop to the TOP RING | (9,25)→(9,15)→(19,15)→(19,5)→(29,5)→(29,10)→(34,10)→(39,10)→**(39,5) refill at act 40, the last action of that life** |
| 41-48 | carry to the east corridor | (34,20) `right` CARRIES to (39,40); row 40 east to (54,40) |
| 49-53 | **chase-press ×2** | climb x54; the patroller walks DOWN its lap as the piece steps down after it, so overlap repeats every tick — press at act 52 (`#.#/.##/##.`) and act 53 = **the ask**. A third press is one more step: escape SIDEWAYS at once |
| 54-59 | side-step and descend x49 | (49,25)→(49,45); x49 never overlaps the x55-57 patroller, so the ask survives |
| 60-62 | EAST RING | (49,50)→`right` picks up x55-57 y51-53 at act 60 |
| 63-67 | carry home | back to (39,40), then (39,35) `up` CARRIES to (29,30) |
| 68-71 | enter | x29 column down; `down` from (29,45) **completes the level** |

Three refills, two carries, zero deaths. What the earlier failures taught, condensed:

- **A press is footprint overlap after the move, and a chase presses every tick.** The
  climb presses nothing when the patroller is elsewhere on its lap (measured twice);
  arriving so that the patroller walks INTO the footprint as the piece follows it down
  gives three consecutive presses — count them and step OFF the column (x49) the moment
  the panel is right. The patroller's lap is y12↔32 bounce, period 8, read live by
  scanning x54-58 for colours 0/1 (`pat=` in probe7).
- **The refills are the choreography's skeleton**: (14,45) mid-ring, (39,5) reached on a
  life's last action, (55-57,51-53) after the quarters. None is optional; east of
  (29,45), south of (39,10)/x19's gap, and west of row 50's x44 block are all walled,
  which is why the route is the loop it is.
- Both `(12, ##./.##/#.#)` and `(8, ##./.##/#.#)` refused at (29,45) — the check is the
  exact pair, ink AND shape.

**What the agent still cannot do** (`compete.py` plays this level to 6/7): compose the
two machineries. ~~The square order search cannot extrapolate a rotator to values it has
not seen~~ — wrong on reading the code: `_step`/`_edges` already extrapolate any rotator
to any value, and `path_for` searches across squares. The real walls were found by
building the composition and watching where each run died (same session, later):

1. `route_moving` knew nothing of square presses — folded in (windowed only), with the
   hole enterable as a checked gate (its void interior never passed `footprints_touching`'s
   walkable filter, so it could not be a goal) and the no-ready-movers guard relaxed when
   squares exist (1,198 rounds died there with halves on period-less churned ids).
2. Press credit: an age-1 sighting, one step inflated, credits the covered patroller
   (ungated this cost level 6 fifty actions; gated on windowed it is clean).
3. Trip marks tolerate an invisible display (all displays under `raw5` fog) so an east
   leg can run open-loop; position checks still validate every step.
4. The square rungs churned the CLOSED ring forever — `moving-learn` now jumps them when
   ANY wrong half is `exhausted`, and ahead of it a `fog-explore` rung walks to the
   nearest never-stood fog-bordering position (the unexplored set IS the fog).

After all four, measured per full run: fog-explore 346-514 actions, presses still all
west, east-of-x44 coverage 22 actions, `(54,*)` never learned in-run. **The binding wall
is the (34,20) carry** — the only entrance to the east half, a +5,+20 warp `slides`
cannot hypothesise from any marker, so no route can aim east before the carry is walked
once by luck. Next: deliberate frontier pokes (press the unexplored direction where the
routable map dead-ends), then the x55 period from `track` once the east is routine —
the plan machinery past that point is already in place.

## The union garble, caught in the act and fixed (2026-08-01)

The KNOWN GAP at the stitch site is closed, and the three byte-identical suppressor
runs are explained. Instrumented (`ARC_UGDBG`: per-frame paint-back cells inside the
window + every plate change with old → new), then reproduced offline
(`results/ug-repro.txt`, prefix + the solution's first 23 actions with the agent's
stitch running alongside): during ink/ring presses at (9,40)/(19,40) the RAW indicator
is clean while the COMPOSITE wears the union of its states — the off-pixels of the
previous glyph are painted back from memory **in the same frame the press changes the
rest**, with the box fully in view. The "late report on re-entering reading range"
hypothesis pointed at ticks that never coincide with the garble, which is why every
suppressor built on it executed zero times.

The fix is one rule in `stitch`, scoped tight: for boxes in `gate.displays` that sit
fully inside the window, record their colour-5 cells as KNOWN 5 — an off-pixel is
state, and painting 5 into 5 is a no-op forever. Nothing else moves: `dirty` is not
touched (the whole-window dirty repair is what made patroller tracks permanent fog
holes), memory outside the boxes is untouched.

Two measured traps on the way:

- **Scoping to `icons | displays` flickers.** The door's ask-picture (x29-34 y49-55)
  is STATIC; its right pixel (32,53) is visible from (19,40) (dx=13) and fogged from
  (14,40) (dx=18) — the window is wall-clipped, so the ±18/+21 geometric test
  overestimates visibility and no fixed margin fixes it. Recording those fogged
  pixels as OFF made the box's reading follow the piece — 85 phantom edges
  (`#.#/##./.##` ↔ `#.#/##./.#.`) under (14,40)/(14,45)/(19,35) in one run. A static
  plate is exactly what the old paint-back was silently stabilising; only a box that
  has actually changed has off-pixels worth recording.
- The first-press hole does not exist: a changer changes its **ink before its shape**
  (the ink walk starts every choreography), so the box is in `displays` before the
  first shape transition can leave a union pixel behind.

Measured on the full run (`results/ug-run3.txt` vs `ug-run1.txt`, all four games
sweep-clean and identical, `results/sweep-ugfix.log`): junk shape-edges 85 → **0**
(every change event now at (9,40)/(19,40), every after-value a real ring state),
`desperate` 113 → **0**, `cand` 182 → 55, level-7 deaths 22 → **11**. The shape ring
assembles CLEAN in-run for the first time: 4 of 6 edges, no phantoms mixed in.

**What still stops 7/7** — the panel parks on `#.#/#.#/###`, which has no outgoing
edge in `cycles`, and nothing presses (19,40) again for ~800 ticks (presses at ticks
13/83-89, then 917/999 repeating the first edge after deaths reset the panel). The
missing edges are exactly `#.#/#.#/### → .##/#.#/.#. → .#./##./.##`. The wall is now
the planner's: from a state with no outgoing edge, `path_for` is blind and whatever
round-owner follows (heading 280 / turn-walk 298 in the accounting) never spends two
re-entries on the known changer to learn the rest of the ring.

## The ring press is every-second-MOVE, not every re-entry (2026-08-01, driven)

`results/l7-hashpress.txt`: prefix → ink column → (14,40) → (19,40), then oscillate
(19,35)↔(19,40) with plain `1,2` pairs. The display advances one ring state per TWO
piece-moves for as long as the oscillation continues — including on the step-OFF move
(the glyph changes while the piece stands at (19,35), which no footprint-overlap or
entry model predicts) — and it never no-ops: 21 actions walked the full six-state ring
and kept going. Two consequences:

- **"Press per re-entry" is the wrong model for this changer.** The response is gated
  on a period-2 clock, and a single bounce that lands on the wrong tick of it changes
  nothing. That is exactly what the agent measures: its one `cycle-on-turn` bounce at
  the parked state no-oped (`chg=0`), it ceded the round (to `near-fuel` at `left=6`,
  legitimately), and the changer was never bounced twice in a row — while a walk that
  merely passes through the square (`cand` at i=984→986) presses it and skips a state
  past every reader. One more bounce after a no-op is all the probe needed, ever.
- The intermediate state `.##/#.#/.#.` is real but worn briefly between reads on
  walk-through presses, which is why the agent's cycles hold 4 of 6 edges with the
  two edges out of `#.#/#.#/###` and `.##/#.#/.#.` never booked.

## The fold family: every way a stale reading poisons a booked edge (2026-08-01)

Fixing the union garble exposed a family of subtler bookings, each found by the same
loop (instrumented run → wrong entry in `cycles` → mechanism → guard → re-measure).
All landed, all sweeps clean:

1. **Death fold.** The panel reset of a death, read late, booked `#.#/#.#/### ->
   .#./.#./###` under the ink square — a phantom that closed the ring graph two real
   edges short, so the closed-graph `exhausted` (itself fixed this session to demand
   every seen state have an outgoing edge) declared the shape half done. Tick-age
   guards have an equality hole — a death on a blocked action leaves `ticks` flat —
   so the guard is life-scoped: `gate._fresh` (boxes read fresh since the last death,
   cleared at both death sites) must contain the box.
2. **Walk-through fold.** A press made where the display is unreadable surfaces
   squares later; two presses in the gap booked as one edge (`#.#/#.#/### ->
   .#./##./.##`, the `.##` state worn unread in between) — closed the graph again,
   minus a whole state, and `fog-explore` inherited the level (487 actions). Age-1
   booking rejects these but also rejects every bounce whose off-square is a
   wall-clipped blind spot — measured at 2 booked edges over ~80 bounces, the ring's
   knowledge thrown away wholesale. The correct discriminator: **count ARRIVALS of
   the pressed square since the display's last fresh reading** — one arrival is one
   press however stale the reading (this is also the only channel the x54 rotators
   can ever be learned through), two arrivals are a fold. `_arrivals`/`_foldsafe`,
   windowed-gated.
3. **Wall-clip blindness.** A display `plates` cannot read from a position the
   ±18/+21 geometry calls readable fell out of `icons` entirely, emptying `state()`
   and pruning `displays` — 354 of 355 planning rounds ran blind and `cand` owned
   the level. A display on a windowed board never stops existing: unreadable keeps
   its last reading (like a plate under the piece). One run later, state=[] rounds:
   1 of 290.

Where this leaves level 7: `cycles` are finally CLEAN — four true ring edges under
(19,40), the ink cycle under (9,40), correct halves, zero junk — but the ring still
does not close in-run. The missing edges are the two out of `#.#/#.#/###` and
`.##/#.#/.#.`; the probe proves a persistent bounce session books them (one state
per two moves, no no-ops), and `cycle-on-turn` now commits three bounces when a
wrong half is unplannable-but-open, but the fuel rungs (`turn-fuel` 295 /
`near-fuel` 248 in the last run) own the rounds a bounce session needs. The wall is
round-ownership economics: a bounce session costs ~12 actions plus the (14,45)
refill, a life is 21, and nothing prices "two more bounces close the ring" against
"top up first". Deaths run 16-23 a run against the hand solution's zero.

First economics finding (same day, kept — sweep clean): `refuel()` chose its refill
off `cands`, the rarity shortlist that cuts refills ("a refill is rarely rare" —
`stage`'s fuel had the widening for years, `refuel` never did), so `turn-fuel`
walked the piece between whichever far northern rings survived the ranking:
**twenty consecutive lives** ran the exact loop `stage1(4) → near-fuel(10) →
turn-fuel(14) → cand(13) → desperate(2) → death` — the whole life spent walking to
fuel, dying at (9,40) with `left=1`, zero presses. Widened to every refill seen,
the 44-action loop is gone (deaths 23 → 20) but the level still does not fall: the
late game now thrashes `stage1`/`wander` in single-action alternation — a plan is
issued and dropped every other action. That thrash is the next thing to read
(`results/ug-acct12.jsonl`, `l7-gate9.jsonl`, a=1950 onward).

One hypothesis about the thrash already measured OUT: the refill rings do read as
marked plates (a donut of colour 11 wearing `###/#.#/###`, `locked=True` in the
gate log) and "stage is aiming at a ring-door" fit the northern oscillation — but
filtering tank-colour objects out of `locked` was **byte-identical over a full
run**, so the rings sit behind the real door in the list and nothing ever aimed at
them; the filter was reverted as inert. The plan-drop log (`ARC_PDBG`) then showed
the decisive negative: **zero drops in the thrash region** — the plans were not
being dropped, they were SHORT, completing normally. stage was aiming 2-3-action
fuel hops at rings **already eaten this life**: the rings respawn with the next
life (turn-fuel picked the same northern ring up on twenty consecutive lives), but
within one they are spent, and nothing knew that — the piece bounced between two
spent rings until the clock ran out. Fixed with `gate.spent` (pickup positions,
recorded when the clock rises on an ordinary walked step, cleared at both death
sites, windowed-gated) excluded from `refuel`'s pool and `stage`'s fuel list.
Measured: the thrash pattern is gone (long `stage1` runs return), deaths 20 → 19,
chg 36 → 52, `turn-fuel` 176 → 121, `desperate` 93 → 52, `stage2` reappears (15
actions). Sweep clean, all four games identical. Still 6/7 — the ring's last two
edges remain unbooked in-run.

A second hypothesis also measured OUT after that: "the bounce's off-square is a
wall-clipped blind spot, so its presses surface as folds" — teaching `cycle` to
avoid positions where a display failed to read while geometrically visible was
**byte-identical**, because no such position ever registered: the indicator box is
readable from (14,40); the wall-clip flicker belonged to the DOOR's box. Reverted.
The `_foldsafe` refusal log (`ARC_FDBG`) then named the channel — 15 refusals in a
full run tell the whole story:

- **Six of the refusals are deaths wearing `#.#/#.#/###`** (`NOT-FRESH-THIS-LIFE`,
  old `#.#`, new the post-death `.#./.#./###`). The sequencing puts shape presses at
  the tail of a life, and the life ends there.
- **The `#.#` press is NOT dead — it fires on walk-throughs** (tick 21: gap
  `(19,40),(14,40),(9,40),(14,40),(19,40)`, old `#.#`, both missing edges consumed
  inside one 2-arrival gap; tick 512 same). The fold guard refuses these correctly:
  two presses, the `.##` state worn unread between.
- **The bounce at `#.#` no-ops while the walk-through fires**, and the lattice
  explains it: the response is phase-gated (the x55 patroller runs period 8, frozen
  on refused presses), and a 4-connected lattice is bipartite — every closed walk
  has even length, so a bounce session samples only `p, p+2, p+4, p+6` of the
  phases and a session born on the wrong parity no-ops until it gives up
  (`cycled` hands off after two tries). What breaks the parity is a CARRY — the
  piece displaces five cells in one tick — which is exactly what a walk-through
  route via the redirects does and a bounce cannot.

Ranked levers for next session: (a) after two no-op bounces at a no-outgoing
state, plan the next re-entry THROUGH a known carry (odd effective displacement —
changes the phase-position relationship the bounce is stuck in); (b) make the
shape press the life's FIRST errand while fuel is full, not its last (six deaths
wear `#.#`); (c) NOT inference-booking of unique 2-paths — the `.##` state has
never been observed and the repo does not book what was not seen.

## Lever (b) landed — and the "six-state closed ring" model is WRONG (2026-08-02)

`changer_for` now prefers the BLIND half on windowed boards (the plannable half
can be fixed any time; insertion order used to hand every life to the ink square
first). Sweep clean, all four games identical. The run it produced
(`results/ug-run19.txt`, `l7-gate13.jsonl`) booked **8 shape edges under (19,40)**
— the 4 known ring edges plus a chain of four states never seen in any prior run
or hand drive:

    .#./###/#.. -> #.#/..#/### -> #.#/.##/##. -> #../###/#.. -> ###/#../###

Two facts about that chain: `.#./###/#..` is EXACTLY the clockwise quarter turn
of the ring state `.#./##./.##` (verified cell by cell), and `#.#/.##/##.` is
**the ask minus one quarter** — the state the hand solution wore at act 52, one
x55 press before the door opened. So the (19,40) changer's response is
phase-dependent between two DIFFERENT acts: some presses STEP the six-state ring,
others TURN the glyph a quarter — the "ring closes at six and the ask is not in
it" conclusion was sampling only the step half. The shape graph is the ring x
rotation composite, the ask (`#.#/##./.##` = 180 deg of `##./.##/#.#`) lives in
the turned family, and **the (19,40) square alone may reach it** — no x55 chase,
no (54,*) rotators. What is still missing: no edge INTO the ask is booked yet,
and no edge out of `###/#../###` or `#.#/#.#/###`; `path_for` needs one of the
remaining edges to plan the last hop. The level is still 6/7 (deaths 19, fuel
rungs 455 of 1,154 actions) — but for the first time the ask is reachable in the
booked graph's own terms, two or three unexplored presses away.

## The family mechanics, pinned by three experiments (2026-08-02)

- **A death does NOT turn the panel** — probed directly (`results/l7-deathturn.txt`:
  press shape once to `#.#/#.#/###`, then starve through two deaths on a
  non-pressing oscillation): the glyph resets to `.#./.#./###` at each death and
  never wears a turned state. The death-turn hypothesis is dead; the turned
  families in agent runs enter ONLY on lives that reach x54 (the two lives with
  maxX=54 are exactly the two lives with 90-degree-family states) — the x55
  patroller's chase press, taken by accident on east excursions.
- **The step law COMMUTES with rotation, verified 4/4**: the four booked
  90-degree-family edges are exactly the k=1 conjugates of the four booked ring
  edges. `_edges` now admits, for every booked shape edge, its three conjugates as
  PLANNABLE edges (windowed-gated; same epistemic class as `turned()`'s orbit
  filling — a law verified on overlap, refutable at execution). Two conjugates
  point INTO the ask. Sweep clean. It cannot alone produce the ask: steps stay
  within a family, and the panel only changes family via a quarter-turner.
- **The late quarter-turn mover credit measured INERT** (reverted): a chase press
  out of view never surfaces as a pure quarter — it composites with the ring
  steps taken before the display is next read, so `turned(old, new)` never
  matches and the credit condition cannot fire. Crediting the x55 mover's half
  from surfaced reports is structurally impossible; the half has to be earned
  IN VIEW (level 6 earned it because the display sat beside the corridor) or
  assumed by the learn planner.

**Where the composition stands**: plannable within-family movement (conjugates) +
open-loop trip tolerance (raw5 trip marks) + fuel weaving + spent-ring hygiene are
all in place. The single missing primitive is a DELIBERATE quarter: a moving-learn
trip east that presses the x55 patroller ONCE (chase one tick, side-step to x49
immediately — the hand solution's own recipe for stopping at a count), timed so
the panel worn at departure is `##./.##/#.#` (ring, plannable) and two such trips
bracket a walk to (29,45). Alternatively the x54 squares, if they can ever be
booked in view. That executor — a chase leg with a press budget — is the one
piece of machinery the level still lacks.

Two more attempts at the credit, both measured and reverted (2026-08-03): the
family-delta decomposition (new = rot^k(step^m(old)), order-independent because
the step law commutes with rotation — book the unique overlapping mover as a
rotator when k is unique and positive) is implemented-and-proven logic, but it
fired ZERO times: **the current deterministic trajectory never chases at all** —
no level-7 family shift happens in it (the 90-degree states in this run's [ug]
log are all LEVEL 6, same alphabet, x49 positions), and even the (34,20) east
carry is unlearned in this trajectory (`redirects` = {(34,30),(39,30),(39,20)}).
The family shifts of earlier runs came from a different trajectory (pre
bfs-avoid). So the dependency chain for 7/7 is now exact:

    east discovery (fog-poke reaches (34,20) carry)
    -> x55 track exists (piece sees the patroller)
    -> mute-patroller learn trip goes east and chases
    -> family-delta credit books the rotator      [logic written, reverted, in git history]
    -> route_moving composes ring + two quarters   [conjugates + offline proof in place]
    -> door matched, (29,45) down.

Every arrow past the first is built or proven; the first is a determinism
problem — WHICH frontier fog-poke explores, in what order, decides whether the
east half exists in a given run. That is the next session's single target.

## Three levers measured byte-identical in one night (2026-08-03) — and a probe
## contradiction that outranks all of them

1. **Stuck-yield** (`exhausted OR tried>=2` on the frontier gate): zero change.
2. **Six-bounce sessions** and **phase-slip wall-press** in the blind branch:
   zero change — the block action was always None (`refused` expires on display
   changes mid-session; `tried`-minus-`sure` has no entry at (19,40) either).
3. **Family-delta v2** (patroller = >=3 distinct hist boxes): zero fires — the
   decomposition dead-ends because `#.#/#.#/###` has no step edge, and its whole
   CONJUGACY CLASS is unbooked (`###/#../###` is its own rotation): the one
   missing edge blocks every algebraic path that could infer around it.

The contradiction to resolve FIRST next session: `results/l7-hashpress.txt`
walked the whole ring including `#.# -> .##` with plain 1,2 bounces (changes at
ticks 9 AND 10 — both parities pressed), while the agent's five consecutive
bounces at the same square change nothing. Same square, same 2-cycle, same
spawn-parity (every path (19,15)->(19,40) is 5 lattice steps, odd). Whatever
separates them is none of: entry-vs-exit, lattice parity, session length. It IS
one of: the x55 patroller's mod-8 phase (shifted arbitrarily by the agent's
refusal history — a refused press freezes the patroller), or some panel/level
state the probe run carried that the agent's mid-run state does not (the probe
pressed at ink=9; the agent parks at ink=8/12/14 — the hand solution's ring walk
at ink=8 worked, so ink alone is not it). The decisive experiment is cheap and
scripted: replay the prefix, take a KNOWN number of refused presses to shift the
patroller phase k ticks for k=0..7, then bounce at `#.#` and record which k
press — one probe7 line per k, eight runs, the law falls out.

## The parity law CONFIRMED in-agent, and the quarter-trip executor (2026-08-03)

The law, final form, all measured: **pressing (19,40) from a `#.#`-class state
fires only on an even patroller phase**; every walked arrival carries odd
moves-since-death (bipartite lattice, death resets the lap); the flip is a carry
of odd total displacement — and the stored redirect offset is measured from the
AIM cell, so total displacement = one step + offset: **an odd carry is one whose
stored offset is EVEN**, which every confirmed redirect on this board is. The
parity-walk rung (parked-class trigger: panel value seen-as-TO with no outgoing
edge; walk into an odd carry, refuel toward one if needed) unlocked it: the ring
walks FULL CIRCLE in-run for the first time — `#.#` pressed 28 times, chg 52 →
156, sweep clean.

The quarter-trip executor (panel k quarters from the ask → walk into the x55
patroller's lap so footprint overlap presses quarters) took eleven measured
iterations to aim true — each wrong target was a real lesson: piece fragments
pass a distinct-box filter; death-churned tracks pass a span filter; the piece's
own column-pacing ghost passes a linearity filter (kill it with `stood`); cells
across the invisible x19 wall are "un-stood" for the wrong reason; lap targets
must sit on the PIECE's lattice (x ≡ 4 mod 5 here, not 0); and its bfs needs
`avoid=refused` like every east-going route. With all six fixed, `gate.lapmem`
holds exactly the true lap ((55,11),(55,21)) and the trips CLIMB x54 through the
patroller's track in both directions — but in the last twenty actions of the
budget: the loop (trip → return west → read panel → re-ring → repeat) never got
a full cycle. Two known gaps for next session: the RETURN leg is unplanned (a
death after the trip resets the shape and wastes the quarters — the east-side
refill ring at (55-57,51-53) is the hand solution's answer), and the trip should
be admissible earlier in the run (lapmem fills at the first east sighting;
everything after that is eligible).

## The quarter loop, assembled end to end (2026-08-04) — and the last two walls

Built and swept clean this arc: `quarter-trip` (panel k quarters from the ask →
walk into the lap; bootstrap to the FARTHEST carry landing when lapmem is empty;
persistent walls from tried-minus-sure in its routes), `quarter-home` (gated on
`gate.qt_out`, latched only by a real outbound leg, cleared when a display is
readable again), `ask_q` over EVERY locked target, VIRTUAL ROTATORS (the x54
lap-overlap squares seeded into `gate.rotates` — `path_for` composes ring +
quarters, stage1 285 → 368 and STAGE owns the fuel weaving), and the axis-chase
trip tail that first SIGHTS the east refill ring into the tank.

Measured state: round trips run, all 17 deaths are WEST (ring work) — trips do
not die east — and the read panel has still never worn a turned state. The two
walls left, in order:

1. **Phase at the lap.** Entries at (54,y) press only when the patroller
   overlaps after the move; stage plans entry counts, not timings, and blind
   phase-sampling across 1-2 trips a run hits nothing. The machinery that can
   time it exists — route_moving's phase-counting BFS — and needs the mover's
   halves; seeding them via the same virtual law (this session's last edit) did
   not execute because the x55 track is only ALIVE during a trip and the seeding
   runs west at ask_q time. Seed at TRIP TIME (when the track is live), or
   persist the track's phase map the way lapmem persists its boxes.
2. **Trip cadence.** One or two trips a run cannot sample eight phases. The
   ask_q trigger fires only on ask-orbit panel states; with ring+rotator
   composition any panel state is reachable, so the trigger can widen to
   "shape wrong AND lapmem known AND affordable" once the phase timing exists.

Everything else — fuel, walls, return, reading, composition — is in place.

## The chase saga (2026-08-04) — reactive interception is RIGHT, its trigger is wrong

Assembled this arc, each step measured: trip-time mover seeding (halves + one
quarter edge on tracks overlapping the lap — west-side seeding is inert because
the track only lives east), rotator squares folded into `route_moving`'s press
set (the x54 virtuals lived in `rotates` alone; 1,680 "bfs exhausted" refusals
fell to plans — the `moving` rung went 0 → 188 actions and the agent reached
(29,45) twelve times a run, always wearing an unturned panel), the fuel-long
axis-chase tail, lapmem line-hygiene (the largest collinear cluster only — the
chase was measured following a ring flicker at (50,6) west while the patroller
paced x55), and a REACTIVE CHASE rung with live overlap counting in the play
loop (`qt_need`/`qt_hits` — the phase is unknowable from the west within a
life, so the press must be counted at execution, not planned).

Where it stands: x55-region tracks now carry halves and some carry PERIODS
(p=10 measured live); `moving` plans traverse (54,25)→(54,35) four times a run;
the chase steps correctly along Y once its inputs are clean — and its TRIGGER
is wired to `gate.qt_out`, which only the quarter-trip rung sets, while the
actual east traversals belong to the `moving` rung: [ch] fired 11 times chasing
junk, then 0 after the on-line gate. The redesign for a fresh session, one
sentence: **the chase is an INTERCEPTOR — it should key on (piece on the lap
line) AND (fresh lap track) AND (shape half wrong), regardless of which rung
brought the piece there, and the overlap counter should run under the same
condition.** Everything upstream of that trigger — plans that reach the column,
fuel to survive there, the lap's identity, the press law, the return leg, the
door walk — is measured working. Also note for the trap list: the TRAJECTORY IS
ENV-DEPENDENT — a run with ARC_RMDBG+ARC_L6 diverges from one without (run69 vs
run70: chase 10 vs 0) — so iterate with ONE fixed env set and never compare
across sets.

## The interceptor closes the loop — and the BUDGET becomes the last wall (2026-08-04)

The chase saga's ending, each step measured in one afternoon: the play-loop
INTERCEPTOR (unpaid quarters + on the lap line + live track drops the running
plan, so the chase rung gets rounds a multi-action plan used to hold), lap-SPAN
filters (the chase was measured following the east refill ring's flicker at
(55,51) — same column, wrong end), column-first steering (a whole chase ridden
at x49 against a lap at x55-57 — the footprint spans +4, overlap needs x54),
LEAD-the-target (at equal speeds a follow never closes; aim two ticks ahead
along the patroller's own velocity — the hand recipe), the occlusion-aware hit
counter (an overlap COVERS the patroller, so the sighting that would prove the
hit is exactly the one perception loses — project the last sighting forward),
and LIVE validation of the demand (a standing quarter-demand paid itself at the
wrong panel — rot^2 of `#.#/#.#/###` instead of the ask's own family).

The result, in one run's tail: panel `(8, ##./.##/#.#)` — the ask minus two
quarters, ink right — rides the (34,20) carry east at a=1925, the chase pays
two overlap-hits at a=1935/1942 following the live patroller down x54, the
piece walks home and presses the door at (29,45)... and `down` is REFUSED,
twice, at a=1959 and a=1994 — with the budget dying at 2,000 before any west
read could tell whether the two counted hits were two real quarters. The whole
hand choreography now EXECUTES; what is not yet true is (a) the hit counter's
fidelity (a projected-box overlap is a count, not a confirmed press — the door
judged the ENGINE's panel and said no) and (b) the CLOCK: the full sequence
first aligns around a=1900 of 2,000. Next session, two targets in order:
**start the loop earlier** (the ring is drivable from ~a900; lapmem needs one
east sighting — make the far-stone bootstrap trip fire in the first half), and
**verify the press count by reading between chase and door** (route the home
leg through a panel-readable cell before allowing the door walk).

## Early bootstrap + colour truth (2026-08-04, later) — the record run

Two changes, swept clean, and the run transformed: the bootstrap sighting trip
fires on any shape-wrong round while the lap is unknown (first trip a=1894 →
**a=857**), and tracks now carry their COLOUR (`gate.track` stores it; the lap
filter rejects tank colours — ring flickers — and the piece's own body colours
— fragments). `lapmem` came out PURE for the first time: exactly (55,17), the
patroller and nothing else. Deaths **25 → 8** (2 silent + 6 game-overs), chg
127, the calmest level-7 run ever recorded. The chase went silent again for a
knowable reason: with ONE box in lapmem the span filters collapse to a
zero-width window and reject every fresh track. Next single edit: when
`len(lapmem) < 3`, widen the span window to box ±15 along the axis implied by
the track's own velocity — then the chase, the pay, the home-read and the door
run on the clean lap from a=900 with eleven hundred actions to spare.

The wide-span edit for the single-box lap then measured byte-identical
(reverted): the chase block never runs in the new calm trajectory at all,
because its live-validated demand needs the panel at a `##./.##/#.#`-class
state WHILE the piece is east with the track fresh — and the early-bootstrap
trips go east at any shape-wrong moment, when the panel is usually elsewhere.
The final composition step, for a fresh session: **sequence the trip** — drive
the ring to the state whose orbit contains the ask (`X`: scan `step^m(cv)`
through the conjugate table for the state with `ask in turned(X)`) BEFORE
departing east; the ask_q-gated trips already encode this implicitly but fire
only on chance coincidences of panel, fuel and affordability. Wire `X` as the
ring target ahead of the trip leg and every piece of the machine — bootstrap,
lap, chase, pay, home-read, door — is already measured working on its own.

Fourth lever, same night, same verdict — **parity-walk** (walk into a known carry
to flip the piece/patroller parity, then re-bounce): the parked-class trigger
works (it fired — and crashed on `rules`' mixed key shapes, since fixed: `rules`
merges cell-keyed `redirects` with `(square, action)`-keyed `button`), but with
cell keys only it never fires again because **every known carry lies on the
northern loop**: the leg from (19,40) is 15+ actions before the 6-action return,
over a 21-action life — the affordability guard is unpassable without weaving a
refill into the trip. The parity-flip walk has to be a STAGE-class plan (legs +
refills), not a single bfs leg; that executor is the concrete next build, and the
parity law itself is still the best-supported explanation of the `#.#`-class
no-op (it explains hashpress-vs-agent, survives the mod-8 and bipartite
arguments, and nothing has refuted it).

Three more measurements from the same run's tail, for next session:

- The five-press streak at a=1799-1807 walked the 90-degree family `.#./###/#..
  -> #.#/..#/### -> #.#/.##/##. -> #../###/#.. -> ###/#../###` on consecutive
  bounces — no no-op — straight THROUGH the ask-minus-one state. Entry into the
  turned family coincides with deaths (panel `#.#/#.#/###` before a death, a
  turned state after): if a death turns the panel a quarter, the NEXT death lands
  in the 180-degree family, where the ask itself lives, one step-walk away.
- After a=1807 the panel parked on `###/#../###` for the last **193 actions with
  zero presses**. The bounce-persistence lever (5x + `tried` reset in the blind
  branch) was measured byte-identical — the branch never runs, because
  `cycle-on-turn` requires the piece to BE at (19,40) at plan time and it never
  arrives again: `turn-walk` spent 60 actions walking toward the changer without
  arriving (plus `wander` 61, `stage2` 45). WHY turn-walk fails to arrive in the
  endgame is the sharpest open question — trail-blocking, a fuel guard at
  arrival, or the leg being re-planned every round.
- A refused press freezes the x55 patroller, so every no-op bounce slips the
  phase one tick — parity is not a permanent trap; persistence at the changer
  would sample all phases within a period. The lever is sound; the round
  ownership to APPLY it is what is missing.

## The endgame park was an INVISIBLE WALL the router could not learn (2026-08-02)

Re-running the plan-drop log in the current equilibrium (the earlier "zero drops"
claim came from a run before blind-half-first — a stored conclusion expired):
all 58 endgame drops were `expect: here=(19,15) wanted=(19,20)` — the leg's FIRST
step, refused by the engine **fifty times in a row** while the frame shows floor
there. The x19 gap south of the respawn is an unmarked wall: `refused` was being
fed on every blocked step (compete:1457) and expiring on display changes, but
**no route ever consumed it** — `bfs` had no notion of it, so every turn-walk leg
was re-planned straight back through the square that had just refused.

`bfs` now takes `avoid` (a refused square is not walked THROUGH; it may still be
a GOAL, because a press at a door aims at a square that refuses), and the
turn-walk leg passes `refused`. Sweep clean. Measured: (19,20)-drops 58 → 6,
deaths 16, chg 37 → 52, `wander` 109 → 47, and the drop frontier MOVED — the new
refusals are at (24,15), (19,45), (19,30), (14,30): the router is discovering the
southern wall map one refusal at a time and walking deeper each life. Still 6/7.
Extending `avoid` into `routed()` — every walk route — looked like the obvious
next step and **loses cd82 its only level** (0/6): that level needs routes into
squares that refused BEFORE any display exists, and with no display the refusal
never expires, so the avoidance walls the level off — the same measurement that
killed "remember which target refused and stop walking to it" for m0r0, in a new
place. Reverted; the sweep restores. The turn-walk leg keeps `avoid` because that
rung only runs when something is `locked`, which requires a display, which is the
expiry working. On ls20 the reverted version had measured chg 74 (best ever) and
136 actions of `cycle-last` bounce sessions — those numbers went WITH the broken
cd82 and do not survive the revert. The stage-leg extension remains untried and
must carry the same display-exists guard if it is ever tried.

## Also measured, not yet explained

- **A carrying cell.** From (34, 20) a single `right` moved the piece to (39, 40) — five
  right and twenty down. Level 4's mechanic, on a board where the map is partial.
- **`hud` colour 8 is the LIVES counter** — answered, four cells a life. Starved three
  times on purpose (70 blocked presses, `results/l7-lives.txt`): `8: 12` at the start,
  `8: 8` after 22 actions, `8: 4` after 44, GAME OVER at 66, and `8: 12` again after the
  reset. It reads 12 at the start of levels 2, 4, 6 and 7, so it belongs to the game.
  A life is 22 actions; the third death is a game over, which also clears the patrol
  model and the alphabet.
- **The colour-1 object at y19** is not a marker but a horizontal BAR that extends as the
  window moves right: x39-40 at the start, x39-43 from (29, 5), 16 cells from (34, 15).
  It sits in a one-row gap between floor (x34-38) and wall (x44-46), so a 5x5 footprint
  cannot stand on it from any position tried.
- The big colour-12 L/boot glyph at x3-8 y55-60 is static in every frame and straddles
  the HUD line (14 cells in the play area, 6 counted in `hud`).
