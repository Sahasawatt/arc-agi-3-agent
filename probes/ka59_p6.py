"""ka59: what is actually IN the right room -- and what does the timer do to
a piece standing there?

The ferry line (kick, then click the landing) puts the piece in the right
room for the first time in the campaign. Dump the whole board from there,
walk the room's perimeter to surface anything interactive, and hold through
a timer expiry -- the death was only ever measured in the LEFT room, and a
level whose bar drains at y63 may treat the timer as the level clock rather
than a death (the re86 lesson: the bottom row is a budget, and what refills
it is a level event).
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
    ys, xs = np.nonzero(g[:63] == 0)
    return (int(xs.min()), int(ys.min())) if len(ys) else None


def dot(g):
    ys, xs = np.nonzero(g[:63] == 5)
    return (int(xs.min()), int(ys.min())) if len(ys) else None


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["ka59"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
d = dot(g)
# stand west of the dot, kick, follow
px = piece(g)
steps = 0
while piece(g)[0] < d[0] - 3 and steps < 10:
    obs = env.step(A[4])
    g = grid_of(obs)
    steps += 1
obs = env.step(A[4])
g = grid_of(obs)
d2 = dot(g)
obs = env.step(A[6], data={"x": d2[0], "y": d2[1]})
g = grid_of(obs)
print(f"in the right room: piece={piece(g)}")
print("== the board, from inside the right room ==")
for y in range(64):
    line = "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in g[y])
    if len(set(line)) > 1:
        print(f"  y{y:2d} {line}")
sys.stdout.flush()

print("\n== walk the room, log every refusal and every board answer ==")
# snake the room: right, down, left, up around the slot
for v in [4] * 4 + [1] * 4 + [3] * 4 + [2] * 6 + [4] * 6 + [1] * 8:
    p0 = piece(g)
    obs = env.step(A[v])
    g2 = grid_of(obs)
    if g2 is None:
        print("  DEAD FRAME")
        break
    n = int((g != g2).sum())
    p1 = piece(g2)
    if n > 1 or p1 == p0:
        print(f"  A{v}: piece {p0} -> {p1} n={n}"
              f"{'  REFUSED' if p1 == p0 else ''}"
              f" lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]}")
        break
print(f"final piece={piece(g)} lvl={obs.levels_completed} "
      f"state={str(obs.state).split('.')[-1]}")
