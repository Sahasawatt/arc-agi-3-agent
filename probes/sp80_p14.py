"""sp80 probe 14: is transfer legality clock- or route-dependent?

    ./.venv/Scripts/python.exe sp80_p14.py

Same position, different action counts and different routes -> same outcome?
(20,24) was legal at 3 moves; (16,28) illegal at 3 moves. Vary both.
"""

import sys

import numpy as np

import arc_agi

RECIPE1 = [4, 4, 4, 5]


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def nine_at(g, xy, size):
    ys, xs = np.nonzero(g == 9)
    if len(xs) == 0:
        return False
    return (int(xs.min()), int(ys.min())) == xy and len(xs) == size


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
obs = env.reset()
obs = env.step(A[1])

CASES = [
    ("(20,24) 3 ups (baseline legal)", [1, 1, 1], (20, 24)),
    ("(20,24) down+4ups (5 moves)", [2, 1, 1, 1, 1], (20, 24)),
    ("(20,24) R,L,3ups (5 moves)", [4, 3, 1, 1, 1], (20, 24)),
    ("(20,24) 9 wasted then 3 ups", [4, 3] * 4 + [4, 3] + [1, 1, 1], (20, 24)),
    ("(16,28) L,2ups (baseline illegal)", [3, 1, 1], (16, 28)),
    ("(16,28) 2ups,L (y-first)", [1, 1, 3], (16, 28)),
    ("(16,28) with 6 wasted moves", [4, 3, 4, 3, 4, 3, 3, 1, 1], (16, 28)),
    ("(16,28) via top: 5U,L,2D", [1, 1, 1, 1, 1, 3, 2, 2], (16, 28)),
    ("(24,20) baseline legal", [4, 1, 1, 1, 1], (24, 20)),
    ("(24,20) via ceiling: 5U,R,1D", [1, 1, 1, 1, 1, 4, 2], (24, 20)),
    ("(28,20) baseline illegal", [4, 4, 1, 1, 1, 1], (28, 20)),
    ("(28,20) via ceiling: 5U,2R,1D", [1, 1, 1, 1, 1, 4, 4, 2], (28, 20)),
]

for name, moves, target in CASES:
    obs = env.reset()
    if obs.levels_completed == 0:
        for a in RECIPE1:
            obs = env.step(A[a])
    ok = True
    for a in moves:
        obs = env.step(A[a])
        if obs.state.name != "NOT_FINISHED":
            ok = False
            break
    if not ok:
        print(f"  {name}: DIED en route")
        continue
    g = grid(obs)
    if not nine_at(g, target, 80):
        print(f"  {name}: arrival check failed")
        continue
    obs = env.step(A[5])
    g = grid(obs)
    transferred = not nine_at(g, target, 80)
    print(f"  {name}: transfer={transferred} (after {len(moves) + 1} actions)")
sys.stdout.flush()
