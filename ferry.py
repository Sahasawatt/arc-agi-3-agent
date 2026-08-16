"""The swap-and-station family: put the dot in one closed box and the piece
in the other.

`ka59` is the family on the public roster.  Measured forward-only
(`results/ka59-p11..p18.txt`, verified twice with a floor control in
`ka59-solve.txt`):

  * the piece and a colour-5 dot each sit inside a colour-14 ring, a
    full-height colour-15 bar splits the board, and each side holds a
    CLOSED colour-4 box no walk can enter through a gap -- but movement is
    a 3-cell lattice step that checks only the LANDING cell, so the piece
    steps OVER a box wall onto its interior;
  * walking into the dot KICKS it: it flies up to 15 cells, over the bar
    (permeable to flight), clamped by outer walls -- the one reachable
    kick sends it across;
  * the aimed click is a SWAP: the piece teleports to the dot's square and
    the dot -- recoloured to the boxes' own 4 -- lands on the piece's OLD
    square.  Standing inside the near box when clicking therefore PLACES
    the dot in that box;
  * with the 4-dot in the near box, the piece walking onto the far box's
    interior completes the level.

Three days of earlier probes misread all of this because their detectors
looked only for colour 5: the swapped dot is colour 4, so "the click
consumes the dot" and "the piece carries a ring" were both artifacts of a
blind census.  Everything here re-reads the live frame each round.
"""

import numpy as np

RING = 14
BAR = 15
BOX = 4


def find_cell(g, colour):
    """The single OBJECT of `colour`: one cell, or a tight cluster (the
    piece smears over 2-4 cells on animation frames -- spread beyond 2 in
    either axis means several objects, which is a different level shape,
    not a transient)."""
    ys, xs = np.nonzero(g[:63] == colour)
    if len(ys) == 0:
        return None
    if xs.max() - xs.min() > 2 or ys.max() - ys.min() > 2:
        return None
    return int(round(xs.mean())), int(round(ys.mean()))


def in_ring(g, p):
    """All eight neighbours are the ring colour."""
    if p is None:
        return False
    x, y = p
    h, w = g.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            yy, xx = y + dy, x + dx
            if not (0 <= yy < h and 0 <= xx < w) or int(g[yy, xx]) != RING:
                return False
    return True


def bar_cols(g):
    """Columns where the bar colour runs at least 15 rows deep."""
    cols = []
    for x in range(g.shape[1]):
        run = best = 0
        for v in g[:63, x]:
            run = run + 1 if int(v) == BAR else 0
            best = max(best, run)
        if best >= 15:
            cols.append(x)
    return cols


def boxes_of(g):
    """Closed 4-framed boxes -> [(cx, cy)] interior centres.

    A box is a full-width top run of 4, side walls at its ends, and a
    matching full-width bottom run.  A wall cell may read as the RING
    colour instead: a dot's travelling ring parks against a box and
    occludes the corner it overlaps (measured: the landed dot's ring at
    (44,30) erased the right box from the read and stalled the driver)."""
    wall = (BOX, RING)
    out = []
    bottoms = set()
    h = 63
    for y in range(h):
        x = 0
        while x < g.shape[1]:
            if int(g[y, x]) == BOX and (x, y) not in bottoms:
                x0 = x
                while x + 1 < g.shape[1] and int(g[y, x + 1]) == BOX:
                    x += 1
                x1 = x
                if x1 - x0 >= 2:
                    yb = y + 1
                    while yb < h and int(g[yb, x0]) in wall \
                            and int(g[yb, x1]) in wall \
                            and not all(int(g[yb, xx]) in wall
                                        for xx in range(x0, x1 + 1)):
                        yb += 1
                    if y + 1 < yb < h and all(int(g[yb, xx]) in wall
                                              for xx in range(x0, x1 + 1)):
                        out.append(((x0 + x1) // 2, (y + yb) // 2))
                        for xx in range(x0, x1 + 1):
                            bottoms.add((xx, yb))
            x += 1
    return out


def signature(g):
    """A piece in a ring, a 5-dot in a ring, a full-height bar, and two
    closed boxes."""
    if g is None or g.ndim < 2 or g.size == 0:
        return False
    p, d = find_cell(g, 0), find_cell(g, 5)
    if not (in_ring(g, p) and in_ring(g, d)):
        return False
    return bool(bar_cols(g)) and len(boxes_of(g)) >= 2


class Ferry:
    """One level's worth of the measured line; answers None anywhere the
    board stops reading as level 1's shape (level 2 has multi-cell dots,
    which `find_cell`'s exactly-one rejects)."""

    def __init__(self, values):
        self.values = values
        self.lvl = None
        self.spent = 0
        self.prev = None
        self.geo = None
        self.done = False

    def _step(self, p, t):
        """One greedy lattice step toward t; axis-swap if the last try
        did not move the piece."""
        dx, dy = t[0] - p[0], t[1] - p[1]
        if dx == 0 and dy == 0:
            return None
        long_x = abs(dx) >= abs(dy)
        if p == self.prev:      # blocked last round: lead with the other axis
            long_x = not long_x
        self.prev = p
        if long_x and dx:
            return 4 if dx > 0 else 3
        if dy:
            return 2 if dy > 0 else 1
        return 4 if dx > 0 else 3

    def act(self, g, lvl):
        if lvl != self.lvl:
            self.lvl = lvl
            self.spent = 0
            self.prev = None
            self.geo = None
            self.done = False
        if self.done or g is None or g.ndim < 2 or g.size == 0:
            return None
        self.spent += 1
        if self.spent > 80:     # a loop here means the shape is not ours
            self.done = True
            return None
        # Geometry -- the bar and the two boxes -- is read ONCE per level,
        # on the entry frame, where nothing occludes it: a travelling ring
        # parks against a box wall and erases it from a live read (the
        # landed dot's ring at (44,30) cost the right box; the piece's own
        # ring walking past cost the left one).
        if self.geo is None:
            bars = bar_cols(g)
            bxs = boxes_of(g)
            if not bars or len(bxs) != 2:
                self.done = True
                return None
            self.geo = (bars, bxs)
        bars, bxs = self.geo
        p = find_cell(g, 0)
        if p is None:
            self.done = True
            return None
        barx = (min(bars) + max(bars)) / 2
        mine = [b for b in bxs if (b[0] < barx) == (p[0] < barx)]
        theirs = [b for b in bxs if (b[0] < barx) != (p[0] < barx)]
        if len(mine) != 1 or len(theirs) != 1:
            self.done = True
            return None
        d = find_cell(g, 5)
        if d is not None:
            if (d[0] < barx) == (p[0] < barx):
                # kick: walk into the dot
                v = self._step(p, d)
            elif p == mine[0]:
                # placed: swap
                return ("click", d[0], d[1], (d[0], d[1], d[0], d[1]))
            else:
                v = self._step(p, mine[0])
            return v
        # dot swapped away: the box on this side is the one to enter
        if p == mine[0]:
            self.done = True    # arrived without a level: not our shape
            return None
        return self._step(p, mine[0])
