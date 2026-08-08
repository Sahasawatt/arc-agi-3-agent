"""The carry family: pick a crate up, carry it, drop it into the frame.

⚠️ WORK IN PROGRESS -- NOT wired into `compete.py`, so nothing under the sweep
gate is touched by this file. It does not clear a level yet. What is DONE and
what is left is at the bottom of this docstring.

`wa30` is the family on the public roster, and the signature is measured rather
than proposed: of the seventeen playable games it is the only one whose reset
frame shows two or more CRATES -- a rectangle whose border is one colour and
whose interior is a single other one -- with the biggest of them strictly bigger
than the rest and wearing an interior colour none of the others has
(`results/haul-sig.txt`). re86 shows eight crates and fails on `bigger`; cd82
shows two and fails the same way.

Mechanics, all measured offline (`results/wa30-*.txt`):

  * one action GRABS the crate the piece is facing: its border takes the piece's
    own edge colour and the two move as one body. A second press puts it down.
  * **the grab acts along the HEADING, and the heading is whichever way the piece
    last walked.** Arriving beside a crate sideways refuses -- the first hand
    solve died on exactly that, standing directly under a crate facing left. This
    is what the piece's one-row edge is for, and it is why every approach here
    ends with a step TOWARD the target.
  * a crate dropped over the frame slots in, and the frame interior cells beneath
    it are consumed for good -- still gone when the piece steps away, so the
    reading is not occlusion. The level ends on the press that empties it.
  * the piece is the union of its body and its edge, not the body alone: reading
    it by the body colour reports a position that shifts by one every time it
    turns (`results/wa30-p1.txt`).

Level 1 falls in 27 actions against a baseline of 71 BY HAND
(`results/wa30-solve.txt`); this rung is the attempt to derive that line rather
than replay it.

STATE (2026-08-08). It gets TWO of level 1's three crates into the frame --
the interior count falls 20 -> 12 -> 6, read from afar both times
(`results/wa30-haul9.txt`) -- and then livelocks. Seven bugs down, each with the
run that showed it, and six of the seven are one family: a reading taken from a
PART of a thing, or taken while something was standing on it.

  1. `moved()` took the first translating colour and got the piece's 4-cell
     heading edge, not its 12-cell body -> dirs (0, 7) and (7, 0) on a step-4
     board (`wa30-haul-dbg.txt`). Takes the largest now.
  2. `blob()` flood-filled all non-background, so a carried crate touching the
     frame swallowed the frame (`wa30-haul-dbg.txt` i=16). Restricted to the
     piece's own latched colours.
  3. `_slots()` offered rectangles off the crates' stride, which no plan can
     reach. Filtered to the lattice.
  4. Displacement must come from the piece's whole BOUNDING BOX: its body is a
     4x3 that swaps ends on a turn, so a heading change translates it by the step
     minus one -- dirs[2] read (0, 3) (`wa30-haul-dbg2.txt`).
  5. A refused probe has to count as ATTEMPTED. At reset the piece stands under a
     crate, so UP never moves and the bootstrap pressed it forever
     (`wa30-haul3.txt`).
  6. `_approach` walked two steps back and one forward, parking one square short,
     so every grab fired from nowhere (`wa30-haul5.txt`, plan [2, 1, 5] on loop).
  7. The frame must be LATCHED. Once the first crate slots in, its interior is no
     longer one colour, `crates()` stops seeing it, and the "biggest" becomes an
     ordinary crate -- which carried the second one off the board
     (`wa30-haul6.txt` i=25). Its slots are latched with it, because reading them
     live counts whatever the piece is standing on as filled: the free count
     oscillated 20 -> 14 -> 12 -> 14 -> 6 while nothing was dropped
     (`wa30-haul7.txt`).

WHAT IS LEFT, named: the grab acts along the HEADING, so it takes whatever the
piece happens to be facing -- not the crate the plan chose. After two crates are
in, the route to the third leaves the piece facing a crate already slotted and
picks it straight back OUT of the frame (`wa30-haul9.txt` i=22-24, interior 12 ->
14). The approach has to guarantee the final heading points at the INTENDED
crate, and a crate whose position is inside the frame must never be a candidate
under any heading. Everything downstream of that -- the carry and the drop -- is
already measured working.
"""

import sys

import numpy as np

DIRS = (1, 2, 3, 4)
GRAB = 5


def grid_of(obs):
    """The full frame, or None -- the engine hands back empty ones mid-level."""
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def background(g):
    return int(np.bincount(g.ravel()).argmax())


def crates(g):
    """[(w, h, ring, inner, x0, y0)] largest first -- rectangles with a uniform
    border of one colour and an interior of a single other colour."""
    out, seen = [], set()
    H, W = g.shape
    for y0 in range(H - 3):
        for x0 in range(W - 3):
            if (x0, y0) in seen:
                continue
            c = int(g[y0, x0])
            x1, y1 = x0, y0
            while x1 + 1 < W and int(g[y0, x1 + 1]) == c:
                x1 += 1
            while y1 + 1 < H and int(g[y1 + 1, x0]) == c:
                y1 += 1
            w, h = x1 - x0 + 1, y1 - y0 + 1
            if w < 3 or h < 3:
                continue
            if not ((g[y0, x0:x1 + 1] == c).all() and (g[y1, x0:x1 + 1] == c).all()
                    and (g[y0:y1 + 1, x0] == c).all() and (g[y0:y1 + 1, x1] == c).all()):
                continue
            vals = set(g[y0 + 1:y1, x0 + 1:x1].ravel().tolist())
            if len(vals) != 1 or int(next(iter(vals))) == c:
                continue
            out.append((w, h, c, int(next(iter(vals))), x0, y0))
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    seen.add((xx, yy))
    return sorted(out, reverse=True)


def signature(g):
    """Two or more crates, the biggest strictly bigger than the rest and wearing
    an interior colour none of them has. wa30 alone of the seventeen at reset
    (`results/haul-sig.txt`)."""
    if g is None or g.ndim < 2:
        return False
    cr = crates(g)
    if len(cr) < 2:
        return False
    big, rest = cr[0], cr[1:]
    return (big[0] * big[1] > rest[0][0] * rest[0][1]
            and len({c[2] for c in rest}) == 1
            and big[3] not in {c[3] for c in rest})


def shifted(prev, cur, colour):
    """The vector `colour` moved by, or None if it did not move as a rigid body."""
    a = set(zip(*np.nonzero(prev == colour)[::-1]))
    b = set(zip(*np.nonzero(cur == colour)[::-1]))
    if not a or len(a) != len(b) or a == b:
        return None
    d = (min(x for x, _ in b) - min(x for x, _ in a),
         min(y for _, y in b) - min(y for _, y in a))
    return d if {(x + d[0], y + d[1]) for x, y in a} == b else None


def moved(prev, cur):
    """(colour, vector) of the LARGEST body that translated, or (None, None).

    Largest, not first: the piece's heading edge is a rigid translate too while
    the heading holds, and taking it made `dirs` read (0, 7) and (7, 0) on a
    board whose step is 4 -- because the edge changes SIDE when the piece turns,
    which moves its bounding box by the piece's width minus one
    (`results/wa30-haul-dbg.txt`). The body outnumbers its own edge."""
    best = (None, None, 0)
    for c in sorted(set(prev.ravel().tolist()) & set(cur.ravel().tolist())):
        d = shifted(prev, cur, c)
        if d is not None and d != (0, 0):
            n = int((prev == c).sum())
            if n > best[2]:
                best = (c, d, n)
    return best[0], best[1]


def blob(g, colour, allowed):
    """The connected region containing `colour`, restricted to the piece's OWN
    colours.

    Not "everything that is not background": a carried crate is repainted into
    the piece's edge colour, so the moment it touches the frame a flood fill over
    non-background swallows the frame too and the piece reads 16 cells wide
    (`results/wa30-haul-dbg.txt` i=16)."""
    ys, xs = np.nonzero(g == colour)
    if not len(ys):
        return None
    H, W = g.shape
    stack, seen = [(int(xs[0]), int(ys[0]))], set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < W and 0 <= y < H):
            continue
        if int(g[y, x]) not in allowed:
            continue
        seen.add((x, y))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            stack.append((x + dx, y + dy))
    return seen


class Haul:
    """Drives one game. `act(grid, level)` returns the next action value or None.

    None means "not my board" or "out of ideas" -- the caller falls back to its
    own machinery, so a wrong reading costs actions and never the run.
    """

    def __init__(self, values):
        self.on = set(DIRS) | {GRAB} <= set(values)
        self.lvl = None
        self.body = None      # the colour the arrows drive
        self.base = None      # (w, h) of the piece alone, before any crate
        self.dirs = {}        # action -> its measured displacement
        self.mine = None      # the piece's own colour set, latched
        self.prev = None
        self.last = None
        self.queue = []       # actions already decided
        self.done = False
        self.stuck = 0
        self.lattice = None   # the piece's own (x, y) parity, latched at base
        self.was = None       # the piece's top-left last round
        self.tried = set()    # directions asked since the last reposition
        self.frame = None     # the target rectangle, latched per level
        self.slotlist = None  # its slots, latched with it
        self.filled = set()   # slots a crate has been sent to
        self.claim = None     # the slot the plan in hand is for

    # -- reading -----------------------------------------------------------
    def _piece(self, g, bg):
        if self.body is None:
            return None
        if self.mine is None:
            # the piece's own colours, learned once while it stands alone
            first = blob(g, self.body,
                         set(g.ravel().tolist()) - {bg})
            if not first:
                return None
            self.mine = {int(g[y, x]) for x, y in first}
        cells = blob(g, self.body, self.mine)
        if not cells:
            return None
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        return (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)

    def _carrying(self, box):
        return self.base is not None and (box[2], box[3]) != self.base

    def _held_rect(self, g, box):
        """Where the carried crate sits inside the piece's blob: the base-sized
        half that holds none of the body colour."""
        bw, bh = self.base
        x, y, w, h = box
        if h > bh:      # stacked vertically
            top = (x, y, bw, bh)
            ys = np.nonzero(g[y:y + bh, x:x + bw] == self.body)[0]
            return (x, y + h - bh, bw, bh) if len(ys) else top
        ok = np.nonzero(g[y:y + bh, x:x + bw] == self.body)[1]
        return (x + w - bw, y, bw, bh) if len(ok) else (x, y, bw, bh)

    def _slots(self, g, frame):
        """Free slot rectangles, from the frame as it was LATCHED plus a record of
        what has been dropped -- never re-read live.

        Reading the interior each round counts whatever the piece is standing on
        as filled: the free-cell count oscillated 20 -> 14 -> 12 -> 14 -> 6 -> 14
        across consecutive rounds while nothing was dropped, and the plan flipped
        with it (`results/wa30-haul7.txt`). The piece covers what it stands on --
        the repo's oldest trap, in a new place.
        """
        if self.slotlist is None:
            w, h, ring, inner, fx, fy = frame
            bw, bh = self.base
            sx = abs(next((d[0] for d in self.dirs.values() if d[0]), 0)) or 1
            sy = abs(next((d[1] for d in self.dirs.values() if d[1]), 0)) or 1
            out = []
            for y in range(fy, fy + h - bh + 1):
                for x in range(fx, fx + w - bw + 1):
                    if (x - self.lattice[0]) % sx or (y - self.lattice[1]) % sy:
                        continue
                    sub = g[y:y + bh, x:x + bw]
                    if (sub == inner).any() and                             set(sub.ravel().tolist()) <= {inner, ring}:
                        out.append((x, y, int((sub == inner).sum())))
            self.slotlist = sorted(out, key=lambda t: -t[2])
        return [t for t in self.slotlist if (t[0], t[1]) not in self.filled]

    # -- the round ---------------------------------------------------------
    def act(self, g, lvl):
        if not self.on or g is None or g.ndim < 2:
            return None
        if lvl != self.lvl:
            self.lvl, self.queue, self.done, self.stuck = lvl, [], False, 0
            self.prev, self.last = None, None
            self.base, self.mine, self.lattice = None, None, None
            self.was, self.tried, self.frame = None, set(), None
            self.slotlist, self.filled, self.claim = None, set(), None
        if self.done:
            return None
        bg = background(g)

        if self.prev is not None and self.last in DIRS:
            c, d = moved(self.prev, g)
            if c is not None and self.body is None:
                self.body = c
            # The DISPLACEMENT comes from the piece's whole bounding box, never
            # from one of its colours. The body is a 4x3 that swaps ends when the
            # piece turns, so it translates by the step MINUS ONE on any move that
            # changes heading -- measured as dirs[2] = (0, 3) on a board whose
            # step is 4 (`results/wa30-haul-dbg2.txt`). The union of the piece's
            # colours is the only part of it that is rigid.
            now = self._piece(g, bg)
            if now is not None and self.was is not None and                     (now[0], now[1]) != self.was:
                self.dirs[self.last] = (now[0] - self.was[0], now[1] - self.was[1])
            if c is None and not self.queue:
                self.stuck += 1
                if self.stuck > 6:
                    self.done = True
                    return None
            if c is not None:
                self.stuck = 0

        # The piece is read, and `was` recorded, BEFORE any early return. Setting
        # it only on the planning path left it None for the whole bootstrap, so
        # every displacement was measured against nothing and `dirs` stayed empty
        # while the piece was visibly walking (`results/wa30-haul4.txt`).
        box = self._piece(g, bg) if self.body is not None else None
        if box is not None:
            if self.base is None:
                self.base, self.lattice = (box[2], box[3]), (box[0], box[1])
            self.was = (box[0], box[1])

        if self.body is None:
            self.prev, self.last = g, next((a for a in DIRS if a not in self.dirs), 1)
            return self.last
        # A probe the board REFUSED still counts as attempted. At reset the piece
        # stands directly under a crate, so UP never moves it, and retrying until
        # a displacement appears presses the same blocked action forever
        # (`results/wa30-haul3.txt`, i=9) -- the sp80 lesson that only two of five
        # actions move anything from a starting corner. When all four have been
        # asked and some are still unknown, walk one step on a direction that DOES
        # work and ask the rest again from there.
        unknown = [a for a in DIRS if a not in self.dirs and a not in self.tried]
        if unknown:
            self.tried.add(unknown[0])
            self.prev, self.last = g, unknown[0]
            return unknown[0]
        if len(self.dirs) < len(DIRS):
            if not self.dirs:
                self.done = True
                return None
            self.tried = set()
            a = sorted(self.dirs)[0]
            self.prev, self.last = g, a
            return a

        if box is None:
            self.done = True
            return None

        if self.queue:
            a = self.queue.pop(0)
            self.prev, self.last = g, a
            return a

        self.claim = None
        plan = self._plan(g, box)
        if not plan:
            self.done = True
            return None
        if self.claim is not None:
            self.filled.add(self.claim)
            self.claim = None
        self.queue = plan[1:]
        self.prev, self.last = g, plan[0]
        return plan[0]

    # -- planning ----------------------------------------------------------
    def _step(self, a):
        return self.dirs[a]

    def _walk(self, frm, to):
        """Axis-by-axis walk. The boards this fires on are open; a refusal simply
        leaves the piece where it was and the next round replans from the frame."""
        out, (x, y) = [], frm
        for axis in (0, 1):
            while (to[axis] - (x, y)[axis]) != 0:
                gap = to[axis] - (x, y)[axis]
                cand = [a for a, d in self.dirs.items()
                        if d[axis] and (d[axis] > 0) == (gap > 0) and not d[1 - axis]]
                if not cand:
                    return None
                a = cand[0]
                d = self._step(a)
                if abs(d[axis]) > abs(gap):
                    return None
                out.append(a)
                x, y = x + d[0], y + d[1]
                if len(out) > 60:
                    return None
        return out if (x, y) == to else None

    def _approach(self, frm, target, side):
        """Reach the square touching `target` on `side`, ARRIVING along `side` so
        the heading faces the crate. The last step is always toward it."""
        d = self._step(side)
        # `target` IS the square to stand on. Walk to the one step BEFORE it and
        # take a single step along `side`, which both lands on the target and
        # leaves the heading facing the crate. Walking two steps back and one
        # forward parks one square short, so the grab fires from nowhere and the
        # rung relivelocks on the same plan forever (`results/wa30-haul5.txt`,
        # plan [2, 1, 5] repeating from i=12).
        legs = self._walk(frm, (target[0] - d[0], target[1] - d[1]))
        return None if legs is None else legs + [side]

    def _plan(self, g, box):
        cr = crates(g)
        # The frame is LATCHED for the level. Once the first crate is slotted its
        # interior is no longer a single colour, so `crates()` stops seeing the
        # frame at all and the "biggest" becomes an ordinary crate -- which is how
        # the second crate got carried off the board (`results/wa30-haul6.txt`,
        # i=25, frame read as (4, 4, 4, 9, 32, 36)). A signature detector and a
        # per-round tracker are not the same instrument, the same lesson as
        # `swap.py`'s clock bands.
        if self.frame is None:
            if len(cr) < 2 or cr[0][0] * cr[0][1] <= cr[1][0] * cr[1][1]:
                return None
            self.frame = cr[0]
        frame = self.frame
        fx0, fy0 = frame[4], frame[5]
        fx1, fy1 = fx0 + frame[0] - 1, fy0 + frame[1] - 1
        cr = [c for c in cr
              if not (fx0 <= c[4] <= fx1 and fy0 <= c[5] <= fy1)]
        bw, bh = self.base
        here = (box[0], box[1])

        if self._carrying(box):
            hx, hy, _, _ = self._held_rect(g, box)
            off = (hx - box[0], hy - box[1])
            for sx, sy, _n in self._slots(g, frame):
                legs = self._walk(here, (sx - off[0], sy - off[1]))
                if legs is not None:
                    # CLAIMED, not committed: `_plan` must stay free of side
                    # effects or anything that calls it twice -- a debug trace
                    # did -- books slots that were never used
                    # (`results/wa30-haul8.txt` showed two filled before the
                    # first drop). `act` commits it.
                    self.claim = (sx, sy)
                    return legs + [GRAB]
            return None

        for w, h, ring, inner, cx, cy in cr:
            if (cx, cy) in self.filled:
                continue
            if (w, h) != (bw, bh):
                continue
            for side in DIRS:
                d = self._step(side)
                # the square the piece stands on to face this crate along `side`
                tx = cx - d[0] * bw if d[0] else cx
                ty = cy - d[1] * bh if d[1] else cy
                if d[0] and d[0] < 0:
                    tx = cx + w
                if d[1] and d[1] < 0:
                    ty = cy + h
                legs = self._approach(here, (tx, ty), side)
                if legs is not None:
                    return legs + [GRAB]
        return None


if __name__ == "__main__":   # offline harness: play with nothing else in the loop
    import arc_agi

    game = sys.argv[1] if len(sys.argv) > 1 else "wa30"
    want = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    env = arc.make(envs[game].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    h = Haul([a.value for a in env.action_space if not a.is_complex()])
    print("signature:", signature(grid_of(obs)))
    per, spent, done = [], 0, obs.levels_completed
    for i in range(want):
        v = h.act(grid_of(obs), obs.levels_completed)
        if v is None:
            print(f"i={i} out of ideas at level {obs.levels_completed + 1}")
            break
        obs = env.step(A[v])
        spent += 1
        if obs is None or grid_of(obs) is None or \
                not str(obs.state).endswith("NOT_FINISHED"):
            if obs is None:
                break
            obs = env.reset()
            if obs is None or grid_of(obs) is None:
                break
            continue
        if obs.levels_completed > done:
            per.append(spent)
            spent, done = 0, obs.levels_completed
            print(f"  level {done} cleared, actions={per[-1]} (i={i})")
    print("levels completed:", 0 if obs is None else obs.levels_completed, per)
