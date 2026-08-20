"""ka59 z2 (2026-08-17) -- ARM 2/3 combined: 3 boxes filled + piece inside box2.

Arm 1 (ka59_z1.py) proved: standing on a chosen cell before clicking mints a
NEW colour-4 marker there, and later clicking that marker delivers the piece
to that exact cell (and its phase). This arm spends that fact directly on
the never-achieved config from breadth-recon.md:5658-5660 (three boxes
filled AND the piece inside box2 at the end).

Why "matched pairing" (goal 2) and "any three boxes" (goal 3) are run as
ONE drive, not two: y9 (breadth-recon.md:5531-5545) already proved markers
carry NO identity tag -- "a recycled marker delivers the phase of the CELL
IT CURRENTLY OCCUPIES, never its origin dot's." So "dot0's marker
specifically in box1" is not a pixel-distinguishable game state from "any
marker in box1"; the only observable difference between goal 2 and goal 3
is which dot the DRIVER (this script) chose to route through which box,
which this script's own log records. Both goals collapse onto the same
target board state.

The route, and why it should close the wall y2/y11 hit:
  0. Walk (free, same phase-component as spawn) into box2. Click dot2 from
     there. This MINTS a persistent, recyclable marker inside box2 itself
     (phase (1,1)) -- a "return ticket" that is NOT one of the three dots
     needed for box1/box3/box0, so spending it later does not undo any of
     those three fills. (This is exactly arm 1's mechanism, aimed at box2
     specifically because box2's own phase is spawn's own phase, so it
     costs nothing extra to reach.)
  A-F. y11's already-proven line verbatim: kick dot0 west, kick dot1 west,
     fill box3 with dot1 (piece crosses), chain-kick dot0 north to phase
     (1,2), fill box0 with dot0 (piece crosses to phase (1,2)), walk into
     box1 (phase match).
  G. From inside box1, click box2's OWN recycled marker (not box3's, unlike
     y11) -- this fills box1 (box2's marker relocates to box1's interior,
     the piece's old cell) AND swaps the piece to the marker's OLD
     position, which IS box2's own interior cell. No further walk needed.

Predicted final state: box3 filled (dot1), box0 filled (dot0), box1 filled
(box2's recycled marker), piece standing inside box2 -- exactly the
never-achieved config, using zero waste (dot2 is not "spent" on a fill,
it is spent as the mint trigger, which is the whole point of arm 1).

    ./.venv/Scripts/python.exe ka59_z2.py > results/ka59-z2.txt
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
    print(f"\n  LINE NOT EXECUTABLE: {msg}")
    print(f"  FINAL: levels_completed={o.levels_completed} state={o.state}")
    print(f"  final extra4 census: {extra4(o)}")
    sys.exit(0)


def step_log(e, o, v=None, click=None, tag=""):
    ACT_N[0] += 1
    o2 = e.step(A[6], data={"x": int(click[0]), "y": int(click[1])}) if click else e.step(A[v])
    if o2 is None or o2.state == GameState.GAME_OVER:
        print(f"  act#{ACT_N[0]:3d} {tag:26s} DIED")
        fail(f"death at action {ACT_N[0]} ({tag})", o if o2 is None else o2)
    p = piece_xy(grid(o2))
    print(f"  act#{ACT_N[0]:3d} {tag:26s} {'CLICK' + str(click) if click else 'v=' + str(v):14s} "
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
print(f"L2 entry: piece={piece_xy(grid(cur_o))} dot0={D0} dot1={D1} dot2={D2}")

# --- 0. walk to box2, click dot2 -> mint a persistent marker IN box2 ---------
b = BOXES["box2"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]))
if p is None:
    fail("no route to box2 from spawn", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "0-walk-to-box2")
box2_cell = piece_xy(grid(cur_o))
print(f"\n0: standing at box2 cell {box2_cell} phase={phase(box2_cell)} -- minting here")
cur_e, cur_o = step_log(cur_e, cur_o, click=D2[0], tag="0-MINT-box2-via-dot2")
box2_marker = box2_cell  # the mint lands exactly at the piece's old cell (arm1-proven)
if box2_marker not in extra4(cur_o):
    fail(f"box2 mint did not land at {box2_marker} as arm1 predicted -- extra4={extra4(cur_o)}", cur_o)
print(f"   confirmed: box2 marker sits at {box2_marker}")

# --- A. kick dot0 west --------------------------------------------------------
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(35, 39, 42, 46), avoid=D1 + D2)
if p is None:
    fail("no route to dot0's approach", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "A-approach-dot0")
for _ in range(8):
    before = set(dot_cells(grid(cur_o)))
    cur_e, cur_o = step_log(cur_e, cur_o, v=3, tag="A-kick-dot0")
    if set(dot_cells(grid(cur_o))) - before:
        break

# --- B. kick dot1 west --------------------------------------------------------
d0_now = [c for c in dot_cells(grid(cur_o)) if c[1] > 40]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(48, 52, 33, 35), avoid=d0_now + D2)
if p is None:
    fail("no route to dot1's approach", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "B-approach-dot1")
for _ in range(8):
    before = set(dot_cells(grid(cur_o)))
    cur_e, cur_o = step_log(cur_e, cur_o, v=3, tag="B-kick-dot1")
    if set(dot_cells(grid(cur_o))) - before:
        break

# --- C. box3, click dot1 ------------------------------------------------------
d0_now = [c for c in dot_cells(grid(cur_o)) if c[1] > 40]
b = BOXES["box3"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]), avoid=d0_now + D2)
if p is None:
    fail("no route to box3", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "C-to-box3")
d1_now = [c for c in dot_cells(grid(cur_o)) if c not in d0_now and c not in D2]
tx, ty = d1_now[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="C-FILL-box3-dot1")

# --- D. chain-kick dot0 north --------------------------------------------------
d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D2]
tx, ty = d0_now[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(tx - 1, tx + 4, ty + 3, ty + 8),
                     avoid=d0_now, max_nodes=1500)
if p is None:
    fail("no approach to dot0's crossed position for the chain kick", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "D-approach-chain")
for _ in range(8):
    before = set(dot_cells(grid(cur_o)))
    cur_e, cur_o = step_log(cur_e, cur_o, v=1, tag="D-chain-kick-dot0")
    if set(dot_cells(grid(cur_o))) - before:
        break

# --- E. box0, click dot0 ------------------------------------------------------
b = BOXES["box0"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]), max_nodes=1500)
if p is None:
    fail("no route to box0", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "E-to-box0")
d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D2]
tx, ty = d0_now[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="E-FILL-box0-dot0")

# --- F. walk into box1 --------------------------------------------------------
b = BOXES["box1"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]), max_nodes=3000)
if p is None:
    pp = piece_xy(grid(cur_o))
    fail(f"no route to box1 from {pp} phase={phase(pp)}", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "F-to-box1")

# --- G. click box2's recycled marker from inside box1 -------------------------
if box2_marker not in extra4(cur_o):
    fail(f"box2's marker is gone before step G -- extra4={extra4(cur_o)}", cur_o)
cur_e, cur_o = step_log(cur_e, cur_o, click=box2_marker, tag="G-FILL-box1-via-box2-marker")

# --- final census --------------------------------------------------------------
final_piece = piece_xy(grid(cur_o))
final_extra4 = extra4(cur_o)
print(f"\nFINAL: levels_completed={cur_o.levels_completed} state={cur_o.state}")
print(f"final piece: {final_piece} phase={phase(final_piece)} (predicted: inside box2, {box2_cell})")
print(f"final extra4 census: {final_extra4}")
b1, b3, b0, b2 = BOXES["box1"], BOXES["box3"], BOXES["box0"], BOXES["box2"]


def in_box(c, bb):
    return bb[0] <= c[0] <= bb[2] and bb[1] <= c[1] <= bb[3]


filled = {
    "box1": any(in_box(c, b1) for c in final_extra4),
    "box3": any(in_box(c, b3) for c in final_extra4),
    "box0": any(in_box(c, b0) for c in final_extra4),
    "box2": any(in_box(c, b2) for c in final_extra4),
}
piece_in_box2 = in_box(final_piece, b2) if final_piece else False
print(f"boxes filled: {filled}")
print(f"piece inside box2: {piece_in_box2}")
n_filled_non_box2 = sum(1 for k in ("box1", "box3", "box0") if filled[k])
print(f"\n=== VERDICT: {n_filled_non_box2} of {{box1,box3,box0}} filled, "
      f"piece-in-box2={piece_in_box2}, levels_completed={cur_o.levels_completed} ===")
print(f"total actions: {ACT_N[0]}")
