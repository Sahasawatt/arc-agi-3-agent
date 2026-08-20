"""Positive control for the engine-BFS harness: does it find a win it is KNOWN to
have?

    ./.venv/Scripts/python.exe bfs_control.py

`g50t_p5.py` reports no winning line for g50t level 1 against a human baseline of
78 actions -- a contradiction that means the instrument until proved otherwise.
The control that settles it is to point the same search at a level whose answer
is already measured: sp80 level 1 falls to `[4, 4, 4, 5]` (`results/sp80-p6.txt`).

A search that cannot find a four-action win it is standing on top of is not
evidence of anything when it comes back empty elsewhere.
"""

import copy
import hashlib
import sys
import time
from collections import deque

import numpy as np

import arc_agi

CLOCK_ROW = 63


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def search(game, max_depth, max_nodes, clock_rows):
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    env = arc.make(envs[game].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    g0 = grid_of(obs)

    def bkey(g):
        m = g.copy()
        for r in clock_rows:
            m[r, :] = 0
        return hashlib.md5(m.tobytes()).hexdigest()

    seen = {(bkey(g0), 0)}
    frontier = deque([([], env)])
    expanded, t0, win = 0, time.time(), None
    while frontier and expanded < max_nodes and win is None:
        seq, node = frontier.popleft()
        if len(seq) >= max_depth:
            continue
        for a in sorted(A):
            child = copy.deepcopy(node)
            o = child.step(A[a])
            if o is None:
                continue
            if o.levels_completed > 0 or str(o.state).endswith("WIN"):
                win = seq + [a]
                break
            if not str(o.state).endswith("NOT_FINISHED"):
                continue
            cg = grid_of(o)
            if cg is None:
                continue
            k = (bkey(cg), len(seq) + 1)
            if k in seen:
                continue
            seen.add(k)
            frontier.append((seq + [a], child))
        expanded += 1
    return win, expanded, len(seen), time.time() - t0


print("== CONTROL: sp80 level 1, whose answer [4,4,4,5] is measured ==")
win, exp, states, dt = search("sp80", 8, 4000, (0, 63))
print(f"  win={win} expanded={exp} states={states} t={dt:.0f}s")
print("  VERDICT:", "harness finds a known win -- it is sound"
      if win else "HARNESS IS BROKEN -- it missed a win it was standing on")

print("\n== the same harness on g50t level 1, shallow ==")
win2, exp2, states2, dt2 = search("g50t", 20, 20000, (63,))
print(f"  win={win2} expanded={exp2} states={states2} t={dt2:.0f}s")
sys.stdout.flush()
