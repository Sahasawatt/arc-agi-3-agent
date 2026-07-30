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

**The plate IS the lock, and it refuses.** Driven into it — `3,3,2,2,4,4,4,4,2,2,2,2`
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
