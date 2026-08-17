"""ka59 z1 (2026-08-17) -- ARM 1: measure the mint.

The one untested arm from breadth-recon.md:5772-5775 -- "standing on a
chosen off-phase cell inside a box before clicking mints a marker at a
phase of your choosing, rather than at whatever the auto-route happened to
leave." Everything downstream (arms 2-4) rests on this being real.

Procedure, reusing the harness code from ka59_y11/y13/y15.py verbatim
(reach_l2, grid/piece_xy/dot_cells/marker_cells/phase, bfs_route, extra4):

  1. Reach L2. Walk (no click) to a DELIBERATELY CHOSEN cell: box2's
     interior. This is a free choice (not wherever an auto-route to some
     other goal happens to leave the piece) and its phase is known in
     advance (box2 = phase (1,1), the recon's own measured fact).
  2. From inside box2, click dot2 (untouched, elsewhere on the board).
     MEASURE: does the piece land exactly on dot2's PRE-click cell, and
     does a NEW extra4 marker appear exactly on the piece's OLD cell
     (the box2 cell chosen in step 1)?
  3. From wherever the piece now is, click that newly minted marker.
     MEASURE: does the piece land exactly on the marker's cell, and does
     its phase equal phase(marker's cell) -- the chosen phase from step 1?

Verdict WORKS only if both measurements confirm exactly; any mismatch is
REFUTED with the mismatch printed.

    ./.venv/Scripts/python.exe ka59_z1.py > results/ka59-z1.txt
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


def region(x0, x1, y0, y1):
    return lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1


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


def fail(msg, o):
    print(f"\n  ARM1 NOT EXECUTABLE: {msg}")
    print(f"  FINAL: levels_completed={o.levels_completed} state={o.state}")
    print(f"  final extra4 census: {extra4(o)}")
    sys.exit(0)


def step_log(e, o, v=None, click=None, tag=""):
    ACT_N[0] += 1
    o2 = e.step(A[6], data={"x": int(click[0]), "y": int(click[1])}) if click else e.step(A[v])
    if o2 is None or o2.state == GameState.GAME_OVER:
        print(f"  act#{ACT_N[0]:3d} {tag:20s} DIED")
        fail(f"death at action {ACT_N[0]} ({tag})", o if o2 is None else o2)
    p = piece_xy(grid(o2))
    print(f"  act#{ACT_N[0]:3d} {tag:24s} {'CLICK' + str(click) if click else 'v=' + str(v):14s} "
          f"piece={p} phase={phase(p)} extra4={extra4(o2)} "
          f"levels_completed={o2.levels_completed} state={o2.state}")
    sys.stdout.flush()
    if o2.levels_completed > 1 or o2.state == GameState.WIN:
        print("\n  *** LEVELS_COMPLETED > 1 -- WIN FIRED, STOPPING ALL ARMS ***")
        print(f"  final extra4 census: {extra4(o2)}")
        sys.exit(0)
    return e, o2


def commit(e, o, path, tag):
    for v in path:
        e, o = step_log(e, o, v=v, tag=tag)
    return e, o


cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: piece={piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))} "
      f"dot0={D0} dot1={D1} dot2={D2}")
dot2_pre = D2[0]

# --- step 1: walk (no click) to a DELIBERATELY CHOSEN cell -- box2 -----------
b = BOXES["box2"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]))
if p is None:
    fail("no route to box2 from spawn (expected free -- same phase-component)", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "1-walk-to-box2")
p_stand = piece_xy(grid(cur_o))
print(f"\nARM1 step1: chosen cell p_stand={p_stand} phase={phase(p_stand)} "
      f"(expected box2, phase (1,1))")

# --- step 2: click dot2 from p_stand -- measure the mint ---------------------
extra4_before = set(extra4(cur_o))
cur_e, cur_o = step_log(cur_e, cur_o, click=dot2_pre, tag="2-click-dot2-from-box2")
p_after = piece_xy(grid(cur_o))
extra4_after = set(extra4(cur_o))
new_markers = extra4_after - extra4_before

print(f"\nARM1 step2 MEASUREMENT:")
print(f"  piece landed at {p_after} (dot2's raw pixel group was {D2}, note: the group's "
      f"first SORTED pixel is not necessarily the dot's canonical landing cell -- "
      f"landed-in-group={p_after in D2}): informational, not the load-bearing claim")
print(f"  new extra4 marker(s): {sorted(new_markers)} (expected to contain p_stand={p_stand}): "
      f"{'MATCH' if p_stand in new_markers else 'MISMATCH'}")
mint_verdict = "WORKS" if p_stand in new_markers and len(new_markers) == 1 else "REFUTED"
print(f"  ARM1a (mint lands EXACTLY at the deliberately chosen old cell) verdict: {mint_verdict}")

if mint_verdict != "WORKS":
    fail("mint did not land where predicted -- arm1b skipped, downstream arms invalid", cur_o)

# --- step 3: click the newly minted marker -- verify delivery at its phase ---
cur_e, cur_o = step_log(cur_e, cur_o, click=p_stand, tag="3-click-minted-marker")
p_final = piece_xy(grid(cur_o))
print(f"\nARM1 step3 MEASUREMENT:")
print(f"  piece landed at {p_final} (expected minted marker's cell {p_stand}): "
      f"{'MATCH' if p_final == p_stand else 'MISMATCH'}")
print(f"  phase(p_final)={phase(p_final)} vs phase(p_stand)={phase(p_stand)}: "
      f"{'MATCH' if phase(p_final) == phase(p_stand) else 'MISMATCH'}")
deliver_verdict = "WORKS" if (p_final == p_stand and phase(p_final) == phase(p_stand)) else "REFUTED"
print(f"  ARM1b (delivery at chosen phase) verdict: {deliver_verdict}")

print(f"\n=== ARM1 FINAL: mint={mint_verdict} deliver={deliver_verdict} "
      f"overall={'WORKS' if mint_verdict == 'WORKS' and deliver_verdict == 'WORKS' else 'REFUTED'} ===")
print(f"levels_completed={cur_o.levels_completed} state={cur_o.state} total actions={ACT_N[0]}")
print(f"final extra4 census: {extra4(cur_o)}")
