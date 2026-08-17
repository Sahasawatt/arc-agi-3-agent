"""ka59 z3 (2026-08-17) -- diagnostic: z2 failed routing to dot0's approach
AFTER minting box2's marker via dot2 (piece stranded at dot2's own phase
(2,0)). Before concluding phase (2,0) cannot reach dot0/dot1 at all
(a reachability CLAIM), run the authoritative instrument per this game's
own rule (breadth-recon.md:5763): an exhaustive real BFS that targets
nothing and drains the queue, from the exact post-mint state.

    ./.venv/Scripts/python.exe ka59_z3.py > results/ka59-z3.txt
"""

import copy
import sys
from collections import deque

import numpy as np

import arc_agi
from arcengine.enums import GameState

import ferry


def grid(o):
    if o is None:
        return None
    f = np.array(o.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_xy(g):
    return ferry.find_cell(g, 0) if g is not None else None


def dot_cells(g):
    ys, xs = np.nonzero(g[:63] == 5)
    return sorted(zip(xs.tolist(), ys.tolist()))


def marker_cells(g):
    ys, xs = np.nonzero(g[:63] == 4)
    return sorted(zip(xs.tolist(), ys.tolist()))


def phase(p):
    return None if p is None else (p[0] % 3, p[1] % 3)


def region(x0, x1, y0, y1):
    return lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1


def reach_l2():
    env = arc_agi.Arcade().make("ka59")
    global A
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    drv = ferry.Ferry(None)
    n = 0
    while obs.levels_completed < 1 and n < 200:
        v = drv.act(grid(obs), obs.levels_completed)
        obs = (env.step(A[6], data={"x": int(v[1]), "y": int(v[2])})
               if isinstance(v, tuple) else env.step(A[int(v)]))
        n += 1
    assert obs.levels_completed == 1
    return copy.deepcopy(env), obs


def bfs_route(env, obs, is_target, avoid=(), action_values=(1, 2, 3, 4), max_nodes=1500):
    avoid = set(avoid)
    p0 = piece_xy(grid(obs))
    if p0 is None:
        return None, None, None
    if is_target(p0):
        return [], env, obs
    seen = {p0}
    q = deque([(p0, env, obs, [])])
    nodes = 0
    while q and nodes < max_nodes:
        pos, e, o, path = q.popleft()
        nodes += 1
        for v in action_values:
            e2 = copy.deepcopy(e)
            o2 = e2.step(A[int(v)])
            if o2 is None or o2.state == GameState.GAME_OVER:
                continue
            p2 = piece_xy(grid(o2))
            if p2 is None or p2 in seen or p2 in avoid:
                continue
            seen.add(p2)
            newpath = path + [v]
            if is_target(p2):
                return newpath, e2, o2
            q.append((p2, e2, o2, newpath))
    return None, None, None


ENV0, OBS0 = reach_l2()
FRAME4 = set(marker_cells(grid(OBS0)))


def extra4(o):
    return sorted(set(marker_cells(grid(o))) - FRAME4)


cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: dot0={D0} dot1={D1} dot2={D2}")

b = (51, 51, 53, 53)  # (x0, y0, x1, y1)
p, e2, o2 = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]))
if p is None:
    print("FATAL: no route to box2 from spawn -- unexpected, aborting")
    sys.exit(1)
cur_e, cur_o = e2, o2
box2_cell = piece_xy(grid(cur_o))
o2 = cur_e.step(A[6], data={"x": int(D2[0][0]), "y": int(D2[0][1])})
cur_o = o2
print(f"post-mint: piece={piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))} "
      f"extra4={extra4(cur_o)}")

print("\n=== exhaustive real BFS from post-mint state, cap 8000 ===")


def exhaustive(env, obs, max_nodes):
    p0 = piece_xy(grid(obs))
    seen = {p0}
    q = deque([(p0, env, obs)])
    nodes = 0
    while q and nodes < max_nodes:
        pos, e, o = q.popleft()
        nodes += 1
        for v in (1, 2, 3, 4):
            e2 = copy.deepcopy(e)
            o2 = e2.step(A[int(v)])
            if o2 is None or o2.state == GameState.GAME_OVER:
                continue
            p2 = piece_xy(grid(o2))
            if p2 is None or p2 in seen:
                continue
            seen.add(p2)
            q.append((p2, e2, o2))
    return seen, nodes


seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, 8000)
print(f"expanded {nodes} nodes, {len(seen)} distinct reachable positions "
      f"({'EXHAUSTED' if nodes < 8000 else 'CAP HIT, not exhausted'})")
xs = [c[0] for c in seen]
ys = [c[1] for c in seen]
print(f"reachable bbox: x=[{min(xs)},{max(xs)}] y=[{min(ys)},{max(ys)}]")
print(f"dot0 cells {D0} reachable: {[c in seen for c in D0]}")
print(f"dot1 cells {D1} reachable: {[c in seen for c in D1]}")
print(f"box2 cell {box2_cell} reachable: {box2_cell in seen}")
dot0_approach = [(x, y) for x in range(35, 40) for y in range(42, 47)]
print(f"any of dot0's approach region (35-39,42-46) reachable: "
      f"{any(c in seen for c in dot0_approach)}")
