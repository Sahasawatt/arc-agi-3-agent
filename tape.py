"""The tape family: clear a block, ride the room it opens, walk onto the mark.

`bp35` is the family on the public roster. The board is a vertical stack of
floor-coloured ROOMS separated by background, with 5-wide BLOCKS drawn inside
some of them; the piece holds one screen band and never moves vertically.
Everything it can do was measured forward-only this session
(`results/breadth-recon.md` §bp35, `results/bp35-solution.txt`):

  * a click turns a block into FLOOR (`bp35-p12.txt` E16, rows printed either
    side) -- that is how the room widens, and the wall that stops the walk is
    the blocks, not the one-column background gap beside them (`bp35-p15.txt`,
    with the uncleared control in the same invocation);
  * a click on the block over the piece's OWN columns rides one room up; a
    click anywhere else only clears (`bp35-p13.txt`: 36-43 cells against
    1290-1381);
  * the level ends when the piece walks onto the odd-coloured MARK -- the one
    colour on the board that is neither floor, block, block edge, piece,
    flood nor counter. It lives three rides up, which is why fourteen probes
    never saw one;
  * the budget is actions, not events: the flood starts at action 8 and takes
    about 8 more per ride (`bp35-p8.txt` E7/E8). The hand line spends 20
    against a baseline of 21.

So the policy needs no route and no arithmetic, and re-reads the frame every
round: walk onto the mark if it shares the piece's room, else ride if a block
sits over the piece, else clear a block that walls the room in, else walk
toward the nearest block that could be a door.
"""

import numpy as np

LEFT, RIGHT = 3, 4
BG, EDGE, FLOOR, BLOCK, FLOOD = 5, 3, 10, 14, 15
PIECE = (9, 11)
NOT_MARK = {BG, EDGE, FLOOR, BLOCK, FLOOD, 0, *PIECE}


def runs(xs):
    """Sorted ints -> contiguous [(start, end)] inclusive."""
    out = []
    for x in xs:
        if out and x == out[-1][1] + 1:
            out[-1][1] = x
        else:
            out.append([x, x])
    return [(a, b) for a, b in out]


def piece_box(g):
    ys, xs = np.nonzero((g == PIECE[0]) | (g == PIECE[1]))
    if not len(ys):
        return None
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def room_rows(g, box):
    """The contiguous rows of floor the piece stands in -> (top, bottom).

    Counted over the whole row, never down the piece's middle column: the
    piece is a rocket with a gap under its nose, so its centre column reads
    background one row below its own body and the room comes back four rows
    tall instead of twenty-six."""
    wide = {y for y in range(g.shape[0]) if int((g[y] == FLOOR).sum()) >= 10}
    top, bot = box[2], box[3]
    while top - 1 in wide:
        top -= 1
    while bot + 1 in wide:
        bot += 1
    return top, bot


def blocks(g, y0, y1):
    """Colour-14 rectangles inside a row window -> [(x0, x1, ytop, ybot)]."""
    seen = {}
    for y in range(max(0, y0), min(g.shape[0], y1 + 1)):
        for a, b in runs(sorted(int(x) for x in np.nonzero(g[y] == BLOCK)[0])):
            seen.setdefault((a, b), []).append(y)
    return [(a, b, min(ys), max(ys)) for (a, b), ys in seen.items()]


def chute(g, top):
    """A narrow floor column above the room -- the reset board's way up."""
    for y in range(top - 1, -1, -1):
        wide = [(a, b) for a, b in
                runs(sorted(int(x) for x in np.nonzero(g[y] == FLOOR)[0]))]
        if wide and all(b - a + 1 <= 10 for a, b in wide):
            return True
    return False


def mark(g):
    """Cells of the odd colour, if the board carries one."""
    cols = [c for c in np.unique(g) if int(c) not in NOT_MARK]
    if not cols:
        return None
    ys, xs = np.nonzero(g == cols[0])
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def signature(g):
    """A stacked-rooms board: a piece standing in a wide floor room, blocks
    drawn in floor colour's neighbours, and a narrow floor column above it."""
    if g is None or g.ndim < 2 or g.size == 0:
        return False
    box = piece_box(g)
    if box is None:
        return False
    top, bot = room_rows(g, box)
    width = int((g[bot] == FLOOR).sum())
    return bool(width >= 30 and bot - top >= 4
                and len(blocks(g, 0, top - 1)) >= 3 and chute(g, top))


class Tape:
    """Constructed once if the reset frame matches; asked with the rest of the
    drivers; answers None the moment it runs out of ideas."""

    def __init__(self, values):
        self.on = {LEFT, RIGHT} <= set(values)
        self.lvl = None
        self.spent = set()      # clicks already made this level, never repeated

    def act(self, g, lvl):
        if not self.on or g is None or g.ndim < 2 or g.size == 0:
            return None
        if lvl != self.lvl:
            self.lvl, self.spent = lvl, set()
        box = piece_box(g)
        if box is None:
            return None         # mid-transition frame, not a verdict
        x0, x1, py0, py1 = box
        top, bot = room_rows(g, box)

        m = mark(g)
        if m is not None and m[3] >= top and m[2] <= bot:
            if m[1] < x0:
                return LEFT
            if m[0] > x1:
                return RIGHT
            return None         # standing on it already: nothing left to drive

        def click(b):
            cx, cy = (b[0] + b[1]) // 2, (b[2] + b[3]) // 2
            if (cx, cy) in self.spent:
                return None
            self.spent.add((cx, cy))
            return ("click", cx, cy, (b[0], b[2], b[1], b[3]))

        above = blocks(g, 0, top - 1)
        if above:
            band = max(b[3] for b in above)
            low = [b for b in above if b[3] == band]
            over = [b for b in low if b[0] <= x1 and b[1] >= x0]
            if over:                                  # the door: ride
                v = click(max(over, key=lambda b: min(b[1], x1) - max(b[0], x0)))
                if v is not None:
                    return v
            beside = [b for b in blocks(g, py0, py1) if b[1] < x0 or b[0] > x1]
            if beside:                                # the wall: clear it
                v = click(min(beside, key=lambda b: min(abs(b[1] - x0),
                                                        abs(b[0] - x1))))
                if v is not None:
                    return v
            tgt = min(low, key=lambda b: abs((b[0] + b[1]) // 2 - x0))
            return RIGHT if (tgt[0] + tgt[1]) // 2 > x1 else LEFT
        return None
