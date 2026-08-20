"""g50t probe 5: the same search with the CLOCK back in the visited key.

    ./.venv/Scripts/python.exe g50t_p5.py

Probe 3 found no win and only 12 reachable positions -- against a human baseline
of 78 actions for level 1, which means the instrument, not the game. Its key
masked the clock row so that states would dedup at all; that is exactly the shape
of the sp80 null, where the missing piece of the key was the magazine
(`results/sp80-p11.txt` vs `sp80-p9.txt`). If anything on this board reads the
clock, two boards that look identical at different clock values are different
states and probe 3 pruned the answer away.

Keyed on (board without the clock row, actions taken). The clock is a
deterministic function of the action count, so this is the complete key for any
mechanic that reads it.
"""

import copy
import hashlib
import sys
import time
from collections import deque

import numpy as np

import arc_agi

MAX_DEPTH = 130
MAX_NODES = 60000
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
    return None if not best else (min(p[0] for p in best), min(p[1] for p in best))


def board_key(g):
    m = g.copy()
    m[CLOCK_ROW, :] = 0
    return hashlib.md5(m.tobytes()).hexdigest()


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["g50t"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g0 = grid_of(obs)

seen = {(board_key(g0), 0)}
positions, boards = {piece(g0)}, {board_key(g0)}
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
        bk = board_key(cg)
        k = (bk, len(seq) + 1)
        if k in seen:
            continue
        seen.add(k)
        boards.add(bk)
        p = piece(cg)
        if p is not None:
            positions.add(p)
        frontier.append((seq + [a], child))
    expanded += 1
    if expanded % 2000 == 0:
        print(f"  expanded={expanded} frontier={len(frontier)} states={len(seen)} "
              f"boards={len(boards)} positions={len(positions)} depth~{len(seq)} "
              f"t={time.time() - t0:.0f}s")
        sys.stdout.flush()

print(f"\nexpanded={expanded} states={len(seen)} distinct boards={len(boards)} "
      f"deaths={deaths} t={time.time() - t0:.0f}s")
print(f"distinct piece positions: {len(positions)}")
print(sorted(p for p in positions if p))
touch = [p for p in positions if p
         and p[0] <= GOAL[2] and p[0] + 4 >= GOAL[0] and p[1] <= GOAL[3] and p[1] + 4 >= GOAL[1]]
print(f"positions touching the goal box: {touch}")
print("NO WIN within the search" if win is None else "WIN FOUND")
sys.stdout.flush()
