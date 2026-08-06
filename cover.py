"""The framed-box family: park every shape so its boxes lie on its own cells.

`re86` is the whole family on the public roster, and the signature is exact -- at
reset it is the only one of the seventeen playable games with a cell ringed by
eight identical cells (`results/re86-sig.txt`), so the rung is silent everywhere
else by construction.

Mechanics, all measured offline (`results/re86-*.txt`):

  * action 5 cycles which shape the arrows drive; the board's single colour-0
    cell (`@`) rides the ACTIVE shape's centre. Arrows move it +/-3 on one axis,
    clamped to the board, and every shape and frame is TRANSPARENT to the walk.
  * the centre standing on a frame cell is GAME_OVER.
  * the bottom row is a 100-action-per-level budget bar, refilled on level-up.
  * **a group of boxes -- all the boxes of one colour -- is consumed the moment
    shapes WEARING THAT COLOUR cover all of it at once** (`re86-l4p*.txt`: both
    groups covered by the wrong wearers is inert; the same centres with the
    right coats end the level). Levels 1-3 hide the colour clause because every
    shape spawns wearing its own group's colour; level 4 breaks the match and
    supplies SWATCHES -- blocks ringed in a non-frame colour -- and standing a
    shape's CENTRE on one recolours the shape to the swatch's colour, for keeps.
    Arms sweeping a swatch do nothing; it is the centre that counts.

Two readings that cost a session each are baked in as comments below: the modal
centre of a shape's colour DRIFTS (track the `@`), and a shape's arms are
measured SHORT when they hang off the board edge.
"""

import sys
from collections import Counter, deque

import numpy as np

DIRS = {1: (0, -3), 2: (0, 3), 3: (-3, 0), 4: (3, 0)}
UNDO = {1: 2, 2: 1, 3: 4, 4: 3}
TOGGLE, MARK = 5, 0


def grid_of(obs):
    """The full frame, or None -- the engine hands back empty ones mid-level."""
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def at(g):
    ys, xs = np.nonzero(g == MARK)
    return (int(xs[0]), int(ys[0])) if len(xs) else None


def boxes(g):
    """Every cell ringed by 8 cells of one other colour -> {(x, y): inner colour}."""
    out = {}
    for y in range(1, g.shape[0] - 1):
        for x in range(1, g.shape[1] - 1):
            ring = np.concatenate([g[y - 1, x - 1:x + 2], g[y + 1, x - 1:x + 2],
                                   [g[y, x - 1], g[y, x + 1]]])
            f = int(ring[0])
            if f != int(g[y, x]) and (ring == f).all():
                out[(x, y)] = int(g[y, x])
    return out


def swatches(g, bg):
    """Recolour stations: a uniform block (2x2 or larger) ringed by ONE colour
    that is neither the block's nor the background -> {inner colour: inner rect}.

    The background exclusion is what keeps a solid piece of a shape from
    reading as a station; the block-size floor is what keeps the 1x1 framed
    boxes out."""
    out, H, W = {}, g.shape[0], g.shape[1]
    for y0 in range(1, H - 2):
        for x0 in range(1, W - 2):
            c = int(g[y0, x0])
            if c == bg or int(g[y0 - 1, x0]) == c or int(g[y0, x0 - 1]) == c:
                continue
            x1 = x0
            while x1 + 1 < W - 1 and int(g[y0, x1 + 1]) == c:
                x1 += 1
            y1 = y0
            while y1 + 1 < H - 1 and (g[y1 + 1, x0:x1 + 1] == c).all():
                y1 += 1
            if x1 - x0 < 1 or y1 - y0 < 1:
                continue
            ring = np.concatenate([g[y0 - 1, x0 - 1:x1 + 2], g[y1 + 1, x0 - 1:x1 + 2],
                                   g[y0:y1 + 1, x0 - 1], g[y0:y1 + 1, x1 + 1]])
            r = int(ring[0])
            if r != c and r != bg and (ring == r).all():
                out[c] = (x0, y0, x1, y1)
    return out


def signature(g):
    """Four framed boxes is the family; every other public game reads zero."""
    return g is not None and len(boxes(g)) >= 4


def route(start, goal, lava):
    """Shortest lattice walk whose every centre position avoids the frame cells."""
    q, seen = deque([(start, [])]), {start}
    while q:
        (x, y), path = q.popleft()
        if (x, y) == goal:
            return path
        for a, (dx, dy) in DIRS.items():
            n = (min(63, max(0, x + dx)), min(63, max(0, y + dy)))
            if n in seen or n in lava:
                continue
            seen.add(n)
            q.append((n, path + [a]))
    return None


def candidates(shape, bxs, lava):
    """Centres this shape can reach, by the box set each one would cover."""
    out = {}
    for b in bxs:
        for o in shape["offs"]:
            c = (b[0] - o[0], b[1] - o[1])
            if not (0 <= c[0] < 64 and 0 <= c[1] < 64) or c in lava:
                continue
            if (c[0] - shape["pos"][0]) % 3 or (c[1] - shape["pos"][1]) % 3:
                continue
            cov = frozenset(m for m in bxs if (m[0] - c[0], m[1] - c[1]) in shape["offs"])
            out.setdefault(cov, c)
    return sorted(out.items(), key=lambda t: -len(t[0]))


def swatch_zone(offs, rects):
    """Centre positions from which ANY shape cell touches a swatch block.

    The recolour trigger is overlap, not the centre: driving the L5 X toward
    the 9-swatch flipped it at (9, 54) -- an arm cell entering the RING -- three
    cells before the inner (`re86-l5p6.txt`). A route that only keeps the
    centre out therefore scrambles the coat on the way past; the avoid set has
    to be the swatch dilated by the shape's own cells."""
    bad = set()
    for (x0, y0, x1, y1) in rects:
        for cy in range(y0 - 1, y1 + 2):
            for cx in range(x0 - 1, x1 + 2):
                for ox, oy in offs:
                    bad.add((cx - ox, cy - oy))
    return bad


def group_plan(shapes, gb, lava):
    """The cheapest way to lay shapes over ONE colour group all at once.

    Returns [(index into shapes, centre)] covering every box in `gb`, fewest
    shapes first and shortest total walk within that, or None. The walk cost is
    manhattan distance -- an estimate, since the true routes dodge frames."""
    # a shape PARKED with a cell on a swatch changes coat right there, so a
    # centre inside the shape's dilated swatch zone is no cover at all
    per = [(i, candidates(s, gb, lava | s.get("zone", frozenset())))
           for i, s in enumerate(shapes)]
    best = None

    def rec(k, plan, done, cost):
        nonlocal best
        if not (set(gb) - done):
            if best is None or (len(plan), cost) < (len(best[1]), best[0]):
                best = (cost, list(plan))
            return
        if k == len(per):
            return
        if best is not None and len(plan) + 1 > len(best[1]):
            return
        i, cands = per[k]
        for cov, c in cands[:12]:
            if cov - done:
                d = abs(c[0] - shapes[i]["pos"][0]) + abs(c[1] - shapes[i]["pos"][1])
                rec(k + 1, plan + [(i, c)], done | cov, cost + d)
        rec(k + 1, plan, done, cost)

    rec(0, [], set(), 0)
    return best[1] if best else None


class Cover:
    """Drives one game. `act(grid, level)` returns the next action value or None.

    None means "not my board" or "out of ideas" -- the caller falls back to its
    own machinery, so a wrong reading costs actions and never the run.
    """

    def __init__(self, values):
        self.on = {1, 2, 3, 4, TOGGLE} <= set(values)
        self.lvl, self.gen = None, None

    def act(self, g, lvl):
        if not self.on or g is None:
            return None
        if lvl != self.lvl:
            self.lvl, self.gen = lvl, self._level(g)
            return self._pump(None)
        return self._pump(g) if self.gen else None

    def _pump(self, g):
        try:
            return self.gen.send(g)
        except StopIteration:
            self.gen = None
            return None

    def _level(self, g):
        bg = self._bg(g)
        lava = {(int(x), int(y)) for y, x in zip(*np.nonzero(g == self._frame(g)))}
        bxs = boxes(g)
        if not bxs:
            return
        sw = swatches(g, bg)
        # a centre PASSING THROUGH a swatch recolours the shape mid-walk, so
        # every route treats swatch interiors as lava unless one is the goal
        swcells = {(x, y) for (x0, y0, x1, y1) in sw.values()
                   for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}

        shapes, seen = [], set()
        while len(shapes) < 6:
            p = at(g)
            if p is None or p in seen:          # a satisfied shape loses its marker
                g = yield TOGGLE
                if g is None or at(g) is None or at(g) in seen:
                    break
                continue
            seen.add(p)
            offs, colour = set(), None
            safe = [a for a, (dx, dy) in DIRS.items()
                    if (min(63, max(0, p[0] + dx)), min(63, max(0, p[1] + dy)))
                    not in lava | swcells]
            # One probe per AXIS: a shape shifted along an arm hides that arm in
            # its own trail, and a colour mask cannot be used instead because
            # level 3 gives three shapes the same colour.
            for probe in [a for a in safe if a in (1, 2)][:1] + [a for a in safe if a in (3, 4)][:1]:
                before = g
                g = yield probe
                if g is None:
                    return
                q = at(g) or (p[0] + DIRS[probe][0], p[1] + DIRS[probe][1])
                gone = np.nonzero((before != bg) & (g == bg))
                came = np.nonzero((before == bg) & (g != bg))
                if len(gone[0]) and colour is None:
                    colour = Counter(int(before[y, x]) for y, x in zip(*gone)).most_common(1)[0][0]
                offs |= {(int(x) - p[0], int(y) - p[1]) for y, x in zip(*gone) if (int(x), int(y)) not in bxs}
                offs |= {(int(x) - q[0], int(y) - q[1]) for y, x in zip(*came) if (int(x), int(y)) not in bxs}
                g = yield UNDO[probe]
                if g is None:
                    return
            # An arm hanging off the board edge is measured SHORT (level 4's plus
            # reads right=9 against left=13); every shape seen here is symmetric.
            offs |= {(-dx, -dy) for dx, dy in offs}
            shapes.append({"pos": p, "colour": colour, "offs": offs})
            g = yield TOGGLE
            if g is None:
                return

        # A box whose ring is under a shape's arm is INVISIBLE to boxes() -- level
        # 5's "two 8-boxes becoming four" was two more hiding under a cross's arms
        # the whole time. So the set is accumulated across frames, and a box only
        # leaves it CONSUMED: its whole 3x3 reads background, which an arm over it
        # (1 cell wide against 6 visible ring cells) can never fake.
        known, prev_sig = dict(bxs), None
        for wave in range(8):
            if g is None:
                return
            known.update(boxes(g))
            for b in list(known):
                x, y = b
                if 1 <= x < 63 and 1 <= y < 63 and (g[y - 1:y + 2, x - 1:x + 2] == bg).all():
                    del known[b]
            sig = frozenset(known)
            if not known or sig == prev_sig:
                return
            prev_sig = sig
            groups = {}
            for b, c in known.items():
                groups.setdefault(c, {})[b] = c
            # groups someone already wears go first; recolour work is saved for last
            order = sorted(groups, key=lambda c: (not any(s["colour"] == c for s in shapes),
                                                  len(groups[c])))
            for c in order:
                elig = [s for s in shapes if s["colour"] == c or c in sw]
                for s in elig:
                    # parked wearing c, touching c's own swatch is a no-op --
                    # every OTHER swatch would swap the coat where it stands
                    s["zone"] = swatch_zone(s["offs"],
                                            [r for col, r in sw.items() if col != c])
                plan = group_plan(elig, groups[c], lava | swcells)
                if plan is None:
                    continue
                for i, centre in plan:
                    s = elig[i]
                    found = False
                    for _ in range(2 * len(shapes) + 2):
                        if g is not None and at(g) == s["pos"]:
                            found = True
                            break
                        g = yield TOGGLE
                    if not found:
                        continue
                    legs = []
                    if s["colour"] != c:
                        x0, y0, x1, y1 = sw[c]
                        cells = sorted(((x, y) for y in range(y0, y1 + 1)
                                        for x in range(x0, x1 + 1)
                                        if not (x - s["pos"][0]) % 3 and not (y - s["pos"][1]) % 3),
                                       key=lambda t: abs(t[0] - s["pos"][0]) + abs(t[1] - s["pos"][1]))
                        if not cells:
                            continue
                        legs.append(cells[0])
                    legs.append(centre)
                    for goal in legs:
                        # swatches of the colour worn NOW and the colour this
                        # errand ends in are no-ops to touch; the rest swap the
                        # coat mid-walk and are avoided at arm's reach
                        zone = swatch_zone(s["offs"],
                                           [r for col, r in sw.items()
                                            if col not in (s["colour"], c)])
                        path = route(s["pos"], goal, (lava | zone) - {goal})
                        if path is None:
                            break
                        for a in path:
                            g = yield a
                            if g is None:
                                return
                        s["pos"] = goal
                        s["colour"] = c

    @staticmethod
    def _bg(g):
        return int(np.bincount(g.ravel()).argmax())

    @staticmethod
    def _frame(g):
        b = boxes(g)
        p = next(iter(b))
        return int(g[p[1] - 1, p[0] - 1])


if __name__ == "__main__":   # offline harness: play re86 with nothing else in the loop
    import arc_agi

    want = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    env = arc_agi.Arcade().make(sys.argv[1] if len(sys.argv) > 1 else "re86")
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    cov = Cover(list(A))
    print("signature:", signature(grid_of(obs)))
    for i in range(want * 200):
        v = cov.act(grid_of(obs), obs.levels_completed)
        if v is None:
            print(f"i={i} out of ideas at level {obs.levels_completed + 1}")
            break
        obs = env.step(A[v])
        if obs is None or str(obs.state) != "GameState.NOT_FINISHED":
            print(f"i={i} {None if obs is None else obs.state}")
            break
    print("levels completed:", 0 if obs is None else obs.levels_completed)
