"""ka59 t2 (2026-08-17) -- diagnostic for t1's CHECK A failure. Does box2
become unreachable BECAUSE of the box3 fill (dot1 click), or was it already
unreachable right after the compound sweep, before box3 is touched?

Reruns leg 1 (compound sweep) identically to ka59_t1.py, then runs the
exhaustive real BFS (this game's authoritative instrument) from THAT state
-- before any box3 click -- targeting box2's interior at the entry phase
(1,1) and at any phase. Positive control included.

    ./.venv/Scripts/python.exe ka59_t2.py > results/ka59-corrected-ticket-diag.txt
"""

import copy
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


def components(cells, adj=1):
    remaining = set(cells)
    comps = []
    while remaining:
        seed = remaining.pop()
        comp = {seed}
        frontier = [seed]
        while frontier:
            cx, cy = frontier.pop()
            near = [c for c in remaining if max(abs(c[0] - cx), abs(c[1] - cy)) <= adj]
            for n in near:
                remaining.discard(n)
                comp.add(n)
                frontier.append(n)
        comps.append(sorted(comp))
    return comps


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


BOX2 = (51, 51, 53, 53)


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
cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
entry_phase = phase(piece_xy(grid(cur_o)))
print(f"L2 entry: piece={piece_xy(grid(cur_o))} phase={entry_phase} dot0={D0} dot1={D1} dot2={D2}")

x1 = max(c[0] for c in D2); y0 = min(c[1] for c in D2); y1 = max(c[1] for c in D2)
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(x1 + 2, x1 + 7, y0 - 1, y1 + 1),
                     avoid=D0 + D1, max_nodes=1500)
assert p is not None, "approach route to dot2 failed (should match t1)"
for v in p:
    cur_o = cur_e.step(A[v])
for _ in range(4):
    before = set(dot_cells(grid(cur_o)))
    cur_o = cur_e.step(A[3])
    if set(dot_cells(grid(cur_o))) - before:
        break

remaining = [c for c in dot_cells(grid(cur_o)) if c not in D1]
comps = components(remaining)
print(f"post-sweep (pre-box3-fill): piece={piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))}")
print(f"dot cells (non-dot1): {remaining}  components={comps}")

print("\n=== DIAGNOSTIC: box2 reachability BEFORE box3 fill (right after compound sweep) ===")
seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
print(f"exhaustive BFS: expanded {nodes} nodes, {len(seen)} distinct reachable positions "
      f"({'EXHAUSTED' if nodes < 15000 else 'CAP HIT'})")
xs = [c[0] for c in seen]; ys = [c[1] for c in seen]
print(f"reachable bbox: x=[{min(xs)},{max(xs)}] y=[{min(ys)},{max(ys)}]")
box2_cells = [(x, y) for x in range(BOX2[0], BOX2[2] + 1) for y in range(BOX2[1], BOX2[3] + 1)]
box2_cells_entry_phase = [c for c in box2_cells if phase(c) == entry_phase]
reachable_box2 = [c for c in box2_cells if c in seen]
reachable_box2_entry_phase = [c for c in box2_cells_entry_phase if c in seen]
print(f"box2 cells: {box2_cells}")
print(f"box2 cells at entry phase {entry_phase}: {box2_cells_entry_phase}")
print(f"box2 cells reachable (any phase): {reachable_box2}")
print(f"box2 cells reachable at entry phase: {reachable_box2_entry_phase}")

# positive control
ctrl_e = copy.deepcopy(cur_e)
p0 = piece_xy(grid(cur_o))
ctrl_p = None
for v in (4, 2, 1, 3):
    ctrl_o = ctrl_e.step(A[v])
    if ctrl_o is not None and ctrl_o.state != GameState.GAME_OVER:
        cp = piece_xy(grid(ctrl_o))
        if cp is not None and cp != p0:
            ctrl_p = cp
            break
    ctrl_e = copy.deepcopy(cur_e)
ctrl_pass = ctrl_p is not None and ctrl_p in seen
print(f"positive control: one real press landed at {ctrl_p}, in reachable set: {ctrl_pass} "
      f"({'PASS' if ctrl_pass else 'FAIL -- INSTRUMENT BROKEN'})")

print(f"\nVERDICT: box2 reachable right after compound sweep (before box3 fill): "
      f"{'YES' if reachable_box2 else 'NO'} ({len(reachable_box2)} cells, "
      f"{len(reachable_box2_entry_phase)} at entry phase)")
