"""What does each action actually do? Press one action repeatedly from a fresh reset."""

import sys

import numpy as np

import arc_agi

GAME = sys.argv[1] if len(sys.argv) > 1 else "ls20"
REPEAT = int(sys.argv[2]) if len(sys.argv) > 2 else 4

arc = arc_agi.Arcade()
env = arc.make(GAME)


def frame(obs):
    return np.array(obs.frame)[-1]


for action in env.action_space:
    obs = env.reset()
    prev = frame(obs)
    print(f"\n== ACTION{action.value} ==")
    for i in range(REPEAT):
        data = {"x": 32, "y": 32} if action.is_complex() else {}
        obs = env.step(action, data=data)
        cur = frame(obs)
        ys, xs = np.nonzero(cur != prev)
        if len(xs) == 0:
            print(f"  {i}: no change  state={obs.state}")
        else:
            print(f"  {i}: {len(xs):4d} cells  x[{xs.min()}-{xs.max()}] y[{ys.min()}-{ys.max()}]"
                  f"  colours {sorted(set(prev[ys, xs].tolist()))} -> {sorted(set(cur[ys, xs].tolist()))}"
                  f"  state={obs.state} lvl={obs.levels_completed}")
        prev = cur
