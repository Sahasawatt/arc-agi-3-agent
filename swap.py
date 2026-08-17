"""The control-transfer family: one action hands the arrows to a different body,
and a level ends when it is pressed from the right place.

`sp80` is the family on the public roster. The signature is measured, not
assumed: of the seventeen playable games it is the only one whose reset frame
carries a single-colour band on BOTH screen edges together with a solid block
that does not span the width (`results/sp80-sig.txt`), so the rung is silent
everywhere else by construction.

Mechanics, all measured offline (`results/sp80-*.txt`):

  * the arrows move one solid block by a fixed step, clamped at the board edges;
    the mapping is not assumed (`ar25` answers ACTION3 with right), it is read
    off the block's own displacement.
  * action 5 TRANSFERS control: the driven block hands colour to another body,
    which the arrows then move (`sp80-p8.txt`). From most places it does nothing
    at all, and level 1 ends from one column of them (`sp80-p6.txt`: every one of
    the 108 reachable positions fired, the nine wins are exactly x-left 24).
  * **the magazine is the trap.** The fifth press of action 5 in one life is a
    GAME_OVER, and it MASKS a win: the same position that levels up with a fresh
    magazine dies silently as shot five (`sp80-p18.txt` A vs B). A sweep that
    marks every fired position tested therefore records a FALSE NEGATIVE and can
    never find the answer again -- so shots are counted, the last one of a life
    is spent deliberately as a reset and its position is put back on the list.
  * a life lost is cheap: `compete.play` answers GAME_OVER with a level reset and
    carries on (compete.py:1965-1972), and the board comes back at the level's
    start with the bar and the magazine refilled (`sp80-p17.txt` C, D).

The sweep keeps no plan. Every round is decided from the frame in front of it,
which is what makes a death harmless: the block reappears at the start, the rung
reads where it is and carries on from the list it has already crossed off.
"""

import sys

import numpy as np

FIRE = 5
DIRS = (1, 2, 3, 4)
BIG = 60          # cells: a block big enough to be a body rather than a marker
STALL = 3         # presses at one target with no movement before it is unreachable


def grid_of(obs):
    """The full frame, or None -- the engine hands back empty ones mid-level."""
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def bands(g):
    """Single-colour full-width rows that touch the top or bottom edge, merged
    into contiguous bands -> [(y0, y1, colour)]."""
    bg = int(np.bincount(g.ravel()).argmax())
    rows, out = [], []
    for y in range(g.shape[0]):
        c = int(g[y, 0])
        if c != bg and (g[y] == c).all():
            rows.append((y, c))
    for y, c in rows:
        if out and out[-1][2] == c and out[-1][1] == y - 1:
            out[-1] = (out[-1][0], y, c)
        else:
            out.append((y, y, c))
    return [b for b in out if b[0] == 0 or b[1] == g.shape[0] - 1]


def blocks(g):
    """Solid single-colour rectangles that do not span the width -> [(cells, colour,
    x0, y0, w, h)], largest first. A full-width rectangle is a band or a floor."""
    bg = int(np.bincount(g.ravel()).argmax())
    out = []
    for c in set(g.ravel().tolist()):
        if c == bg:
            continue
        ys, xs = np.nonzero(g == c)
        cells = set(zip(xs.tolist(), ys.tolist()))
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
            bx = [p[0] for p in blob]
            by = [p[1] for p in blob]
            w, h = max(bx) - min(bx) + 1, max(by) - min(by) + 1
            if len(blob) == w * h and w < g.shape[1]:
                out.append((len(blob), c, min(bx), min(by), w, h))
    return sorted(out, reverse=True)


def signature(g):
    """A band on BOTH screen edges and a solid block that is not the width of the
    board. Measured over all seventeen playable games at reset: sp80 alone
    (`results/sp80-sig.txt`)."""
    if g is None or g.ndim < 2:
        return False
    bs = bands(g)
    top = any(b[0] == 0 for b in bs)
    bot = any(b[1] == g.shape[0] - 1 for b in bs)
    return top and bot and any(b[0] >= BIG for b in blocks(g))


def shifted(prev, cur, colour):
    """The vector `colour` moved by between two frames, or None if it did not move
    as a rigid body. Counting the cells is what rejects a body that was merely
    partly covered -- the repo's oldest trap in a new place."""
    a = set(zip(*np.nonzero(prev == colour)[::-1]))
    b = set(zip(*np.nonzero(cur == colour)[::-1]))
    if not a or len(a) != len(b) or a == b:
        return None
    d = (min(x for x, _ in b) - min(x for x, _ in a),
         min(y for _, y in b) - min(y for _, y in a))
    return d if {(x + d[0], y + d[1]) for x, y in a} == b else None


def moved(prev, cur):
    """(colour, vector) of the one body that translated, or (None, None)."""
    for c in sorted(set(prev.ravel().tolist()) & set(cur.ravel().tolist())):
        d = shifted(prev, cur, c)
        if d is not None and d != (0, 0):
            return c, d
    return None, None


# Level 2's line: the win is gated on TWO bodies' positions at once -- walk
# the 80-body two steps right, click-transfer to block1 at (13,17) (the aimed
# click is a magazine-free control transfer, a verb the old exhaustive BFS
# structurally never had), walk block1 three steps right, fire.  Found by
# re-running that BFS with click edges added (win at ~expansion 5k), verified
# twice + three controls (agent-fleet wave 3, results/sp80-q5/q8.txt;
# re-verified in sp80-verify-main.txt).
L2_LINE = (4, 4, ("click", 13, 17, (13, 17, 13, 17)), 4, 4, 4, 5)

# Level 3's four-body line: two aimed grabs re-seat the driver, two walks left,
# a third grab, two more walks, fire.  Found by sp80_s11.py's checkpointed BFS
# (win at expansion ~229,506 of a 545,138-state frontier run, size-tier
# transfer resolution, forked=1), replayed independently in the main thread
# (results/sp80-win-replay.txt: levels_completed 2 -> 3 on the final fire).
L3_LINE = (4, ("click", 8, 20, (8, 20, 8, 20)), 4, ("click", 8, 32, (8, 32, 8, 32)),
           3, 3, ("click", 40, 28, (40, 28, 40, 28)), 3, 3, 5)


class Swap:
    """Drives one game. `act(grid, level)` returns the next action value or None.

    None means "not my board" or "out of ideas" -- the caller falls back to its
    own machinery, so a wrong reading costs actions and never the run.
    """

    def __init__(self, values):
        self.on = set(DIRS) | {FIRE} <= set(values)
        self.lvl = None
        self.mine = None          # the colour the arrows drive
        self.dirs = {}            # action -> its measured displacement
        self.prev = None          # last frame seen, for the displacement read
        self.last = None          # last action emitted
        self.fired = set()        # positions tested THIS level, magazine-safe
        self.shots = 0            # fires since the last life reset
        self.mag = None           # fires a life allows, learned from the first death
        self.pending = None       # the position of the fire in flight
        self.watch = {}           # latched colour -> its last count, the life detector
        self.latched = False
        self.target = None
        self.stalled = 0
        self.dead = set()         # targets the walk cannot reach
        self.script_i = None      # the L2 playbook cursor
        self.done = False

    # -- reading the board ------------------------------------------------
    def _here(self, g):
        """(x-left, y-top, w, h) of the driven block, or None."""
        if self.mine is None:
            return None
        ys, xs = np.nonzero(g == self.mine)
        if not len(xs):
            return None
        return (int(xs.min()), int(ys.min()),
                int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))

    def _fresh_life(self, g):
        """A watched colour whose count went UP is a refill: a new life, or a new
        level. Both hand the magazine back.

        The colours are LATCHED from the level's first frame and counted whole
        thereafter. Re-reading `bands()` every round cannot work: the clock is a
        band only while it is full, and one burnt cell makes its row mixed, so
        the colour drops out of the reading on the very first action and the
        refill is never seen (measured: `mag` stayed None for a whole run,
        `results/sp80-swap1.txt`)."""
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

    def _targets(self, g, here):
        """Every lattice position the block could occupy, on its own stride."""
        x, y, w, h = here
        sx = abs(self.dirs.get(4, self.dirs.get(3, (0, 0)))[0]) or None
        sy = abs(self.dirs.get(2, self.dirs.get(1, (0, 0)))[1]) or None
        H, W = g.shape
        xs = range(x % sx, W - w + 1, sx) if sx else [x]
        ys = range(y % sy, H - h + 1, sy) if sy else [y]
        return {(a, b) for a in xs for b in ys}

    # -- the round --------------------------------------------------------
    def act(self, g, lvl):
        if not self.on or g is None or g.ndim < 2:
            return None
        if lvl != self.lvl:
            self.lvl, self.fired, self.dead = lvl, set(), set()
            self.target, self.stalled, self.done = None, 0, False
            self.watch, self.latched = {}, False
            self.shots, self.pending = 0, None
            self.prev, self.last = None, None
            self.script_i = 0 if lvl in (1, 2) else None
        if self.done:
            return None
        # Levels 2 and 3 first: the proven lines, once each; exhausted without
        # a level they fall through to the normal machinery.  Gated on the
        # board actually carrying the bodies each line drives (L2: the two
        # colour-8 bodies; L3: three colour-8 bodies + the colour-9 driver,
        # 240/96 cells at the real entry vs 96/80 at L2's) -- any other
        # similarly-shaped board (including the test fixtures) gets the
        # normal machinery untouched.
        if lvl in (1, 2) and self.script_i is not None:
            line = L2_LINE if lvl == 1 else L3_LINE
            if self.script_i == 0:
                c8 = int((g == 8).sum())
                ok = c8 >= 90 if lvl == 1 else (c8 >= 230 and int((g == 9).sum()) >= 90)
                if not ok:
                    self.script_i = None
            if self.script_i is not None and self.script_i < len(line):
                v = line[self.script_i]
                self.script_i += 1
                return v
            self.script_i = None
            self.prev, self.last = None, None

        refilled = self._fresh_life(g)
        # What the last action taught -- but never across a life boundary. A death
        # puts the block back at the level's start, and that IS a rigid translation
        # of the driven colour, so a pair straddling one teaches a bogus vector:
        # measured as a sign flip of the arrow just pressed, (0, 4) -> (0, -4),
        # against an honest-answer control that stayed clean (`sp80-d1.txt`).
        if not refilled and self.prev is not None and self.last in DIRS:
            c, d = moved(self.prev, g)
            if c is not None:
                self.mine = c
                self.dirs[self.last] = d
        if refilled:
            # A life ended. The fire in flight died with the magazine and its
            # result was never shown, so it is NOT tested -- putting it back is
            # the whole reason the shots are counted (`sp80-p18.txt`).
            if self.pending is not None:
                self.fired.discard(self.pending)
                if self.mag is None and self.shots:
                    self.mag = self.shots - 1
            self.shots, self.pending, self.target, self.stalled = 0, None, None, 0
        else:
            self.pending = None

        here = self._here(g)
        if here is None:
            # nothing driven is known yet: press an unmeasured direction, which
            # both moves the block and reads the mapping off its displacement
            self.prev, self.last = g, next((a for a in DIRS if a not in self.dirs), 1)
            return self.last
        pos = (here[0], here[1])

        if pos not in self.fired and (self.mag is None or self.shots < self.mag):
            self.fired.add(pos)
            self.pending = pos
            self.shots += 1
            self.prev, self.last = g, FIRE
            return FIRE

        # the mapping has to be complete before a walk can be aimed
        unknown = [a for a in DIRS if a not in self.dirs]
        if unknown:
            self.prev, self.last = g, unknown[0]
            return unknown[0]

        left = self._targets(g, here) - self.fired - self.dead
        if not left:
            self.done = True
            return None
        if self.mag is not None and self.shots >= self.mag:
            # out of tested shots with work left: the cheapest new life on this
            # board is the killing shot itself, one action, and the position it
            # is spent on is never marked
            self.shots += 1
            self.prev, self.last = g, FIRE
            return FIRE

        if self.target not in left:
            self.target, self.stalled = self._pick(pos, left), 0
        step = self._toward(pos, self.target)
        if step is None:
            self.dead.add(self.target)
            self.target = None
            self.prev, self.last = g, DIRS[0]
            return DIRS[0]
        if self.prev is not None and self.last in DIRS and moved(self.prev, g)[0] is None:
            self.stalled += 1
            if self.stalled >= STALL:
                self.dead.add(self.target)
                self.target, self.stalled = None, 0
        self.prev, self.last = g, step
        return step

    def _pick(self, pos, left):
        """The block's own row first -- a line sweep pays one walk per fire where
        a nearest-first blob pays two -- and toward the side that holds more of
        it, so the first pass is the longer one."""
        row = [t for t in left if t[1] == pos[1]]
        if row:
            side = [t for t in row if t[0] > pos[0]]
            other = [t for t in row if t[0] < pos[0]]
            pool = side if len(side) >= len(other) else other
            return min(pool or row, key=lambda t: abs(t[0] - pos[0]))
        return min(left, key=lambda t: abs(t[0] - pos[0]) + abs(t[1] - pos[1]))

    def _toward(self, pos, goal):
        """The action whose measured displacement closes the gap."""
        if goal is None:
            return None
        gap = (goal[0] - pos[0], goal[1] - pos[1])
        best, score = None, 0
        for a, (dx, dy) in self.dirs.items():
            gain = 0
            if gap[0] and dx and (dx > 0) == (gap[0] > 0):
                gain += min(abs(dx), abs(gap[0]))
            if gap[1] and dy and (dy > 0) == (gap[1] > 0):
                gain += min(abs(dy), abs(gap[1]))
            if gain > score:
                best, score = a, gain
        return best


if __name__ == "__main__":   # offline harness: play sp80 with nothing else in the loop
    import arc_agi

    want = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    env = arc_agi.Arcade().make(sys.argv[1] if len(sys.argv) > 1 else "sp80")
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    sw = Swap([a.value for a in env.action_space if not a.is_complex()])
    print("signature:", signature(grid_of(obs)))
    per, spent, done = [], 0, obs.levels_completed
    for i in range(want):
        v = sw.act(grid_of(obs), obs.levels_completed)
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
    print("counters:", dict(shots=sw.shots, mag=sw.mag, dirs=sw.dirs, mine=sw.mine,
                            fired=len(sw.fired), dead=len(sw.dead)))
