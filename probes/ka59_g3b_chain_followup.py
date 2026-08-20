"""ka59 g3b (2026-08-17) -- follow-up to g3's crossing table: g3's generic
chain-north probe (single-dot protection) found 0 rounds for all three
dots -- safe_route refused every approach because it fully protects the
OTHER two dots' 8-neighbourhoods, and y11's proven dot0-chain-north recipe
only works AFTER dot1 has ALSO been kicked west (y11 order: A kick dot0
west, B kick dot1 west, ... D chain-kick dot0 north). This script
reproduces that exact precondition (both dot0 and dot1 pre-kicked west)
before attempting dot0's north chain, to tell apart "blocked by my own
over-protection" from "a genuine wall" -- reusing safe_route/safe_kick
harness verbatim from ka59_g2_safe_route.py / ka59_g3_crossing_table.py.

    ./.venv/Scripts/python.exe ka59_g3b_chain_followup.py > results/ka59-g3b-run.txt
"""

import copy
import sys
import time
from collections import deque

import numpy as np

import arc_agi
from arcengine.enums import GameState

import ferry


class RowFailed(Exception):
    pass


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
BAND_Y = (24, 29)
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


def nearest_component(comps, ref_cells):
    if not comps:
        return []
    rx = sum(c[0] for c in ref_cells) / len(ref_cells)
    ry = sum(c[1] for c in ref_cells) / len(ref_cells)

    def dist(comp):
        cx = sum(c[0] for c in comp) / len(comp)
        cy = sum(c[1] for c in comp) / len(comp)
        return (cx - rx) ** 2 + (cy - ry) ** 2

    return min(comps, key=dist)


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


def guarded_step(e, o, tag, v=None, click=None, target_cells=()):
    before = live_objects(o)
    ACT_N[0] += 1
    o2 = (e.step(A[6], data={"x": int(click[0]), "y": int(click[1])}) if click
          else e.step(A[v]))
    if o2 is None or o2.state == GameState.GAME_OVER:
        raise RowFailed(f"death at action {ACT_N[0]} ({tag})")
    p = piece_xy(grid(o2))
    if click is not None and p is None:
        dots_before = set(dot_cells(grid(o2)))
        trials = []
        for sv in (1, 4, 3, 2):
            e3 = copy.deepcopy(e)
            o3 = e3.step(A[sv])
            if o3 is None or o3.state == GameState.GAME_OVER:
                continue
            p3 = piece_xy(grid(o3))
            resolved = p3 is not None
            dots_after = set(dot_cells(grid(o3)))
            disturbed = dots_after != dots_before
            trials.append((sv, e3, o3, resolved, dots_after, disturbed))
        clean = [t for t in trials if t[3] and not t[5]]
        if clean:
            chosen = clean[0]
        else:
            resolved_only = [t for t in trials if t[3]]
            if not resolved_only:
                raise RowFailed(f"piece_xy stayed None after click + all settle attempts ({tag})")
            chosen = min(resolved_only, key=lambda t: len(t[4].symmetric_difference(dots_before)))
        sv, e3, o3, resolved, dots_after, disturbed = chosen
        ACT_N[0] += 1
        e, o2 = e3, o3
    after = live_objects(o2)
    vanished = before - after
    bad = vanished - set(target_cells)
    if bad:
        raise RowFailed(f"SAFE-ROUTE VIOLATION in '{tag}': moved {sorted(bad)} "
                         f"not in declared target {sorted(target_cells)}")
    return e, o2


def safe_walk(e, o, path, tag, target_cells=()):
    for v in path:
        e, o = guarded_step(e, o, tag, v=v, target_cells=target_cells)
    return e, o


def safe_kick(e, o, v, tag, target_cells_now, max_presses=8):
    moved = False
    for i in range(max_presses):
        e, o = guarded_step(e, o, f"{tag}-p{i + 1}", v=v, target_cells=target_cells_now)
        if not (set(target_cells_now) & live_objects(o)):
            moved = True
            break
    return e, o, moved


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


def census(cur_e, cur_o):
    p0 = piece_xy(grid(cur_o))
    seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
    exhausted = nodes < 15000
    ctrl_e = copy.deepcopy(cur_e)
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
    return seen, nodes, exhausted, ctrl_pass


def kick_west(cur_e, cur_o, dot_now, protect_others, extra_target=(), tag="kick-west"):
    xs = [c[0] for c in dot_now]
    ys = [c[1] for c in dot_now]
    x1, y0, y1 = max(xs), min(ys), max(ys)
    p = None
    for lo, hi in ((y0, y1), (y0 - 1, y1 + 1), (y0, y0), (y1, y1)):
        tgt = region(x1 + 2, x1 + 12, lo, hi)
        p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, tgt,
                              protect=list(protect_others) + list(dot_now), max_nodes=3000)
        if p is not None:
            break
    if p is None:
        raise RowFailed(f"{tag}: no safe approach route (west)")
    cur_e, cur_o = safe_walk(cur_e, cur_o, p, f"{tag}-approach", target_cells=())
    targets = list(dot_now) + list(extra_target)
    cur_e, cur_o, moved = safe_kick(cur_e, cur_o, 3, f"{tag}-kick", targets, max_presses=8)
    if not moved:
        raise RowFailed(f"{tag}: kick west did not move the dot")
    return cur_e, cur_o


def kick_north_once(cur_e, cur_o, dot_now, protect_others, tag="kick-north"):
    tx, ty = dot_now[0]
    tgt = region(tx - 1, tx + 4, ty + 3, ty + 8)
    p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, tgt,
                          protect=list(protect_others) + list(dot_now), max_nodes=2500)
    if p is None:
        return cur_e, cur_o, False
    cur_e, cur_o = safe_walk(cur_e, cur_o, p, f"{tag}-approach", target_cells=())
    cur_e, cur_o, moved = safe_kick(cur_e, cur_o, 1, f"{tag}-kick", dot_now, max_presses=8)
    return cur_e, cur_o, moved


t0 = time.time()
cur_e, cur_o = copy.deepcopy(ENV0), OBS0
d = dot_cells(grid(cur_o))
D0 = [c for c in d if 33 <= c[0] <= 35]
D1 = [c for c in d if 40 <= c[0] <= 43]
D2 = [c for c in d if c[0] >= 44]
print(f"entry: D0={D0} D1={D1} D2={D2}")

print("\n--- A: kick dot0 west ---")
cur_e, cur_o = kick_west(cur_e, cur_o, D0, D1 + D2, tag="A-dot0-west")
live = [c for c in dot_cells(grid(cur_o)) if c not in D1 and c not in D2]
d0_now = nearest_component(components(live, adj=1), D0)
print(f"dot0 now at {d0_now}")

print("\n--- B: kick dot1 west (clears the corridor y11 needs) ---")
cur_e, cur_o = kick_west(cur_e, cur_o, D1, d0_now + D2, tag="B-dot1-west")
live = [c for c in dot_cells(grid(cur_o)) if c not in d0_now and c not in D2]
d1_now = nearest_component(components(live, adj=1), D1)
print(f"dot1 now at {d1_now}")

print("\n--- D: chain-kick dot0 north (protect only dot1's NEW position + dot2) ---")
cur = list(d0_now)
completed = 0
for i in range(4):
    prior = cur
    cur_e, cur_o, moved = kick_north_once(cur_e, cur_o, cur, d1_now + D2, tag=f"D-chain-r{i}")
    print(f"round {i}: moved={moved}")
    if not moved:
        break
    completed += 1
    live = [c for c in dot_cells(grid(cur_o)) if c not in d1_now and c not in D2]
    comps = components(live, adj=1)
    cur = nearest_component(comps, prior) if comps else prior
    print(f"  dot0 now at {cur}")

print(f"\nchain completed {completed} rounds, dot0 final position {cur}")

if completed > 0:
    print("\n--- click dot0 from wherever piece is, measure landing + census ---")
    cur_e, cur_o = guarded_step(cur_e, cur_o, "CLICK-dot0-chained", click=cur[0], target_cells=cur)
    landing = piece_xy(grid(cur_o))
    ph = phase(landing)
    print(f"landing={landing} phase={ph} actions={ACT_N[0]}")
    seen, nodes, exhausted, ctrl_pass = census(cur_e, cur_o)
    print(f"census: nodes={nodes} size={len(seen)} exhausted={exhausted} ctrl={ctrl_pass}")
    for bn in ("box0", "box1", "box3", "box2"):
        b = BOXES[bn]
        cells = [(x, y) for x in range(b[0], b[2] + 1) for y in range(b[1], b[3] + 1)]
        cells_ph = [c for c in cells if phase(c) == ph]
        reach_any = [c for c in cells if c in seen]
        reach_ph = [c for c in cells_ph if c in seen]
        print(f"  {bn}: reach_any_phase={reach_any} reach_at_phase{ph}={reach_ph}")
else:
    print("\nNo chain round completed even with dot1 pre-cleared -- genuine wall, "
          "not a protect-list artifact. No click/census attempted for this arm.")

print(f"\nwall time: {time.time() - t0:.1f}s total actions: {ACT_N[0]}")
