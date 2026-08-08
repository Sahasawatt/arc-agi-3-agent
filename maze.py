"""The fixed-pitch maze family: walk a notched heading-piece through a wall
lattice read directly from the frame to a distinct goal block.

`tu93` is the family on the public roster. The signature is measured, not
assumed (`results/maze-sig.txt`): a "notched" 3x3 window -- one body colour
filling 8 of its 9 cells, a second colour filling the ninth -- is how tu93's
heading-marked piece renders. Sliding a 3x3 window over all 64x64 positions
of a game's reset frame finds this pattern by *accident* all over busy or
rounded art (0 to 69 hits across the other sixteen games); tu93 alone comes
back with **exactly one**, because its board is otherwise a clean two-colour
grid where a 3x3 window almost never lands on an 8:1 split. `notched_all()`
== 1 hit is therefore the signature, not merely "at least one".

Mechanics, all measured offline (`results/tu93-*.txt`):

  * the piece is a notched 3x3: one body colour filling 8 cells, the ninth
    cell (a second colour) rotating to whichever side the piece last moved
    -- it names the heading. The union of both colours is the only rigid
    reading: on a heading-changing press the missing cell moves to a
    *different* side, so the body colour ALONE is not a pure translation of
    itself between those two frames (it is missing a different cell each
    time), and a `shifted()`-style rigid-body check on it would wrongly
    refuse a real move.
  * the four actions are ordinary fixed directions, one lattice step per
    press, and the mapping is not assumed -- it is read off the piece's own
    displacement, the same as every other whole-game driver here (one game
    in this roster answers ACTION3 with right).
  * corridors and walls share the lattice with the piece and the goal, in
    two more colours; there is no need to name which is which -- the colour
    sitting in the gap of the FIRST successful press is "open", learned
    once and read off every frame after that. A colour never seen in an
    open gap is treated as blocked, never guessed passable (this also
    quietly retires the board edge itself: pressing off the maze into the
    background colour never succeeds, so background never enters the open
    set).
  * the goal is a single solid block, the size of the piece, in a colour
    that is none of the above and forms exactly one connected region on the
    board -- unlike a wall or corridor colour, which always tiles the maze
    in many separate pieces (or one hole-riddled network, never a solid
    rectangle). Reaching it -- the piece's box landing on the goal's own
    box -- ends the level.

The sweep keeps no plan: BFS is re-run from the actual position every round,
so a death or a misread costs at most one action, never a stale plan.
"""

import sys
from collections import deque

import numpy as np

DIRS = (1, 2, 3, 4)
STUCK_LIMIT = 40   # consecutive no-progress presses before handing back control


def grid_of(obs):
    """The full frame, or None -- the engine hands back empty ones mid-level."""
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def bands(g):
    """Single-colour full-width rows touching an edge, merged into contiguous
    bands -- the budget bar, excluded from every terrain read."""
    bg = int(np.bincount(g.ravel()).argmax())
    rows_, out = [], []
    for y in range(g.shape[0]):
        c = int(g[y, 0])
        if c != bg and (g[y] == c).all():
            rows_.append((y, c))
    for y, c in rows_:
        if out and out[-1][2] == c and out[-1][1] == y - 1:
            out[-1] = (out[-1][0], y, c)
        else:
            out.append((y, y, c))
    return [b for b in out if b[0] == 0 or b[1] == g.shape[0] - 1]


def notched_all(g, exclude):
    """Every solid 3x3 window with exactly two colours -- 8 cells of one, 1
    of the other -- neither in `exclude` -> [(x0, y0, body, notch)]."""
    out = []
    H, W = g.shape
    for y0 in range(H - 2):
        for x0 in range(W - 2):
            win = g[y0:y0 + 3, x0:x0 + 3]
            vals, counts = np.unique(win, return_counts=True)
            if len(vals) != 2 or 8 not in counts.tolist():
                continue
            counts_l = counts.tolist()
            body = int(vals[counts_l.index(8)])
            notch = int(vals[counts_l.index(1)])
            if body in exclude or notch in exclude:
                continue
            out.append((x0, y0, body, notch))
    return out


def signature(g):
    """Exactly one notched 3x3 window at reset -- tu93 alone of the
    seventeen playable games (`results/maze-sig.txt`: 0 for five games, 1
    for tu93, 3-69 for the rest -- "at least one" is not the discriminator,
    the exact count is)."""
    if g is None or g.ndim < 2:
        return False
    bg = int(np.bincount(g.ravel()).argmax())
    return len(notched_all(g, {bg})) == 1


def blocks(g, exclude, size):
    """Solid single-colour rectangles the SAME size as the piece, whose
    colour forms exactly ONE connected region on the board and is not in
    `exclude` -> [(cells, colour, x0, y0, w, h)].

    A wall or corridor colour tiles the maze in many disconnected pieces (or
    one connected but hole-riddled network), which the "one region" filter
    catches -- but level 2 also has small decorations (a lone 1-cell speck,
    an 8-cell non-rectangular blob) that pass THAT filter too and are
    smaller than the real goal, so an unsized pick returns the wrong one
    (`results/tu93-l2-goal.txt`). Matching the piece's own size is what
    tells the goal from the decorations."""
    out = []
    for c in set(g.ravel().tolist()) - set(exclude):
        ys, xs = np.nonzero(g == c)
        cells = set(zip(xs.tolist(), ys.tolist()))
        blobs = []
        while cells:
            stack, blob = [next(iter(cells))], set()
            while stack:
                p = stack.pop()
                if p in blob or p not in cells:
                    continue
                blob.add(p)
                x, y = p
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (x + dx, y + dy) in cells:
                        stack.append((x + dx, y + dy))
            cells -= blob
            blobs.append(blob)
        if len(blobs) != 1:
            continue
        blob = blobs[0]
        bx = [p[0] for p in blob]
        by = [p[1] for p in blob]
        w, h = max(bx) - min(bx) + 1, max(by) - min(by) + 1
        if len(blob) == w * h and (w, h) == size:
            out.append((len(blob), c, min(bx), min(by), w, h))
    return sorted(out)


def find_goal(g, exclude, size):
    """The lone solid isolated rectangle the piece's own size -> (x0, y0, w,
    h), or None."""
    b = blocks(g, exclude, size)
    return (b[0][2], b[0][3], b[0][4], b[0][5]) if b else None


def _gap(box, d, size):
    """The pixel rectangle between two adjacent lattice positions -> (x0,
    y0, w, h), or None if the step equals the piece's own extent (adjacent
    cells, nothing between them to read)."""
    x, y, w, h = box[0], box[1], size[0], size[1]
    dx, dy = d
    if dx:
        x0 = x + w if dx > 0 else x + dx + w
        gw, y0, gh = abs(dx) - w, y, h
    else:
        y0 = y + h if dy > 0 else y + dy + h
        gh, x0, gw = abs(dy) - h, x, w
    return (x0, y0, gw, gh) if gw > 0 and gh > 0 else None


def _gap_colours(g, box, d, size):
    """The colours found in the gap, read from `g` -- pass the PRE-move
    frame so the piece's own body never occludes the strip it is about to
    cross (the repo's oldest trap, in a new place)."""
    r = _gap(box, d, size)
    if r is None:
        return set()
    x0, y0, w, h = r
    strip = g[y0:y0 + h, x0:x0 + w]
    return set(strip.ravel().tolist()) if strip.size else set()


def _passable(g, box, d, size, open_colours):
    """True iff every pixel in the gap is a colour already proven open.
    Adjacent cells (no gap) are always passable; an unproven colour is
    treated as blocked, never guessed open."""
    r = _gap(box, d, size)
    if r is None:
        return True
    x0, y0, w, h = r
    strip = g[y0:y0 + h, x0:x0 + w]
    return bool(strip.size) and set(strip.ravel().tolist()) <= open_colours


def lattice_bfs(start, goal, dirs, size, open_colours, g, avoid=frozenset()):
    """Shortest press sequence on the piece's own lattice, walls read
    directly from THIS frame -- no bumping. `avoid` is target cells already
    proven fatal (a moving hazard, not a wall) so a repeat life does not
    repeat the same death."""
    H, W = g.shape
    w, h = size
    q, seen = deque([(start, [])]), {start}
    while q:
        pos, path = q.popleft()
        if pos == goal:
            return path
        for a, (dx, dy) in dirs.items():
            nxt = (pos[0] + dx, pos[1] + dy)
            if nxt in seen or nxt in avoid or not (0 <= nxt[0] <= W - w and 0 <= nxt[1] <= H - h):
                continue
            if not _passable(g, pos, (dx, dy), size, open_colours):
                continue
            seen.add(nxt)
            q.append((nxt, path + [a]))
    return None


class Maze:
    """Drives one game. `act(grid, level)` returns the next action value or
    None.

    None means "not my board" or "out of ideas" -- the caller falls back to
    its own machinery, so a wrong reading costs actions and never the run.
    """

    def __init__(self, values):
        self.on = set(DIRS) <= set(values)
        self.lvl = None
        # Game facts, learned once and kept across levels (the same
        # convention as `swap.py`'s driven colour and `haul.py`'s arrow
        # mapping -- the physical piece and its controls do not change
        # level to level, only the maze layout and the goal position do).
        self.dirs = {}
        self.open_colours = set()
        self.body = None
        self.notch = None
        self.size = None
        # Per-level state.
        self.goal = None
        self.prev = None
        self.last = None
        self.tried = set()
        self.stuck = 0
        self.watch = {}      # latched budget-band colour -> its last count
        self.latched = False
        self.avoid = set()   # lattice targets a GAME_OVER landed on -- not walls,
                              # a moving hazard, but routing around it is the same
                              # move either way
        self.done = False

    # -- reading ------------------------------------------------------
    def _piece_box(self, g):
        if self.body is None:
            return None
        ys, xs = np.nonzero((g == self.body) | (g == self.notch))
        if not len(xs):
            return None
        return (int(xs.min()), int(ys.min()),
                int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))

    def _fresh_life(self, g):
        """A watched budget-band colour whose count went UP is a refill: a
        GAME_OVER reset the piece to the level's start. Re-reading `bands()`
        every round cannot see this -- the band is a full-width row only
        while it is full, so it drops out the moment one cell burns
        (`swap.py`'s exact lesson, same trap, new game). The colours are
        latched from the level's first frame and counted whole thereafter."""
        if not self.latched:
            self.watch = {c: int((g == c).sum()) for _, _, c in bands(g)}
            self.latched = True
            return False
        up = False
        for c, was in self.watch.items():
            n = int((g == c).sum())
            if n > was:
                up = True
            self.watch[c] = n
        return up

    # -- the round ------------------------------------------------------
    def act(self, g, lvl):
        if not self.on or g is None or g.ndim < 2:
            return None
        if lvl != self.lvl:
            self.lvl, self.goal, self.done = lvl, None, False
            self.prev, self.last, self.tried, self.stuck = None, None, set(), 0
            self.watch, self.latched, self.avoid = {}, False, set()
        if self.done:
            return None

        bg = int(np.bincount(g.ravel()).argmax())
        excl_bands = {c for _, _, c in bands(g)}
        refilled = self._fresh_life(g)

        if self.body is None:
            found = notched_all(g, {bg} | excl_bands)
            if len(found) != 1:
                self.done = True
                return None
            x0, y0, self.body, self.notch = found[0]
            self.size = (3, 3)

        box = self._piece_box(g)
        # A life ended: the engine's own GAME_OVER reset -- measured to fire
        # well before the budget bar empties (60/64 left), so it is a
        # collision, not a clock (`results/tu93-life-reset.txt`,
        # `tu93-death.txt`: a second, MOVING body -- colour 8, absent from
        # the gap a moment before -- occupies the exact cell the piece's own
        # rigid-translation press was walking into). The lattice step read
        # off the frame is still true; the target is not permanently a
        # wall, but a moving hazard reaches the same verdict either way, so
        # it goes on the avoid list the same as an unreachable target.
        if refilled and self.prev is not None and self.last in self.dirs:
            prev_box = self._piece_box(self.prev)
            if prev_box is not None:
                dx, dy = self.dirs[self.last]
                self.avoid.add((prev_box[0] + dx, prev_box[1] + dy))
        # What the last press taught -- read from the PRE-move frame (Trap
        # 3: a reading taken while the piece stands on something is
        # occlusion, and the gap the piece just crossed is exactly that).
        # Never across a life boundary: a life reset puts the piece back at
        # the level's start, and that IS a rigid translation of the piece,
        # so a frame pair straddling one teaches a bogus vector -- measured
        # as dirs[4] flipping to (-12, 6) on a board whose real step is
        # (6, 0) (`results/tu93-life-reset.txt`, i=34-35: the pre/post-reset
        # frame pair read as one bogus press).
        if not refilled and self.prev is not None and self.last in DIRS and box is not None:
            prev_box = self._piece_box(self.prev)
            if prev_box is not None:
                d = (box[0] - prev_box[0], box[1] - prev_box[1])
                if d != (0, 0):
                    self.dirs[self.last] = d
                    self.open_colours |= _gap_colours(self.prev, prev_box, d, self.size)
                    self.stuck = 0
                else:
                    self.stuck += 1

        if box is None:
            return None
        if self.stuck > STUCK_LIMIT:
            self.done = True
            return None

        # Bootstrap: learn all four directions before trusting any route.
        # Trap 1 -- three of tu93's four actions are dead from the reset
        # corner, so a refusal is not retried in place; once every
        # direction has been asked once from here, walk on a direction that
        # DOES work and ask the rest again from the new position.
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

        w, h = self.size
        if self.goal is None:
            excl = {bg, self.body, self.notch} | self.open_colours | excl_bands
            found = find_goal(g, excl, self.size)
            if found is None:
                self.done = True
                return None
            self.goal = (found[0], found[1])

        pos = (box[0], box[1])
        if pos == self.goal:
            return None

        path = lattice_bfs(pos, self.goal, self.dirs, self.size, self.open_colours, g, self.avoid)
        if not path:
            self.done = True
            return None
        self.prev, self.last = g, path[0]
        return path[0]


if __name__ == "__main__":   # offline harness: play tu93 with nothing else in the loop
    import arc_agi

    want = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    env = arc_agi.Arcade().make(sys.argv[1] if len(sys.argv) > 1 else "tu93")
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    mz = Maze([a.value for a in env.action_space if not a.is_complex()])
    print("signature:", signature(grid_of(obs)))
    per, spent, done = [], 0, obs.levels_completed
    for i in range(want):
        v = mz.act(grid_of(obs), obs.levels_completed)
        if v is None:
            print(f"i={i} out of ideas at level {obs.levels_completed + 1}")
            break
        obs = env.step(A[v])
        spent += 1
        if obs is None or grid_of(obs) is None or str(obs.state) != "GameState.NOT_FINISHED":
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
    print("counters:", dict(dirs=mz.dirs, body=mz.body, notch=mz.notch,
                            open_colours=mz.open_colours, goal=mz.goal))
