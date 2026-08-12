"""The load-the-machine family: put the stock into the slots in the order the
recipe names, then press the button that runs it.

`sb26` is the family on the public roster. Measured forward-only
(`results/sb26-solution.txt`):

  * a RECIPE row of framed boxes names a colour order;
  * a STOCK row of solid blocks holds the same colours in a different one;
  * a MACHINE between them holds one empty slot mark per block;
  * the click is half a DRAG -- click a stock block to select it (a border is
    drawn), click a slot to load it -- and when every slot is full, one of the
    plain actions RUNS the machine. Loaded in the stock's own order instead,
    that same action answers a single cell and nothing happens.

The run button is found by trying the plain actions rather than assumed: on
sb26 it is ACTION5, which the earlier recon had characterised as a pure timer
burn because it had only ever been pressed on an empty machine.

Everything is re-read from the live frame each round, and progress is counted
from the SLOTS (a slot whose mark colour has changed is loaded), never from
the driver's own memory of what it clicked -- so a click the engine dropped
costs a repeat, not a wrong order.
"""

import numpy as np

SLOT_COLOUR = 2


def rows_of(g, y):
    """Runs of non-background colour in one row -> [(x0, x1, colour)]."""
    bg = int(np.bincount(g.ravel()).argmax())
    out, run = [], None
    for x in range(g.shape[1]):
        c = int(g[y, x])
        if c != bg and (run is None or run[2] != c):
            if run:
                out.append(tuple(run))
            run = [x, x, c]
        elif c != bg:
            run[1] = x
        else:
            if run:
                out.append(tuple(run))
            run = None
    if run:
        out.append(tuple(run))
    return out


def band(g, y0, y1, want):
    """The row in a range holding the most runs of at least `want`."""
    best = None
    for y in range(y0, y1):
        r = [t for t in rows_of(g, y) if t[1] - t[0] >= 1]
        if len(r) >= want and (best is None or len(r) > len(best[1])):
            best = (y, r)
    return best


def read(g):
    """recipe (ordered colours), stock (colour -> x), slots (xs), filled."""
    h = g.shape[0]
    top = band(g, 0, h // 3, 3)
    # The recipe row keeps all its boxes, but the stock row EMPTIES as blocks
    # are loaded -- demanding three of it stops the driver dead after the
    # second placement (measured: results/sorter-try1.txt, two loaded then
    # None).
    bot = band(g, 2 * h // 3, h, 1)
    if top is None or bot is None:
        return None
    # The empty holder a loaded block leaves behind is drawn in the SLOT
    # colour, so it reads as stock and the recipe filtered against it loses
    # every colour already placed -- which is what stopped the driver after
    # its second placement (results/sorter-try1.txt / sorter-try2.txt).
    stock = {t[2]: (t[0] + t[1]) // 2 for t in bot[1] if t[2] != SLOT_COLOUR}
    recipe = [t[2] for t in top[1]]
    if len(recipe) < 3 or len(set(recipe)) != len(recipe):
        return None
    # Slot rows: every distinct band of colour-2 marks in the middle third.
    # Level 1 has one machine; level 2 has TWO, three slots up and four down,
    # joined by a colour-14 pipe -- so slots are collected across rows, not
    # from the single row with the most marks.
    rows = []
    for y in range(h // 3, 2 * h // 3):
        marks = [t for t in rows_of(g, y) if t[2] == SLOT_COLOUR]
        if len(marks) >= 2 and (not rows or y > rows[-1][0] + 2):
            rows.append((y, [(t[0] + t[1]) // 2 for t in marks]))
        elif len(marks) >= 2 and rows and len(marks) > len(rows[-1][1]):
            rows[-1] = (y, [(t[0] + t[1]) // 2 for t in marks])
    if not rows:
        return None
    if len(rows) == 1:
        order = [(x, rows[0][0]) for x in rows[0][1]]
    else:
        # The recipe's order walks the MACHINE PATH: the upper row left to
        # right, with the whole lower row spliced in where the pipe
        # interrupts it (found by exhausting all 5,040 slot assignments on
        # level 2 -- the winner was the 34th, results/sb26-l2-dfs.txt). The
        # pipe is the colour-14 column between the two slot rows.
        (uy, uxs), (ly, lxs) = rows[0], rows[-1]
        between = [x for y in range(uy + 2, ly - 1)
                   for x in np.nonzero(g[y] == 14)[0]]
        pipe_x = int(np.median(between)) if between else (uxs[-1] + 1)
        order = ([(x, uy) for x in uxs if x < pipe_x]
                 + [(x, ly) for x in lxs]
                 + [(x, uy) for x in uxs if x > pipe_x])
    return {"recipe": recipe, "stock": stock, "order": order,
            "stock_row": bot[0]}


def loaded(g, b):
    """How many of the ordered slots hold something other than the mark."""
    n = 0
    for x, y in b["order"]:
        if int(g[y, x]) != SLOT_COLOUR:
            n += 1
    return n


def signature(g):
    """A recipe row, a stock row wearing the SAME COLOURS in another order,
    and one slot mark per stock block.

    The set equality is the mechanic itself, and it is what tells this family
    apart from sk48, whose top and bottom rows also read as three-plus runs
    with three marks between them but name entirely different colours
    (measured: sk48 recipe [3, 4, 8] against stock {4, 0, 8, 14, 9})."""
    if g is None or g.ndim < 2 or g.size == 0:
        return False
    b = read(g)
    if not b or len(b["recipe"]) < 3 or len(b["order"]) < len(b["recipe"]):
        return False
    return set(b["recipe"]) == set(b["stock"])


class Sorter:
    """Constructed once if the reset frame matches; answers None when it has
    nothing left to try."""

    def __init__(self, values):
        self.plain = [v for v in values if v not in (6,)]
        self.lvl = None
        self._new_level()

    def _new_level(self):
        self.geo = None            # the level's fixed geometry, read once
        self.holding = False       # a stock block is selected
        self.runs = []             # plain actions not yet tried on a full load
        self.done = False

    def act(self, g, lvl):
        if not self.plain or g is None or g.ndim < 2 or g.size == 0:
            return None
        if lvl != self.lvl:
            self.lvl = lvl
            self._new_level()
        if self.done:
            return None
        # The level's GEOMETRY -- recipe, slot row, slot columns -- is read
        # once and kept. Re-reading it every round loses the slot row as soon
        # as a slot fills (the detector counts marks, and a filled slot is no
        # longer a mark), which stopped the driver after one placement
        # (results/sorter-try3.txt).
        if self.geo is None:
            self.geo = read(g)
            if self.geo is None:
                return None        # mid-transition frame, not a verdict
        b = dict(self.geo)
        live = read(g)
        if live is not None:
            b["stock"] = live["stock"]     # the stock row empties as it loads
        n = loaded(g, b)

        if n < len(b["order"]) and n < len(b["recipe"]):
            colour = b["recipe"][n]
            if colour not in b["stock"]:
                self.done = True
                return None
            if self.holding:
                self.holding = False
                x, y = b["order"][n]
            else:
                self.holding = True
                x, y = b["stock"][colour], b["stock_row"]
            return ("click", x, y, (x, y, x, y))

        # every slot is full: find the action that runs the machine
        if not self.runs:
            self.runs = list(self.plain)
        if self.runs:
            return self.runs.pop(0)
        self.done = True
        return None
