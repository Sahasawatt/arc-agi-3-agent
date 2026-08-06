"""sp80 probe 6: the FULL win map of level 1 -- every position that clears it.

    ./.venv/Scripts/python.exe sp80_p6.py

Uses the reset-after-transition trap as a tool: env.reset() with zero actions
since a level-up is a full GAME reset, which puts level 1 back. Verified inline.
"""

import sys

import numpy as np

import arc_agi


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def blk(g):
    if g is None:
        return None
    ys, xs = np.nonzero(g == 9)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()))


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
obs = env.reset()

wins = []
fired = 0
unreachable = []
X0, Y0 = 12, 16
for tx in range(0, 61, 4):
    for ty in range(0, 61, 4):
        if obs.levels_completed != 0:
            obs = env.reset()  # zero actions since the transition -> game reset
            if obs.levels_completed != 0:
                print("GAME-RESET TRICK FAILED, lvl =", obs.levels_completed)
                sys.exit(1)
        else:
            obs = env.reset()
        dx = (tx - X0) // 4
        dy = (ty - Y0) // 4
        moves = [4] * max(dx, 0) + [3] * max(-dx, 0) + [2] * max(dy, 0) + [1] * max(-dy, 0)
        if len(moves) + 1 > 29:
            continue
        dead = False
        for a in moves:
            obs = env.step(A[a])
            if obs.state.name != "NOT_FINISHED":
                dead = True
                break
        if dead:
            continue
        if blk(grid(obs)) != (tx, ty):
            unreachable.append((tx, ty))
            continue
        obs = env.step(A[5])
        fired += 1
        if obs.levels_completed > 0 or obs.state.name == "WIN":
            wins.append((tx, ty))

print(f"fired from {fired} positions")
print(f"unreachable: {len(unreachable)} {unreachable}")
print(f"WINS: {len(wins)} {wins}")
sys.stdout.flush()
