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

from collections import deque

import numpy as np

from discover import walkable
from plan import step_to
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


class Gate:
    """What the board's displays are showing, and what was seen to change them.

    One per level: the mechanic carries across a level boundary but the positions do not.
    """

    def __init__(self):
        self.icons = {}        # plate box -> (ink colour, shape) when last looked at
        self.displays = set()  # plates that have changed: they report state
        self.changer = None    # (x, y) the piece was standing on when one changed
        self.tried = 0         # re-entries since the changer last actually changed one
        self.rejected = set()  # display states a door refused the piece under
        self.doubted = set()   # marks whose bitmap match the engine disagreed with
        self.changers = {}     # (x, y) -> which halves of a display it was seen to move
        self.heading = None    # where the last plan that existed was walking to
        self.cycles = {}       # (changer, half) -> {value seen: the value it became}

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
        return bool(changed)

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

        Two shapes compare equal when their collapsed bitmaps are equal, and collapsing runs
        of identical rows and columns is what makes a glyph comparable across the two scales
        it is drawn at. It also throws away detail, so equal is a **hypothesis**, and the
        engine is the oracle: a door that refuses the piece under some display state settles
        that state. Once the state the bitmaps agreed on has been refused, the comparison has
        been proved wrong for this plate, and every state that has not been tried is worth a
        try — there are only ever a handful.
        """
        if self.state() in self.rejected:
            return False
        marks = self._marks(o)
        return bool(marks & self.state()) or bool(marks & self.doubted)

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
        edges = {pos: step for (pos, h), step in self.cycles.items() if h == half and step}
        if here == want:
            return []
        if not edges:
            return None
        seen, queue = {here: []}, deque([here])
        while queue:
            cur = queue.popleft()
            for pos, step in edges.items():
                nxt = step.get(cur)
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
        return out if len(out) == len(wrong) else {}

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
