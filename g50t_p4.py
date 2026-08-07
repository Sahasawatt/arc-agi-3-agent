"""g50t probe 4: is the BFS trustworthy, and does the maze stay open across a death?

    ./.venv/Scripts/python.exe g50t_p4.py

Probe 3 says the reachable state space from reset is 25 states / 12 positions and
the goal box is not among them (`results/g50t-p3.txt`). Two things have to be true
for that to mean anything:

  A. `copy.deepcopy(env)` must be faithful and independent HERE. It was measured on
     sp80 (`sp80-p10.txt`) and never on g50t -- a claim about one game's engine
     object is not a claim about another's.
  B. the search covers ONE life. Covering an 8 opens walls; if those stay open
     after a death, the level is a multi-life excavation and a single-life search
     answers the wrong question.
"""

import copy
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def census(g):
    vals, cnt = np.unique(g, return_counts=True)
    return dict(zip(vals.tolist(), cnt.tolist()))


def piece(g):
    ys, xs = np.nonzero(g == 9)
    cells = {(int(x), int(y)) for x, y in zip(xs, ys) if y < 60 and x > 10}
    best = set()
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
        if len(blob) > len(best):
            best = blob
    return None if not best else (min(p[0] for p in best), min(p[1] for p in best))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["g50t"].game_id)
A = {a.value: a for a in env.action_space}

print("== A: deepcopy control, on THIS game ==")
obs = env.reset()
env.step(A[4])
try:
    twin = copy.deepcopy(env)
except Exception as e:
    print("  deepcopy FAILED:", type(e).__name__, e)
    sys.exit(0)
o1 = env.step(A[4])
o2 = twin.step(A[4])
g1, g2 = grid_of(o1), grid_of(o2)
print("  same next frame:", g1 is not None and g2 is not None and np.array_equal(g1, g2))
o3 = twin.step(A[2])
g3 = grid_of(o3)
print("  copy advances independently:", not np.array_equal(g1, g3))
print("  parent unaffected by the copy's step:",
      np.array_equal(g1, grid_of(env.step(A[5]))[:63]. shape and g1[:63], g1[:63]))
# the real independence test: the parent's piece must not have moved when the twin did
print("  parent piece", piece(g1), "twin piece", piece(g3))

print("\n== B: do the opened walls survive a death? ==")
env2 = arc.make(envs["g50t"].game_id)
obs = env2.reset()
c0 = census(grid_of(obs))
for a in [4, 4, 4, 4]:
    obs = env2.step(A[a])
c1 = census(grid_of(obs))
print(f"  after opening: piece={piece(grid_of(obs))}")
print(f"  census delta vs reset: "
      f"{ {k: c1.get(k, 0) - c0.get(k, 0) for k in set(c0) | set(c1) if c1.get(k, 0) != c0.get(k, 0)} }")
# now burn the clock down with refused presses until the life ends
n = 0
while n < 300 and str(obs.state).endswith("NOT_FINISHED"):
    obs = env2.step(A[4])           # refused at (38,8), pure clock burn
    n += 1
print(f"  died after {n} further actions, state={str(obs.state).split('.')[-1]}")
obs = env2.reset()
g = grid_of(obs)
if g is None:
    print("  reset gave an empty frame")
else:
    c2 = census(g)
    print(f"  after the reset: piece={piece(g)}")
    print(f"  census delta vs RESET BOARD: "
          f"{ {k: c2.get(k, 0) - c0.get(k, 0) for k in set(c0) | set(c2) if c2.get(k, 0) != c0.get(k, 0)} }")
    print("  walls stayed open:" if c2.get(0, 0) < c0.get(0, 0) else "  board was put back:",
          f"colour0 {c0.get(0)} -> {c2.get(0)}, colour8 {c0.get(8)} -> {c2.get(8)}")
sys.stdout.flush()
