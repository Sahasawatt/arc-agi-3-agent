"""Replay the BFS-found level-1 solution on a FRESH env (real forward play,
not the deepcopy-forked BFS tree) and confirm obs.levels_completed increases.
"""
import sys
import numpy as np
import arc_agi

SOLUTION = [4, 2, 2, 4, 1, 4, 2, 2, 3, 3, 2, 4, 4, 2, 4, 1, 4, 2]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tu93"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
print(f"reset: lvl={obs.levels_completed} state={obs.state}")
for i, a in enumerate(SOLUTION):
    obs = env.step(A[a])
    state = "obs=None" if obs is None else str(obs.state)
    lvl = None if obs is None else obs.levels_completed
    print(f"  step {i} action{a}: state={state} lvl={lvl}")
    if obs is None:
        break

print(f"\nFINAL: lvl={obs.levels_completed if obs else None} state={obs.state if obs else None}")
sys.stdout.flush()
