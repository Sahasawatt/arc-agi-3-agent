"""ka59 w3 (2026-08-17) -- diagnostic: does minting via dot0 straight from
its ENTRY position (no pre-kick at all) land the piece somewhere that
connects to box1 by a plain walk? If yes, the whole dot1-crossing problem
(w2's finding) is moot -- no chain-kick needed.

    ./.venv/Scripts/python.exe ka59_w3.py > results/ka59-w3.txt
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


def phase(p):
    return None if p is None else (p[0] % 3, p[1] % 3)


def region(x0, x1, y0, y1):
    return lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1


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


def exhaustive(env, obs, max_nodes=15000):
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


BOXES = {"box1": (9, 9, 11, 14), "box3": (54, 39, 59, 41),
         "box0": (6, 42, 11, 47), "box2": (51, 51, 53, 53)}

ENV0, OBS0 = reach_l2()
cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"entry piece={piece_xy(grid(cur_o))} dot0={D0} dot1={D1} dot2={D2}")

b = BOXES["box2"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]))
for v in p:
    cur_o = cur_e.step(A[v])
box2_cell = piece_xy(grid(cur_o))
print(f"standing in box2 at {box2_cell} phase={phase(box2_cell)}")

# MINT via raw dot0 (unkicked)
cur_o = cur_e.step(A[6], data={"x": int(D0[0][0]), "y": int(D0[0][1])})
p_after = piece_xy(grid(cur_o))
print(f"after MINT-click-dot0(raw): piece={p_after} phase={phase(p_after)} (expected dot0's own cell)")

print("\n=== exhaustive BFS from this state -- is box1 reachable? ===")
seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
print(f"expanded {nodes} nodes, {len(seen)} distinct reachable positions "
      f"({'EXHAUSTED' if nodes < 15000 else 'CAP HIT'})")
xs = [c[0] for c in seen]
ys = [c[1] for c in seen]
print(f"reachable bbox: x=[{min(xs)},{max(xs)}] y=[{min(ys)},{max(ys)}]")
b1 = BOXES["box1"]
box1_cells = [(x, y) for x in range(b1[0], b1[2] + 1) for y in range(b1[1], b1[3] + 1)]
reachable_box1 = [c for c in box1_cells if c in seen]
print(f"box1 interior cells reachable: {reachable_box1}")
print(f"dot0's OTHER cell {D0[1] if len(D0)>1 else None} reachable: "
      f"{(D0[1] in seen) if len(D0)>1 else 'n/a'}")
