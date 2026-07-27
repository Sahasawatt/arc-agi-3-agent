# Autonomous mechanic discovery — what the agent works out for itself

9 MAZE_LIKE games, 410 actions total. Nothing here is configured per game: the piece, its footprint, what each action does and which colours stop it are all measured by acting.

| game | piece | footprint | step | directions | walls found | floor |
|---|---|---|---|---|---|---|
| ar25 | colour 5 | 9x9 | 3 | 5 | **none** | — |
| cn04 | colour 0 | 15x15 | 3 | 5 | **none** | [8] |
| dc22 | colour 14 | 2x2 | 2 | 4 | [4, 9] | [2] |
| ka59 | colour 0 | 1x1 | 3 | 4 | [2] | [1] |
| ls20 | colour 12 | 5x5 | 5 | 4 | [4] | [3] |
| m0r0 | colour 10 | 5x5 | 5 | 4 | [12] | [5] |
| re86 | colour 0 | 1x1 | 3 | 5 | **none** | [9, 11] |
| sc25 | colour 10 | 2x4 | 2 | 4 | **none** | [2, 5, 9] |
| sp80 | colour 9 | 20x4 | 4 | 4 | **none** | [12] |

## What this does and does not establish

- **Movement is solved.** All 9 games yield a piece, a footprint, a step size and a direction per action.
- **Walls are found on 4 of 9** (dc22, ka59, ls20, m0r0). Without a wall colour every cell reads as walkable, so BFS will happily route through terrain — a discovered model with an empty `walls` column is not usable for planning yet.
- **`ls20` reproduces the hand-read model exactly**: footprint 5x5, step 5, wall colour 4, and BFS to the goal box returns the same 6 moves the hand-tuned `solver.py` finds. That is the only game where the discovered model has been checked against a known-good one.
- **Goal identification is still hardcoded.** Knowing where you can walk is not knowing where to walk to; `solver.py` still names the target colours by hand. That is the next problem, and the harder one.

## Why a game ends with no walls

A wall is only observable from a move that failed, so a run that never gets blocked learns nothing about terrain. Two fixed causes are recorded in the tests: cycling the actions in order made the piece oscillate in place (47 of 48 moves succeeded, one wall seen), and breaking ties by action number made it walk in a straight line (`sp80` used one of its five actions). What remains is games whose piece perception over-segments — `ar25` reports a 9x9 footprint for a 40-cell piece — so the destination measured is not the destination entered.
