"""sb26 L5: WHERE is the single answer cell A5 changes, per arm?

All four instrument-(a) arms load cleanly and A5 answers n=1 with no level
(results/sb26-l5-arms.txt). If that one cell's POSITION or COLOUR varies
with the assignment, it is a feedback channel and the 10,080-leaf exhaust
collapses to a guided walk. Also pressed: A5 a second time (does the answer
cell toggle/advance?), and one deliberately-absurd arm (everything reversed)
as a control -- a cell that never moves regardless is a timer, not feedback.
"""
import copy
import sys

import numpy as np

import arc_agi
from sorter import Sorter

STOCK = {"f": 6, "6": 13, "8a": 20, "8b": 27, "b": 34, "e": 41,
         "9h1": 48, "9h2": 55}
STOCK_Y = 58
U = [(19, 22), (25, 22), (31, 22), (37, 22), (43, 22)]
L = [(25, 36), (31, 36), (37, 36)]
ORDER_AFTER = [U[0], U[1], U[2], L[0], L[1], L[2], U[3], U[4]]
SEQ_8 = ["6", "e", "8a", "8b", "9h1", "9h2", "b", "f"]

ARMS = [
    ("greedy 9h=8 after", SEQ_8, ORDER_AFTER),
    ("reversed control", list(reversed(SEQ_8)), ORDER_AFTER),
    ("stock order", ["f", "6", "8a", "8b", "b", "e", "9h1", "9h2"],
     ORDER_AFTER),
]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def cells(a, b):
    return [(int(y), int(x), int(a[y, x]), int(b[y, x]))
            for y, x in np.argwhere(a != b)]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = grid_of(obs)
drv = Sorter([a.value for a in env.action_space])
for i in range(200):
    v = drv.act(g, obs.levels_completed)
    if v is None:
        break
    if isinstance(v, tuple):
        obs = env.step(A[6], data={"x": v[1], "y": v[2]})
    else:
        obs = env.step(A[v])
    g = grid_of(obs)
assert obs.levels_completed == 4
BASE = env
G_BASE = grid_of(obs)
print(f"at level 5 after {i} driver actions")
sys.stdout.flush()

for label, seq, order in ARMS:
    e = copy.deepcopy(BASE)
    prev = G_BASE
    for key, slot in zip(seq, order):
        e.step(A[6], data={"x": STOCK[key], "y": STOCK_Y})
        o = e.step(A[6], data={"x": slot[0], "y": slot[1]})
        prev = grid_of(o)
    o = e.step(A[5])
    g1 = grid_of(o)
    o = e.step(A[5])
    g2 = grid_of(o)
    print(f"arm [{label}]")
    print(f"  A5 #1: {cells(prev, g1)} lvl={o.levels_completed}")
    print(f"  A5 #2: {cells(g1, g2)}")
    sys.stdout.flush()
