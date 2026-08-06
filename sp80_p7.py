"""sp80 probe 7: level-2 fire sweep with FULL diff -- does any shot change anything?

    ./.venv/Scripts/python.exe sp80_p7.py

p4's sweep only checked for level-up; a shot that moves an 8-block (or anything)
would have been invisible. Fire up to 4 shots per reachable position, report any
non-clock cell change. Clock row on this board = y63 (bar flipped to the bottom).
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
obs = env.step(A[1])

X0, Y0 = 20, 36
hits = []
fired = 0
for tx in range(0, 61, 4):
    for ty in range(0, 61, 4):
        obs = env.reset()
        if obs.levels_completed == 0:
            # reset right after a transition game-reset us to L1; replay and use
            # the fresh L2 board directly (another reset would game-reset again)
            for a in RECIPE1:
                obs = env.step(A[a])
        if obs.levels_completed != 1:
            print("cannot hold level 2, lvl =", obs.levels_completed)
            sys.exit(1)
        dx = (tx - X0) // 4
        dy = (ty - Y0) // 4
        moves = [4] * max(dx, 0) + [3] * max(-dx, 0) + [2] * max(dy, 0) + [1] * max(-dy, 0)
        if len(moves) + 4 > 29:
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
            continue
        pre = grid(obs)
        fired += 1
        for shot in range(4):
            obs = env.step(A[5])
            cur = grid(obs)
            if obs.state.name != "NOT_FINISHED" or obs.levels_completed > 1:
                hits.append((tx, ty, shot + 1, "TERMINAL",
                             obs.state.name, obs.levels_completed))
                break
            if cur is None or pre is None:
                hits.append((tx, ty, shot + 1, "EMPTY-FRAME", obs.state.name, 1))
                break
            d = (pre != cur)
            d[63, :] = False
            ys, xs = np.nonzero(d)
            if len(xs):
                cells = [(int(x), int(y), int(pre[y, x]), int(cur[y, x]))
                         for y, x in zip(ys[:8], xs[:8])]
                hits.append((tx, ty, shot + 1, f"{len(xs)} cells {cells}",
                             obs.state.name, 1))
            pre = cur

print(f"fired from {fired} positions (up to 4 shots each)")
if hits:
    for h in hits:
        print("  HIT:", h)
else:
    print("  no shot changed a single non-clock cell anywhere")
sys.stdout.flush()
