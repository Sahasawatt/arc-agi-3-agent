"""sb26: if the click selects and nothing commits, the click is half a DRAG.

p2 measured A7 as answering zero cells in every state (with and without a
selection) and A5 as deselect-plus-burn -- so neither is a commit. What has
not been tried is the other half of a drag: select a bottom block, then click
a DESTINATION.

The reset sweep only found the bottom blocks live, but that sweep had nothing
selected. This re-sweeps every component WITH a block selected -- the same
lesson dc22 taught, where a whole channel only wakes up once the board is in
the right state.

E6  the full reset board, so the machine's slots can be named.
E7  select each bottom block, then click every component centre; anything
    that answers is printed with the region it changed.
"""
import sys

import numpy as np

import arc_agi

ROW = 58


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def boxes(g, row):
    bg = int(np.bincount(g.ravel()).argmax())
    out, run = [], None
    for x in range(g.shape[1]):
        c = int(g[row, x])
        if c != bg and (run is None or run[2] != c):
            if run:
                out.append(((run[0] + run[1]) // 2, run[2]))
            run = [x, x, c]
        elif c != bg:
            run[1] = x
        elif run:
            out.append(((run[0] + run[1]) // 2, run[2]))
            run = None
    if run:
        out.append(((run[0] + run[1]) // 2, run[2]))
    return out


def components(g):
    bg = int(np.bincount(g.ravel()).argmax())
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
            out.append(((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2,
                        col, len(cells)))
    return out


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def fresh():
    env = arc.make(envs["sb26"].game_id)
    return env, {a.value: a for a in env.action_space}, env.reset()


env, A, obs = fresh()
g0 = grid_of(obs)
print("== E6: the reset board ==")
for y in range(64):
    line = "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in g0[y])
    if len(set(line)) > 1:
        print(f"  y{y:2d} {line}")
where = {c: x for x, c in boxes(g0, ROW)}
order = [c for _, c in boxes(g0, 6) if c in where]
cands = components(g0)
print(f"  blocks {where}  order {order}  components {len(cands)}")
sys.stdout.flush()

print("\n== E7: select a block, then click every component ==")
for c in order[:2]:                      # two sources is enough to see a rule
    hits = 0
    for cx, cy, col, size in cands:
        if cy >= ROW - 2:
            continue                     # the source row itself is known
        env, A, obs = fresh()
        obs = env.step(A[6], data={"x": where[c], "y": ROW})
        g1 = grid_of(obs)
        obs = env.step(A[6], data={"x": cx, "y": cy})
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  src {c} -> ({cx:2d},{cy:2d}): DEAD FRAME")
            continue
        n = int((g1 != g2).sum())
        if n > 1:
            hits += 1
            ys, xs = np.nonzero(g1 != g2)
            print(f"  src {c:2d} -> ({cx:2d},{cy:2d}) colour{col:3d} "
                  f"size{size:4d}: n={n:5d} changed y{ys.min()}-{ys.max()} "
                  f"x{xs.min()}-{xs.max()} lvl={obs.levels_completed}")
        sys.stdout.flush()
    print(f"  source {c}: {hits} destinations answered")
