"""Drive dc22 with bridge.py alone, before wiring anything.

The hand line clears level 1 in 20 actions against a baseline of 59
(results/dc22-solution.txt); this asks whether the policy derived from it
rediscovers the route from the frame.
"""
import sys

import numpy as np

import arc_agi
from bridge import Bridge, read, signature


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["dc22"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
print(f"signature at reset: {signature(g)}")
print(f"read: {read(g)}")
drv = Bridge([a.value for a in env.action_space])
lvls = []
for i in range(120):
    v = drv.act(g, obs.levels_completed)
    if v is None:
        print(f"  i={i:2d} driver answered None -- the rungs would take over")
        break
    if isinstance(v, tuple):
        obs = env.step(A[6], data={"x": v[1], "y": v[2]})
        what = f"click({v[1]},{v[2]})"
    else:
        obs = env.step(A[v])
        what = f"A{v}"
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d} {what}: DEAD FRAME")
        break
    print(f"  i={i:2d} {what:14s} n={int((g != g2).sum()):5d} "
          f"mover={drv.mover} lvl={obs.levels_completed} "
          f"st={str(obs.state).split('.')[-1]}")
    if obs.levels_completed > len(lvls):
        lvls.append(i + 1)
        print(f"  ** LEVEL {obs.levels_completed} at action {i + 1} **")
    g = g2
    if str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END state={str(obs.state).split('.')[-1]}")
        break
    sys.stdout.flush()
print(f"levels: {obs.levels_completed}, at actions {lvls}")
