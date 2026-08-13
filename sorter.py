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

from collections import Counter
from itertools import permutations

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
    """recipe (ordered colours), stock (colour -> x), slots (xs), filled.

    Also returns "plan": the colour to load into order[i].  For a
    duplicate-free recipe the plan IS the recipe (levels 1-4).  A recipe
    with DUPLICATE colours is read as the upper row FLATTENED: a hollow
    stock block is a REFERENCE to the child box wearing its frame colour,
    and each occurrence expands to the child's own content -- level 5's
    [6,e,8,8,e,8,8,b,f] is upper [6,9h,9h,b,f] with the child box loaded
    (e,8,8) once and called twice (found by exhausting the 10,080
    assignments, sb26-l5-dfs.txt; forward-only twice with a swapped
    control, sb26-l5-solve.txt)."""
    h = g.shape[0]
    top = band(g, 0, h // 3, 3)
    # The recipe row keeps all its boxes, but the stock row EMPTIES as blocks
    # are loaded -- demanding three of it stops the driver dead after the
    # second placement (measured: results/sorter-try1.txt, two loaded then
    # None).
    bot = band(g, 2 * h // 3, h, 1)
    if top is None or bot is None:
        return None
    # Read the stock from the band's TOP edge: a HOLLOW block (level 4's
    # e44e -- a real, placeable block) reads as two width-1 wall runs on its
    # interior rows and as a solid run on its top edge.  Climb on WIDE
    # non-slot runs only: level 8's mostly-empty stock row is six colour-2
    # holders plus width-1 hollow fragments, and counting the fragments
    # kept the walk pinned to the interior row.
    def _wide(runs):
        return [t for t in runs if t[2] != SLOT_COLOUR and t[1] - t[0] >= 1]

    while bot[0] - 1 > 2 * h // 3 and rows_of(g, bot[0] - 1):
        if len(_wide(rows_of(g, bot[0] - 1))) >= len(_wide(bot[1])):
            bot = (bot[0] - 1, rows_of(g, bot[0] - 1))
        else:
            break
    # The empty holder a loaded block leaves behind is drawn in the SLOT
    # colour, so it reads as stock and the recipe filtered against it loses
    # every colour already placed -- which is what stopped the driver after
    # its second placement (results/sorter-try1.txt / sorter-try2.txt).
    stock = {t[2]: (t[0] + t[1]) // 2 for t in bot[1] if t[2] != SLOT_COLOUR}
    # HOLLOWNESS is a property of the RUN, not of the colour: level 7's
    # stock holds two solid 9s AND a hollow 9 (the interior row, one below
    # the top edge, is background).
    bg = int(np.bincount(g.ravel()).argmax())
    hollow = set()
    if bot[0] + 1 < h:
        for x0, x1, c in bot[1]:
            if c != SLOT_COLOUR and int(g[bot[0] + 1, (x0 + x1) // 2]) == bg:
                hollow.add((x0, x1))
    # Slot rows: every distinct band of colour-2 marks above the stock row
    # -- level 7's boxes stack from y16 to y42 on a 64-high board, so the
    # old middle-third window cut off both ends.
    rows = []
    for y in range(top[0] + 1, bot[0]):
        marks = [t for t in rows_of(g, y) if t[2] == SLOT_COLOUR]
        if len(marks) >= 2 and (not rows or y > rows[-1][0] + 2):
            rows.append((y, [(t[0] + t[1]) // 2 for t in marks]))
        elif len(marks) >= 2 and rows and len(marks) > len(rows[-1][1]):
            rows[-1] = (y, [(t[0] + t[1]) // 2 for t in marks])
    if not rows:
        return None
    # The recipe can span SEVERAL bands: level 8 writes the same six boxes
    # twice (y1-6 and y8-13) and means their CONCATENATION -- the two rows
    # spell out two unrollings of a self-referencing machine.  A band's
    # frame is six tall, so accepted rows less than six apart are the same
    # band; a candidate row has three-plus wide runs in two-plus colours,
    # above the first slot row.
    reps = []
    for y in range(0, rows[0][0]):
        r = [t for t in rows_of(g, y) if t[1] - t[0] >= 1]
        if len(r) >= 3 and len({t[2] for t in r}) >= 2:
            if not reps or y >= reps[-1][0] + 6:
                reps.append((y, r))
    if not reps:
        return None
    recipe = [t[2] for band_ in reps for t in band_[1]]
    if len(recipe) < 3:
        return None
    dup = len(set(recipe)) != len(recipe)
    if len(rows) == 1:
        if dup:
            return None
        order = [(x, rows[0][0]) for x in rows[0][1]]
        plan = [(c, None) for c in recipe]
    elif dup:
        # Expansion reading.  A hollow stock block REFERENCES the box
        # wearing its frame colour, and the recipe is a box's contents
        # flattened in x order, references expanding RECURSIVELY.  Measured
        # shapes: level 5 one child called twice; level 6 three
        # fixture-carrying boxes; level 7 nested two deep with a fixture
        # whose colour is not its box's (a b between the e-box's slots);
        # level 8 a SELF-REFERENCING box ([8, b, ref9, ref8]) whose
        # infinite expansion the doubled recipe row spells out twice --
        # matched as a PREFIX of the unrolling.
        #
        # Boxes are found by wall pairs, not slot groups: on a content row
        # a WALL is a width-1 run, a FIXTURE a width>=3 run (blocks are
        # four wide), a slot mark a colour-2 pair, and one box may show
        # fixtures and no slots at all (level 8's 9-box).  Per box the
        # row with the most content wins; slots more than a frame apart
        # still group together when the same walls enclose them.
        boxes = {}
        for y in range(rows[0][0] - 6, bot[0]):
            if y < 0:
                continue
            runs = rows_of(g, y)
            content = [t for t in runs
                       if (t[2] == SLOT_COLOUR and t[1] - t[0] == 1)
                       or (t[2] != SLOT_COLOUR and t[1] - t[0] >= 2)]
            for t in content:
                wl = [w for w in runs if w[1] < t[0] and w[0] == w[1]]
                wr = [w for w in runs if w[0] > t[1] and w[0] == w[1]]
                if not wl or not wr:
                    continue
                key = (wl[-1][0], wr[0][0], wl[-1][2])
                boxes.setdefault(key, {})
                boxes[key].setdefault(y, []).append(t)
        built = {}
        for (x0, x1, fc), rowmap in boxes.items():
            if fc == SLOT_COLOUR:
                continue
            y, content = max(rowmap.items(), key=lambda kv: len(kv[1]))
            xs = [(t[0] + t[1]) // 2 for t in content if t[2] == SLOT_COLOUR]
            items = []
            si = 0
            for t in sorted(content):
                if t[2] == SLOT_COLOUR:
                    items.append(("slot", si))
                    si += 1
                else:
                    items.append(("fix", t[2]))
            if fc in built and len(built[fc]["items"]) >= len(items):
                continue
            built[fc] = {"fc": fc, "y": y, "xs": xs, "items": items}
        if not built:
            return None
        blocks = tuple(sorted((t[2], (t[0], t[1]) in hollow)
                              for t in bot[1] if t[2] != SLOT_COLOUR))
        pointed = {c for c, hh in blocks if hh}
        # A slotless box nothing points at is a wall artifact (a frame's
        # 0-cornered edge rows read as walls around one long run) -- level
        # 8 grew one and it stole the root.  A slotless box that IS
        # pointed at is real (level 8's fixtures-only 9-box).
        built = {fc: bx for fc, bx in built.items()
                 if bx["xs"] or fc in pointed}
        if not pointed <= set(built):
            return None
        slots_seq = []
        for fc in built:
            for i in range(len(built[fc]["xs"])):
                slots_seq.append((fc, i))
        if len(blocks) != len(slots_seq) or not blocks:
            return None
        # Roots: the unpointed boxes first, but EVERY box is a candidate
        # -- level 8's mutually-recursive variant points at both.
        roots = ([fc for fc in built if fc not in pointed]
                 + [fc for fc in built if fc in pointed])

        def flatten(fc0, assign):
            out = []

            def emit(fc, depth):
                if depth > 16:      # a ref cycle that emits nothing
                    return
                for kind, val in built[fc]["items"]:
                    if len(out) > len(recipe):
                        return
                    if kind == "fix":
                        out.append(val)
                    else:
                        c, hh = assign[(fc, val)]
                        if hh:
                            emit(c, depth + 1)
                        else:
                            out.append(c)

            emit(fc0, 0)
            return out

        found = None
        for perm in sorted(set(permutations(blocks))):
            assign = dict(zip(slots_seq, perm))
            for rfc in roots:
                f = flatten(rfc, assign)
                if len(f) >= len(recipe) and f[:len(recipe)] == recipe:
                    found = assign
                    break
            if found:
                break
        if found is None:
            return None
        order, plan = [], []
        for fc, i in slots_seq:
            bx = built[fc]
            order.append((bx["xs"][i], bx["y"]))
            plan.append(found[(fc, i)])
    else:
        # The recipe's order walks the MACHINE PATH -- a depth-first walk of
        # the machine TREE. Level 2: one pipe, one lower machine, the whole
        # lower row spliced in at the pipe (found by exhausting all 5,040
        # slot assignments, winner the 34th, results/sb26-l2-dfs.txt).
        # Level 3: TWO pipes into two framed sub-machines, and each pipe
        # splices in only ITS OWN box's slots (first guess from the tree
        # reading, confirmed forward-only twice with a reversed-order
        # control, results/sb26-l3c.txt). A pipe is a hollow non-slot frame
        # sitting in the upper machine's slot band; its box is the lower
        # slots nearest it in x -- colour cannot be the key, because level
        # 2's pipe is colour 14 over a colour-8 machine.
        (uy, uxs), (ly, lxs) = rows[0], rows[-1]
        # Where a child machine splices into the upper row is its own
        # CENTROID in x -- no pipe detection at all. Levels 2 (pipe at 34,
        # machine centred 32), 3 (two boxes centred 22.5 and 40.5) and 4
        # (box centred 31.5, pipe invisible) all agree; the earlier
        # pipe-reading misread level 4's two PRE-LOADED blocks as pipes,
        # since a placed block is exactly a width-4 run in the pipe's row.
        # Child boxes: cluster the lower slots by their gaps -- slots more
        # than 8 apart belong to different boxes.
        groups = [[lxs[0]]]
        for x in lxs[1:]:
            if x - groups[-1][-1] > 8:
                groups.append([])
            groups[-1].append(x)
        marks = [(sum(gr) / len(gr), gr) for gr in groups]
        order = []
        events = sorted([(float(x), "u", x) for x in uxs]
                        + [(cx, "g", gr) for cx, gr in marks])
        for _, kind, val in events:
            if kind == "u":
                order.append((val, uy))
            else:
                order += [(x, ly) for x in val]
        plan = [(c, None) for c in recipe]
    return {"recipe": recipe, "stock": stock, "order": order,
            "plan": plan, "stock_row": bot[0]}


def loaded(g, b):
    """How many of the ordered slots hold something other than the mark."""
    n = 0
    for x, y in b["order"]:
        if int(g[y, x]) != SLOT_COLOUR:
            n += 1
    return n


def stock_x(g, row, colour, want_hollow):
    """x of a stock run of `colour` still present on the stock row;
    hollowness must match unless want_hollow is None."""
    bg = int(np.bincount(g.ravel()).argmax())
    for x0, x1, c in rows_of(g, row):
        if c != colour or c == SLOT_COLOUR:
            continue
        hh = (row + 1 < g.shape[0]
              and int(g[row + 1, (x0 + x1) // 2]) == bg)
        if want_hollow is None or hh == want_hollow:
            return (x0 + x1) // 2
    return None


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
        self.runs_spent = False    # the run-button hunt happens once per level
        self.unwound = False       # A7-unwind of game-placed blocks, once
        self.unwinding = 0
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
        n = loaded(g, b)

        # Level 4 opens with blocks the GAME already placed. They unwind
        # with A7 (LIFO, back to their stock holders) and are part of the
        # puzzle, not of the answer's prefix -- with them unwound, every
        # recipe colour is back in stock (the recipe's e is the HOLLOW
        # block; the middle machine's solid e is a fixture with no slot
        # mark, so it sits outside `order` entirely) and the plain
        # recipe-order load works. Unwind once, one press per filled slot.
        if not self.unwound:
            self.unwound = True
            self.unwinding = n
        if self.unwinding > 0:
            self.unwinding -= 1
            return 7
        if n < len(b["order"]) and n < len(b["plan"]):
            colour, want_h = b["plan"][n]
            if self.holding:
                self.holding = False
                x, y = b["order"][n]
            else:
                # Stock is re-read from the frame every round (the row
                # empties as it loads, and a colour that appears twice must
                # resolve to a run still PRESENT); hollowness is matched
                # when the plan cares -- level 7 holds two solid 9s and a
                # hollow 9 side by side.
                x = stock_x(g, b["stock_row"], colour, want_h)
                if x is None:
                    self.done = True
                    return None
                self.holding = True
                y = b["stock_row"]
            return ("click", x, y, (x, y, x, y))

        # Every slot is full: find the action that runs the machine -- ONCE.
        # Refilling the list unconditionally is an infinite loop when the
        # order is wrong: the last plain action tried was A7, which is UNDO,
        # so the load drops by one, the driver reloads it, and the pair
        # repeats forever (measured: ~2,000 actions of it on level 3 before
        # the tree order was found, results/sb26-l3a.txt).
        if not self.runs_spent:
            self.runs_spent = True
            self.runs = list(self.plain)
        if self.runs:
            return self.runs.pop(0)
        self.done = True
        return None
