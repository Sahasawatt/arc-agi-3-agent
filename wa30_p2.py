"""wa30 probe 2: action 5 away from home, and pushing a box from each side.

    ./.venv/Scripts/python.exe wa30_p2.py

Two questions the first probe could not answer:

  A. action 5 reads as a no-op from reset (`results/wa30-acts.txt`) -- which is
     exactly how g50t's RECALL read, because from reset the piece was already
     standing where the recall puts it (`results/g50t-p8.txt`). Ask it from
     somewhere else.
  B. a box's ring turns 4 -> 3 while the piece is beside it and back on leaving
     (`wa30-p1.txt`), and pressing into it is refused. Whether the SIDE matters is
     unmeasured, and the piece carries a heading, so "which side" and "which way
     am I facing" are two different questions.

Board: piece 4x4 (colour-0 edge + colour-14 body) at (32,48) stepping 4; boxes
4x4 colour-4 ring / colour-9 inner at (44,24), (16,28), (32,36); a 12x4 colour-9
ring / colour-2 inner at (28,28); clock colour 7 on y63.
"""

import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece(g):
    """Top-left of the piece as the union of its body and its heading edge."""
    ys, xs = np.nonzero((g == 14) | (g == 0))
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def heading(g):
    """Which side of the piece's 4x4 the colour-0 edge is on."""
    ys, xs = np.nonzero(g == 0)
    if not len(xs):
        return None
    p = piece(g)
    if ys.min() == p[1] and ys.max() == p[1]:
        return "top"
    if ys.max() == p[3] and ys.min() == p[3]:
        return "bottom"
    if xs.min() == p[0] and xs.max() == p[0]:
        return "left"
    if xs.max() == p[2] and xs.min() == p[2]:
        return "right"
    return f"?{sorted(zip(xs.tolist(), ys.tolist()))}"


def rings(g):
    return (int(g[24, 44]), int(g[28, 16]), int(g[36, 32]), int(g[28, 28]))


def cens(g):
    return {c: int((g == c).sum()) for c in sorted(set(g.ravel().tolist()))}


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
NAME = {1: "up", 2: "down", 3: "left", 4: "right", 5: "act5"}


def fresh():
    env = arc.make(envs["wa30"].game_id)
    return env, {a.value: a for a in env.action_space}


print("== A: action 5 from four different places ==")
for label, route in (("home (no moves)", []),
                     ("2 left", [3, 3]),
                     ("2 up", [1, 1]),
                     ("2 up 3 left", [1, 1, 3, 3, 3]),
                     ("4 right 2 up", [4, 4, 4, 4, 1, 1])):
    env, A = fresh()
    obs = env.reset()
    for a in route:
        obs = env.step(A[a])
    g = grid_of(obs)
    p0, h0 = piece(g), heading(g)
    obs = env.step(A[5])
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  {label}: empty frame")
        continue
    changed = int((g2[:63] != g[:63]).sum())
    print(f"  {label:14s}: piece {p0} h={h0} -> {piece(g2)} h={heading(g2)} "
          f"non-clock cells changed={changed}")

print("\n== B: press into a box from each side that can reach one ==")
# B3 is at (32,36)-(35,39). Reach it from below (32,40), above (32,32),
# left (28,36), right (36,36).
APPROACH = {
    "from BELOW, pressing up": ([1, 1], 1),
    "from LEFT, pressing right": ([1, 1, 1, 3, 3, 3, 3, 1], 4),
    "from ABOVE, pressing down": ([3, 3, 3, 3, 1, 1, 1, 1, 4, 4, 4, 4], 2),
    "from RIGHT, pressing left": ([1, 1, 1, 4, 4, 4, 4, 1], 3),
}
for label, (route, press) in APPROACH.items():
    env, A = fresh()
    obs = env.reset()
    ok = True
    for a in route:
        obs = env.step(A[a])
        if obs is None or not str(obs.state).endswith("NOT_FINISHED"):
            ok = False
            break
    if not ok:
        print(f"  {label}: died on the approach")
        continue
    g = grid_of(obs)
    p0 = piece(g)
    obs = env.step(A[press])
    g2 = grid_of(obs)
    print(f"  {label}: at {p0} h={heading(g)} rings={rings(g)} -> "
          f"{piece(g2)} h={heading(g2)} rings={rings(g2)} "
          f"lvl={obs.levels_completed} "
          f"{'REFUSED' if piece(g2) == p0 else 'MOVED'}")

print("\n== C: walk into the BIG ring at (28,28)-(39,31) from below ==")
env, A = fresh()
obs = env.reset()
for i, a in enumerate([1, 1, 1, 1, 1, 1]):
    obs = env.step(A[a])
    g = grid_of(obs)
    if g is None:
        print(f"  {i}: empty frame")
        break
    print(f"  up {i}: piece={piece(g)} h={heading(g)} rings={rings(g)} "
          f"census={cens(g)} lvl={obs.levels_completed}")
sys.stdout.flush()
