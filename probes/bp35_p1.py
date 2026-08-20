"""bp35: what do the actions actually DO?

The board (`bp35-found.txt`): two groups of colour-14 blocks (three top-left
y1-5, four mid-right y13-17), colour-10 boxes (top-right, middle, a narrow
connector, and a big bottom one holding a 4x5 marker of colours 9/11), a
colour-0 row at y63 that fills one cell per action. Frame has TWO layers.
`bp35-acts.txt`: A3/A4 shift a 47-cell body sideways, one A4 press moved
1141 cells across the whole frame, A7 changed 311 cells at y57-63.

Per-press dumps of the moving regions, both layers, for a few cadences.
"""
import sys

import numpy as np

import arc_agi


def layers(obs):
    f = np.array(obs.frame)
    return f if f.ndim == 3 else f[None]


def diff(a, b):
    ch = np.argwhere(a != b)
    if not len(ch):
        return "-"
    ys, xs = ch[:, 0], ch[:, 1]
    pairs = {}
    for y, x in ch:
        pairs[(int(a[y, x]), int(b[y, x]))] = pairs.get((int(a[y, x]), int(b[y, x])), 0) + 1
    top = " ".join(f"{u}->{v}:{n}" for (u, v), n in
                   sorted(pairs.items(), key=lambda kv: -kv[1])[:4])
    return f"{len(ch)}c x[{xs.min()}-{xs.max()}] y[{ys.min()}-{ys.max()}] {top}"


def dump(g, y0, y1, x0, x1, label):
    print(label)
    for y in range(y0, y1 + 1):
        print(f"  y{y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                       for v in g[y, x0:x1 + 1]))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = layers(obs)[-1]
print("== the 9/11 marker at reset ==")
dump(g, 36, 42, 13, 30, "  (bottom box, left part)")

print("\n== 6x A4 (right), per press ==")
for i in range(6):
    obs = env.step(A[4])
    g2 = layers(obs)[-1]
    l0 = layers(obs)[0]
    print(f"A4 #{i}: last={diff(g, g2)}")
    if not np.array_equal(l0, g2):
        print(f"       layer0 differs from layer-1: {diff(l0, g2)}")
    g = g2

print("\n== then A7, watching BOTH layers over 3 presses ==")
for i in range(3):
    obs = env.step(A[7])
    g2 = layers(obs)[-1]
    l0 = layers(obs)[0]
    print(f"A7 #{i}: last={diff(g, g2)}  layers={len(layers(obs))}")
    if not np.array_equal(l0, g2):
        print(f"       layer0 vs last: {diff(l0, g2)}")
    g = g2

print("\n== board after, full bottom half ==")
dump(g, 30, 63, 0, 63, "")
sys.stdout.flush()
