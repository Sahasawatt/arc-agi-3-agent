"""sp80 probe 11: BFS over level 2 done right -- depth 44, deepcopy nodes,
ammo in the state key.

    ./.venv/Scripts/python.exe sp80_p11.py

p9's null was an instrument artifact twice over: depth cap 29 on a 45-action
budget, and fires-used (5th fire kills) collapsed out of the visited key.
"""

import copy
import hashlib
import sys
import time
from collections import deque

import numpy as np

import arc_agi

RECIPES = [[4, 4, 4, 5]]
MAX_DEPTH = 44
MAX_NODES = 400000
MAX_FRONTIER = 60000
CLOCK_ROWS = (0, 63)


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def key(g, fires):
    if g is None:
        return ("empty", fires)
    m = g.copy()
    for r in CLOCK_ROWS:
        m[r, :] = 0
    return (hashlib.md5(m.tobytes()).hexdigest(), fires)


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
obs = env.reset()
obs = env.step(A[1])
obs = env.reset()
if obs.levels_completed == 0:
    for rec in RECIPES:
        for a in rec:
            obs = env.step(A[a])
BASE_LVL = len(RECIPES)
assert obs.levels_completed == BASE_LVL

g0 = grid(obs)
seen = {key(g0, 0)}
frontier = deque([([], env, 0)])
expanded = 0
t0 = time.time()
win = None

while frontier and expanded < MAX_NODES and win is None:
    seq, node_env, fires = frontier.popleft()
    if len(seq) >= MAX_DEPTH:
        continue
    for a in [1, 2, 3, 4, 5]:
        child = copy.deepcopy(node_env)
        o = child.step(A[a])
        nf = fires + (1 if a == 5 else 0)
        if o.levels_completed > BASE_LVL or o.state.name == "WIN":
            win = seq + [a]
            print(f"WIN: {win}  (len {len(win)}, fires {nf})  "
                  f"state={o.state.name} lvl={o.levels_completed}")
            break
        if o.state.name != "NOT_FINISHED":
            continue
        k = key(grid(o), nf)
        if k in seen:
            continue
        seen.add(k)
        frontier.append((seq + [a], child, nf))
    expanded += 1
    if len(frontier) > MAX_FRONTIER:
        print(f"FRONTIER CAP HIT at {len(frontier)} -- memory guard, stopping")
        break
    if expanded % 5000 == 0:
        print(f"  expanded={expanded} frontier={len(frontier)} states={len(seen)} "
              f"depth~{len(seq)} t={time.time() - t0:.0f}s")
        sys.stdout.flush()

if win is None:
    print(f"NO WIN: expanded={expanded} states={len(seen)} "
          f"frontier={len(frontier)} t={time.time() - t0:.0f}s")
sys.stdout.flush()
