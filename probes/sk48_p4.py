"""sk48: the full level-1 line. Grab 8, push it through 14 (both retract
together -- the skewer threads on contact), then up to 9's rows, push both
through 9, retract. Expect the level. Count actions."""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sk48"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
spent, lvl = 0, 0
SEQ = ([1, 1, 1] + [4] * 4 + [3] * 4          # grab 8, home
       + [2, 2] + [4] * 4 + [3] * 4          # 14's rows: push 8 into 14, pull both
       + [1] + [4] * 4 + [3] * 4)            # 9's rows: push both into 9, pull all
for v in SEQ:
    prev = grid_of(obs)
    obs = env.step(A[v])
    spent += 1
    if obs is None:
        print(f"obs=None at press {spent}")
        break
    if obs.levels_completed > lvl:
        print(f"LEVEL {obs.levels_completed} at press {spent} (A{v})")
        lvl = obs.levels_completed
        break
    if str(obs.state) != "GameState.NOT_FINISHED":
        print(f"{str(obs.state).split('.')[-1]} at press {spent}")
        break

g = grid_of(obs)
if g is not None:
    print("final rows y18-41 x10-50:")
    for y in range(18, 42):
        print(f"  y{y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                       for v in g[y, 10:50]))
print(f"levels_completed={0 if obs is None else obs.levels_completed} spent={spent}")
sys.stdout.flush()
