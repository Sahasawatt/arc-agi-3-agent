"""tr87: do stations 1 (x22) and 2 (x29) share a common symbol with EACH
OTHER (byte-identical, like 0/3/4 do with each other)? If so, try aligning
ALL FIVE stations to their respective shared symbols in one run and watch
for level completion -- the natural conclusion of the "make all 5 stations
agree" hypothesis, now that partial (0,3,4-only) alignment is refuted.
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def deck_at(x0, moves_to_station):
    obs = env.reset()
    for _ in range(moves_to_station):
        obs = env.step(A[4])
    g = grid_of(obs)
    d = [g[51:58, x0:x0 + 5].copy()]
    for i in range(6):
        obs = env.step(A[1])
        g = grid_of(obs)
        d.append(g[51:58, x0:x0 + 5].copy())
    return d


d1 = deck_at(22, 1)
d2 = deck_at(29, 2)
print("station1(x22) vs station2(x29) cross-matches (byte-identical):")
found = []
for i, a in enumerate(d1):
    for j, b in enumerate(d2):
        if np.array_equal(a, b):
            found.append((i, j))
print(" matches (station1_state, station2_state):", found)

if found:
    i1, i2 = found[0]
    print(f"\n== attempt full 5-station alignment: 0,3,4 -> S0 (as probe8), "
          f"1 -> its state {i1}, 2 -> its state {i2} ==")
    obs = env.reset()
    # station0 already at its state 0 (reset) -- leave it.
    obs = env.step(A[4])          # -> station1 (x22)
    for _ in range(i1):
        obs = env.step(A[1])
    obs = env.step(A[4])          # -> station2 (x29)
    for _ in range(i2):
        obs = env.step(A[1])
    obs = env.step(A[4])          # -> station3 (x36), reset phase S4 -> need +3 to reach S0
    for _ in range(3):
        obs = env.step(A[1])
    obs = env.step(A[4])          # -> station4 (x43), reset phase S2 -> need +5 to reach S0
    for _ in range(5):
        obs = env.step(A[1])
    print("levels_completed:", obs.levels_completed,
          "state:", str(obs.state).split(".")[-1])
else:
    print("no shared symbol between station1 and station2 -- families differ pairwise too")

sys.stdout.flush()
