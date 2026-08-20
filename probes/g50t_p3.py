"""g50t probe 3: the TRUE reachable set, asked of the engine rather than of a model.

    ./.venv/Scripts/python.exe g50t_p3.py

Two readings disagree and both are measured: the piece walks ONTO colour 8 at
(38, 8) and the 8s there are consumed while 24 wall cells open
(`results/g50t-p1.txt` A), and the identical-looking move into (14, 38) is
REFUSED (`g50t-p1.txt` C). A model cannot arbitrate that; the engine can.

BFS over real engine states with `copy.deepcopy` (legal, faithful, ~2-3ms --
measured on sp80, `results/sp80-p10.txt`). The visited key is the board with the
clock row masked, because the clock burns on every action and would otherwise
make every state unique and kill the dedup.
"""

import copy
import hashlib
import sys
import time
from collections import deque

import numpy as np

import arc_agi

MAX_DEPTH = 128     # the clock is 64 cells at 1 per 2 actions -> a life
MAX_NODES = 20000
CLOCK_ROW = 63
GOAL = (43, 49, 49, 55)


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece(g):
    ys, xs = np.nonzero(g == 9)
    cells = {(int(x), int(y)) for x, y in zip(xs, ys) if y < 60 and x > 10}
    best = set()
    while cells:
        stack, blob = [next(iter(cells))], set()
        while stack:
            p = stack.pop()
            if p in blob or p not in cells:
                continue
            blob.add(p)
            x, y = p
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) in cells:
                    stack.append((x + dx, y + dy))
        cells -= blob
        if len(blob) > len(best):
            best = blob
    if not best:
        return None
    return (min(p[0] for p in best), min(p[1] for p in best))


def key(g):
    m = g.copy()
    m[CLOCK_ROW, :] = 0
    return hashlib.md5(m.tobytes()).hexdigest()


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["g50t"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g0 = grid_of(obs)

seen = {key(g0)}
positions = {piece(g0)}
frontier = deque([([], env)])
expanded, t0, win, deaths = 0, time.time(), None, 0

while frontier and expanded < MAX_NODES and win is None:
    seq, node = frontier.popleft()
    if len(seq) >= MAX_DEPTH:
        continue
    for a in sorted(A):
        child = copy.deepcopy(node)
        o = child.step(A[a])
        if o is None:
            continue
        if o.levels_completed > 0 or str(o.state).endswith("WIN"):
            win = seq + [a]
            print(f"WIN in {len(win)} actions: {win}")
            break
        if not str(o.state).endswith("NOT_FINISHED"):
            deaths += 1
            continue
        cg = grid_of(o)
        if cg is None:
            continue
        k = key(cg)
        if k in seen:
            continue
        seen.add(k)
        p = piece(cg)
        if p is not None:
            positions.add(p)
        frontier.append((seq + [a], child))
    expanded += 1
    if expanded % 500 == 0:
        print(f"  expanded={expanded} frontier={len(frontier)} states={len(seen)} "
              f"positions={len(positions)} depth~{len(seq)} t={time.time() - t0:.0f}s")
        sys.stdout.flush()

print(f"\nexpanded={expanded} states={len(seen)} deaths={deaths} t={time.time() - t0:.0f}s")
print(f"distinct piece positions reachable: {len(positions)}")
print(sorted(positions))
touch = [p for p in positions
         if p[0] <= GOAL[2] and p[0] + 4 >= GOAL[0] and p[1] <= GOAL[3] and p[1] + 4 >= GOAL[1]]
print(f"positions whose footprint touches the goal box {GOAL}: {touch}")
if win is None:
    print("NO WIN within the search")
sys.stdout.flush()
