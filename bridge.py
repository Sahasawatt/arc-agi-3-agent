"""The toggle-and-bridge family: press the panel's buttons to lay a route, then
walk the piece onto the marker.

`dc22` is the family on the public roster. Measured forward-only
(`results/dc22-solution.txt`, `results/breadth-recon.md` §dc22):

  * the play area's background colour is VOID -- the only walkable ground is
    the blocks drawn on it, and the frames the markers sit in;
  * the right panel's display boxes are BUTTONS, and each swaps a pair of
    blocks: one stands a 6x4 block up into a 4x6 bridge, the other swaps a
    checkered pad (wall) for a solid block (floor). Pressing one twice puts
    the board back;
  * the piece and the marker are the same size in the same frame, and the
    level ends when the piece walks onto the marker.

Which twin is the piece is learned by MOTION -- pressing a direction and
seeing which one moved. Assuming it from the colour or the position is the
cn04 trap, and this board offers no way to tell them apart at rest.

The policy is then: walk the route if the board as it stands has one, else
press a button that has not been tried from here and look again. Every
reading is re-taken from the live frame, so a toggle pressed by anything else
costs the plan nothing.
"""

from collections import deque

import numpy as np

UP, DOWN, LEFT, RIGHT = 1, 2, 3, 4
STEP = 2
MOVES = {UP: (0, -STEP), DOWN: (0, STEP), LEFT: (-STEP, 0), RIGHT: (STEP, 0)}


def components(g, bg):
    """4-connected same-colour components -> [(x0, x1, y0, y1, colour, size)]."""
    seen = np.zeros(g.shape, dtype=bool)
    out = []
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            if seen[y, x] or g[y, x] == bg:
                continue
            col = int(g[y, x])
            stack, cells = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < g.shape[0] and 0 <= nx < g.shape[1]
                            and not seen[ny, nx] and g[ny, nx] == col):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            out.append((min(xs), max(xs), min(ys), max(ys), col, len(cells)))
    return out


def split(g):
    """(play cols, panel cols, play bg, panel bg).

    Taken as the longest PREFIX whose columns are dominated by column 0's
    colour and the longest SUFFIX dominated by the last column's -- dc22 puts
    a two-column divider between them, and a rule that stops at the first
    change swallows it into the play area, where its cells then read as the
    framed markers this driver is looking for."""
    dom = [int(np.bincount(g[:, x]).argmax()) for x in range(g.shape[1])]
    pbg, nbg = dom[0], dom[-1]
    if pbg == nbg:
        return None
    px = 0
    while px + 1 < len(dom) and dom[px + 1] == pbg:
        px += 1
    nx = len(dom) - 1
    while nx - 1 >= 0 and dom[nx - 1] == nbg:
        nx -= 1
    if nx <= px:
        return None
    return (0, px), (nx, len(dom) - 1), pbg, nbg


def twins(g, play, bg):
    """The two framed markers: the SMALLEST pair of equal-sized components of
    different colours.

    Smallest, not first: dc22's board also carries a pair of 4x4 blocks that
    match on size, and taking the first pair found reads those as the piece
    and the goal -- after which nothing ever moves and the driver retires
    itself. The markers are the two 2x2s sitting in their own frames."""
    small = [c for c in components(g[:, play[0]:play[1] + 1], bg)
             if 1 <= c[5] <= 16 and c[1] - c[0] <= 3 and c[3] - c[2] <= 3]
    small.sort(key=lambda c: c[5])
    for i, a in enumerate(small):
        for b in small[i + 1:]:
            if a[5] == b[5] and a[4] != b[4]:
                return a, b
    return None


def read(g):
    s = split(g)
    if s is None:
        return None
    play, panel, pbg, nbg = s
    tw = twins(g, play, pbg)
    if tw is None:
        return None
    return {"play": play, "panel": panel, "pbg": pbg, "nbg": nbg, "twins": tw}


def route(g, b, start, goal):
    """BFS on the STEP lattice; a position is legal when the marker's own 2x2
    footprint lands entirely on non-void ground."""
    w = g != b["pbg"]
    w[:, b["panel"][0]:] = False
    h, wid = g.shape
    seen = {start}
    q = deque([(start, [])])
    while q:
        (x, y), path = q.popleft()
        if (x, y) == goal:
            return path
        for v, (dx, dy) in MOVES.items():
            nx, ny = x + dx, y + dy
            if not (0 <= nx < wid - 1 and 0 <= ny < h - 1) or (nx, ny) in seen:
                continue
            if not w[ny:ny + 2, nx:nx + 2].all():
                continue
            seen.add((nx, ny))
            q.append(((nx, ny), path + [v]))
    return None


def signature(g):
    """A play area and a panel, two identically sized framed markers in the
    play area, and a panel object big enough to be a button."""
    if g is None or g.ndim < 2 or g.size == 0:
        return False
    s = split(g)
    if s is None:
        return False
    play, panel, pbg, nbg = s
    if panel[1] - panel[0] < 8 or play[1] - play[0] < 20:
        return False
    if twins(g, play, pbg) is None:
        return False
    return any(c[5] >= 20 for c in components(g[:, panel[0]:panel[1] + 1], nbg))


class Bridge:
    """Constructed once if the reset frame matches; answers None whenever it
    has nothing left to try, so the rungs take the level back."""

    def __init__(self, values):
        self.on = {UP, DOWN, LEFT, RIGHT} <= set(values)
        self.lvl = None
        self._new_level()

    def _new_level(self):
        self.mover = None      # the colour that MOVED: the piece
        self.probes = [UP, RIGHT, DOWN, LEFT]
        self.was = None        # twin positions before the last probe
        self.plan = []
        self.tried = set()     # (button, piece position) already pressed
        self.buttons = None
        self.done = False

    def act(self, g, lvl):
        if not self.on or g is None or g.ndim < 2 or g.size == 0:
            return None
        if lvl != self.lvl:
            self.lvl, = (lvl,)
            self._new_level()
        if self.done:
            return None
        b = read(g)
        if b is None:
            return None        # a mid-transition frame is not a verdict
        here = {t[4]: (t[0], t[2]) for t in b["twins"]}

        if self.mover is None:
            if self.was is not None:
                moved = [c for c, p in here.items()
                         if c in self.was and self.was[c] != p]
                if moved:
                    self.mover = moved[0]
            if self.mover is None:
                if not self.probes:
                    self.done = True
                    return None
                self.was = here
                return self.probes.pop(0)

        if self.buttons is None:
            panel = g[:, b["panel"][0]:b["panel"][1] + 1]
            wide = panel.shape[1] - 1
            seen_at = []
            for c in components(panel, b["nbg"]):
                if c[5] < 20 or c[0] == 0 or c[1] >= wide:
                    continue            # a full-width band is scenery
                at = ((c[0] + c[1]) // 2 + b["panel"][0], (c[2] + c[3]) // 2)
                if at not in seen_at:   # a box and its border share a centre
                    seen_at.append(at)
            self.buttons = seen_at
            if not self.buttons:
                self.done = True
                return None

        goal_c = [c for c in here if c != self.mover]
        if not goal_c:
            self.done = True
            return None
        start, target = here[self.mover], here[goal_c[0]]

        if self.plan:
            return self.plan.pop(0)
        path = route(g, b, start, target)
        if path:
            self.plan = path
            return self.plan.pop(0)

        # No route yet, so the board is not finished being built. Stand at the
        # reachable position CLOSEST to the goal and press from there: a button
        # lays ground next to wherever the piece can already get, and pressing
        # them all from the start square is what makes this look unsolvable
        # (measured: both buttons tried at the start, driver retires, 0 levels
        # -- results/bridge-try2.txt). The real line alternates walk and press.
        best = self.frontier(g, b, start, target)
        if best is not None and best != start:
            path = route(g, b, start, best)
            if path:
                self.plan = path
                return self.plan.pop(0)
        for bx, by in self.buttons:
            key = (bx, by, start)
            if key in self.tried:
                continue
            self.tried.add(key)
            return ("click", bx, by, (bx, by, bx, by))
        self.done = True
        return None

    @staticmethod
    def frontier(g, b, start, target):
        """The reachable position nearest the goal, by walking distance."""
        w = g != b["pbg"]
        w[:, b["panel"][0]:] = False
        h, wid = g.shape
        seen = {start}
        q = deque([start])
        while q:
            x, y = q.popleft()
            for dx, dy in MOVES.values():
                nx, ny = x + dx, y + dy
                if not (0 <= nx < wid - 1 and 0 <= ny < h - 1) or (nx, ny) in seen:
                    continue
                if not w[ny:ny + 2, nx:nx + 2].all():
                    continue
                seen.add((nx, ny))
                q.append((nx, ny))
        return min(seen, key=lambda p: abs(p[0] - target[0]) + abs(p[1] - target[1]))
