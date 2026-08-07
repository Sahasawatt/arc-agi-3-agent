"""wa30 probe 1: what turns a box's ring from 4 to 3, and does turning them all end
the level?

    ./.venv/Scripts/python.exe wa30_p1.py

Measured in `results/wa30-acts.txt`: two presses of UP from reset changed 12 cells
of colour 4 into colour 3 -- exactly the ring of the 4x4 box at (32-35, 36-39),
which the piece had just arrived below. Board: piece (14-ring, 0-inner) 4x4 at
(32,48) stepping 4; three 4-ring/9-inner boxes at (44,24), (16,28), (32,36); one
12x4 9-ring with a colour-2 inner at (28,28); clock colour 7 on y63.
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
    ys, xs = np.nonzero(g == 14)
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()))


def state(g):
    return {c: int((g == c).sum()) for c in sorted(set(g.ravel().tolist()))}


def boxrings(g):
    """Ring colour of each known box, read from its top-left cell."""
    return {"B1(44,24)": int(g[24, 44]), "B2(16,28)": int(g[28, 16]),
            "B3(32,36)": int(g[36, 32]), "BIG(28,28)": int(g[28, 28]),
            "BIGinner": int(g[29, 29])}


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["wa30"].game_id)
A = {a.value: a for a in env.action_space}
NAME = {1: "up", 2: "down", 3: "left", 4: "right", 5: "act5"}

obs = env.reset()
g = grid_of(obs)
print(f"reset: piece={piece(g)} rings={boxrings(g)}")
print(f"       census={state(g)}")

# B3 sits directly above the piece: two ups. Then left/up to B2, then across to B1.
plan = ([1, 1]                              # under B3
        + [1]                               # into/past it?
        + [3, 3, 3, 3] + [1]                # west then up, toward B2
        + [4] * 7 + [1]                     # east and up, toward B1
        )
last = piece(g)
for i, a in enumerate(plan):
    obs = env.step(A[a])
    g = grid_of(obs)
    if g is None:
        print(f"  {i:2d} {NAME[a]:5s}: empty frame state={obs.state}")
        break
    p = piece(g)
    print(f"  {i:2d} {NAME[a]:5s}: piece={p} {'MOVED' if p != last else 'REFUSED'} "
          f"rings={boxrings(g)} lvl={obs.levels_completed} "
          f"state={str(obs.state).split('.')[-1]}")
    last = p
    if obs.levels_completed > 0:
        print("  LEVEL CLEARED")
        break

print("\nboard rows with content now:")
for y in range(64):
    row = g[y]
    if len(set(row.tolist())) > 1 or int(row[0]) != int(np.bincount(g.ravel()).argmax()):
        print(f"  y={y:2d} " + "".join(CHARS[int(v) & 0xF] for v in row))
sys.stdout.flush()
