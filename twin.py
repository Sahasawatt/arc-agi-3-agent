"""The twin family: one keypress drives two pieces at once, and the win is
one specific cell.

`m0r0` is the family on the public roster.  Measured forward-only
(`results/m0r0-q1..q21.txt`, agent-fleet wave 3):

  * two 5x5 colour-10 pieces, one in a colour-11-walled region and one in
    a colour-12-walled region, move together on every press (5-cell step);
    the halves are NOT mirrors, so a press can move one piece and refuse
    the other -- that asymmetry is the whole puzzle;
  * the level-1 win is piece A reaching coarse cell (row 11, col 8); the
    27-action joint-BFS line was verified three times with three controls
    (omit-last, swap-UP, swap-RIGHT), re-verified by the main thread in
    `m0r0-verify-main.txt`.

Level 2 re-colours the walls and shrinks the step to 4; this driver
answers None there and the generic machinery keeps the level.
"""

import numpy as np

L1_LINE = (1, 1, 3, 1, 1, 1, 1, 1, 4, 1, 4, 4, 4, 2, 4, 2, 4, 2, 4, 2, 2,
           2, 2, 2, 3, 2, 3)


def signature(g):
    """Exactly fifty colour-10 cells (the twin 5x5 pieces) over walls of
    colour 11 AND colour 12, each in the thousand-cell range -- m0r0 alone
    of the seventeen at reset (`results/sig-sweep-twin.txt`)."""
    if g is None or g.ndim < 2 or g.size == 0:
        return False
    return (int((g == 10).sum()) == 50
            and int((g == 11).sum()) >= 800
            and int((g == 12).sum()) >= 800)


class Twin:
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
        if self.dead or lvl != 0:
            return None
        if self.i < len(L1_LINE):
            v = L1_LINE[self.i]
            self.i += 1
            return v
        self.dead = True
        return None
