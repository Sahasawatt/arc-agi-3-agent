# Generalisation probe — do the solver's assumptions hold?

25 games probed, 200 actions spent.

| game | tags | levels | verdict | step | dirs | why |
|---|---|---|---|---|---|---|
| ar25 | keyboard_click | 8 | **MAZE_LIKE** | 3 | 4 | grid-stepped by 3, 4 directions, terrain separable |
| cn04 | keyboard_click | 6 | **MAZE_LIKE** | 3 | 5 | grid-stepped by 3, 5 directions, terrain separable |
| dc22 | keyboard_click | 6 | **MAZE_LIKE** | 2 | 4 | grid-stepped by 2, 4 directions, terrain separable |
| ka59 | keyboard_click | 7 | **MAZE_LIKE** | 3 | 6 | grid-stepped by 3, 6 directions, terrain separable |
| ls20 | keyboard | 7 | **MAZE_LIKE** | 5 | 4 | grid-stepped by 5, 4 directions, terrain separable |
| m0r0 | keyboard_click | 6 | **MAZE_LIKE** | 5 | 4 | grid-stepped by 5, 4 directions, terrain separable |
| re86 | keyboard_click | 8 | **MAZE_LIKE** | 3 | 6 | grid-stepped by 3, 6 directions, terrain separable |
| sc25 | keyboard_click | 6 | **MAZE_LIKE** | 2 | 6 | grid-stepped by 2, 6 directions, terrain separable |
| sp80 | keyboard_click | 6 | **MAZE_LIKE** | 4 | 4 | grid-stepped by 4, 4 directions, terrain separable |
| cd82 | keyboard_click | 6 | **NEEDS_POINTER** | - | 0 | no keyboard action moved anything; game exposes click actions |
| ft09 | - | 6 | **NEEDS_POINTER** | - | 0 | no keyboard action moved anything; game exposes click actions |
| lf52 | click | 10 | **NEEDS_POINTER** | - | 0 | no keyboard action moved anything; game exposes click actions |
| lp85 | click | 8 | **NEEDS_POINTER** | - | 0 | no keyboard action moved anything; game exposes click actions |
| s5i5 | click | 8 | **NEEDS_POINTER** | - | 0 | no keyboard action moved anything; game exposes click actions |
| sb26 | keyboard_click | 8 | **NEEDS_POINTER** | - | 0 | no keyboard action moved anything; game exposes click actions |
| su15 | click | 9 | **NEEDS_POINTER** | - | 0 | no keyboard action moved anything; game exposes click actions |
| tn36 | click | 7 | **NEEDS_POINTER** | - | 0 | no keyboard action moved anything; game exposes click actions |
| vc33 | click | 7 | **NEEDS_POINTER** | - | 0 | no keyboard action moved anything; game exposes click actions |
| bp35 | keyboard_click | 9 | **NOT_GRID_STEPPED** | 8 | 2 | movements are not multiples of one step (mode 8) |
| g50t | keyboard | 7 | **NOT_GRID_STEPPED** | 6 | 3 | movements are not multiples of one step (mode 6) |
| r11l | click | 6 | **NOT_GRID_STEPPED** | 12 | 2 | movements are not multiples of one step (mode 12) |
| sk48 | keyboard_click | 8 | **NOT_GRID_STEPPED** | 6 | 4 | movements are not multiples of one step (mode 6) |
| tr87 | keyboard | 6 | **NOT_GRID_STEPPED** | 7 | 4 | movements are not multiples of one step (mode 7) |
| wa30 | keyboard | 9 | **NOT_GRID_STEPPED** | 4 | 6 | movements are not multiples of one step (mode 4) |
| tu93 | keyboard_click | 9 | **PARTIAL** | 6 | 1 | only 1 distinct movement direction(s) |

## Tally

- MAZE_LIKE: 9
- NEEDS_POINTER: 9
- NOT_GRID_STEPPED: 6
- PARTIAL: 1

## How much to trust this

Every verdict is a **lower bound**. The probe presses each action 2x from a single reset, so it samples one state — a game whose piece starts against a wall, or that needs a mode set before anything moves, reads as if nothing moves. Two independent cross-checks on the run of 2026-07-27:

- `ft09` came out NEEDS_POINTER, but arXiv 2512.24156 Table 1 reports a keyboard agent clearing 3 of its levels — a confirmed false negative.
- `cd82` and `sb26` are tagged `keyboard_click` yet no keyboard action moved anything, which is suspicious for the same reason.
- Games with very high object counts (`bp35` 183, `tu93` 64, `tr87` 56) most likely fail `constant_step` because perception over-segments and the colour+size match links the wrong pair, not because the board is not grid-stepped.

So MAZE_LIKE is the trustworthy number; the failure classes are hypotheses about *why*, and each needs a per-game follow-up before being believed.
