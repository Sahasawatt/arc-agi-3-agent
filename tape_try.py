"""Drive bp35 with tape.py alone, before wiring anything.

Standalone: the driver's own act() against a live env, forward-only, with the
flood and the level printed per action. The hand line clears level 1 in 20
actions (results/bp35-solution.txt); this asks whether the policy that was
derived FROM that line rediscovers it from the frame.
"""
import sys

import numpy as np

import arc_agi
from tape import Tape, signature


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
print(f"signature at reset: {signature(g)}")
drv = Tape([a.value for a in env.action_space])
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
    n = int((g != g2).sum())
    ys, _ = np.nonzero(g2[:63] == 15)
    print(f"  i={i:2d} {what:14s} n={n:5d} cnt={int((g2[63] == 15).sum()):2d} "
          f"flood={int(ys.min()) if len(ys) else None} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
          f"{'  RIDE' if n > 600 else ''}")
    if obs.levels_completed > len(lvls):
        lvls.append(i + 1)
        print(f"  ** LEVEL {obs.levels_completed} at action {i + 1} **")
    g = g2
    if str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END state={str(obs.state).split('.')[-1]}")
        break
    sys.stdout.flush()
print(f"levels: {obs.levels_completed}, at actions {lvls}")
