"""tr87: build the universal 7-symbol sequence from station 1, then read each
of the 5 stations' RESET phase offset into that same sequence (by content
match, not just visual guess). If all 5 stations draw from one shared
7-symbol cycle, this tells us exactly how many ACTION1/ACTION2 presses each
station needs to reach any common target symbol.
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}
STATIONS = [15, 22, 29, 36, 43]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def window(g, x0):
    return g[51:58, x0:x0 + 5].copy()


# Build the universal sequence S0..S6 from station 1 (x15), which sits there
# at reset with zero cursor moves.
obs = env.reset()
g = grid_of(obs)
S = [window(g, 15)]
for i in range(6):
    obs = env.step(A[1])
    g = grid_of(obs)
    S.append(window(g, 15))
print("universal sequence built, S0..S6 (station 1 own cycle)")

# For each station, reset fresh and read its OWN reset window, then find
# which S[i] it equals.
for st_idx, x0 in enumerate(STATIONS):
    obs = env.reset()
    moves = st_idx  # ACTION4 presses to reach station st_idx from station 0
    for _ in range(moves):
        obs = env.step(A[4])
    g = grid_of(obs)
    w = window(g, x0)
    match = [i for i, s in enumerate(S) if np.array_equal(s, w)]
    print(f"station{st_idx} (x{x0}): reset window matches S{match}")

sys.stdout.flush()
