"""Some targets refuse the piece until the board says the right thing.

`ls20` level 2 draws a small glyph inside the goal box, and a plate in the corner shows the
glyph the piece is currently wearing. The box **physically refuses the piece** until the two
are the same — it is not a scoring rule, the move simply does not happen. Walking onto a
white cross turns the corner glyph a quarter turn, and turning it twice means stepping off
the square and back on, because it is *entering* that counts, not standing there.

None of that is known here, and none of it is game-specific once it is written down
generically:

* a **plate** is a region with a shape drawn inside it and its own colour all the way round,
* a plate whose shape *changes* is a **display** — it reports state, it is not a place,
* wherever the piece was standing when a display changed is a **changer**,
* a target wearing a shape no display is currently showing is **locked**, and walking to it
  buys nothing but the walk back.

`perception.icon` does the comparing. The two plates draw the same glyph at different
scales — the indicator is 2x the marker — so a shape is trimmed to its own bounding box and
runs of identical adjacent rows and columns are collapsed before anything is compared.
"""

import os
from collections import deque
from math import gcd as _gcd

import numpy as np

from discover import walkable
from plan import footprints_touching, step_to
from perception import components, icon

MIN_SIDE = 4   # anything narrower is an icon's own notch, not a panel
MIN_INK = 3    # a couple of stray cells inside a region is not a glyph


def _framed(grid, x0, x1, y0, y1, c):
    """Is the region's whole border one colour? A plate holds a shape; a blob does not.

    Without this every large component is a plate, because the bounding box of anything
    ragged contains most of the board — the floor would be a plate displaying the walls.
    """
    return bool((grid[y0, x0:x1 + 1] == c).all() and (grid[y1, x0:x1 + 1] == c).all()
                and (grid[y0:y1 + 1, x0] == c).all() and (grid[y0:y1 + 1, x1] == c).all())


def _ring(grid, x0, x1, y0, y1):
    """The set of colours immediately surrounding a region, clipped to the frame."""
    h, w = grid.shape
    out = set()
    for y in (y0 - 1, y1 + 1):
        if 0 <= y < h:
            out.update(int(v) for v in grid[y, max(0, x0 - 1):min(w, x1 + 2)])
    for x in (x0 - 1, x1 + 1):
        if 0 <= x < w:
            out.update(int(v) for v in grid[max(0, y0 - 1):min(h, y1 + 2), x])
    return out


def plates(frame):
    """{(x0, x1, y0, y1): (ink colour, icon)} for every region with a shape inside it.

    Read over the WHOLE frame rather than the play area: `ls20` draws its indicator across
    the row where the HUD begins, and a reader that stops at that line cuts the glyph in
    half — which is trap 3 in `NOTES-ls20.md`, in a different disguise.
    """
    grid = np.array(frame)[-1]
    out = {}
    # A region that spans the board IS the board: a background colour reaching all four
    # edges is framed by definition and holds everything drawn on top of it, so without an
    # upper bound the floor reads as one enormous display and every target on it is locked.
    wide, tall = grid.shape[1] // 3, grid.shape[0] // 3
    # A bare shape counts only where it is drawn on the OUTSIDE — the colour that reaches
    # the frame's own edge. A shape on the floor is a thing to walk to; a shape in the void
    # is a sign. Admitting both reads right and costs `cd82` 179 actions (1,034 -> 1,213).
    void = {int(v) for v in np.concatenate([grid[0], grid[-1], grid[:, 0], grid[:, -1]])}
    for c in np.unique(grid):
        for x0, x1, y0, y1, _ in components(grid, int(c)):
            if not MIN_SIDE <= x1 - x0 + 1 <= wide or not MIN_SIDE <= y1 - y0 + 1 <= tall:
                continue
            if not _framed(grid, x0, x1, y0, y1, int(c)):
                # A shape can report state without a box around it. `ls20` level 7 draws
                # its indicator as a bare colour-12 glyph on the void — it turns a quarter
                # per press, four states and back — and the frame test is exactly what made
                # `gate.displays` read 0 there for the whole level, so nothing was `locked`
                # and its door was just another rarity target. A shape ALONE against ONE
                # background is the other way a board can say something; a shape touching
                # anything else is part of a bigger object and stays out.
                ring = _ring(grid, x0, x1, y0, y1)
                if len(ring) == 1 and int(c) not in ring and ring <= void:
                    out[(x0, x1, y0, y1)] = (int(c),
                                             icon(frame, x0, x1, y0, y1, ink=int(c)))
                continue
            inner = grid[y0 + 1:y1, x0 + 1:x1]
            inks = [(int(d), int(n)) for d, n in zip(*np.unique(inner, return_counts=True))
                    if int(d) != int(c) and n >= MIN_INK]
            # One ink, so there is one shape to compare. `ls20` draws its indicator in blue
            # on levels 1-2 and orange on level 3, which this reads off the plate rather
            # than assuming — but a plate holding two colours at once is not read at all.
            if len(inks) == 1:
                out[(x0, x1, y0, y1)] = (inks[0][0], icon(frame, x0, x1, y0, y1, ink=inks[0][0]))
    return out


def _overlaps(o, box):
    x0, x1, y0, y1 = box
    return o["x"][0] <= x1 and o["x"][1] >= x0 and o["y"][0] <= y1 and o["y"][1] >= y0


def cycle(grid, model, at, redirects=None):
    """Step off the square and back onto it — two actions, one more state change.

    On a floor that carries the piece, "step back the way you came" is not a step back:
    `ls20` level 5's ink cluster sits beside a cell that throws the piece ten squares away,
    so the return action is aimed from a square it is no longer on and the turn is lost —
    with it, four actions of fuel and the only chance that life had to close the cycle.
    So the step off has to land somewhere a single action actually returns from, under the
    map of the cells known to carry.
    """
    for a in model.dirs:
        off = step_to(model, (at[0], at[1]), a, redirects)
        if off == (at[0], at[1]) or not walkable(grid, model, off[0], off[1]):
            continue
        for back in model.dirs:
            if step_to(model, off, back, redirects) == (at[0], at[1]):
                return [a, back]
    return []


def turned(a, b=None):
    """The whole orbit when `b` is `a` given a quarter turn, else None.

    A changer that rotates its glyph is telling the agent everything in one press: four
    states, in order, and which one follows which. Walked instead, the same cycle costs an
    entry per edge — and on a board where a life is 21 actions those are the actions the
    level needed. Measured on `ls20`: every shape change on levels 1, 2 and 3 is exactly a
    quarter turn (7 of 7 on level 2, 3 of 3 on level 3), and level 5's second changer is
    too. Levels whose changer walks an alphabet instead simply do not match, and nothing is
    inferred.
    """
    if not isinstance(a, str) or (b is not None and not isinstance(b, str)):
        return None                     # an ink colour has no orientation to turn
    rows = a.split("/")
    n = len(rows)
    if n < 2 or any(len(r) != n for r in rows):
        return None
    orbit = [a]
    for _ in range(3):
        cur = orbit[-1].split("/")
        orbit.append("/".join("".join(cur[n - 1 - j][i] for j in range(n))
                              for i in range(n)))
    if b is None:
        return orbit if len(set(orbit)) == 4 else None
    return orbit if orbit[1] == b and len(set(orbit)) == 4 else None


class Gate:
    """What the board's displays are showing, and what was seen to change them.

    One per level: the mechanic carries across a level boundary but the positions do not.
    """

    def __init__(self, legacy=None):
        # The ink ALPHABET is a property of the game, not the level: `ls20` runs the same
        # 12 -> 9 -> 14 -> 8 on levels 3 and 5, and paying to watch it again on every
        # board is the single most expensive part of a deep level's learning. `legacy` is
        # the game-level value graph for INK values only — an ink is an int, a shape is a
        # bitmap string, and a shape must NOT carry: level 5 alone has two shape-changers
        # walking two different graphs. A wrong seed on a game whose levels disagree costs
        # one entry: the square does nothing, and the refutation that already handles a
        # phantom edge drops the legacy claim with it.
        self.legacy = {} if legacy is None else legacy
        self.icons = {}        # plate box -> (ink colour, shape) when last looked at
        self.displays = set()  # plates that have changed: they report state
        self.changer = None    # (x, y) the piece was standing on when one changed
        self.tried = 0         # re-entries since the changer last actually changed one
        self.rejected = set()  # display states a door refused the piece under
        self.doubted = set()   # marks whose bitmap match the engine disagreed with
        self.changers = {}     # (x, y) -> which halves of a display it was seen to move
        self.heading = None    # where the last plan that existed was walking to
        self.trip = None       # the staged plan's per-action display prediction, if any
        self.rung = None       # which rung of choose() returned the plan (accounting)
        self.cycles = {}
        self.stuck = 0     # planning rounds in a row with nothing left to watch
        self.rotates = set()  # (square, half) seen to TURN its glyph, not merely change it       # (changer, half) -> {value seen: the value it became}
        # Changers that MOVE. `ls20` level 6's crosses patrol the corridors — a small
        # object advances one lattice step per PIECE MOVE (a refused press freezes it)
        # on a short cycle, and a "press" is the piece's footprint overlapping the
        # object after the move. Keyed on track id; a track that churns simply starts
        # a new history and earns its period again.
        self.ticks = 0        # piece-moves so far: the clock every patroller runs on
        self.movers = {}      # track id -> {"hist": [(tick, box)], "halves": set}
        self.mover_edges = {}  # (track id, half) -> {value: value it became}
        # A death puts every patroller back at the start of its lap. What that destroys
        # is the PHASE — where on the lap each one is — and not the period, which is a
        # property of the object and the same on the next life. Splitting the two is
        # what lets a plan exist again a lap after a death instead of three.
        self.reset = 0        # the tick a life last ended on
        self.mover_p = {}     # track id -> the period it has been seen to earn
        self._laps = {}       # track id -> the squares of its circuit: its identity
        # Marked plates the piece has STOOD INSIDE. The engine only lets it in matched,
        # and a door passed that way stays open: measured on `ls20` level 6, door B
        # refused (9, A-glyph) cold and passed it after one matched entry. A death puts
        # the panel back, so the caller clears this when a life ends.
        self.opened = set()
        # (action, position) pairs already POKED into the unroutable dark on a windowed
        # board — each is pressed once; a wall refuses, a carry teaches `redirects` the
        # only entrance to a region no route can otherwise aim at (level 7's east half).
        self.poked = set()
        # Refill colours, LATCHED for the level once earned — windowed boards only. On a
        # board whose frame slides, `refills()`'s with/without ratio decays whenever the
        # piece is far from a ring for a while, and the rounds it goes empty are exactly
        # the early-level and post-death windows where a learn trip most needs fuel to
        # weave. A refill colour is a property of the LEVEL, not of the last few hundred
        # trace rows; the Gate dies at the level boundary, so the latch scopes with it.
        self.tank = set()
        # Plate boxes read FRESH (present in `now`, not kept) THIS LIFE — the caller
        # clears it when a life ends. An edge is only booked for a box already read
        # fresh since the death:
        # a change reported against a value kept from before a death folds the death's
        # panel reset into one "transition" — that is the phantom shape edge the ink
        # square carried on level 7 (`#.#/#.#/### -> .#./.#./###`, which closed the ring
        # graph two real edges short), and the phantom `12 -> 14` that poisoned `legacy`
        # on level 6. A late report with no death in between still books: the x54
        # rotators are learned exactly that way.
        self._fresh = {}
        self._obs = 0         # observe() calls so far: the freshness clock for _fresh
        # Square arrivals, for the fold test below: (observe #, square) each time the
        # piece lands on a new square. An edge is a fold exactly when the pressed
        # square was ENTERED more than once since the display was last read fresh —
        # one entry is one press however stale the reading (the bounce's off-square
        # can be a wall-clipped blind spot, and the x54 rotators are only ever
        # learned from a stale reading); two entries are two presses in one report.
        self._arrivals = deque(maxlen=500)
        self._last_at = None
        # Refill positions already eaten THIS LIFE (windowed boards; caller clears on
        # death). The rings respawn with the life — turn-fuel picked the same northern
        # ring up on twenty consecutive lives — but within one they are spent, and a
        # fuel plan aimed at a spent ring walks for nothing: the late-game thrash was
        # stage bouncing the piece between two eaten rings until the clock ran out.
        self.spent = set()
        # Lap cells of every REAL patroller ever tracked this level (three distinct
        # boxes = it moves). The track itself dies when the piece walks away — out
        # of a windowed frame nothing is sighted — but the lap is a property of the
        # level: the quarter-trip planner needs somewhere to aim long after the
        # track is gone.
        self.lapmem = set()
        self.qt_out = False   # a quarter-trip is outbound: come home to read
        self.qt_need = 0      # quarters this trip still owes (counted by overlap)
        self.qt_hits = 0

    def observe(self, frame, at, walked):
        """Look at the plates. Returns True if any display changed since the last look.

        A plate is remembered as **(ink colour, shape)**, because both are part of what it
        says. `ls20` level 3 has two things that change the indicator and they change
        different halves of it: the white cross turns the shape a quarter turn, and the
        multi-coloured square recolours the ink — 12, then 9, then 14. Its goal box is drawn
        in 9, so a run that compares shapes alone walks to a door wearing the right shape in
        the wrong colour and is refused, which is exactly what happened.
        """
        self._obs += 1
        cur = None if at is None else (int(at[0]), int(at[1]))
        if cur is not None and cur != self._last_at:
            self._arrivals.append((self._obs, cur))
        self._last_at = cur
        now, old = plates(frame), self.icons
        # On a WINDOWED board colour 5 is the fog, and a "plate" whose ink is 5 is the
        # fog framing itself — the hazard that once read the door's hole as a plate.
        # Purge standing entries too: one kept while fogged would otherwise never leave.
        # A plate whose box holds ANY fog is not readable either: the glyph comes back
        # garbled (seven-cell "shapes" were read off the half-visible indicator), the
        # garble reads as a CHANGE, and the phantom edge lands in some square's cycle —
        # this run's ink block carried four shape edges it never earned. Unreadable
        # keeps its last full reading, exactly like a plate under the piece.
        if getattr(self, "windowed", False):
            # "Contains any colour 5" cannot be the test: the bare indicator sits ON
            # the void, so its box always holds 5s and that rule blinded every display
            # (one run: 977 of 1,154 actions in `cand`, zero presses). What makes a
            # plate unreadable is being partly OUTSIDE the window, and the window is
            # geometry: piece ± (-18, +21) on both axes, measured on this board.
            def foggy(box):
                return at is None or not (
                    box[0] >= at[0] - 18 and box[1] <= at[0] + 21
                    and box[2] >= at[1] - 18 and box[3] <= at[1] + 21)

            now = {b: v for b, v in now.items() if v[0] != 5 and not foggy(b)}
            self.icons = {b: v for b, v in self.icons.items() if v[0] != 5}
            self.displays = {b for b in self.displays if b in self.icons or b in now}

        # A plate the piece is standing on is not being read, it is being obscured. The
        # piece is 5x5 and `ls20` level 5's goal box is 7x7, so walking in first garbles
        # what the box is asking for and then hides it altogether. Read fresh, the garbled
        # value looks like a display changing under the square the piece is on — which is
        # exactly how a changer is recognised, so the square that touches the goal box gets
        # recorded as one and the agent stands there turning nothing for 549 rounds. What
        # was last seen from off the plate is the honest reading.
        w, h = (at[2], at[3]) if at is not None and len(at) > 3 else (5, 5)

        def under_piece(box):
            return (at is not None and at[0] < box[1] + 1 and at[0] + w > box[0]
                    and at[1] < box[3] + 1 and at[1] + h > box[2])

        now = {b: v for b, v in now.items() if not under_piece(b)}
        # Standing fully inside a marked plate means the engine let the piece in — the
        # door is open, and it stays open (see `opened` above).
        if at is not None:
            for box in self.icons:
                if box not in self.displays and at[0] >= box[0] and at[0] + w <= box[1] + 1 \
                        and at[1] >= box[2] and at[1] + h <= box[3] + 1:
                    self.opened.add(box)
        changed = {box for box, v in now.items() if old.get(box, v) != v}
        if os.environ.get("ARC_UGDBG") and changed:
            for box in changed:
                print("[ug] tick=%d at=%s box=%s %s -> %s"
                      % (self.ticks, None if at is None else tuple(at[:2]),
                         box, old.get(box), now[box]))
        # A change reported against a reading kept from BEFORE the last death is real —
        # the display moved — but the TRANSITION is not one press's work: the death's
        # panel reset is folded in. Book edges only for boxes read fresh since the
        # death (`self._fresh`, see __init__); the change itself still updates
        # `displays`/`icons`.
        # On a windowed board a walk can press a changer where the display cannot be
        # read (the window is wall-clipped), and the change then surfaces squares
        # later. Whether that report is bookable depends on HOW MANY presses are in
        # the gap: one entry of the pressed square since the display's last fresh
        # reading is one press however stale the reading — refuse those and the
        # bounce whose off-square is a blind spot books nothing, which left the ring
        # at 2 booked edges over 80 bounces. Two entries are two presses folded into
        # one "transition": one run booked `#.#/#.#/### -> .#./##./.##` that way
        # (the `.##` state worn unread between them), which CLOSED the shape graph
        # minus a state and sent `exhausted` exploring with the ring short.
        def _foldsafe(box):
            if not getattr(self, "windowed", False):
                return True
            if cur is None:
                return False
            since = self._fresh.get(box, -1)
            n = sum(1 for o, sq in self._arrivals if o > since and sq == cur)
            if n > 1 and os.environ.get("ARC_FDBG"):
                gap = [sq for o, sq in self._arrivals if o > since]
                print("[fd] tick=%d cur=%s box=%s arrivals=%d gap=%s %s -> %s"
                      % (self.ticks, cur, box, n, gap[-8:],
                         self.icons.get(box), now.get(box)))
            return n <= 1
        booked = {box for box in changed if box in self._fresh and _foldsafe(box)}
        if os.environ.get("ARC_FDBG"):
            for box in changed:
                if box not in self._fresh:
                    print("[fd] tick=%d cur=%s box=%s NOT-FRESH-THIS-LIFE %s -> %s"
                          % (self.ticks, cur, box, self.icons.get(box), now.get(box)))
        moved = {i for box in booked
                 for i, (was, is_) in enumerate(zip(self.icons.get(box, now[box]), now[box]))
                 if was != is_}
        self.displays |= changed
        # And keep the last reading of one that has stopped being reported *because the
        # piece is on it*. A refill that has been taken is gone for good, and remembering
        # that one leaves the planner routing to fuel that is not there.
        # On a WINDOWED board, also keep one whose box is under the FOG: it slid out of
        # view, it did not vanish — dropping it blanks `state()`, and with the panel
        # unreadable `path_for` answers None, `exhausted` reads closed-graph where it
        # should read blind, and the planner explores forever with a complete graph in
        # hand. The kept value can be stale by the presses made while away; a replan the
        # moment it is visible again corrects that, and the door's own mark never moves.
        def fogged(box):
            return at is None or not (
                box[0] >= at[0] - 18 and box[1] <= at[0] + 21
                and box[2] >= at[1] - 18 and box[3] <= at[1] + 21)

        # ...and on a windowed board keep a DISPLAY whenever `plates` fails to read it,
        # not only when the ±18/+21 geometry calls it fogged: the window is wall-clipped
        # (measured — the door glyph's (32,53) pixel is fog at dx=18), so there are
        # positions the geometry calls readable where the half-fogged glyph defeats
        # `plates` — and dropping the icon there empties `state()`, prunes `displays`,
        # and blinds the whole lock machinery mid-walk (state=[] in most of one run's
        # planning rounds; `cand` owned the level). A display on a windowed board never
        # stops existing; unreadable keeps its last reading, like a plate under the piece.
        kept = {k: v for k, v in self.icons.items() if k not in now
                and (under_piece(k)
                     or (getattr(self, "windowed", False)
                         and (fogged(k) or k in self.displays)))}
        self.icons = {**kept, **now}
        # Losing a life also rewrites the display, and teleports the piece back to the
        # start; reading that as a discovery would name the starting square as the changer.
        if booked and walked and at is not None:
            self.changer, self.tried = (at[0], at[1]), 0
            # And remember WHICH half it moved. A board can have more than one of these:
            # `ls20` level 3 has a cross that turns the shape and a multi-coloured square
            # that recolours the ink, and a gate that remembers one square keeps pressing it
            # while the other half of the mismatch never changes.
            self.changers.setdefault(self.changer, set()).update(moved)
            # And what it turned that half INTO. A changer walks its half round a small
            # cycle, and knowing the cycle is the difference between "go and press it" and
            # knowing the press costs two actions or six: `ls20` level 2 needs three extra
            # turns of the shape, level 4's inks are four deep.
            for box in booked:
                before, after = old.get(box), now[box]
                if before is not None:
                    for h in moved:
                        self.cycles.setdefault((self.changer, h), {})[before[h]] = after[h]
                        if isinstance(before[h], int) and isinstance(after[h], int):
                            self.legacy[before[h]] = after[h]
                        # A quarter turn states the whole cycle in one press: fill the
                        # orbit instead of paying an entry per edge to walk it round.
                        orbit = turned(before[h], after[h])
                        if orbit:
                            self.rotates.add((self.changer, h))
                            step = self.cycles[(self.changer, h)]
                            for i, v in enumerate(orbit):
                                step.setdefault(v, orbit[(i + 1) % len(orbit)])
            # A changer that MOVES: when the press was the footprint overlapping a
            # patroller after the move, the edge belongs to the OBJECT — the square it
            # happened on is one of many footprint-overlap positions and never repeats
            # reliably, which is exactly why `ls20` level 6's presses read as random.
            # The patroller being pressed is COVERED by the piece, so its own track id
            # churns on exactly this tick: the overlap test asks each mover's PHASE MAP
            # where it should be, and falls back to a sighting from this tick.
            # The footprint is re-read here because the loop above reuses `h` for a
            # half index — which silently turned the footprint 5x1 and cost every
            # mover its credit until it was traced.
            fw, fh = (at[2], at[3]) if len(at) > 3 else (5, 5)
            crdbg = os.environ.get("ARC_CRDBG")
            if crdbg:
                near = {k: (info["hist"][-1] if info["hist"] else None,
                            self.mover_p.get(k), self.mover_at(k, 0))
                        for k, info in self.movers.items()
                        if info["hist"] and abs(info["hist"][-1][1][0] - at[0]) <= 12
                        and abs(info["hist"][-1][1][1] - at[1]) <= 12}
                print("[cr] lvl=%s tick=%d at=%s moved=%s near=%s"
                      % (getattr(self, "lvl", -1), self.ticks, at[:2], moved, near))
            for k, info in self.movers.items():
                hist = info["hist"]
                b = hist[-1][1] if hist and hist[-1][0] == self.ticks else None
                if b is None:
                    b = self.mover_at(k, 0)
                if (b is None and hist and hist[-1][0] == self.ticks - 1
                        and getattr(self, "windowed", False)):
                    # The pressed patroller is COVERED, so it has no sighting on this
                    # tick, and before a period is earned `mover_at` has no answer
                    # either — which is why level 7's x55 patroller went 0-for-8 on
                    # credits. A sighting from ONE tick ago is the object beside where
                    # the piece now stands, at most one lattice step from where it was;
                    # widen its box by that step before the overlap test. One tick only:
                    # every extra tick of age widens the reach and with it the odds of
                    # crediting a bystander's halves.
                    bb = hist[-1][1]
                    b = (bb[0] - 5, bb[1] - 5, bb[2] + 10, bb[3] + 10)
                if not b or not (at[0] < b[0] + b[2] and at[0] + fw > b[0]
                                 and at[1] < b[1] + b[3] and at[1] + fh > b[1]):
                    continue
                if crdbg:
                    print("[cr] CREDIT k=%s b=%s" % (k, b))
                info.setdefault("halves", set()).update(moved)
                for box in booked:
                    before, after = old.get(box), now[box]
                    if before is not None:
                        for hh in moved:
                            self.mover_edges.setdefault((k, hh), {})[before[hh]] = after[hh]
        for box in now:
            self._fresh[box] = self._obs
        return bool(changed)

    def track(self, boxes, body, moved, at=None, colours=None):
        """Record every small object's box against the patrol clock, when it ticked.

        The clock is the PIECE MOVING: `ls20` level 6's patrollers advance one lattice
        step per piece move and freeze while a press is refused — measured three times
        in one probe. Feeding a frozen tick would smear every period, so the caller
        only reports ticks on which the piece actually moved.

        Entries carry the tick, because a patroller is INVISIBLE at the very moment it
        matters most: the piece pressing it covers it, its track id churns, and a
        history that pretends the ticks were contiguous slips phase on every press.

        Anything overlapping the piece's own footprint is skipped: the piece's parts
        churn ids past the `body` filter, and a piece pacing back and forth earns its
        own parts a period and a press credit — a phantom patroller glued to the piece
        that blankets every neighbouring square with unplannable presses. A patroller
        loses only its occluded ticks to this, which the phase map already tolerates.
        """
        if not moved:
            return
        self.ticks += 1
        w, h = (at[2], at[3]) if at is not None and len(at) > 3 else (5, 5)
        # Tried and measured out: a patroller on a board bigger than the frame is out of
        # view most of the time and the tracker issues a NEW id every time it comes back,
        # so no id accumulates the three laps a period needs — level 7 tracks 25 to 61
        # objects with full histories and earns one. What survives leaving the frame is
        # what the object is MADE of, so `movers` was keyed on (colour, size) wherever
        # that was UNAMBIGUOUS in the frame — the uniqueness guard being there because
        # `see` documents what keying on it outright costs (two objects sharing a key
        # collide, and 55 went missing across the MAZE_LIKE games). The guard is not
        # enough: it costs `ls20` level 5 a hundred actions and level 6 eighteen
        # (292 -> 393, 209 -> 227, 40.503% -> 36.884%), because a signature that is
        # unique in one frame and not in the next flips the key back and forth and
        # splits the very history it was meant to join.
        for k, b in boxes.items():
            if body and k in body:
                continue
            if b[2] > 8 or b[3] > 8:
                continue                      # a mover here is a small marker-sized thing
            if at is not None and (at[0] < b[0] + b[2] and at[0] + w > b[0]
                                   and at[1] < b[1] + b[3] and at[1] + h > b[1]):
                continue
            hist = self.movers.setdefault(k, {"hist": []})["hist"]
            hist.append((self.ticks, (int(b[0]), int(b[1]), int(b[2]), int(b[3]))))
            del hist[:-48]                    # period detection needs 2 cycles, not a run
        # AT TRIP TIME, while the lap's track is ALIVE: a track whose recent boxes
        # overlap the remembered lap gets the virtual rotator law (halves + one
        # quarter edge — `_mover_step` extrapolates the rest), which is what
        # `route_moving`'s phase-counting BFS needs to TIME a chase press instead
        # of sampling phases blind. Seeding this from the west, at planning time,
        # measured inert: the track only lives while the piece is east.
        if getattr(self, "windowed", False) and getattr(self, "lapmem", None):
            h_sh = next((h for (p9, h), st9 in self.cycles.items()
                         if any(isinstance(a9, str) for a9 in st9)), None)
            if h_sh is not None:
                for k9, info9 in self.movers.items():
                    if self.mover_edges.get((k9, h_sh)):
                        continue
                    recent9 = [b9 for _, b9 in (info9.get("hist") or [])[-8:]]
                    if any(b9[0] < L[0] + L[2] and b9[0] + b9[2] > L[0]
                           and b9[1] < L[1] + L[3] and b9[1] + b9[3] > L[1]
                           for b9 in recent9 for L in self.lapmem):
                        info9.setdefault("halves", set()).add(h_sh)
                        cv9 = next((v9[h_sh] for v9 in
                                    (self.icons.get(bb) for bb in self.displays)
                                    if v9 and isinstance(v9[h_sh], str)), None)
                        if cv9 and turned(cv9):
                            self.mover_edges.setdefault((k9, h_sh), {})[cv9] =                                 turned(cv9)[1]

    def mover_period(self, k, cap=16):
        """Shortest cycle the object's recent positions are CONSISTENT with, or None.

        Consistency is judged per phase of the global clock — every recorded box at the
        same `tick mod p` must agree — so a history with occlusion gaps still earns its
        period. A static object repeats with every period, so a real cycle must contain
        more than one distinct position; and enough entries are demanded that at least
        one phase has been seen twice, or a fresh track would pass vacuously.
        """
        hist = self.movers.get(k, {}).get("hist", [])
        for p in range(2, cap + 1):
            window = [(t, b) for t, b in hist if t > self.ticks - 3 * p]
            if len(window) < p + 2:
                continue
            by = {}
            for t, b in window:
                if by.setdefault(t % p, b) != b:
                    by = None
                    break
            if by and len(set(by.values())) > 1:
                self.mover_p[k] = p
                self._adopt(k, p)
                return p
        # Nothing is consistent across the whole window, which after a death is the
        # normal case and not an unknown object: the patrollers went back to the start
        # of their laps, so every entry from the previous life contradicts this one at
        # the same phase, and the period stays lost for the three laps it takes them to
        # age out. Meanwhile no plan can be made at all — not even by the LEARN planner,
        # which is the only thing that deliberately goes and watches an edge.
        #
        # A period, though, is a property of the OBJECT. Clearing the histories to earn
        # it again in one lap was measured and lost the level, because a period earned
        # off a handful of post-respawn frames can be the wrong one. Re-using the period
        # already earned is not that: it is never read off the short history, only
        # CHECKED against it, so this life's frames can refute it and can never invent
        # one. The phase comes from this life only — see `mover_at`.
        p = self.mover_p.get(k)
        live = [(t, b) for t, b in hist if t > self.reset]
        if p is None or len(live) < 2:
            return None
        by = {}
        for t, b in live:
            if by.setdefault(t % p, b) != b:
                return None
        self._adopt(k, p)
        return p

    def _adopt(self, k, p):
        """A track that churned is the same patroller: give the new id what the old knew.

        The alphabet is the expensive half and it was being paid for again and again.
        Level 6 ends its 285 actions holding **122 edges under 26 keys** for three
        patrollers, and its learning arrives in six-action bursts that repeat six times —
        the same six edges, relearned every time the tracker renamed the object that
        carries them. A patroller is invisible exactly when it is pressed (the piece
        covers it), so churn is not an edge case here, it is the normal course of play.

        Identity is the LAP: two objects standing on two of the same squares of a
        deterministic circuit are one object. Two rather than one, because one shared
        square is where two tracks cross. The records are copied rather than aliased so
        every reader stays as it was, and a wrong adoption is refutable the same way any
        wrong edge is — the phantom-edge check drops what does not pay out.

        Asked on every reading of the period, not only on the one that EARNS it, and
        against a lap that ACCUMULATES: a snapshot taken the moment a period is first
        earned holds whatever few phases had been sighted by then, and a partial circuit
        matches nothing. That is why the first version only closed 26 keys to 24 where
        three patrollers of two halves want six. The squares of a circuit are the same
        on the next life — a death moves a patroller back along its track, not off it —
        so the union is across lives while `mover_at`'s phase map stays within one.
        """
        lap = set()
        by = {}
        for t, b in self.movers.get(k, {}).get("hist", []):
            if t > max(self.ticks - 3 * p, self.reset):
                by[t % p] = b
        lap = self._laps.get(k, set()) | set(by.values())
        if len(lap) < 2:
            return
        for j, other in list(self._laps.items()):
            if j != k and len(other & lap) >= 2:
                self.movers[k].setdefault("halves", set()).update(
                    self.movers.get(j, {}).get("halves", ()))
                for (kk, h), edges in list(self.mover_edges.items()):
                    if kk == j:
                        self.mover_edges.setdefault((k, h), {}).update(edges)
                break
        self._laps[k] = lap

    def mover_at(self, k, ahead):
        """The object's box `ahead` piece-moves from now, read off its phase map.

        None when that phase has never been observed — which is exactly the occluded
        stretch of the lap; the components of the same patroller that survive the piece
        passing over are the ones that answer there.

        Only this life's sightings, because a death moves every patroller back to the
        start of its lap: where one was at a phase before that says nothing about where
        it is at the same phase now, and the period may have been inherited across
        exactly that boundary."""
        p = self.mover_period(k)
        if p is None:
            return None
        by = {}
        for t, b in self.movers[k]["hist"]:
            if t > max(self.ticks - 3 * p, self.reset):
                by[t % p] = b
        return by.get((self.ticks + ahead) % p)

    def cycled(self):
        """Book one re-entry of the changer, and forget a square that has stopped paying.

        The square is a guess — a display can be seen to change on a step the piece merely
        happened to be walking on — and a wrong guess is an infinite loop: step off, step
        back on, nothing happens, plan the same two actions again.
        """
        self.tried += 1
        if self.tried > 2:
            self.changer, self.tried = None, 0

    def state(self):
        """Everything the displays currently say, as one comparable value — ink and shape."""
        return frozenset(self.icons[b] for b in self.displays if b in self.icons)

    def _marks(self, o):
        """The (ink, shape) pairs worn by the non-display plates this target sits on."""
        return {v for box, v in self.icons.items()
                if box not in self.displays and _overlaps(o, box)}

    def entered(self, o):
        """Has the piece already stood inside this target's plate? A door that was
        entered and did not end the level is a passage, not a goal worth re-entering."""
        return any(box not in self.displays and _overlaps(o, box) for box in self.opened)

    def marked(self, o):
        """Does this target sit on a plate that is not a display?

        Those are the places the board has drawn a shape on, and there are one or two of
        them. Rarity can still sort them past the cut: on `ls20` level 3 the goal box is a
        region of a colour that also paints the border and the status strip, so it comes
        tenth and was never considered at all.
        """
        return bool(self._marks(o))

    def locked(self, o):
        """Does this target wear a shape that no display is showing?"""
        marks = self._marks(o) if self.displays else set()
        return bool(marks) and not (marks & self.state())

    def matched(self, o):
        """Is this target wearing what a display says the piece is wearing — and untried?

        Exactly what a display says — nothing looser. Two glyphs compare equal when their
        bitmaps are equal after each is divided by the scale it is drawn at, and that
        division is exact, so equal means equal.

        It used to mean less. Collapsing runs of identical rows and columns also made the
        two scales comparable, but not injectively — `#.#/#.#/###` collapsed onto `#.#/###`
        — so equality was a hypothesis and a rejected state was allowed to un-reject every
        glyph it had been confused with, on the grounds that one of them might be the right
        one. With an exact normal form that escape hatch only walks the piece into a shut
        door wearing a glyph that visibly does not match.
        """
        if self.state() in self.rejected:
            return False
        return bool(self._marks(o) & self.state())

    def reject(self, o=None):
        """The door refused the piece while the display said this. Do not believe it again.

        And stop believing the comparison for that door at all: the shape it wears matched
        what the display showed, and it still would not open.
        """
        self.rejected.add(self.state())
        if o is not None:
            self.doubted |= self._marks(o)

    def changing(self, o, box):
        """Would walking onto this target land the piece on a square that turns a display?
        Reaching one thing by standing on another is how a match gets thrown away one action
        before it was going to be spent."""
        return any(_overlaps(o, (x, x + box[0] - 1, y, y + box[1] - 1))
                   for x, y in self.changers or ([self.changer] if self.changer else []))

    def wrong_halves(self, o):
        """Which parts of what this target wears no display is currently showing.

        A plate says two things — an ink colour and a shape — and `ls20` level 3 has a
        different square for each. Knowing *which* is wrong is what turns "go and press
        something" into a route.
        """
        marks, state = self._marks(o), self.state()
        if not marks or not state:
            return set()
        want, here = min(marks), min(state)
        return {i for i, (a, b) in enumerate(zip(want, here)) if a != b}

    def presses_for(self, o, half, pos):
        """How many entries of `pos` it takes to bring `half` to what `o` wears, or None.

        Walked over the cycle actually observed. Unknown ground — a value the changer has
        never been seen to produce — reads as one press, which is what the planner assumed
        everywhere before this and is why it kept arriving with the wrong half showing.
        """
        marks, state = self._marks(o), self.state()
        if not marks or not state:
            return None
        want, here = min(marks)[half], min(state)[half]
        step = self.cycles.get((pos, half), {})
        seen, n = {here}, 0
        while here != want and n < 8:
            nxt = step.get(here)
            # The edge is unknown, or the cycle has closed without passing what the door
            # wants. Either way this square cannot be shown to get there, and saying so
            # beats guessing: the caller falls back to the single press it always assumed.
            if nxt is None or nxt in seen:
                return None
            here, n = nxt, n + 1
            seen.add(here)
        return n if here == want else None

    def _edges(self, half):
        """{square: {before: after}} for this half — watched tables, plus an empty one for
        every square known to TURN the glyph.

        A rotating square answers for any state (`_step` computes it), so it belongs in the
        search whether or not it has been watched in the state being asked about. Left out
        because its table happens to be empty, `ls20` level 5 can never plan its shape: the
        square was pressed in one orbit and the glyph the door wants lives in another.
        """
        out = {pos: dict(step) for (pos, h), step in self.cycles.items()
               if h == half and step}
        # On a windowed board a shape square's step COMMUTES with rotation — verified
        # on `ls20` level 7, where the four booked 90-degree-family edges are exactly
        # the k=1 conjugates of the four booked ring edges (4 of 4, independent
        # measurements: the x55 patroller turns the panel a quarter, and the same
        # square then steps the turned family the same way). So every booked edge
        # states its whole conjugacy class, the way a quarter turn states its whole
        # orbit — plannable, not booked, and refutable at execution like any wrong
        # edge. Two of the conjugates point INTO the door's ask.
        if getattr(self, "windowed", False):
            for pos, table in out.items():
                for a, b in list(table.items()):
                    oa, ob = turned(a), turned(b)
                    if oa and ob:
                        for k in (1, 2, 3):
                            table.setdefault(oa[k], ob[k])
        for pos, h in self.rotates:
            if h == half:
                out.setdefault(pos, {})
        return out

    def _step(self, pos, half, value, edges):
        """What `pos` turns `value` into — watched, or computed when the square ROTATES.

        Rotation is a law, not a fact about the one state it was watched in. Filling only
        the orbit it was observed in leaves `ls20` level 5 unable to plan: its spin square
        was pressed in one orbit while the glyph the goal box wants lives in another, and
        the two halves of a known law never joined up.
        """
        seen = edges.get(pos, {}).get(value)
        if seen is not None:
            return seen
        if (pos, half) in self.rotates:
            spun = turned(value)
            if spun:
                return spun[1]
        # The game's own ink alphabet, learned on an earlier level. Only for a square that
        # has already been watched moving THIS half on THIS board (it is in `edges` at
        # all), and only for ink — an int — because shapes have per-square graphs.
        if isinstance(value, int):
            return self.legacy.get(value)
        return None

    def path_for(self, o, half):
        """Every leg of the shortest way to bring `half` to what `o` wears, or None.

        A leg is `(square, entries)`. One changer walked on its own comes back to where it
        started: `ls20` level 5 has two squares that write the shape — six states round one,
        four round the other — and the glyph its goal box asks for is in neither. It exists
        only in the states the two reach by being **interleaved**, so the answer is a
        sequence of squares, not a square. `[( (19,10), 2 ), ( (14,35), 2 )]` is that level:
        the cross twice, then the one that turns the glyph a quarter clockwise, twice.
        """
        marks, state = self._marks(o), self.state()
        if not marks or not state:
            return None
        want, here = min(marks)[half], min(state)[half]
        edges = self._edges(half)
        if here == want:
            return []
        if not edges:
            return None
        seen, queue = {here: []}, deque([here])
        while queue:
            cur = queue.popleft()
            for pos in edges:
                nxt = self._step(pos, half, cur, edges)
                if nxt is None or nxt in seen:
                    continue
                seen[nxt] = seen[cur] + [pos]
                if nxt == want:
                    legs = []
                    for sq in seen[nxt]:
                        if legs and legs[-1][0] == sq:
                            legs[-1] = (sq, legs[-1][1] + 1)
                        else:
                            legs.append((sq, 1))
                    return legs
                queue.append(nxt)
        return None

    def learning_path(self, o, half):
        """Legs to the nearest state whose outgoing edges are not all known, or None.

        `path_for` answers "how do I get the display to what the door wants" and gives up
        whole when the known edges do not reach it — which on `ls20` level 5 is every round,
        so the order search falls back to pressing one square a fixed number of times and
        hoping. Knowing part of a graph is not knowing nothing: the states with an unwatched
        edge are exactly where a press buys a new edge, and walking to one is the difference
        between learning on purpose and learning by accident.
        """
        marks, state = self._marks(o), self.state()
        if not marks or not state:
            return None
        here = min(state)[half]
        edges = self._edges(half)
        if not edges:
            return None
        seen, queue = {here: []}, deque([here])
        while queue:
            cur = queue.popleft()
            unwatched = [pos for pos in edges if cur not in edges.get(pos, {})
                         and (pos, half) not in self.rotates]
            if unwatched:
                path = seen[cur] + [unwatched[0]]
                legs = []
                for sq in path:
                    if legs and legs[-1][0] == sq:
                        legs[-1] = (sq, legs[-1][1] + 1)
                    else:
                        legs.append((sq, 1))
                return legs
            for pos in edges:
                nxt = self._step(pos, half, cur, edges)
                if nxt is not None and nxt not in seen:
                    seen[nxt] = seen[cur] + [pos]
                    queue.append(nxt)
        return None

    def leg_for(self, o, half):
        """The first leg of `path_for`, or None. Only the first is ever committed — the
        rest is re-planned from what actually happens."""
        path = self.path_for(o, half)
        return path[0] if path else None

    def exhausted(self, o, half, seen_states=5):
        """True when this half has been watched turn through `seen_states` distinct values
        and still cannot be brought to what the door wants — so another square writes it.

        The distinction is against "not enough watched yet", which is every level's opening
        and wants the opposite response: walk to the changer already in sight, not off to
        explore. `ls20` levels 2, 3 and 4 turn their glyph a quarter at a time, four states
        to the cycle, and reach what the door wants inside it. Level 5's cross walks an
        alphabet of six and more, and the glyph its goal box asks for is in none of them —
        it is written by a second square, which is what this sends the agent to look for.
        """
        steps = [step for (pos, h), step in self.cycles.items() if h == half]
        states = {v for step in steps for v in list(step) + list(step.values())}
        # A state with no outgoing edge is a walk stopped mid-cycle, not a closed
        # alphabet — the ring on `ls20` level 7 parks on exactly such a state at 5 of
        # its 6 values seen, and declaring it exhausted there sends the agent off to
        # explore two presses short of closing the ring. Exhausted means CLOSED and
        # still short of the ask; blind means keep pressing.
        outgoing = {v for step in steps for v in step}
        return (len(states) >= seen_states and states <= outgoing
                and self.path_for(o, half) is None)

    def turns_for(self, o):
        """{half that is wrong: the square to enter}, empty if any half has none.

        The square is the one the combined search wants entered FIRST, which is not always
        the only square that moves the half — with two changers writing the same half it is
        the difference between reaching a state and orbiting past it.
        """
        wrong = self.wrong_halves(o)
        out = {}
        for h in wrong:
            leg = self.leg_for(o, h)
            if leg is not None:
                out[h] = leg[0]
                continue
            for pos, moves in self.changers.items():
                if h in moves:
                    out[h] = pos
                    break
        # What is known, even when it is only half of what is needed. Returning nothing
        # unless every wrong half has a square abandons the half that DOES have one: on
        # `ls20` that is 21 of the order search's failures, and the agent falls through to
        # walking at whatever is rarest instead of turning the changer it can see.
        return out

    def _mover_step(self, k, half, value):
        """What patroller `k` turns `half`'s `value` into, or None when unplannable.

        Watched edge first; a patroller whose every watched edge is a quarter turn is a
        rotator and rotation is a law; an ink value falls back to the game's alphabet.
        """
        step = self.mover_edges.get((k, half), {})
        got = step.get(value)
        if got is not None:
            return got
        if step and all(turned(a, b) for a, b in step.items()
                        if isinstance(a, str) and isinstance(b, str)) \
                and isinstance(value, str):
            spun = turned(value)
            if spun:
                return spun[1]
        if isinstance(value, int):
            return self.legacy.get(value)
        return None

    def route_moving(self, grid, model, start, door, refills, full, left,
                     redirects=None, learn=False):
        """(actions, display-change marks) to enter `door` wearing its ask, on a board
        whose changers PATROL — or None.

        BFS over (position, patrol phase, panel value, refills used), fuel carried as a
        value to maximise per state. A press is the footprint overlapping a patroller
        AFTER the move (both tick together, and only when the piece moves), so the panel
        along any route is fully determined — the plan arrives with the panel right
        instead of matching first and hoping the walk keeps it.

        Every marked plate is a checked gate: a position inside one is entered only when
        the simulated panel equals its mark at that step — which makes a door with
        another door behind it a corridor with a toll, not a special case.

        `learn=True` inverts the goal: the plan ends on the first press whose edge is
        NOT known, walking there through the presses that are. Without it the planner
        can only ever teach itself the edge leading out of the value it is standing in,
        so a door whose ask is several unwatched presses away is unreachable and the
        old square-changer rungs fill the gap — 483 of level 6's 1,187 actions, spent
        planning trips to footprint-overlap positions that are not places.
        """
        dbg = (lambda *a: print("[rm]", *a)) if os.environ.get("ARC_RMDBG") else (lambda *a: None)
        marks_door = self._marks(door)
        state = self.state()
        if not marks_door or not state:
            dbg("no marks/state", marks_door, state)
            return None
        want = min(marks_door)
        panel0 = min(state)
        # Tried and measured exactly inert: learn the half the DOOR is waiting on first,
        # in a strict pass before the general one, on the grounds that the search returns
        # the NEAREST unwatched press and will as happily go and learn a half that is
        # already right. Every per-level count came back identical, because the restriction
        # almost never bites — the panel differs from a door's ask in BOTH halves nearly
        # all the time on this board, so the wanted set is every half and the strict pass
        # is the general one.
        movers = [(k, self.mover_period(k)) for k in self.movers
                  if self.mover_period(k) and self.movers[k].get("halves")]
        # Letting LEARN mode through this guard on mute patrollers alone — a mover with
        # a period and no known half is exactly the thing to go and press, and level 7
        # reaches here with one to three of those in 1,034 of its 1,816 refusals — was
        # measured twice and **costs ls20 levels 5 AND 6 both times** (4/7, 20.489%).
        # First with the guard alone, where `period` degenerates to 1 and the plans press
        # blind; then with the mute periods folded into the LCM properly, where the score
        # comes back identical to the digit — so the deaths are not the degenerate phase
        # axis, they are the rung itself: on a board that HAS a ready mover coming, a
        # learn trip aimed at a mute one pre-empts the rungs that were winning the level.
        # Level 7's deadlock (nothing ever becomes ready because nothing is ever pressed
        # on purpose) needs a key that does not turn this lock: the board being WINDOWED,
        # which levels 5 and 6 never are — on a windowed board there are no square-changer
        # rungs pressing things by accident, so a deliberate trip to a mute patroller is
        # the only way anything ever becomes ready at all. `self.windowed` is set by the
        # play loop when the fog latch fires.
        # On a windowed board the recorded SQUARES can carry a whole plan with no ready
        # mover at all — level 7's ask is ink + ring + two quarter turns, every press of
        # it recorded under a square (the x54 sites hold the rotation, and `_step`
        # extrapolates a rotator to any value) — so the guard lets squares through.
        # Measured before this: 1,198 of the level's rounds died here with the halves
        # credited but no period on the same track id.
        if not movers and not (getattr(self, "windowed", False) and self.changers) \
                and not (learn and getattr(self, "windowed", False) and any(
                self.mover_period(k) and not self.movers[k].get("halves")
                for k in self.movers)):
            dbg("no ready movers: lvl=%s withp=%d withh=%d n=%d"
                % (getattr(self, "lvl", -1),
                   sum(1 for k in self.movers if self.mover_period(k)),
                   sum(1 for k in self.movers if self.movers[k].get("halves")),
                   len(self.movers)))
            return None
        # The combined period covers the mute patrollers when learn may aim at them:
        # with `movers` empty it otherwise degenerates to 1 and the phase axis vanishes.
        mute_p = [self.mover_period(k) for k in self.movers
                  if learn and self.mover_period(k) and not self.movers[k].get("halves")]
        period = 1
        for p in [p for _, p in movers] + (mute_p if not movers else []):
            g = _gcd(period, p)
            period = period // g * p
            if period > 64:
                return None                   # cycles that long are not yet believable
        # Patroller boxes per phase, indexed by ticks-from-now (1-based ahead).
        ahead_box = {k: [self.mover_at(k, m) for m in range(period + 1)]
                     for k, _ in movers}

        # Positions inside each marked plate, and the pair it wears. The DOOR's own
        # inside is the goal; any other marked plate is a toll gate on the way — paid
        # either with the panel matching its mark at that step, or by having ALREADY
        # been entered matched: a door passed that way stays open (measured, level 6),
        # and a plan may open one mid-route on the way to the one behind it.
        boxes = [b for b in self.icons if b not in self.displays]
        gates = {}
        for n, box in enumerate(boxes):
            o = {"x": [box[0], box[1]], "y": [box[2], box[3]]}
            w, h = model.box
            inside = {(x, y) for x, y in footprints_touching(grid, model, o)
                      if x >= box[0] and x + w <= box[1] + 1
                      and y >= box[2] and y + h <= box[3] + 1}
            if not inside and getattr(self, "windowed", False):
                # A door drawn as a HOLE (level 7): its interior is the void colour,
                # so the walkable filter above returns nothing and the door can never
                # be a goal. Enumerate the contained positions directly — entry is
                # still gated on the panel matching, and the engine enforces its own.
                inside = {(x, y) for x in range(box[0], box[1] + 2 - w)
                          for y in range(box[2], box[3] + 2 - h)}
            for p in inside:
                gates[p] = (n, self.icons[box])
        opened0 = sum(1 << n for n, b in enumerate(boxes) if b in self.opened)
        # The goal is THIS door's inside, not every plate that happens to wear the same
        # pair. The gates check above already demands the panel equal `want` on entry.
        goals = {p for p in gates
                 if p[0] >= door["x"][0] - model.box[0] and p[0] <= door["x"][1]
                 and p[1] >= door["y"][0] - model.box[1] and p[1] <= door["y"][1]}
        if not goals:
            dbg("no goals for door", door["x"], door["y"])
            return None

        picks = [footprints_touching(grid, model, f) for f in refills]

        w, h = model.box

        def presses(pos, m):
            """Which halves patrollers move on landing at `pos`, `m` ticks from now."""
            out = {}
            for k, _ in movers:
                b = ahead_box[k][m % period] if m % period else ahead_box[k][period]
                if b is None:
                    continue
                if (pos[0] < b[0] + b[2] and pos[0] + w > b[0]
                        and pos[1] < b[1] + b[3] and pos[1] + h > b[1]):
                    for half in self.movers[k].get("halves", ()):
                        out.setdefault(half, k)
            return out

        # A patroller with a period and NO known halves is not scenery, and `movers` above
        # cannot represent it: with no half to move it contributes nothing to `presses`, so
        # walking over it is not modelled as a press at all and the planner has no way to
        # go and find out what it does. That is what "nothing left to learn" was: measured
        # on level 6, **183 of the 189 rounds** the learn planner gave up on had two to
        # seven such patrollers on the board, every one of them carrying period 8, while
        # the search correctly reported no unknown press among the ones it could see —
        # even handed an infinite tank (159 of 189). In learn mode they ARE the unknown
        # press. `mover_at` reads each one against its own period, so the LCM above does
        # not have to cover them.
        mute = [k for k in self.movers
                if not self.movers[k].get("halves") and self.mover_period(k)] if learn else []
        mute_box = {k: [self.mover_at(k, m) for m in range(period + 1)] for k in mute}

        def unknown_mover(pos, m):
            """Does landing at `pos` `m` ticks from now press something never watched?"""
            for k in mute:
                b = mute_box[k][m % period] if m % period else mute_box[k][period]
                if b is None:
                    continue
                if (pos[0] < b[0] + b[2] and pos[0] + w > b[0]
                        and pos[1] < b[1] + b[3] and pos[1] + h > b[1]):
                    return True
            return False

        # On a WINDOWED board the changers are effectively square-pressable (one press
        # per re-entry — l7-model.md) and every press is recorded under its SQUARE, so
        # fold them into this search: one plan can then walk the ink, the shape ring,
        # the quarter turns and the refills — the composition level 7's ask demands,
        # which neither machinery could plan alone. Windowed only: everywhere else the
        # square rungs own these squares and this rung is silent by the movers guard.
        squares = dict(self.changers) if getattr(self, "windowed", False) else {}
        if squares:
            # rotator squares carry presses too — `_step` extrapolates them to any
            # value, but only squares in THIS set are ever pressed by the search:
            # the x54 virtual rotators lived in `rotates` alone and the ask sat
            # unreachable behind 1,680 "bfs exhausted" refusals.
            for pos_r, h_r in self.rotates:
                squares.setdefault(pos_r, set()).add(h_r)
        sq_edges = {h: self._edges(h) for hs in squares.values() for h in hs}

        fuel0 = left if left is not None else (full or 10 ** 6)
        seen = {(start, 0, panel0, 0, opened0): (fuel0, None)}
        q = deque([(start, 0, panel0, 0, opened0)])
        best = None
        while q and best is None:
            node = q.popleft()
            pos, t, panel, used, opened = node
            fuel = seen[node][0]
            if fuel <= 0:
                continue
            for a in model.dirs:
                nxt = step_to(model, pos, a, redirects)
                # A marked plate's inside is enterable when the panel matches — the
                # engine's own rule, checked at the gates test below. On level 7 the
                # door is a HOLE: its interior is the fog/void colour, so `walkable`
                # alone would keep the goal out of the search forever.
                if not walkable(grid, model, nxt[0], nxt[1]) \
                        and not (squares and nxt in gates):
                    continue
                t2 = (t + 1) % period
                hit = presses(nxt, t + 1)
                panel2, ok, blind = list(panel), True, False
                for half, k in hit.items():
                    got = self._mover_step(k, half, panel2[half])
                    if got is None:
                        # An unplannable press. Ordinarily that is ground not to walk
                        # on; when the job is to LEARN, it is the destination — but
                        # only with fuel left to spend on what it teaches, because a
                        # death resets the panel and the doors with it.
                        if learn and fuel - 1 >= 6:
                            blind = True
                            break
                        ok = False
                        break
                    panel2[half] = got
                # A recorded square changer presses on every arrival; walk the panel
                # through it the same way, and in learn mode an unknown edge is a
                # destination here too.
                if ok and not blind and nxt in squares:
                    for half in squares[nxt]:
                        got = self._step(nxt, half, panel2[half],
                                         sq_edges.get(half, {}))
                        if got is None:
                            if learn and fuel - 1 >= 6:
                                blind = True
                                break
                            ok = False
                            break
                        panel2[half] = got
                if not ok:
                    continue
                if learn and not blind and fuel - 1 >= 6 and unknown_mover(nxt, t + 1):
                    blind = True
                if blind:
                    acts, cur = [], node
                    while seen[cur][1]:
                        cur, act = seen[cur][1]
                        acts.append(act)
                    return acts[::-1] + [a], [False] * len(acts) + [True], 0
                panel2 = tuple(panel2)
                opened2 = opened
                if nxt in gates:
                    n, val = gates[nxt]
                    if opened & (1 << n):
                        pass                    # passed matched once already: it stays open
                    elif panel2 == val:
                        opened2 = opened | (1 << n)
                    else:
                        continue                # a checked gate, and the panel is wrong
                used2, fuel2 = used, fuel - 1
                for n, pk in enumerate(picks):
                    if nxt in pk and not used2 & (1 << n):
                        used2, fuel2 = used2 | (1 << n), full or fuel0
                key = (nxt, t2, panel2, used2, opened2)
                if key in seen and seen[key][0] >= fuel2:
                    continue
                seen[key] = (fuel2, (node, a))
                if nxt in goals and panel2 == want:
                    best = key
                    break
                q.append(key)
        if best is None:
            dbg("bfs exhausted: lvl=%s learn=%s states=%d want=%s panel0=%s movers=%s fuel0=%s"
                % (getattr(self, "lvl", -1), learn, len(seen), want, panel0,
                   [(k, p) for k, p in movers], fuel0))
            return None
        # How many checked gates this plan passes for the first time — the goal door's
        # own entry is among them. A plan through MORE gates has demonstrated more of
        # the lock, and the caller prefers it: entering the shallow door first was
        # measured to strand the piece there with no fuel for the one behind it.
        gates_opened = bin(best[4]).count("1") - bin(opened0).count("1")
        acts, cur = [], best
        while seen[cur][1]:
            cur, a = seen[cur][1]
            acts.append(a)
        acts = acts[::-1]
        # Re-walk the winning route for the per-action display prediction the play
        # loop validates a staged trip with.
        marks, pos, panel, m = [], start, panel0, 0
        for a in acts:
            pos = step_to(model, pos, a, redirects)
            m += 1
            hit = presses(pos, m)
            changed = False
            for half, k in hit.items():
                got = self._mover_step(k, half, panel[half])
                if got is not None and got != panel[half]:
                    panel = tuple(got if i == half else v for i, v in enumerate(panel))
                    changed = True
            if pos in squares:
                for half in squares[pos]:
                    got = self._step(pos, half, panel[half], sq_edges.get(half, {}))
                    if got is not None and got != panel[half]:
                        panel = tuple(got if i == half else v
                                      for i, v in enumerate(panel))
                        changed = True
            marks.append(changed)
        return acts, marks, gates_opened

    def changer_for(self, o):
        """The square that moves the half of the display this target disagrees on.

        With one changer this is just the changer. With two it is the difference between
        finishing the level and pressing the same square forever: `ls20` level 3 wants ink 9
        and a particular quarter turn, and the two are moved by squares 20 actions apart.
        """
        marks, state = self._marks(o), self.state()
        if not marks or not state or not self.changers:
            return self.changer
        want, here = min(marks), min(state)
        differ = {i for i, (a, b) in enumerate(zip(want, here)) if a != b}
        # On a windowed board, when both halves are wrong, go learn the BLIND one
        # first — the plannable half can be fixed any time, and the blind one is
        # the level's bottleneck: six deaths a run arrived wearing `#.#` because
        # the shape errand was always the life's last. Insertion order otherwise
        # (the ink square is learned first every life, so it used to win here).
        if getattr(self, "windowed", False) and len(differ) > 1:
            for h in sorted(differ,
                            key=lambda h: 0 if self.path_for(o, h) is None
                            and not self.exhausted(o, h) else 1):
                for pos, moves in self.changers.items():
                    if h in moves:
                        return pos
        for pos, moves in self.changers.items():
            if moves & differ:
                return pos
        # Nothing known moves the half that is wrong. Re-entering the square that moves the
        # other half is the cheapest way to never finish: on `ls20` level 3 the agent stood
        # on the colour-changer recolouring a shape that was never going to be right. No
        # answer here means the rung above gives way and ordinary exploration goes looking.
        return None if differ else self.changer
