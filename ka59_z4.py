"""ka59 z4 (2026-08-17) -- probe: can dot2 be KICKED to relocate its
delivery phase away from the isolated (2,0) pocket z3 just measured?
Gap flagged in notes/next-session-prompt.md:374: "dot2's kick geometry has
never been cleanly measured." Try approaching from several directions and
pressing repeatedly, same technique as dot0/dot1's kicks in ka59_y11.py,
on independent deepcopy branches from ONE real reach_l2() (no real actions
wasted on failed directions -- each branch is exploratory).

    ./.venv/Scripts/python.exe ka59_z4.py > results/ka59-z4.txt
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
dots0 = dot_cells(grid(OBS0))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: dot0={D0} dot1={D1} dot2={D2}")

# approach dot2 from 4 different offset regions (N/S/E/W of it) so pressing
# toward it kicks it in a KNOWN direction, mirroring dot0/dot1's technique.
APPROACHES = {
    "from-east-press-west": (region(46, 50, 46, 50), 3),
    "from-west-press-east": (region(38, 42, 46, 50), 4),
    "from-north-press-south": (region(43, 47, 40, 43), 2),
    "from-south-press-north": (region(43, 47, 51, 55), 1),
}

for tag, (approach_region, press_v) in APPROACHES.items():
    e0 = copy.deepcopy(ENV0)
    p, e1, o1 = bfs_route(e0, OBS0, approach_region, avoid=D0 + D1)
    if p is None:
        print(f"{tag}: NO ROUTE to approach cell")
        continue
    e, o = e1, o1
    before = set(dot_cells(grid(o)))
    kicked = False
    for i in range(8):
        o2 = e.step(A[press_v])
        if o2 is None or o2.state == GameState.GAME_OVER:
            print(f"{tag}: DIED during kick presses")
            kicked = None
            break
        o = o2
        now = set(dot_cells(grid(o)))
        if now - before:
            kicked = True
            break
    if kicked is None:
        continue
    if not kicked:
        print(f"{tag}: approached ok, pressed 8x v={press_v}, dot2 never moved "
              f"(still at {sorted(now)})")
        continue
    new_d2 = sorted([c for c in dot_cells(grid(o)) if c not in D0 and c not in D1])
    piece_after = piece_xy(grid(o))
    print(f"{tag}: dot2 kicked from {D2} -> {new_d2}, "
          f"piece now at {piece_after} phase={phase(piece_after)}, "
          f"dot2 landing phase(s)={[phase(c) for c in new_d2]}")
