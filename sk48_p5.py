"""sk48: WHY does the 14-action line win? Replay it forward-only and dump the
room after every press -- the win fired on an extend at 9's rows with the arm
apparently too short to reach anything, so the model in p1-p4's head is wrong
somewhere. Watch the queue positions especially."""
import sys

import numpy as np

import arc_agi

LINE = [1, 1, 1, 4, 4, 4, 4, 3, 2, 2, 4, 3, 1, 4]

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sk48"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()


def room(g, label):
    print(label)
    for y in range(12, 42):
        print(f"  y{y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                       for v in g[y, 10:48]))


room(np.array(obs.frame)[-1], "reset:")
for i, v in enumerate(LINE):
    obs = env.step(A[v])
    if obs is None:
        print(f"press {i+1}: None")
        break
    g = np.array(obs.frame)[-1]
    room(g, f"after press {i+1} (A{v})  lvl={obs.levels_completed}:")
    if obs.levels_completed:
        break
    sys.stdout.flush()
