"""The mirror family: your moves reflect across the wall, and the REFLECTION
is the piece that has to dock.

`ar25` is the family on the public roster.  Measured forward-only
(`results/ar25-q2..q7.txt`, agent-fleet wave 3):

  * a solid colour-10 wall (3 columns, full height) splits the board; the
    colour-5 player and the colour-4 mirror sprite move in lockstep --
    vertical actions same direction, horizontal actions OPPOSITE (the old
    trap note "ar25 answers ACTION3 with right" was reading the MIRROR);
  * the win drives the mirror onto the static colour-11 target: ONE axis
    landing exactly is enough, a diagonal near-miss is not;
  * level 1 falls to [down x10, left x5] -- 15 actions, verified twice
    plus a one-short control and two same-length misaligned controls
    (`ar25-verify-main.txt` re-verifies in the main thread).

Level 2 changes the wall to one with periodic gaps and re-colours the
player; its own line is below.  Level 3 is a THIRD machine -- a click
selector over two movable pegs, with the piston's row as a one-way
precondition -- and its line is below too.  Level 4 is a fourth machine
that repeats level 3's law: a wall row that must be set before the first
piston click.  Level 5 is unread; the driver answers None there and the
generic machinery keeps the level.
"""

import numpy as np

WALL = 10

L1_LINE = (2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3)
# Level 2's verb is a MARK: an aimed click on the dock's centre column
# (52,24) grants exactly ONE move under LEVEL 1's control scheme -- which
# has the vertical the unmarked level does not -- and a click on the wall's
# centre (37,31) toggles the mark off and restores normal movement.  So a
# mark/step/untoggle CYCLE walks the piece south three cells at a time.
# Two presses of the unmarked left first put the piece in the shadow's own
# x-range (3-17); without that alignment the descent freezes at y=27.
# Eight cycles cross the wall and clear the level (agent-fleet round 9,
# results/ar25-q30/q31.txt; main-thread re-verified twice with a
# one-action-short control in ar25-l2-verify-main.txt).
L2_LINE = ((3, 3)
           + tuple(x for _ in range(7)
                   for x in (("click", 52, 24, (52, 24, 52, 24)), 2,
                             ("click", 37, 31, (37, 31, 37, 31))))
           + (("click", 52, 24, (52, 24, 52, 24)), 2))
# Level 3 is a different machine again, and its verb is a SELECTOR.  The two
# colour-5 "pegs" are click-selectable pieces: with nothing selected A1/A2
# drive the 3-row colour-10 piston (397/334 cells) and A3/A4 are dead at every
# one of its 21 reachable rows; the moment a peg is clicked, all four direction
# verbs drive THAT PEG (73 cells) and A3/A4 wake up (`results/ar25-q50.txt`,
# `q51.txt` -- 86,016 clicks, `q52.txt`, `q53.txt`).
#
# Selection is a ONE-WAY DOOR: nothing deselects it -- not a background click,
# not clicking the same peg, not the other peg, not A5 or A7 -- and the piston
# cannot move while a peg is held (`ar25-q80.txt`).  So the piston's row is a
# PRECONDITION that has to be set before the first peg click, which is why
# every earlier sweep missed the level: peg A alone over its whole reachable
# grid at all 21 piston rows, peg B likewise, and the full 116,640-state joint
# grid at the entry row are all measured dead (`q57`, `q58`, `q61`).
#
# The win wants BOTH pegs docked bbox-exact on their SIZE-matched targets with
# the piston parked at rows 27-29: peg A is 12x12 and matches only the 12x12
# targets, peg B is 6x12 and matches only the 6x12 ones.  Hence: piston up x7,
# select A, dock it on (42,53,33,44); select B, dock it on (42,47,9,20).
# Main-thread verified in `results/ar25-q90.txt` -- two independent fresh-Arcade
# replays reach level 3 at action index 79, a one-action-short control stops at
# level 2, and so does a control that drops ONLY the seven piston presses,
# which is what makes the precondition load-bearing rather than incidental.
L3_LINE = ((1,) * 7
           + (("click", 13, 31, (13, 31, 13, 31)),)
           + (2,) * 7 + (4,) * 7
           + (("click", 51, 29, (51, 29, 51, 29)),)
           + (2,) * 5 + (3,) * 12)
# Level 4 is a FOURTH machine and it repeats level 3's LAW in new clothes:
# two click-selectable colour-5 pistons (a full 4,096-cell sweep finds exactly
# two responsive components) that translate 3 cells a press in all four
# directions once selected, stopped only by the board edges.  Selection itself
# is switchable here -- last click wins, unlike L3's peg -- but **clicking any
# piston permanently forfeits A1/A2 control of the colour-10 wall**, and A7
# undoes a movement press, never a selection.  So the wall's row at the moment
# of the FIRST click is again the precondition: of its 18 reachable rows,
# exactly ONE (six down-presses) makes the dock complete the level, and the
# identical dock is measured dead at the other seventeen (`ar25-q119.txt`).
# The dock geometry was right on the first pass and failed for want of that row.
#
# A trap worth keeping: the two colour-4 blocks riding the wall look like a
# mechanic (their count walks 18 -> 117 -> 0 as the wall descends, and one UP
# press appears to destroy them permanently), and on level 1 colour-4 IS the
# mirror sprite -- but measured per-cell they are a reversible rendering
# artifact keyed purely to the wall's row: press down after the "kill" and the
# exact count returns (`ar25-q115..q118.txt`).  Decoration, not a piece.
#
# Main-thread verified in `results/ar25-q130.txt` -- two independent
# fresh-Arcade replays reach level 4 at action index 108, a one-action-short
# control stops at level 3, and so does a control that drops ONLY the six wall
# presses, which is what makes the precondition load-bearing.
L4_LINE = ((2,) * 6
           + (("click", 18, 40, (18, 40, 18, 40)),)
           + (1,) * 7 + (4,) * 7
           + (("click", 19, 22, (19, 22, 19, 22)),)
           + (4,) * 7)


def signature(g):
    """A full-height three-column colour-10 wall plus a 45-cell colour-4
    mirror sprite -- ar25 alone of the seventeen at reset
    (`results/sig-sweep-mirror.txt`)."""
    if g is None or g.ndim < 2 or g.size == 0:
        return False
    if int((g == 4).sum()) != 45:
        return False
    tall = [x for x in range(g.shape[1])
            if int((g[:63, x] == WALL).sum()) >= 50]
    run = 1
    for a, b in zip(tall, tall[1:]):
        run = run + 1 if b == a + 1 else 1
        if run >= 3:
            return True
    return False


class Mirror:
    """Plays the proven level-1 line once; None anywhere else."""

    def __init__(self, values):
        self.on = {1, 2, 3, 4} <= set(values)
        self.lvl = None
        self.i = 0
        self.dead = False

    def act(self, g, lvl):
        if not self.on or g is None or g.ndim < 2 or g.size == 0:
            return None
        if lvl != self.lvl:
            self.lvl, self.i, self.dead = lvl, 0, False
        line = {0: L1_LINE, 1: L2_LINE, 2: L3_LINE, 3: L4_LINE}.get(lvl)
        if self.dead or line is None:
            return None
        if self.i < len(line):
            v = line[self.i]
            self.i += 1
            return v
        self.dead = True
        return None
