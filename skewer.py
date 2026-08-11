"""The skewer family: a grabber machine rides a vertical track, its woven arm
extends sideways and PIERCES wall blocks; the level ends the moment every
recipe block is threaded on the arm in the order the HUD picture names.

`sk48` is the family on the public roster. Mechanics, all measured frame by
frame (`results/sk48-p5.txt`, the winning line replayed with a room dump per
press; the level-1 line is 14 actions against a baseline of 61,
`results/sk48-verify.txt`):

  * the ARM is a 2-row woven strip (two colours alternating 121/211) issuing
    from a framed machine box; extend and retract move it one 6px segment a
    press. The same weave drawn inside the HUD picture is what makes the
    signature two-sided.
  * piercing: extending until the weave enters a block's box threads it; the
    block then rides the ARM (retract pulls it inward segment by segment)
    and rides the MACHINE vertically. An earlier session read "blocks slide
    along a queue" out of exactly these frames -- the blocks were riding the
    arm, and the queue never existed.
  * the HUD picture at the bottom is the goal: machine glyph + the block
    colours left to right in the order they must sit on the arm, which is
    the order they are pierced in.
  * the win fires ON the pierce of the last recipe block -- no delivery trip.
  * one retract after each pierce clears the threaded block off the wall
    column so the machine can travel; without it the vertical move is
    refused (measured as p4's "dropped" block -- another misreading: the
    move was refused and the block stayed put).

The drive re-reads the frame every round: align the arm's rows to the next
unpierced recipe block, extend until the weave is inside it, retract once,
repeat. Action -> effect is learned by pressing, never assumed.
"""

import sys

import numpy as np

STEP = 6          # track pitch and arm segment, both measured at 6px
STUCK_LIMIT = 12  # consecutive no-effect presses before handing back control


def weave_rows(g, floor):
    """y-coordinates carrying the arm's braid: a >=6-cell horizontal run
    drawn in exactly TWO non-floor colours, both present, neither ever
    repeating more than twice in a row (sk48's braid is `112112...` /
    `211211...` -- period three, not a cell-by-cell alternation)
    -> [(y, colours)]."""
    # The braid's neighbours (machine interior on one side, room floor on
    # the other) are not the global background, so a run cannot be delimited
    # by any one colour -- take, from every start, the longest stretch that
    # stays within two colours, and keep it if the braid rules hold.
    out = []
    H, W = g.shape
    for y in range(H):
        x = 0
        while x < W:
            cols, x1 = set(), x
            while x1 < W:
                nxt = cols | {int(g[y, x1])}
                if len(nxt) > 2:
                    break
                cols, x1 = nxt, x1 + 1
            run = [int(v) for v in g[y, x:x1]]
            if len(run) >= 6 and len(cols) == 2 and floor not in cols \
                    and len(set(run)) == 2:
                streak, worst, prev = 0, 0, None
                for v in run:
                    streak = streak + 1 if v == prev else 1
                    worst, prev = max(worst, streak), v
                if worst <= 2:
                    out.append((y, frozenset(cols)))
                    x = x1
                    continue
            x += 1
    return out


def solid_blocks(g, exclude, size=4):
    """Solid size x size single-colour squares not in `exclude`
    -> [(colour, x0, y0)], the wall stock and nothing else."""
    out = []
    H, W = g.shape
    seen = set()
    for y0 in range(H - size + 1):
        for x0 in range(W - size + 1):
            c = int(g[y0, x0])
            if c in exclude or (x0, y0) in seen:
                continue
            win = g[y0:y0 + size, x0:x0 + size]
            if (win == c).all():
                ys, xs = np.nonzero(g == c)
                out.append((c, x0, y0))
                for yy in range(y0, y0 + size):
                    for xx in range(x0, x0 + size):
                        seen.add((xx, yy))
    return out


def braid_cluster(g):
    """The live arm: EXACTLY one pair of adjacent braid rows -> (rows, weave
    colour pair) or None. The HUD's own braid never surfaces here -- its
    segments between the pictured blocks are two cells, under the run
    minimum."""
    if g is None or g.ndim < 2 or g.size == 0:
        return None
    floor = int(np.bincount(g.ravel()).argmax())
    pairs = {}
    for y, cols in weave_rows(g, floor):
        pairs.setdefault(cols, []).append(y)
    hits = [(sorted(set(ys)), cols) for cols, ys in pairs.items()]
    hits = [(ys, cols) for ys, cols in hits
            if len(ys) == 2 and ys[1] == ys[0] + 1]
    return hits[0] if len(hits) == 1 else None


def room_of(g, x, y, floor):
    """Bounding box of the connected `floor`-coloured region touching
    (x, y) -> (x0, y0, x1, y1), flood fill on the one colour."""
    H, W = g.shape
    seen, stack = set(), [(x, y)]
    while stack:
        cx, cy = stack.pop()
        if not (0 <= cx < W and 0 <= cy < H) or (cx, cy) in seen \
                or int(g[cy, cx]) != floor:
            continue
        seen.add((cx, cy))
        stack += [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]
    if not seen:
        return None
    xs = [c for c, _ in seen]
    ys = [r for _, r in seen]
    return (min(xs), min(ys), max(xs), max(ys))


def signature(g):
    """One live braid arm, and solid blocks BOTH inside the arm's room (the
    stock) and outside it (the HUD's picture of the goal). Measured against
    all seventeen reset frames by `sigs.py` -- sk48 alone."""
    b = read_static(g)
    return b is not None and len(b["stock"]) >= 2 and len(b["recipe"]) >= 2


def read_static(g, floor=None):
    """Everything positional -> dict or None. Shared by the signature and
    the driver so they cannot disagree. `floor` is passed by a driver that
    latched it earlier: with the arm's tip pressed against a block, the
    cell past the tip is the BLOCK, and deriving the floor from it reads
    the wrong room."""
    hit = braid_cluster(g)
    if hit is None:
        return None
    arm_rows, weave = hit
    ay = arm_rows[0]
    wx = [x for x in range(g.shape[1]) if int(g[ay, x]) in weave]
    if not wx:
        return None
    if floor is None:
        # The room floor is whatever the arm extends INTO: the cell just
        # past the braid's tip. (The commonest colour on the arm's rows is
        # the global background -- the rows cross both.)
        if max(wx) + 1 >= g.shape[1]:
            return None
        floor = int(g[ay, max(wx) + 1])
        if floor in weave:
            return None
    # A fully extended arm runs wall to wall and SPLITS the room's floor in
    # two, so one flood fill sees half of it -- seed a flood both above and
    # below the arm and take the union of whatever exists.
    rooms = []
    for y in (arm_rows[0] - 1, arm_rows[1] + 1):
        if not 0 <= y < g.shape[0]:
            continue
        seed = next(((x, y) for x in range(min(wx), g.shape[1])
                     if int(g[y, x]) == floor), None)
        if seed is not None:
            r = room_of(g, seed[0], seed[1], floor)
            if r is not None:
                rooms.append(r)
    if not rooms:
        return None
    room = (min(r[0] for r in rooms), min(r[1] for r in rooms),
            max(r[2] for r in rooms), max(r[3] for r in rooms))
    bg = int(np.bincount(np.concatenate(
        [g[0], g[-1], g[:, 0], g[:, -1]]).ravel()).argmax())
    blocks = solid_blocks(g, weave | {floor, bg})
    x0, y0, x1, y1 = room
    stock = [b for b in blocks if x0 <= b[1] <= x1 and y0 <= b[2] <= y1]
    hud = sorted([b for b in blocks if not (x0 <= b[1] <= x1 and y0 <= b[2] <= y1)],
                 key=lambda b: b[1])
    return {"weave": weave, "arm_rows": arm_rows, "tip": max(wx),
            "floor": floor, "stock": stock,
            "recipe": [c for c, _, _ in hud]}


class Skewer:
    """Constructed once if the reset frame matches; asked every round;
    answers None the moment it is lost so the rungs take the level back."""

    def __init__(self, values):
        self.values = list(values)
        self.on = len(values) >= 4
        self.lvl = None
        # Game facts: which action moves the machine up/down, which
        # extends/retracts the arm -- learned by pressing, kept for the game.
        self.up = self.down = self.ext = self.ret = None
        # Per-level state.
        self.prev = None
        self.last = None
        self.untried = []
        self.stuck = 0
        self.recipe = None
        self.floor = None
        self.done = False

    # -- reading ----------------------------------------------------------
    def read(self, g):
        b = read_static(g, self.floor)
        if b is not None and self.floor is None:
            self.floor = b["floor"]
        return b

    def pierced(self, g, b, colour):
        """Is `colour`'s block threaded? A threaded block stays a solid 4x4
        riding the arm -- what marks it is the braid ARRIVING at it: a weave
        cell immediately left of its box on an arm row (`sk48-p5.txt`, press
        7 vs press 4: the wall block has floor on its left until the pierce,
        braid after)."""
        for c, x0, y0 in b["stock"]:
            if c != colour:
                continue
            if x0 == 0:
                return False
            return any(y0 <= y < y0 + 4 and int(g[y, x0 - 1]) in b["weave"]
                       for y in b["arm_rows"])
        return False

    # -- the round --------------------------------------------------------
    def act(self, g, lvl):
        if not self.on or self.done:
            return None
        if g is None or g.ndim < 2 or g.size == 0:
            return None
        if lvl != self.lvl:
            self.lvl = lvl
            self.prev, self.last, self.stuck = None, None, 0
            self.recipe, self.floor = None, None
            self.untried = [v for v in self.values]
        b = self.read(g)
        if b is None:
            # A frame with no braid right after one WITH a braid: the last
            # press collapsed the arm to zero segments -- that press is the
            # retract, and the way back into view is one extend.
            if self.prev is not None and self.last is not None \
                    and self.read(self.prev) is not None:
                self.ret = self.last
                v = self.ext
                if v is None:
                    if not self.untried:
                        return None
                    v = self.untried.pop(0)
                self.prev, self.last = g, v
                return v
            return None
        if self.recipe is None:
            stock = {c for c, _, _ in b["stock"]}
            self.recipe = [c for c in b["recipe"] if c in stock]
            if len(self.recipe) < 2:
                self.done = True
                return None

        # What did the last press do? Learn the controls from displacement.
        moved = True
        if self.prev is not None and self.last is not None:
            pb = self.read(self.prev)
            if pb is not None:
                dy = b["arm_rows"][0] - pb["arm_rows"][0]
                dx = b["tip"] - pb["tip"]
                if dy < 0:
                    self.up = self.last
                elif dy > 0:
                    self.down = self.last
                elif dx > 0:
                    self.ext = self.last
                elif dx < 0:
                    self.ret = self.last
                moved = bool(dx or dy)
                self.stuck = 0 if moved else self.stuck + 1
        if self.stuck > STUCK_LIMIT:
            self.done = True
            return None

        # Controls are learned BY NEED, not upfront: an action can be a no-op
        # from the current state (down is dead with the machine parked at the
        # bottom -- the roster's no-op trap), so a press that moves something
        # refills the untried pool rather than retiring for good.
        if moved:
            self.untried = [v for v in self.values
                            if v not in (self.up, self.down, self.ext, self.ret)]

        target = next((c for c in self.recipe if not self.pierced(g, b, c)), None)
        if target is None:
            self.done = True     # everything threaded and no win: not ours
            return None
        hit = next(((x0, y0) for c, x0, y0 in b["stock"] if c == target), None)
        if hit is None:
            self.done = True
            return None
        tx0, ty0 = hit
        ay = b["arm_rows"][0]
        if ty0 + 1 <= ay <= ty0 + 2:
            v = self.ext
        else:
            want = self.down if ay < ty0 + 1 else self.up
            # A vertical press refused with threaded blocks against the wall
            # (`sk48-p4.txt`): one retract clears them, then travel again.
            if want is not None and self.last == want and not moved:
                v = self.ret
            else:
                v = want
        if v is None:
            # The wanted control is not known yet -- learn it by pressing the
            # next untried action; its displacement labels it above.
            if not self.untried:
                self.done = True
                return None
            v = self.untried.pop(0)
        self.prev, self.last = g, v
        return v


if __name__ == "__main__":   # offline harness: play with nothing else in the loop
    import arc_agi

    want = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    env = arc_agi.Arcade().make(sys.argv[1] if len(sys.argv) > 1 else "sk48")
    A = {a.value: a for a in env.action_space}
    obs = env.reset()

    def grid(o):
        if o is None:
            return None
        f = np.array(o.frame)
        return None if f.ndim < 2 or f.size == 0 else f[-1]

    sk = Skewer([a.value for a in env.action_space if not a.is_complex()])
    print("signature:", signature(grid(obs)))
    per, spent, done = [], 0, obs.levels_completed
    for i in range(want):
        v = sk.act(grid(obs), obs.levels_completed)
        if v is None:
            print(f"i={i} out of ideas at level {obs.levels_completed + 1}")
            break
        obs = env.step(A[v])
        spent += 1
        if obs is None or grid(obs) is None or str(obs.state) != "GameState.NOT_FINISHED":
            if obs is None:
                break
            obs = env.reset()
            if obs is None or grid(obs) is None:
                break
            continue
        if obs.levels_completed > done:
            per.append(spent)
            spent, done = 0, obs.levels_completed
            print(f"  level {done} cleared, actions={per[-1]} (i={i})")
    print("levels completed:", 0 if obs is None else obs.levels_completed, per)
    print("controls:", dict(up=sk.up, down=sk.down, ext=sk.ext, ret=sk.ret))
