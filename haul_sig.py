"""Which of the seventeen playable games show wa30's carry-puzzle shape?

    ./.venv/Scripts/python.exe haul_sig.py

Same discipline as `sp80_sig.py`: print the candidate features for every game's
reset frame and CHOOSE the predicate from the table, rather than proposing one and
defending it afterwards.

The shape: rectangular outlines of one colour with a solid inner of another (a
"crate"), several of them, one strictly bigger than the rest (the frame), and the
five arrows-plus-one action set.
"""

import sys

import numpy as np

import arc_agi
from compete import PLAYABLE


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def crates(g):
    """Rectangles whose border is one colour and whose interior is a single OTHER
    colour -> [(w, h, ring colour, inner colour, x0, y0)]."""
    out, H, W = [], g.shape[0], g.shape[1]
    seen = set()
    for y0 in range(H - 3):
        for x0 in range(W - 3):
            if (x0, y0) in seen:
                continue
            c = int(g[y0, x0])
            x1 = x0
            while x1 + 1 < W and int(g[y0, x1 + 1]) == c:
                x1 += 1
            y1 = y0
            while y1 + 1 < H and int(g[y1 + 1, x0]) == c:
                y1 += 1
            w, h = x1 - x0 + 1, y1 - y0 + 1
            if w < 3 or h < 3:
                continue
            top = (g[y0, x0:x1 + 1] == c).all()
            bot = (g[y1, x0:x1 + 1] == c).all()
            lf = (g[y0:y1 + 1, x0] == c).all()
            rt = (g[y0:y1 + 1, x1] == c).all()
            if not (top and bot and lf and rt):
                continue
            inner = g[y0 + 1:y1, x0 + 1:x1]
            vals = set(inner.ravel().tolist())
            if len(vals) != 1:
                continue
            ic = int(next(iter(vals)))
            if ic == c:
                continue
            out.append((w, h, c, ic, x0, y0))
            for yy in range(y0, y1 + 1):
                for xx in range(x0, x1 + 1):
                    seen.add((xx, yy))
    return sorted(out, reverse=True)


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
rows = {}
print("game  acts            crates (w,h,ring,inner,x,y)")
for name in PLAYABLE:
    env = arc.make(envs[name].game_id)
    obs = env.reset()
    g = grid_of(obs)
    if g is None:
        print(f"{name}  EMPTY FRAME")
        continue
    acts = sorted(a.value for a in env.action_space)
    cr = crates(g)
    rows[name] = (acts, cr)
    print(f"{name}  {str(acts):15s} n={len(cr):3d}  {cr[:4]}")
    sys.stdout.flush()

print("\n== candidate: >=2 crates, all the same ring colour except the biggest, "
      "and actions 1-5 present ==")
for name, (acts, cr) in rows.items():
    ok5 = {1, 2, 3, 4, 5} <= set(acts)
    if len(cr) < 2:
        print(f"  {name}: crates={len(cr)} has1-5={ok5} -> False")
        continue
    big = cr[0]
    rest = cr[1:]
    same = len({c[2] for c in rest}) == 1
    bigger = big[0] * big[1] > rest[0][0] * rest[0][1]
    distinct_inner = big[3] not in {c[3] for c in rest}
    hit = ok5 and same and bigger and distinct_inner
    print(f"  {name}: crates={len(cr)} biggest={big[:4]} rest_same_ring={same} "
          f"bigger={bigger} distinct_inner={distinct_inner} has1-5={ok5} -> {hit}")
sys.stdout.flush()
