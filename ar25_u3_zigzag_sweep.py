"""ar25 u3 (2026-08-17): exhaustive-in-region position sweep of S around L5's
colour-11 zigzag, testing levels_completed at EVERY visited cell plus one
A5-click-alias branch per cell.  Reuses ar25_u2.py's proven axis pairing
(A1=up dy-3, A2=down dy+3, A3=left dx-3, A4=right dx+3) and get_to_l5()
bootstrap.  New probe file -- does not import ar25_u2.py (that file is a
top-level script, importing it would replay its whole ARM1-3 run).

    PYTHONUTF8=1 ./.venv/Scripts/python.exe ar25_u3_zigzag_sweep.py > results/ar25-u3-sweep-run.txt
"""
import copy
import time
import sys
import json
import numpy as np

import arc_agi
from arcengine.enums import GameState
import mirror

T0 = time.time()
DEADLINE = T0 + 20 * 60          # hard stop for the sweep phases
WRITEUP_RESERVE = 3 * 60          # keep 3 min free for the results file
A = None


class Win(Exception):
    pass


def elapsed():
    return time.time() - T0


def time_left():
    return DEADLINE - time.time()


def step(env, v, data=None):
    global A
    if A is None:
        A = {a.value: a for a in env.action_space}
    return env.step(A[v], data=data) if data else env.step(A[v])


def grid(o):
    if o is None:
        return None
    f = np.array(o.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def s_bbox(g):
    if g is None:
        return None
    ys, xs = np.nonzero(g == 5)
    keep = (xs < 62) & (ys < 62)
    ys, xs = ys[keep], xs[keep]
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()), len(xs))


def get_center(o):
    bb = s_bbox(grid(o))
    if bb is None:
        return None
    return ((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2)


def check_win(o, ctx):
    if o is not None and (o.state == GameState.WIN or o.levels_completed >= 5):
        msg = f"{ctx} levels_completed={o.levels_completed} state={o.state}"
        print(f"*** WIN *** {msg}", flush=True)
        raise Win(msg)


AXIS_ACT = {("x", -1): 3, ("x", 1): 4, ("y", -1): 1, ("y", 1): 2}


def move_one(env, o, axis, sign, ctx):
    """One press along axis.  Returns (obs, moved, blocked). Raises Win."""
    v = AXIS_ACT[(axis, sign)]
    prev = s_bbox(grid(o))
    o2 = step(env, v)
    if o2 is None:
        return None, False, True
    check_win(o2, ctx)
    if o2.state == GameState.GAME_OVER:
        return o2, False, True
    now = s_bbox(grid(o2))
    moved = now is not None and prev is not None and now[:4] != prev[:4]
    return o2, moved, not moved


def nav_to(env, o, tx, ty, ctx, max_steps=60):
    for _ in range(max_steps):
        c = get_center(o)
        if c is None:
            print(f"  [{ctx}] center unreadable, abort nav", flush=True)
            return o
        cx, cy = c
        if cx == tx and cy == ty:
            return o
        if cx != tx:
            sign = 1 if tx > cx else -1
            o, moved, blocked = move_one(env, o, "x", sign, ctx)
        else:
            sign = 1 if ty > cy else -1
            o, moved, blocked = move_one(env, o, "y", sign, ctx)
        if o is None:
            return None
        if blocked:
            print(f"  [{ctx}] nav BLOCKED at {get_center(o)} heading ({tx},{ty})", flush=True)
            return o
    return o


VISITED = {}          # (cx,cy) -> bbox
BLOCKED_CELLS = []     # (target_x, target_y, axis, ctx)
A5CLICK_TESTS = 0


def visit_and_test(env, o, ctx):
    global A5CLICK_TESTS
    c = get_center(o)
    bb = s_bbox(grid(o))
    if c is not None:
        VISITED[c] = bb
    benv = copy.deepcopy(env)
    bo = step(benv, 5)
    A5CLICK_TESTS += 1
    check_win(bo, f"{ctx} A5CLICK@{c}")
    return o


def lattice_range(center, lo, hi, step=3):
    vals = set()
    v = center
    while v >= lo - step:
        if lo <= v <= hi:
            vals.add(v)
        v -= step
    v = center
    while v <= hi + step:
        if lo <= v <= hi:
            vals.add(v)
        v += step
    return sorted(vals)


def get_to_l5():
    env = arc_agi.Arcade().make("ar25")
    obs = env.reset()
    d = mirror.Mirror({a.value for a in env.action_space})
    acts = 0
    while obs.levels_completed < 4 and acts < 400:
        v = d.act(grid(obs), obs.levels_completed)
        if v is None:
            break
        obs = step(env, int(v)) if not isinstance(v, tuple) else \
            step(env, 6, {"x": int(v[1]), "y": int(v[2])})
        acts += 1
        if obs is None:
            break
        if obs.state == GameState.GAME_OVER:
            obs = env.reset()
    assert obs.levels_completed == 4, f"did not reach L5 ({obs.levels_completed})"
    return env, obs


print("=== reaching L5 root ===", flush=True)
BASE_ENV, BASE_OBS = get_to_l5()
print(f"at L5 entry, t={elapsed():.1f}s", flush=True)

ENTRY_BB = s_bbox(grid(BASE_OBS))
print(f"entry S bbox={ENTRY_BB}", flush=True)

# select S: A5 x2 (sel_phase n=2, n%3==2 -> arrows drive S). Assert bookkeeping.
sel_n = 0
o = BASE_OBS
env0 = copy.deepcopy(BASE_ENV)
o = step(env0, 5); sel_n += 1
o = step(env0, 5); sel_n += 1
assert sel_n % 3 == 2, f"sel_phase bookkeeping broken: n={sel_n}"
ROOT_SEL_ENV = copy.deepcopy(env0)
ROOT_SEL_OBS = o
ecx, ecy = get_center(ROOT_SEL_OBS)
print(f"S selected (sel_n={sel_n}, n%3={sel_n%3} -> S driven), center=({ecx},{ecy})", flush=True)

ZX0, ZX1, ZY0, ZY1 = 12, 38, 15, 41
MARKER1 = (37, 16)
MARKER2 = (13, 40)
half_w = (ENTRY_BB[1] - ENTRY_BB[0]) // 2
half_h = (ENTRY_BB[3] - ENTRY_BB[2]) // 2
cx_lo, cx_hi = ZX0 - half_w, ZX1 + half_w
cy_lo, cy_hi = ZY0 - half_h, ZY1 + half_h
print(f"overlap region: cx[{cx_lo},{cx_hi}] cy[{cy_lo},{cy_hi}] (half_w={half_w} half_h={half_h})",
      flush=True)

cx_list = lattice_range(ecx, cx_lo, cx_hi)
cy_list = lattice_range(ecy, cy_lo, cy_hi)
print(f"raster grid: {len(cx_list)} x-cols x {len(cy_list)} y-rows = "
      f"{len(cx_list)*len(cy_list)} cells", flush=True)
print(f"cx_list={cx_list}", flush=True)
print(f"cy_list={cy_list}", flush=True)

# marker exact-reachability check (lattice parity)
for name, (mx, my) in [("marker1", MARKER1), ("marker2", MARKER2)]:
    reach_x = (mx - ecx) % 3 == 0
    reach_y = (my - ecy) % 3 == 0
    print(f"{name}=({mx},{my}) exact-reachable: x={reach_x} y={reach_y}", flush=True)
for name, v in [("ZX0", ZX0), ("ZX1", ZX1)]:
    print(f"{name}={v} exact-x-reachable={(v-ecx)%3==0}", flush=True)
for name, v in [("ZY0", ZY0), ("ZY1", ZY1)]:
    print(f"{name}={v} exact-y-reachable={(v-ecy)%3==0}", flush=True)

CHUNK_ROWS = 5   # rows per life-chunk, budget guard (~5*13 + nav <127)


def raster_chunk(cy_rows, chunk_idx):
    ctx0 = f"chunk{chunk_idx}"
    env = copy.deepcopy(ROOT_SEL_ENV)
    o = ROOT_SEL_OBS
    o = nav_to(env, o, cx_list[0], cy_rows[0], f"{ctx0}-nav")
    if o is None:
        print(f"[{ctx0}] nav died, abort chunk", flush=True)
        return
    print(f"[{ctx0}] nav done center={get_center(o)} t={elapsed():.1f}s", flush=True)
    direction = 1
    for ri, cy in enumerate(cy_rows):
        c = get_center(o)
        if c is None:
            print(f"[{ctx0}] row{ri} center unreadable, abort", flush=True)
            return
        if c[1] != cy:
            o = nav_to(env, o, c[0], cy, f"{ctx0}-row{ri}-y")
            if o is None:
                return
        xs = cx_list if direction == 1 else list(reversed(cx_list))
        c = get_center(o)
        if c is not None and c[0] != xs[0]:
            o = nav_to(env, o, xs[0], cy, f"{ctx0}-row{ri}-x0")
            if o is None:
                return
        o = visit_and_test(env, o, f"{ctx0}-row{ri}@{xs[0]},{cy}")
        for tx in xs[1:]:
            c = get_center(o)
            if c is None:
                break
            if c[0] == tx:
                o = visit_and_test(env, o, f"{ctx0}-row{ri}@{tx},{cy}")
                continue
            sign = 1 if tx > c[0] else -1
            o, moved, blocked = move_one(env, o, "x", sign, f"{ctx0}-row{ri}")
            if o is None:
                print(f"[{ctx0}] row{ri} obs None mid-row", flush=True)
                return
            if o.state == GameState.GAME_OVER:
                print(f"[{ctx0}] row{ri} GAME_OVER mid-row, abort chunk", flush=True)
                return
            if blocked:
                BLOCKED_CELLS.append((tx, cy, "x", f"{ctx0}-row{ri}"))
                print(f"  [{ctx0}] row{ri} BLOCKED heading x->{tx} at {get_center(o)}", flush=True)
                break
            o = visit_and_test(env, o, f"{ctx0}-row{ri}@{get_center(o)}")
        if time_left() < WRITEUP_RESERVE:
            print(f"[{ctx0}] deadline approaching, stop mid-chunk after row{ri}", flush=True)
            return
        if ri < len(cy_rows) - 1:
            c = get_center(o)
            if c is None:
                return
            o = nav_to(env, o, c[0], cy_rows[ri + 1], f"{ctx0}-row{ri}->next-y", max_steps=5)
            if o is None:
                return
            direction *= -1
    print(f"[{ctx0}] done, visited-so-far={len(VISITED)} t={elapsed():.1f}s", flush=True)


print("\n=== PHASE 1: main raster sweep (overlap region) ===", flush=True)
raster_done = "INCOMPLETE"
chunks_run = 0
try:
    for ci in range(0, len(cy_list), CHUNK_ROWS):
        if time_left() < WRITEUP_RESERVE:
            print(f"deadline approaching before chunk {ci}, stopping raster", flush=True)
            break
        rows = cy_list[ci:ci + CHUNK_ROWS]
        raster_chunk(rows, ci)
        chunks_run += 1
    else:
        raster_done = "COMPLETE"
except Win:
    raise
print(f"phase 1 chunks_run={chunks_run}/{ -(-len(cy_list)//CHUNK_ROWS) } status={raster_done}",
      flush=True)

print("\n=== PHASE 2: axis-exact extension outside overlap region ===", flush=True)
FULL_X = lattice_range(ecx, 0, 61)
FULL_Y = lattice_range(ecy, 0, 61)
extra_y = sorted(set(FULL_Y) - set(cy_list))
extra_x = sorted(set(FULL_X) - set(cx_list))
below_y = [v for v in extra_y if v < cy_lo]
above_y = [v for v in extra_y if v > cy_hi]
below_x = [v for v in extra_x if v < cx_lo]
above_x = [v for v in extra_x if v > cx_hi]
print(f"extension ranges: y-below={below_y} y-above={above_y} "
      f"x-below={below_x} x-above={above_x}", flush=True)


def axis_walk(fixed_axis, fixed_val, sweep_vals, ctx0):
    if not sweep_vals or time_left() < WRITEUP_RESERVE:
        print(f"[{ctx0}] skipped (empty range or deadline) NOT RUN", flush=True)
        return "NOT_RUN"
    env = copy.deepcopy(ROOT_SEL_ENV)
    o = ROOT_SEL_OBS
    if fixed_axis == "x":
        o = nav_to(env, o, fixed_val, sweep_vals[0], f"{ctx0}-nav")
    else:
        o = nav_to(env, o, sweep_vals[0], fixed_val, f"{ctx0}-nav")
    if o is None:
        return "DIED"
    for v in sweep_vals:
        c = get_center(o)
        if c is None:
            break
        cur = c[1] if fixed_axis == "x" else c[0]
        if cur == v:
            o = visit_and_test(env, o, f"{ctx0}@{c}")
            continue
        axis = "y" if fixed_axis == "x" else "x"
        sign = 1 if v > cur else -1
        o, moved, blocked = move_one(env, o, axis, sign, ctx0)
        if o is None or o.state == GameState.GAME_OVER:
            return "DIED_MIDWAY"
        if blocked:
            BLOCKED_CELLS.append((fixed_val if fixed_axis == "x" else v,
                                   v if fixed_axis == "x" else fixed_val, axis, ctx0))
            print(f"  [{ctx0}] BLOCKED at {get_center(o)}", flush=True)
            break
        o = visit_and_test(env, o, f"{ctx0}@{get_center(o)}")
    return "DONE"


axis_status = {}
try:
    axis_status["marker1col-below"] = axis_walk("x", MARKER1[0], below_y, "m1col-below")
    axis_status["marker1col-above"] = axis_walk("x", MARKER1[0], above_y, "m1col-above")
    axis_status["marker2col-below"] = axis_walk("x", MARKER2[0], below_y, "m2col-below")
    axis_status["marker2col-above"] = axis_walk("x", MARKER2[0], above_y, "m2col-above")
    axis_status["marker1row-below"] = axis_walk("y", MARKER1[1], below_x, "m1row-below")
    axis_status["marker1row-above"] = axis_walk("y", MARKER1[1], above_x, "m1row-above")
    axis_status["marker2row-below"] = axis_walk("y", MARKER2[1], below_x, "m2row-below")
    axis_status["marker2row-above"] = axis_walk("y", MARKER2[1], above_x, "m2row-above")
except Win:
    raise
print(f"phase 2 status: {axis_status}", flush=True)

print("\n=== PHASE 3: band+10 variant (10 most-central overlap positions) ===", flush=True)
phase3_status = "NOT_RUN"
if time_left() > WRITEUP_RESERVE + 60:
    mid_cx = cx_list[len(cx_list) // 2 - 2: len(cx_list) // 2 + 3]
    mid_cy = cy_list[len(cy_list) // 2 - 1: len(cy_list) // 2 + 1]
    central = [(x, y) for y in mid_cy for x in mid_cx][:10]
    print(f"central positions to re-sweep: {central}", flush=True)
    env = copy.deepcopy(BASE_ENV)
    o = BASE_OBS
    band_n = 10
    try:
        for i in range(band_n):
            o = step(env, 2)  # A2 drives band at n%3==0
            if o is None or o.state == GameState.GAME_OVER:
                print("band+10 setup died", flush=True)
                o = None
                break
        if o is not None:
            o = step(env, 5); sel_n_p3 = 1
            o = step(env, 5); sel_n_p3 = 2
            assert sel_n_p3 % 3 == 2
            for (tx, ty) in central:
                o = nav_to(env, o, tx, ty, f"band10@{tx},{ty}")
                if o is None:
                    break
                o = visit_and_test(env, o, f"band10@{get_center(o)}")
            phase3_status = "DONE"
    except Win:
        raise
else:
    print("skipped: insufficient time budget remaining", flush=True)

print(f"\nphase3 status={phase3_status}", flush=True)
print(f"\n=== SWEEP COMPLETE (no win), t={elapsed():.1f}s ===", flush=True)
print(f"total visited={len(VISITED)} a5click_tests={A5CLICK_TESTS} "
      f"blocked_cells={len(BLOCKED_CELLS)}", flush=True)

RESULT = {
    "win": False,
    "verdict": "SWEPT_NO_WIN",
    "elapsed_s": elapsed(),
    "entry_bb": ENTRY_BB,
    "entry_center": [ecx, ecy],
    "overlap_region": {"cx": [cx_lo, cx_hi], "cy": [cy_lo, cy_hi]},
    "raster_grid": {"cx_list": cx_list, "cy_list": cy_list,
                     "cells": len(cx_list) * len(cy_list), "status": raster_done,
                     "chunks_run": chunks_run},
    "phase2_axis_status": axis_status,
    "phase3_status": phase3_status,
    "visited_count": len(VISITED),
    "a5click_tests": A5CLICK_TESTS,
    "blocked_cells": BLOCKED_CELLS,
    "visited_bbox_range": None,
}
xs_v = [c[0] for c in VISITED]
ys_v = [c[1] for c in VISITED]
if xs_v:
    RESULT["visited_bbox_range"] = [min(xs_v), max(xs_v), min(ys_v), max(ys_v)]

with open("results/ar25-u3-result.json", "w") as f:
    json.dump(RESULT, f, indent=1, default=str)
print("wrote results/ar25-u3-result.json", flush=True)
print("done", flush=True)
