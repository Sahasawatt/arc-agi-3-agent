"""tu93 probe 2: dump full piece(9)+notch(4) cell set after EVERY single
action4 press (not just diff counts) to see the real per-press trajectory.
"""
import sys
import numpy as np
import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def cells(g, color):
    ys, xs = np.nonzero(g == color)
    return sorted(zip(ys.tolist(), xs.tolist()))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tu93"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = grid_of(obs)
c9 = cells(g, 9)
c4 = cells(g, 4)
print(f"reset: piece9={c9} notch4={c4}")

for i in range(15):
    obs = env.step(A[4])
    g = grid_of(obs)
    if g is None:
        print(f"  {i}: empty frame")
        break
    c9 = cells(g, 9)
    c4 = cells(g, 4)
    lvl = obs.levels_completed
    print(f"  {i}: piece9(n={len(c9)})={c9} notch4={c4} lvl={lvl}")
sys.stdout.flush()
