"""sb26: only the bar ever moves, and ACTION7 is FREE (70 presses, no burn,
no change). A free action next to a burn action smells like "commit": maybe
the win is pressing 7 with the bar at the right LENGTH. Scan k = 0..63 burns
then one ACTION7 -- and since a commit might need repetition, press it three
times. Cheap: one episode per k.
"""
import sys

import numpy as np

import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
A = {a.value: a for a in env.action_space}

for k in range(64):
    obs = env.reset()
    ok = True
    for _ in range(k):
        obs = env.step(A[5])
        if obs is None or str(obs.state) != "GameState.NOT_FINISHED":
            ok = False
            break
    if not ok:
        print(f"k={k}: died during burn")
        continue
    for j in range(3):
        obs = env.step(A[7])
        if obs is None:
            print(f"k={k}: obs=None on ACTION7 #{j+1}")
            break
        if obs.levels_completed > 0 or str(obs.state) != "GameState.NOT_FINISHED":
            print(f"k={k}: lvl={obs.levels_completed} "
                  f"state={str(obs.state).split('.')[-1]} after ACTION7 #{j+1}")
            break
    sys.stdout.flush()
print("scan done")
