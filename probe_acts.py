"""What does each action do? Press one action repeatedly from a fresh reset.

    ./.venv/Scripts/python.exe probe_acts.py <game> [repeat]

`probe.py` does the same and reads `np.array(obs.frame)[-1]` unguarded, so it dies
with IndexError the moment a game hands back an empty frame -- which is what a
GAME_OVER looks like, and is why sp80's action 6 went unprobed for a session
(`results/sp80-probe8.txt`). Every read here is guarded, and the diff names the
colour pairs that changed rather than only counting cells.
"""

import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


game = sys.argv[1] if len(sys.argv) > 1 else "ls20"
repeat = int(sys.argv[2]) if len(sys.argv) > 2 else 6
arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs[game].game_id)

for action in env.action_space:
    obs = env.reset()
    prev = grid_of(obs)
    print(f"\n== ACTION{action.value} (complex={action.is_complex()}) ==")
    for i in range(repeat):
        data = {"x": 32, "y": 32} if action.is_complex() else {}
        obs = env.step(action, data=data)
        cur = grid_of(obs)
        state = "obs=None" if obs is None else str(obs.state).split(".")[-1]
        lvl = "" if obs is None else f" lvl={obs.levels_completed}"
        if cur is None or prev is None:
            print(f"  {i}: frame empty  state={state}{lvl}")
            if obs is None or state != "NOT_FINISHED":
                break
            prev = cur
            continue
        ys, xs = np.nonzero(cur != prev)
        if not len(xs):
            print(f"  {i}: no change  state={state}{lvl}")
        else:
            pairs = {}
            for y, x in zip(ys.tolist(), xs.tolist()):
                pairs[(int(prev[y, x]), int(cur[y, x]))] = \
                    pairs.get((int(prev[y, x]), int(cur[y, x])), 0) + 1
            top = sorted(pairs.items(), key=lambda t: -t[1])[:5]
            print(f"  {i}: {len(xs):4d} cells  x[{xs.min()}-{xs.max()}] "
                  f"y[{ys.min()}-{ys.max()}]  "
                  + " ".join(f"{a}->{b}:{n}" for (a, b), n in top)
                  + f"  state={state}{lvl}")
        prev = cur
        if state != "NOT_FINISHED":
            break
sys.stdout.flush()
