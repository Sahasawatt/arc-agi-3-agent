# ls20 level 6: the measured model (session 2026-07-30)

Every claim below has a run in this directory. Prefixes replay the deterministic
compete run (`out-l6v.jsonl` carries per-action values; `prefix963.txt` = actions
0..962, ending on the death-respawn that starts a fresh life at (24, 50)).

## The changers PATROL — the earlier "static crosses" reading is refuted

`l6-circuits.txt` (probe6.py, 18 safe oscillation actions): three small objects walk
deterministic tracks, **period 8**, advancing exactly one lattice step per **piece
move** — a refused press freezes all of them (seen three times in `l6-probe-ink2.txt`:
piece blocked at (29,35)/(19,35), patrollers hold).

| patroller | cells (colours) | track | effect on the panel |
|---|---|---|---|
| ink cluster | 3x3-ish, 9/14/8/0/12 | ring around the mid-left block, anchors (25,31),(20,31),(20,26),(20,21),(25,21),(30,21),(30,26),(30,31) | ink one step along `12 -> 9 -> 14 -> 8 -> 12` |
| cross-1 | 4 cells colour 0 | y=11-13, x anchor 15,20,25,30,35,30,25,20 (back-and-forth) | shape one step along an ALPHABET: `#.#/.##/##.` -> `#../###/#..` -> `###/#../###` -> `.#./#.#/.##` -> `.#./###/#..` -> `#.#/..#/###` (door A's glyph) |
| cross-2 | 6 cells colours 0+1 | y=41-43, x anchor 35,30,25,20,15,20,25,30 | shape a quarter turn CW |

**A press is the piece's 5x5 footprint overlapping a patroller's cells after the
move** (both move on the same tick). Checked 4/4 against the compete run's confusing
(19,40) entries — the "non-deterministic press" was patroller phase all along. The
gate's 13 "changer squares" are footprint-overlap positions of moving objects; the
phantom-edge refutation deleting `rotates` was the model meeting a mover it had no
way to represent.

`l6drive.py` (BFS over position x phase x ink x shape, fuel + one-shot refills)
predicted **every position and every panel value of a 23-action drive exactly**
(`l6-driveB.txt`), and the longer drives only diverge where the piece reader had the
panel-glyph bug (fixed: when the ink is 12 the panel's 2x glyph is the biggest
colour-12 component on the frame).

## Doors: B is a checked PASSAGE, A sits behind it

- Door B at x53-59, y34-40 asks `(8, #.#/##./.##)`; stand-inside position (54,35).
- Door A at x53-59, y49-55 asks `(9, #.#/..#/###)`; stand-inside position (54,50),
  reachable ONLY through B (x=49 column south of y=30 is wall; x=59 is wall).
- Entering B with its exact ask: allowed, and the level does NOT end (`l6-driveB.txt`,
  also twice in the compete run at a=946/a=1147). The piece walks on south through
  (54,40), (54,45).
- B refuses `(9, A-glyph)`, `(9, B-glyph)`, `(8, A-glyph)` — the FULL pair is checked
  (`l6-driveA2.txt`, `l6-driveMix.txt`, `l6-driveMix2.txt`).
- A refuses `(8, B-glyph)` (`l6-driveB.txt` step 26).
- No patroller reaches x>44, so the panel is FROZEN south of the crossing — the ask
  cannot be changed between B and A on one pass.

## Fuel

Full tank = 84 units = 42 moves — but the AGENT reads that as 21 in 72 of the 121
rounds where both patrol planners come back empty (`l6-fueldbg3.log`): `drain` takes the
most common fall over the last 20 steps and it flips between 2 and 4 within the level.
Fuel is nonetheless NOT what blocks those rounds — at a tank of 200 not one of the 121
has a plan either, so the trip-from-a-full-tank fix is inert and is not in the code.

Three refills, one-shot per life, pickup positions
(9,5), (39,5), (9,45). Death respawns at (24,50) and resets the panel to
`(14, ##./.##/#.#)` — the "12 -> 14" legacy edges the gate learned were death resets
credited as changer edges, which is what poisoned `Gate.legacy` this level.

## Open — both answered the same day

- **Door B stays open once passed while matched** — `l6-driveAB2.txt` leg 2 re-entered
  (54,35) wearing `(9, A-glyph)`, the pair B had refused cold, and walked through. A
  death closes it again (the panel reset implies the door reset; the agent clears
  `opened` on every death and re-opens).
- **Entering door A wearing its ask ENDS THE LEVEL** — same run, step 49: lvl 5 -> 6.
  The full hand recipe from a fresh life: set `(8, B-glyph)`, enter B (opens), exit,
  refuel, set `(9, A-glyph)` (ink 8->12->9, shape via the quarter-turn cross into the
  alphabet), walk back THROUGH B into A. 72 actions, model exact for 71 of them (the
  72nd is the level-7 board appearing).

The agent version of that recipe landed the same session: patrol tracking
(`Gate.track`/`mover_period`), press attribution to the patroller's predicted position,
`route_moving` (BFS over position x phase x panel x refills x opened doors) and
a learn mode that presses what it has no edge for, walking there through the presses it
does know (the alphabet is walked edge by edge this way). With BUDGET at 2000 — the cap
binds mid-choreography now, the old "structural block" measurement predates the planner —
`ls20` clears level 6 unaided: **[23, 45, 99, 178, 292, 844], 23.528%**
(`l6-learn2.log`; the first clear was 1,187 at 23.006%, `rung-ls20m.log`).

Then **570 at 24.85%** (`sweep-phase.log`), by keeping a patroller's period across a
death and re-anchoring only its phase: the period is the object's and the same next
life, and while it was being lost for three laps neither planner — including the one
that teaches edges — could plan at all. Deaths 9 → 6, `stage1` 317 → 209.

Then **285 at 32.144%** (`sweep-mute.log`), by letting the learn planner see the
patrollers it had never watched. A mover with a period but no known half contributes
nothing to `presses`, so walking over it was not modelled as a press at all and no plan
could go and find out what it does — 183 of the 189 rounds the learn planner gave up on
had two to seven of them on the board. `stage1` 209 → 3, `moving-learn` 82 → 154, deaths
6 → 1.
