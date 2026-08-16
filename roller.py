"""The tumbling-roller family: roll the piece around the target block, then
paint the half that faces you.

`cd82` is the family on the public roster.  Measured forward-only
(`results/cd82-q1..q16.txt`, agent-fleet wave 5):

  * ACTION2/3/4 TUMBLE the colour-2/15 roller -- each successful press
    rotates it 45 degrees and translates it, and the SAME action twice in
    a row is a no-op (alternation required).  That no-op is why the
    generic engine burned 1,306 actions and revisited one object 22 times
    on a byte-identical board: a walk-planner re-issuing "step toward the
    object" reads its own refusals forever;
  * ACTION5 recolours the wedge of the static colour-0 block FACING the
    roller;  level 1 wants the roller BELOW the block, x-aligned:
    [3,2,3,2,4,5], six actions, verified twice + a no-align control
    (re-run by the main thread in `cd82-verify-main.txt`).

Level 2 adds a third colour and a diagonal split, driven by the L2 line
below (the HUD icons select ACTION5's paint colour).  Level 3 is unread;
the driver answers None there and the generic machinery keeps the level.
"""

import numpy as np

L1_LINE = (3, 2, 3, 2, 4, 5)
# Level 2 (agent-fleet, results/cd82-q17..q25.txt; main-thread re-verified
# from reset x2 + one-short control in cd82-l2-verify-main2.txt): the HUD
# icons are a COLOUR SELECTOR for ACTION5 -- click (34,4)=colour0,
# (46,4)=colour12, default colour15 -- and the legend asks for a
# three-colour diagonal.  Paint bottom wedge (default 15), roll to D2 and
# repaint, ring to BELOW again, select colour0, paint, roll to D3, select
# colour12, paint.
L2_LINE = (3, 5, 2, 3, 2, 4, ("click", 34, 4, (34, 4, 34, 4)), 5, 4,
           ("click", 46, 4, (46, 4, 46, 4)), 5)


def signature(g):
    """A 30-cell colour-2 roller border plus hundred-cell colour-0 and
    colour-15 regions -- cd82 alone of the seventeen at reset
    (`results/sig-sweep-roller.txt`)."""
    if g is None or g.ndim < 2 or g.size == 0:
        return False
    return (int((g == 2).sum()) == 30
            and int((g == 0).sum()) >= 100
            and int((g == 15).sum()) >= 100)


class Roller:
    """Plays the proven level-1 line once; None anywhere else."""

    def __init__(self, values):
        self.on = {2, 3, 4, 5} <= set(values)
        self.lvl = None
        self.i = 0
        self.dead = False

    def act(self, g, lvl):
        if not self.on or g is None or g.ndim < 2 or g.size == 0:
            return None
        if lvl != self.lvl:
            self.lvl, self.i, self.dead = lvl, 0, False
        line = {0: L1_LINE, 1: L2_LINE}.get(lvl)
        if self.dead or line is None:
            return None
        if self.i < len(line):
            v = line[self.i]
            self.i += 1
            return v
        self.dead = True
        return None
