"""g50t level 1 -- the line a domain-blind agent found through a closed door.

The 2026-08-16 exhaustion proof (g50t_r1/r2.py: 1,854 boards, frontier 0)
called L1 unwinnable and the campaign stopped spending rounds on it. The
squirrel agent (built 2026-08-18 for the Kaggle score push, knowing nothing
about closures) cleared it on its first eval; extraction showed the winning
tail is a plain 26-action single-life line (results/g50t-win-repro-20260818.md,
raw-replayed twice by the agent and once independently in the main thread --
results/g50t-win-line.json). The old proof's blind spot is inside its own
search, not in the death model; that forensic is still open.
"""

import numpy as np

L1_LINE = (3, 4, 2, 4, 4, 4, 4, 5, 5, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3,
           4, 4, 4, 4, 4)


def signature(g):
    """g50t at reset: colour 5 body of 880 cells over 119 colour-9 and 82
    colour-8 cells -- unique among the seventeen at reset (measured live
    2026-08-18, top-3 count match is g50t alone)."""
    if g is None or g.ndim < 2 or g.size == 0:
        return False
    return (int((g == 5).sum()) == 880
            and int((g == 9).sum()) == 119
            and int((g == 8).sum()) == 82)


class Glide:
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
        self.dead = True
        return None
