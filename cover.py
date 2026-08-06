"""The framed-box family: park every shape so its boxes lie on its own cells.

`re86` is the whole family on the public roster, and the signature is exact — at
reset it is the only one of the seventeen playable games with a cell ringed by
eight identical cells (`results/re86-sig.txt`), so the rung is silent everywhere
else by construction.

Mechanics, all measured offline (`results/re86-*.txt`):

  * action 5 cycles which shape the arrows drive; the board's single colour-0
    cell (`@`) rides the ACTIVE shape's centre. Arrows move it +/-3 on one axis,
    clamped to the board, and every shape and frame is TRANSPARENT to the walk.
  * the centre standing on a frame cell is GAME_OVER.
  * the bottom row is a 100-action-per-level budget bar, refilled on level-up.
  * a group of boxes is consumed the moment one shape covers ALL of it, and the
    level falls when every group is covered. Level 1 is two 13-arm pluses,
    level 2 adds hollow diamond rings, level 3 gives three shapes ONE colour
    (so box colour cannot name the owner) and level 4 pairs a shape colour with
    a box colour that differs — hence: read the shape off the board as an offset
    set, search the assignment geometrically, and try the plans in turn.

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
    """The full frame, or None — the engine hands back empty ones mid-level."""
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


def plans(shapes, bxs, limit=8):
    """Assignments of one centre per shape that between them cover every box.

    Ordered by colour agreement, which holds on levels 1-3 and does not on level
    4 — so it ranks the plans and never filters them.
    """
    out = []

    def rec(k, chosen, done):
        if len(out) >= limit:
            return
        if k == len(shapes):
            if not (set(bxs) - done):
                out.append(list(chosen))
            return
        reach = sum(max((len(c) for c, _ in s["cands"]), default=0) for s in shapes[k:])
        if reach < len(set(bxs) - done):
            return
        for cov, c in shapes[k]["cands"]:
            rec(k + 1, chosen + [(c, cov)], done | cov)
        rec(k + 1, chosen + [(shapes[k]["pos"], frozenset())], done)

    rec(0, [], set())
    out.sort(key=lambda p: (-sum(1 for s, (_, cov) in zip(shapes, p)
                                 if cov and all(bxs[b] == s["colour"] for b in cov)),
                            sum(len(cov) for _, cov in p)))
    return [[c for c, _ in p] for p in out]


class Cover:
    """Drives one game. `act(grid, level)` returns the next action value or None.

    None means "not my board" or "out of ideas" — the caller falls back to its
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
        lava = {(int(x), int(y)) for y, x in zip(*np.nonzero(g == self._frame(g)))}
        bxs = boxes(g)
        if not bxs:
            return
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
                    if (min(63, max(0, p[0] + dx)), min(63, max(0, p[1] + dy))) not in lava]
            # One probe per AXIS: a shape shifted along an arm hides that arm in
            # its own trail, and a colour mask cannot be used instead because
            # level 3 gives three shapes the same colour.
            for probe in [a for a in safe if a in (1, 2)][:1] + [a for a in safe if a in (3, 4)][:1]:
                before, bg = g, self._bg(g)
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

        for s in shapes:
            s["cands"] = candidates(s, bxs, lava)
        for plan in plans(shapes, bxs):
            for s, goal in zip(shapes, plan):
                if s["pos"] == goal:
                    continue
                for _ in range(len(shapes) + 1):
                    if at(g) == s["pos"]:
                        break
                    g = yield TOGGLE
                    if g is None:
                        return
                path = route(at(g), goal, lava) if at(g) else None
                if path is None:
                    continue
                for a in path:
                    g = yield a
                    if g is None:
                        return
                s["pos"] = goal

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
