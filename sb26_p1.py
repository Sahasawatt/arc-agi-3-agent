"""sb26: what does a CLICK do at each meaningful spot?

The board (`results/sb26-found.txt`): four FRAMED boxes across the top in
colour order 9, 14, 11, 15; a machine at y24-35 whose slot row holds four 2x2
colour-2 marks; four SOLID 4x4 blocks at the bottom in the different order
14, 15, 9, 11; a full-width colour-2 row at y53 that ACTION5 burns one cell a
press (`sb26-acts.txt`). ACTION6 is the click; ACTION7 read as a no-op from
reset, which on this roster usually means "no-op FROM THIS STATE" (the tu93 /
g50t trap), so it is retried after each click here.

Click each bottom block, each top box, and the machine slot; after every click
print what changed and re-press ACTION7 once.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def diff(a, b):
    if a is None or b is None:
        return "EMPTY FRAME"
    ch = np.argwhere(a != b)
    if not len(ch):
        return "no change"
    ys, xs = ch[:, 0], ch[:, 1]
    pairs = {}
    for y, x in ch:
        pairs[(int(a[y, x]), int(b[y, x]))] = pairs.get((int(a[y, x]), int(b[y, x])), 0) + 1
    return (f"{len(ch)} cells x[{xs.min()}-{xs.max()}] y[{ys.min()}-{ys.max()}] "
            + " ".join(f"{u}->{v}:{n}" for (u, v), n in sorted(pairs.items())))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
click = next(a for a in env.action_space if a.is_complex())
A = {a.value: a for a in env.action_space}

SPOTS = [
    ("bottom e(14)", 20, 58), ("bottom f(15)", 28, 58),
    ("bottom 9",     36, 58), ("bottom b(11)", 44, 58),
    ("top 9",  21, 3), ("top e", 28, 3), ("top b", 35, 3), ("top f", 41, 3),
    ("machine slot", 32, 29),
]

for name, x, y in SPOTS:
    obs = env.reset()
    g0 = grid_of(obs)
    click.set_data({"x": x, "y": y})     # mutates in place; step takes the action itself
    obs = env.step(click)
    g1 = grid_of(obs)
    print(f"click {name:14s} ({x},{y}): {diff(g0, g1)}  "
          f"state={str(obs.state).split('.')[-1]} lvl={obs.levels_completed}")
    obs = env.step(A[7])
    g2 = grid_of(obs)
    print(f"  then ACTION7: {diff(g1, g2)}  "
          f"state={str(obs.state).split('.')[-1]} lvl={obs.levels_completed}")
    sys.stdout.flush()
