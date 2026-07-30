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
was seen at, and treat colour 5 as *unknown* rather than as wall. That is a change to
perception rather than to the gate, and it has to be gated on something this level has
and the others do not (the colour-5 region changing as the piece moves), because on
levels 1-6 colour 5 IS the border.

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
