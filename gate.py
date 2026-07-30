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
    for c in np.unique(grid):
        for x0, x1, y0, y1, _ in components(grid, int(c)):
            if not MIN_SIDE <= x1 - x0 + 1 <= wide or not MIN_SIDE <= y1 - y0 + 1 <= tall:
                continue
            if not _framed(grid, x0, x1, y0, y1, int(c)):
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
        # Marked plates the piece has STOOD INSIDE. The engine only lets it in matched,
        # and a door passed that way stays open: measured on `ls20` level 6, door B
        # refused (9, A-glyph) cold and passed it after one matched entry. A death puts
        # the panel back, so the caller clears this when a life ends.
        self.opened = set()

    def observe(self, frame, at, walked):
        """Look at the plates. Returns True if any display changed since the last look.

        A plate is remembered as **(ink colour, shape)**, because both are part of what it
        says. `ls20` level 3 has two things that change the indicator and they change
        different halves of it: the white cross turns the shape a quarter turn, and the
        multi-coloured square recolours the ink — 12, then 9, then 14. Its goal box is drawn
        in 9, so a run that compares shapes alone walks to a door wearing the right shape in
        the wrong colour and is refused, which is exactly what happened.
        """
        now, old = plates(frame), self.icons

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
        moved = {i for box in changed
                 for i, (was, is_) in enumerate(zip(self.icons.get(box, now[box]), now[box]))
                 if was != is_}
        self.displays |= changed
        # And keep the last reading of one that has stopped being reported *because the
        # piece is on it*. A refill that has been taken is gone for good, and remembering
        # that one leaves the planner routing to fuel that is not there.
        kept = {k: v for k, v in self.icons.items() if k not in now and under_piece(k)}
        self.icons = {**kept, **now}
        # Losing a life also rewrites the display, and teleports the piece back to the
        # start; reading that as a discovery would name the starting square as the changer.
        if changed and walked and at is not None:
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
            for box in changed:
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
            for k, info in self.movers.items():
                hist = info["hist"]
                b = hist[-1][1] if hist and hist[-1][0] == self.ticks else None
                if b is None:
                    b = self.mover_at(k, 0)
                if not b or not (at[0] < b[0] + b[2] and at[0] + fw > b[0]
                                 and at[1] < b[1] + b[3] and at[1] + fh > b[1]):
                    continue
                info.setdefault("halves", set()).update(moved)
                for box in changed:
                    before, after = old.get(box), now[box]
                    if before is not None:
                        for hh in moved:
                            self.mover_edges.setdefault((k, hh), {})[before[hh]] = after[hh]
        return bool(changed)

    def track(self, boxes, body, moved, at=None):
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
                return p
        return None

    def mover_at(self, k, ahead):
        """The object's box `ahead` piece-moves from now, read off its phase map.

        None when that phase has never been observed — which is exactly the occluded
        stretch of the lap; the components of the same patroller that survive the piece
        passing over are the ones that answer there."""
        p = self.mover_period(k)
        if p is None:
            return None
        by = {}
        for t, b in self.movers[k]["hist"]:
            if t > self.ticks - 3 * p:
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
        states = {v for (pos, h), step in self.cycles.items() if h == half
                  for v in list(step) + list(step.values())}
        return len(states) >= seen_states and self.path_for(o, half) is None

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
                     redirects=None):
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
        """
        dbg = (lambda *a: print("[rm]", *a)) if os.environ.get("ARC_RMDBG") else (lambda *a: None)
        marks_door = self._marks(door)
        state = self.state()
        if not marks_door or not state:
            dbg("no marks/state", marks_door, state)
            return None
        want = min(marks_door)
        panel0 = min(state)
        movers = [(k, self.mover_period(k)) for k in self.movers
                  if self.mover_period(k) and self.movers[k].get("halves")]
        if not movers:
            dbg("no ready movers")
            return None
        period = 1
        for _, p in movers:
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
                if not walkable(grid, model, nxt[0], nxt[1]):
                    continue
                t2 = (t + 1) % period
                hit = presses(nxt, t + 1)
                panel2, ok = list(panel), True
                for half, k in hit.items():
                    got = self._mover_step(k, half, panel2[half])
                    if got is None:
                        ok = False              # an unplannable press: do not walk there
                        break
                    panel2[half] = got
                if not ok:
                    continue
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
            dbg("bfs exhausted: states=%d want=%s panel0=%s movers=%s fuel0=%s"
                % (len(seen), want, panel0, [(k, p) for k, p in movers], fuel0))
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
            marks.append(changed)
        return acts, marks, gates_opened

    def route_learn(self, grid, model, start, target, refills, full, left,
                    redirects=None):
        """Actions that press patroller `target` once, fuel-aware, or None.

        The moving planner can only plan through edges it has WATCHED, and a level can
        ask for a value whose path nobody has pressed yet: `ls20` level 6's second door
        wants a glyph five presses down an alphabet the agent has no reason to walk.
        One deliberate press teaches the next edge; replanning after it chains the rest.
        The press has to leave enough in the tank to matter — a press the piece starves
        on resets the panel with it (the blind-probe lesson, again).
        """
        p = self.mover_period(target)
        if p is None:
            return None
        boxes = [b for b in self.icons if b not in self.displays]
        blocked = set()
        for box in boxes:
            if box in self.opened:
                continue
            o = {"x": [box[0], box[1]], "y": [box[2], box[3]]}
            w, h = model.box
            blocked |= {(x, y) for x, y in footprints_touching(grid, model, o)
                        if x >= box[0] and x + w <= box[1] + 1
                        and y >= box[2] and y + h <= box[3] + 1}
        picks = [footprints_touching(grid, model, f) for f in refills]
        w, h = model.box
        fuel0 = left if left is not None else (full or 10 ** 6)
        seen = {(start, 0, 0): (fuel0, None)}
        q = deque([(start, 0, 0)])
        while q:
            node = q.popleft()
            pos, t, used = node
            fuel = seen[node][0]
            if fuel <= 0:
                continue
            for a in model.dirs:
                nxt = step_to(model, pos, a, redirects)
                if nxt in blocked or not walkable(grid, model, nxt[0], nxt[1]):
                    continue
                t2 = (t + 1) % p
                used2, fuel2 = used, fuel - 1
                for n, pk in enumerate(picks):
                    if nxt in pk and not used2 & (1 << n):
                        used2, fuel2 = used2 | (1 << n), full or fuel0
                key = (nxt, t2, used2)
                if key in seen and seen[key][0] >= fuel2:
                    continue
                seen[key] = (fuel2, (node, a))
                b = self.mover_at(target, t + 1)
                if (b is not None and fuel2 >= 6
                        and nxt[0] < b[0] + b[2] and nxt[0] + w > b[0]
                        and nxt[1] < b[1] + b[3] and nxt[1] + h > b[1]):
                    acts, cur = [], key
                    while seen[cur][1]:
                        cur, act = seen[cur][1]
                        acts.append(act)
                    return acts[::-1]
                q.append(key)
        return None

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
        for pos, moves in self.changers.items():
            if moves & differ:
                return pos
        # Nothing known moves the half that is wrong. Re-entering the square that moves the
        # other half is the cheapest way to never finish: on `ls20` level 3 the agent stood
        # on the colour-changer recolouring a shape that was never going to be right. No
        # answer here means the rung above gives way and ordinary exploration goes looking.
        return None if differ else self.changer
