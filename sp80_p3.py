"""sp80 probe 3: is ACTION5 a positional shot? Fire once from every x alignment.

    ./.venv/Scripts/python.exe sp80_p3.py

One reset per attempt (30-action budget each). Diff excludes the bar row (y0).
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
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))


def fire_after(env, A, moves, label):
    obs = env.reset()
    for a in moves:
        obs = env.step(A[a])
    pre = grid(obs)
    b = blk(pre)
    obs = env.step(A[5])
    cur = grid(obs)
    if pre is None or cur is None:
        print(f"  {label}: block={b} frame empty after fire, state={obs.state}")
        return obs
    d = (pre != cur)
    d[0, :] = False  # ignore the bar row
    ys, xs = np.nonzero(d)
    cells = [(int(x), int(y), int(pre[y, x]), int(cur[y, x])) for y, x in zip(ys, xs)]
    print(f"  {label}: block={b} diff(non-bar)={len(cells)} {cells[:10]} state={obs.state} lvl={obs.levels_completed}")
    return obs


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}

print("== fire from every x alignment (home row y16-19) ==")
for k in range(0, 9):
    fire_after(env, A, [4] * k, f"right x{k} (x-left={12 + 4 * k})")
for k in range(1, 4):
    fire_after(env, A, [3] * k, f"left x{k} (x-left={12 - 4 * k})")

print("\n== fire from the ceiling (y12) at stack alignment ==")
fire_after(env, A, [1] + [4] * 6, "up1 right6 (x36-55, y12-15)")
fire_after(env, A, [1], "up1 (x12-31, y12-15)")

print("\n== fire from the floor (y44) ==")
fire_after(env, A, [2] * 7, "down7 (x12-31, y44-47)")
fire_after(env, A, [2] * 7 + [4] * 2, "down7 right2 (x20-39, y44-47)")
sys.stdout.flush()
