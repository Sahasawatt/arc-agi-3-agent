"""The dock-the-claw family: rotate the claw to the right handedness, then
drive it onto the socket's pads.

`cn04` is the family on the public roster.  Measured forward-only
(`results/cn04-q1..q11.txt`, agent-fleet night 2026-08-13/14):

  * ACTION1-4 move the claw exactly 3 cells (up/down/left/right), ACTION5
    is a quarter-turn, ACTION6 is inert;
  * the claw's two colour-8 tip pads must land pixel-exact on the socket's
    two static colour-8 pads -- and the game sets a TRAP: the wrong
    handedness (one rotate instead of three) gives the identical
    tip-to-tip vector, renders the same third-colour "docked" overlap, and
    does NOT win.  Only rotate x3 + down x7 + right x4 completes level 1;
  * verified twice forward-only per process AND cross-process
    (`cn04-q11-main.txt`), with a truncation control and the false-dock
    control both failing as they must.

Level 2 is a four-shape jigsaw (`cn04-q12.txt`) this driver does not read:
it answers None there and the generic machinery takes the level back.
"""

import numpy as np

PAD = 8

L1_LINE = (5, 5, 5, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 4)


def _pad_blobs(g):
    """Connected components of the pad colour -> list of (h, w) sizes."""
    ys, xs = np.nonzero(g == PAD)
    cells = set(zip(map(int, xs), map(int, ys)))
    out = []
    while cells:
        stack = [cells.pop()]
        blob = []
        while stack:
            x, y = stack.pop()
            blob.append((x, y))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in cells:
                    cells.remove(n)
                    stack.append(n)
        bx = [c[0] for c in blob]
        by = [c[1] for c in blob]
        out.append((max(by) - min(by) + 1, max(bx) - min(bx) + 1, len(blob)))
    return out


def signature(g):
    """Exactly four 3x3 pad blobs, plus a claw (colour 0) and a socket
    (colour 14) each over a hundred cells -- cn04 alone of the seventeen
    at reset (`results/sig-sweep-claw.txt`)."""
    if g is None or g.ndim < 2 or g.size == 0:
        return False
    if int((g == 0).sum()) < 100 or int((g == 14).sum()) < 100:
        return False
    blobs = _pad_blobs(g)
    return len(blobs) == 4 and all(b == (3, 3, 9) for b in blobs)


class Claw:
    """Plays the proven level-1 line once; None anywhere else."""

    def __init__(self, values):
        self.on = {1, 2, 3, 4, 5} <= set(values)
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
        self.dead = True    # line exhausted without a level: not our board
        return None
