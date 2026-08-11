"""sb26: the whole grid is click-dead and ACTION7 never answers. What is left:
run each plain action to the end of the bar (what IS the terminal?), and try
mixed cadences (5/7 alternation, 7 bursts) in case something counts invisibly.
Every diff excludes the bar row.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def changed(a, b, skip_row=53):
    if a is None or b is None:
        return -1
    m = a != b
    m[skip_row] = False
    return int(m.sum())


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
A = {a.value: a for a in env.action_space}

for label, seq in [("A5 x70", [5] * 70),
                   ("A7 x70", [7] * 70),
                   ("5,7 alternating x35", [5, 7] * 35),
                   ("A7 x17 then A5", [7] * 17 + [5]),
                   ("A5 x17 then A7", [5] * 17 + [7])]:
    obs = env.reset()
    g0 = grid_of(obs)
    end = "ran out"
    for i, v in enumerate(seq):
        obs = env.step(A[v])
        if obs is None:
            end = f"obs=None at {i}"
            break
        if obs.levels_completed > 0:
            end = f"LEVEL UP at press {i + 1}"
            break
        if str(obs.state) != "GameState.NOT_FINISHED":
            end = f"{str(obs.state).split('.')[-1]} at press {i + 1}"
            break
    g1 = grid_of(obs)
    print(f"{label}: {end}; net change outside bar = {changed(g0, g1)}")
    sys.stdout.flush()
