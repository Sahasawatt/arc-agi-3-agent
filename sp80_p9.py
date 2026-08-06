"""sp80 probe 9: env-driven BFS over level 2 -- find the shortest clearing line.

    ./.venv/Scripts/python.exe sp80_p9.py [level_recipes...]

The engine replays byte-identically in-process at ~80k steps/s, so BFS with the
board hash as the visited key needs no model of the transfer rule at all.
Nodes are action sequences replayed from the level start (env.reset() scopes to
the level; a reset taken with zero actions after a transition would game-reset,
which the replay loop never does -- every node replays >=1 action).

Clock row is excluded from the state hash (it burns every action; keeping it
would make every state unique and kill the dedup).
"""

import hashlib
import sys
import time
from collections import deque

import numpy as np

import arc_agi

RECIPES = [[4, 4, 4, 5]]  # level 1
MAX_DEPTH = 29            # 30-action budget
MAX_NODES = 150000
CLOCK_ROWS = (0, 63)      # bar row either end, depending on the board's flip


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def key(g):
    if g is None:
        return "empty"
    m = g.copy()
    for r in CLOCK_ROWS:
        m[r, :] = 0
    return hashlib.md5(m.tobytes()).hexdigest()


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
obs = env.reset()
obs = env.step(A[1])

BASE_LVL = len(RECIPES)


def to_base(env):
    obs = env.reset()
    if obs.levels_completed == 0:
        for rec in RECIPES:
            for a in rec:
                obs = env.step(A[a])
    assert obs.levels_completed == BASE_LVL, f"at {obs.levels_completed}"
    return obs


obs = to_base(env)
g0 = grid(obs)
start_key = key(g0)

seen = {start_key}
frontier = deque([[]])
expanded = 0
steps_paid = 0
t0 = time.time()
win = None

while frontier and expanded < MAX_NODES and win is None:
    seq = frontier.popleft()
    if len(seq) >= MAX_DEPTH:
        continue
    for a in [1, 2, 3, 4, 5]:
        obs = to_base(env)
        for s in seq:
            obs = env.step(A[s])
        obs = env.step(A[a])
        steps_paid += len(seq) + 1
        if obs.levels_completed > BASE_LVL or obs.state.name == "WIN":
            win = seq + [a]
            print(f"WIN: {win}  (len {len(win)})  state={obs.state.name} "
                  f"lvl={obs.levels_completed}")
            break
        if obs.state.name != "NOT_FINISHED":
            continue
        k = key(grid(obs))
        if k in seen:
            continue
        seen.add(k)
        frontier.append(seq + [a])
    expanded += 1
    if expanded % 2000 == 0:
        print(f"  expanded={expanded} frontier={len(frontier)} states={len(seen)} "
              f"depth~{len(seq)} steps={steps_paid} t={time.time() - t0:.0f}s")
        sys.stdout.flush()

if win is None:
    print(f"NO WIN within depth {MAX_DEPTH}: expanded={expanded} states={len(seen)} "
          f"steps={steps_paid} t={time.time() - t0:.0f}s")
sys.stdout.flush()
