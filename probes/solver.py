"""Solve a level offline.

Probing the maze one action at a time costs an API round-trip per guess and a replay of
the whole prefix per experiment. The board is fully visible in a single frame, so read the
walkable map off that frame once and BFS on it instead.

    uv run python solver.py ls20 <prefix-actions>

Prints the map, self-checks it against moves already known to be blocked/free, then
searches for a route.
"""

import sys
from collections import deque

import numpy as np

import arc_agi
from perception import objects

VOID = 4          # impassable background
STEP = 5          # a move shifts the block 5 cells
DIRS = {1: (0, -STEP), 2: (0, STEP), 3: (-STEP, 0), 4: (STEP, 0)}


def block_box(objs):
    for o in objs:
        if o["colour"] == 12:  # orange half of the piece
            return o["x"][0], o["y"][0]
    raise SystemExit("no block on screen")


def walkable(grid, x, y, w, h):
    """Can the block's 5x5 footprint sit at (x,y)?"""
    if x < 0 or y < 0 or x + w > grid.shape[1] or y + h > grid.shape[0]:
        return False
    return not (grid[y:y + h, x:x + w] == VOID).any()


def bfs(grid, start, goals, w, h):
    seen = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur in goals:
            path, node = [], cur
            while seen[node]:
                act, node = seen[node]
                path.append(act)
            return cur, path[::-1]
        for act, (dx, dy) in DIRS.items():
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt not in seen and walkable(grid, nxt[0], nxt[1], w, h):
                seen[nxt] = (act, cur)
                q.append(nxt)
    return None, None


GAME = sys.argv[1]
PREFIX = [int(a) for a in sys.argv[2].split(",")] if len(sys.argv) > 2 else []

arc = arc_agi.Arcade()
env = arc.make(GAME)
obs = env.reset()
space = {a.value: a for a in env.action_space}
for a in PREFIX:
    obs = env.step(space[a])

grid = np.array(obs.frame)[-1]
objs, _ = objects(obs.frame)
bx, by = block_box(objs)
BW, BH = 5, 5
print(f"level={obs.levels_completed} block at x{bx} y{by}")

# Self-check: the four moves from here must agree with what probing already showed.
for act, (dx, dy) in DIRS.items():
    ok = walkable(grid, bx + dx, by + dy, BW, BH)
    print(f"  map says action {act}: {'free' if ok else 'blocked'}")

targets = {"cross": [o for o in objs if o["colour"] in (0, 1)],
           "yellow": [o for o in objs if o["colour"] == 11],
           "goalbox": [o for o in objs if o["colour"] == 5 and o["cells"] > 30]}
for name, os_ in targets.items():
    for o in os_:
        print(f"  {name} at x{o['x'][0]}-{o['x'][1]} y{o['y'][0]}-{o['y'][1]}")

def overlap_cells(o):
    """Footprint positions that touch object o."""
    out = set()
    for gy in range(by % STEP, 60 - BH, STEP):
        for gx in range(bx % STEP, 64 - BW, STEP):
            if not walkable(grid, gx, gy, BW, BH):
                continue
            if (gx < o["x"][1] + 1 and gx + BW > o["x"][0]
                    and gy < o["y"][1] + 1 and gy + BH > o["y"][0]):
                out.add((gx, gy))
    return out


for name, os_ in targets.items():
    for i, o in enumerate(os_):
        hit, path = bfs(grid, (bx, by), overlap_cells(o), BW, BH)
        tag = f"{name}{i}" if len(os_) > 1 else name
        print(f"\n{tag} at x{o['x'][0]} y{o['y'][0]}: "
              + (f"{len(path)} moves {path} landing x{hit[0]} y{hit[1]}" if path else "NO ROUTE"))

# --- route planner -----------------------------------------------------------
# The budget bar is 84 cells and every action eats 4, so a life is 21 actions.
# A yellow pickup refills it. Chain BFS across waypoints and check the budget holds.
BUDGET_ACTIONS = 21
ROUTE = sys.argv[3].split(",") if len(sys.argv) > 3 else []
if ROUTE:
    named = {}
    for name, os_ in targets.items():
        for i, o in enumerate(os_):
            named[f"{name}{i}" if len(os_) > 1 else name] = o

    pos, full, budget, log = (bx, by), [], BUDGET_ACTIONS, []
    for leg in ROUTE:
        o = named.get(leg)
        if o is None:
            raise SystemExit(f"unknown waypoint {leg!r}; have {sorted(named)}")
        hit, path = bfs(grid, pos, overlap_cells(o), BW, BH)
        if path is None:
            raise SystemExit(f"no route to {leg} from x{pos[0]} y{pos[1]}")
        budget -= len(path)
        log.append(f"  -> {leg}: {len(path)} moves, budget left {budget}"
                   + ("  REFILL to 21" if leg.startswith("yellow") else "")
                   + ("   *** OUT OF BUDGET ***" if budget < 0 else ""))
        if leg.startswith("yellow"):
            budget = BUDGET_ACTIONS
        full += path
        pos = hit
    print("\nroute plan:")
    print("\n".join(log))
    print(f"total {len(full)} moves: {','.join(map(str, full))}")
