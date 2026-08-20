"""ka59 g3g (2026-08-17) -- quick probe, not a full drive: does minting via
dot1 (instead of dot2) avoid the stranding g3d measured for dot2?
Phase1's crossing table already showed dot1@entry lands at (42,34) phase
(0,1) with box3@phase reachable -- this probe checks whether dot0's
approach region (needed for the box0/box1 half of the line) is ALSO
reachable from that same landing, which g3d never tested (it only tested
dot2 as the mint object). One-shot census, no full drive.

    ./.venv/Scripts/python.exe ka59_g3g_probe.py > results/ka59-g3g-run.txt
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


def in_box(c, bb):
    return bb[0] <= c[0] <= bb[2] and bb[1] <= c[1] <= bb[3]


BOXES = {"box1": (9, 9, 11, 14), "box3": (54, 39, 59, 41),
         "box0": (6, 42, 11, 47), "box2": (51, 51, 53, 53)}
ACT_N = [0]


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


ENV0, OBS0 = reach_l2()
FRAME4 = set(marker_cells(grid(OBS0)))


def extra4(o):
    return sorted(set(marker_cells(grid(o))) - FRAME4)


def live_objects(o):
    return set(dot_cells(grid(o))) | set(extra4(o))


def dot_footprint(cells):
    fp = set()
    for (cx, cy) in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                fp.add((cx + dx, cy + dy))
    return fp


def safe_route(env, obs, is_target, protect, avoid=(), action_values=(1, 2, 3, 4), max_nodes=2500):
    forbidden = dot_footprint(protect)
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
            tgt = is_target(p2)
            if p2 in forbidden and not tgt:
                continue
            seen.add(p2)
            newpath = path + [v]
            if tgt:
                return newpath, e2, o2
            q.append((p2, e2, o2, newpath))
    return None, None, None


def step_raw(e, o, v=None, click=None):
    ACT_N[0] += 1
    o2 = e.step(A[6], data={"x": int(click[0]), "y": int(click[1])}) if click else e.step(A[v])
    return e, o2


def walk(e, o, path):
    for v in path:
        e, o = step_raw(e, o, v=v)
    return e, o


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


cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"entry: D0={D0} D1={D1} D2={D2}")

b2 = BOXES["box2"]
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(b2[0], b2[2], b2[1], b2[3]),
                      protect=D0 + D1 + D2, max_nodes=2000)
if p is None:
    print("FAIL: no route to box2")
    sys.exit(0)
cur_e, cur_o = walk(cur_e, cur_o, p)
print(f"at box2: piece={piece_xy(grid(cur_o))}")

# MINT via dot1 (not dot2).
cur_e, cur_o = step_raw(cur_e, cur_o, click=D1[0])
piece_after_mint = piece_xy(grid(cur_o))
mint_cell = next((c for c in extra4(cur_o) if in_box(c, b2)), None)
print(f"after mint-via-dot1: piece={piece_after_mint} phase={phase(piece_after_mint)} "
      f"mint_cell={mint_cell} extra4={extra4(cur_o)} state={cur_o.state}")
if piece_after_mint is None or cur_o.state == GameState.GAME_OVER:
    print("FAIL: mint click died or piece_xy None (no settle logic in this quick probe)")
    sys.exit(0)

seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
exhausted = nodes < 15000
print(f"\ncensus from mint-via-dot1 landing: {nodes} nodes {len(seen)} positions "
      f"({'EXHAUSTED' if exhausted else 'CAP HIT'})")

d0_appr_region = region(35, 39, 42, 46)
d0_appr_cells = [(x, y) for x in range(35, 40) for y in range(42, 47)]
print(f"dot0-approach-region cells reachable: {[c for c in d0_appr_cells if c in seen]}")

for bn in ("box0", "box1", "box3"):
    bb = BOXES[bn]
    cells = [(x, y) for x in range(bb[0], bb[2] + 1) for y in range(bb[1], bb[3] + 1)]
    print(f"{bn} interior reachable (any phase): {[c for c in cells if c in seen]}")

print(f"\ntotal actions: {ACT_N[0]}")
