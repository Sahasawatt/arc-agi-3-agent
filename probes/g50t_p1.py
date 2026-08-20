"""g50t probe 1: what is colour 8? The model calls it a WALL and the board says
otherwise.

    ./.venv/Scripts/python.exe g50t_p1.py

`ARC_MDBG` on a live run reads `block=[0, 8]` -- the discovery layer has decided
colour 8 blocks the piece. But pressing RIGHT four times from reset changed 106
cells with `8->5:25`, `0->5:14`, `0->8:10` (`results/g50t-acts.txt`), which is a
board redrawing itself, not a refusal. One of those two readings is wrong.
"""

import sys

import numpy as np

import arc_agi

CHARS = "0123456789abcdef"


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece(g):
    """The 24-cell colour-9 blob, by connected component, ignoring the clock row
    and the top-left indicator."""
    ys, xs = np.nonzero(g == 9)
    cells = {(int(x), int(y)) for x, y in zip(xs, ys) if y < 60 and x > 10}
    best = None
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
        if best is None or len(blob) > len(best):
            best = blob
    if not best:
        return None
    bx = [p[0] for p in best]
    by = [p[1] for p in best]
    return (min(bx), min(by), max(bx), max(by), len(best))


def dump(g, x0, x1, y0, y1, label):
    print(f"  -- {label} (x{x0}-{x1}, y{y0}-{y1}) --")
    for y in range(y0, y1 + 1):
        print(f"    y={y:2d} " + "".join(CHARS[int(v) & 0xF] for v in g[y, x0:x1 + 1]))


def census(g):
    vals, cnt = np.unique(g, return_counts=True)
    return dict(zip(vals.tolist(), cnt.tolist()))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["g50t"].game_id)
A = {a.value: a for a in env.action_space}

print("== A: walk RIGHT into the colour-8 column, one press at a time ==")
obs = env.reset()
prev = grid_of(obs)
print(f"  start piece={piece(prev)} census={census(prev)}")
for i in range(6):
    obs = env.step(A[4])
    cur = grid_of(obs)
    if cur is None:
        print(f"  press {i}: frame empty state={obs.state}")
        break
    p = piece(cur)
    c = census(cur)
    changed = int((cur != prev).sum())
    print(f"  press {i}: piece={p} changed={changed} census={c} "
          f"state={str(obs.state).split('.')[-1]} lvl={obs.levels_completed}")
    if changed > 60:
        dump(prev, 13, 45, 6, 20, f"BEFORE press {i}")
        dump(cur, 13, 45, 6, 20, f"AFTER press {i}")
    prev = cur

print("\n== B: is colour 8 walkable? press right until the piece stops ==")
obs = env.reset()
prev = grid_of(obs)
last = piece(prev)
for i in range(12):
    obs = env.step(A[4])
    cur = grid_of(obs)
    if cur is None:
        print(f"  press {i}: frame empty")
        break
    p = piece(cur)
    print(f"  press {i}: piece={p} {'MOVED' if p != last else 'REFUSED'}")
    if p == last:
        dump(cur, max(0, p[0] - 4), min(63, p[2] + 10), max(0, p[1] - 2),
             min(63, p[3] + 2), "refused here")
        break
    last = p

print("\n== C: the same, DOWN ==")
obs = env.reset()
last = piece(grid_of(obs))
for i in range(12):
    obs = env.step(A[2])
    cur = grid_of(obs)
    if cur is None:
        print(f"  press {i}: frame empty")
        break
    p = piece(cur)
    print(f"  press {i}: piece={p} {'MOVED' if p != last else 'REFUSED'}")
    if p == last:
        dump(cur, max(0, p[0] - 6), min(63, p[2] + 6), max(0, p[1] - 2),
             min(63, p[3] + 4), "refused here")
        break
    last = p
sys.stdout.flush()
