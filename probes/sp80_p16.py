"""sp80 probe 16: does the L1 exit recipe change the L2 board?

    ./.venv/Scripts/python.exe sp80_p16.py

Enter L2 via three different winning L1 fires (ceiling, home row, floor) and
byte-compare the L2 start frames (clock row masked).
"""

import hashlib
import sys

import numpy as np

import arc_agi


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def masked_hash(g):
    m = g.copy()
    m[0, :] = 0
    m[63, :] = 0
    return hashlib.md5(m.tobytes()).hexdigest()


arc = arc_agi.Arcade()

RECIPES = [
    ("fast (24,16)", [4, 4, 4, 5]),
    ("ceiling (24,12)", [4, 4, 4, 1, 5]),
    ("floor (24,44)", [4, 4, 4] + [2] * 7 + [5]),
]

hashes = []
for name, rec in RECIPES:
    env = arc.make("sp80")
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    for a in rec:
        obs = env.step(A[a])
    assert obs.levels_completed == 1, f"{name}: lvl={obs.levels_completed}"
    g = grid(obs)
    if g is None:
        # transition frame empty; a reset here would GAME-reset (zero actions
        # since the transition) -- take the same harmless action in every
        # variant instead, so the frames stay comparable
        obs = env.step(A[1])
        g = grid(obs)
    h = masked_hash(g)
    hashes.append(h)
    print(f"  {name}: L2 masked hash {h}")

print("all identical:", len(set(hashes)) == 1)
sys.stdout.flush()
