"""tr87: systematically test whether the y40-46 hint icon at each station's x
equals (by colour-5 boolean mask, ink=5) one of that STATION'S OWN 7 reachable
dial states -- computed by code, not by hand, to avoid transcription error.
If a match exists, report exactly how many ACTION1 presses reach it.
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


obs = env.reset()
g0 = grid_of(obs)

hints = {x0: (g0[40:47, x0:x0 + 5] == 5) for x0 in STATIONS}
print("hint masks (True='5'):")
for x0 in STATIONS:
    print(f" x={x0}: {hints[x0].sum()} cells")

for st_idx, x0 in enumerate(STATIONS):
    obs = env.reset()
    for _ in range(st_idx):
        obs = env.step(A[4])
    g = grid_of(obs)
    deck = [g[51:58, x0:x0 + 5] == 5]
    for i in range(1, 7):
        obs = env.step(A[1])
        g = grid_of(obs)
        deck.append(g[51:58, x0:x0 + 5] == 5)
    matches = [i for i, m in enumerate(deck) if np.array_equal(m, hints[x0])]
    matches_inv = [i for i, m in enumerate(deck) if np.array_equal(~m, hints[x0])]
    print(f"station{st_idx} x={x0}: ink=5 match at state {matches}  "
          f"(inverted-mask match at {matches_inv})")

sys.stdout.flush()
