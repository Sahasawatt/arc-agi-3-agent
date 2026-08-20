"""Run the Sorter driver alone on sb26: how many levels, and what does the
first frame after its last cleared level look like?  Touches nothing under
results/compete.json."""
import sys

import numpy as np

import arc_agi
from sorter import Sorter


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def dump(g, label):
    print(f"  --- {label} ---")
    for y in range(g.shape[0]):
        line = "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                       for v in g[y])
        if len(set(line)) > 1:
            print(f"    y{y:2d} {line}")


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
drv = Sorter([a.value for a in env.action_space])
nones = 0
for i in range(600):
    v = drv.act(g, obs.levels_completed)
    if v is None:
        nones += 1
        if nones > 3:
            print(f"driver None at i={i}, level {obs.levels_completed + 1}")
            dump(g, f"level {obs.levels_completed + 1}")
            break
        continue
    nones = 0
    if isinstance(v, tuple):
        obs = env.step(A[6], data={"x": v[1], "y": v[2]})
    else:
        obs = env.step(A[v])
    g = grid_of(obs)
    if g is None:
        print(f"dead frame at i={i}")
        break
    if str(obs.state) != "GameState.NOT_FINISHED":
        print(f"i={i}: state={str(obs.state).split('.')[-1]} "
              f"lvl={obs.levels_completed}")
        break
print(f"levels_completed={obs.levels_completed} actions={i}")
sys.stdout.flush()
