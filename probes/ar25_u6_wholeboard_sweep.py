"""ar25 u6 (2026-08-17): terminal closure sweep of L5's position x phase x
click family over the WHOLE-BOARD FRAME region outside the 169-cell raster
already covered by ar25_u5 (cx 7..43 step 3 x cy 10..46 step 3, all 21
band phases). Reuses ar25_u5's band-phase construction, axis pairing,
frame-equality clamp detection, save-point/checkpoint scheme, and the
boustrophedon walker (generalised to take an explicit cx_list/cy_list per
call instead of one fixed raster).

Remaining candidate region = 3 rectangular sub-grids framing the covered
raster:
  - RIGHT strip:  cx in {46,49,52,55,58}                x cy in {10..46 step3} (13)
  - TOP strip:    cy in {1,4,7}                          x cx in FULL cx lattice (18)
  - BOTTOM strip: cy in {49,52,55,58}                    x cx in FULL cx lattice (18)
FULL cx lattice = the raster's own 13 values (7..43) + the right strip's 5
(46..58), so the top/bottom strips also cover the corners above/below the
right strip. No cell is enumerated twice (cy ranges are disjoint by
construction: right=[10,46], top=[1,7], bottom=[49,58]).

    PYTHONUTF8=1 ./.venv/Scripts/python.exe ar25_u6_wholeboard_sweep.py > results/ar25-u6-run.txt
"""
import copy
import time
import json
import numpy as np

import arc_agi
from arcengine.enums import GameState
import mirror

T0 = time.time()
BUDGET_MIN = 35          # internal engine budget; leaves headroom in the 45-min stop point
DEADLINE = T0 + BUDGET_MIN * 60
WRITEUP_RESERVE = 5 * 60
CHECKPOINT_EVERY = 5      # phases
CHUNK_ROWS = 5
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


def check_win(o, ctx, actions):
    if o is not None and (o.state == GameState.WIN or o.levels_completed > 4):
        msg = f"{ctx} levels_completed={o.levels_completed} state={o.state}"
        print(f"*** WIN *** {msg}", flush=True)
        raise Win(json.dumps({"win_msg": msg, "actions_from_entry": list(actions)}))


def frames_equal(g1, g2):
    """Full-frame byte equality, HUD ticks (row/col 63) excluded -- the
    blocked-press law CLAUDE.md documents for this repo; robust where the
    band visually merges with the static colour-10 column."""
    if g1 is None or g2 is None or g1.shape != g2.shape:
        return False
    d = (g1 != g2)
    d[:, 63:] = False
    d[63:, :] = False
    return not d.any()


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


AXIS_ACT = {("x", -1): 3, ("x", 1): 4, ("y", -1): 1, ("y", 1): 2}


def move_one(env, o, axis, sign, ctx, actions_out):
    v = AXIS_ACT[(axis, sign)]
    prev = s_bbox(grid(o))
    o2 = step(env, v)
    actions_out.append(v)
    if o2 is None:
        return None, False, True
    check_win(o2, ctx, actions_out)
    if o2.state == GameState.GAME_OVER:
        return o2, False, True
    now = s_bbox(grid(o2))
    moved = now is not None and prev is not None and now[:4] != prev[:4]
    return o2, moved, not moved


def nav_to(env, o, tx, ty, ctx, actions_out, max_steps=60):
    for _ in range(max_steps):
        c = get_center(o)
        if c is None:
            return o
        cx, cy = c
        if cx == tx and cy == ty:
            return o
        if cx != tx:
            sign = 1 if tx > cx else -1
            o, moved, blocked = move_one(env, o, "x", sign, ctx, actions_out)
        else:
            sign = 1 if ty > cy else -1
            o, moved, blocked = move_one(env, o, "y", sign, ctx, actions_out)
        if o is None:
            return None
        if blocked:
            return o
    return o


# --------------------------------------------------------------- SETUP -----
print("=== reaching L5 root ===", flush=True)
ROOT_ENV, ROOT_OBS = get_to_l5()
ROOT = copy.deepcopy(ROOT_ENV)
print(f"L5 entry t={elapsed():.1f}s", flush=True)

ENTRY_ROW0 = 15  # measured fact (ar25-joint-sweep-20260817.md): entry sits at row 15
SAVE = {ENTRY_ROW0: {"env": copy.deepcopy(ROOT), "obs": ROOT_OBS, "presses": 0, "prefix": []}}


def build_direction(v_action, max_steps, sign, tag):
    env = copy.deepcopy(ROOT)
    prev_frame = grid(ROOT_OBS)
    prefix = []
    n = 0
    for i in range(max_steps):
        o2 = step(env, v_action)
        if o2 is None:
            print(f"  [{tag}] obs None at step {i}", flush=True)
            break
        check_win(o2, f"band-build {tag} step{i}", prefix + [v_action])
        if o2.state == GameState.GAME_OVER:
            print(f"  [{tag}] GAME_OVER at step {i}", flush=True)
            break
        new_frame = grid(o2)
        if frames_equal(prev_frame, new_frame):
            print(f"  [{tag}] CLAMPED at step {i} (n={n})", flush=True)
            break
        n += 1
        prefix = prefix + [v_action]
        prev_frame = new_frame
        pred_row0 = ENTRY_ROW0 + 3 * sign * n
        if pred_row0 not in SAVE:
            SAVE[pred_row0] = {"env": copy.deepcopy(env), "obs": o2, "presses": sign * n,
                                "prefix": list(prefix)}
    return n


try:
    n_down = build_direction(2, 30, +1, "down")
    n_up = build_direction(1, 30, -1, "up")
except Win as e:
    with open("results/ar25-u6-WIN-actions.json", "w") as f:
        f.write(str(e))
    print(f"WIN DURING BAND-PHASE CONSTRUCTION: {e}", flush=True)
    raise

phases_sorted = sorted(SAVE.items(), key=lambda kv: kv[0])
print(f"down={n_down} up={n_up} distinct phases={len(phases_sorted)}", flush=True)
assert len(phases_sorted) == 21, f"expected 21 phases, got {len(phases_sorted)}"

entry_idx = next(i for i, (rk, _) in enumerate(phases_sorted) if rk == ENTRY_ROW0)
ORDER = sorted(range(len(phases_sorted)), key=lambda i: abs(i - entry_idx))
print(f"entry_idx={entry_idx} run order (phase indices)={ORDER}", flush=True)

# --------------------------------------------------------- CANDIDATE SET ---
# u5's covered raster (NOT re-swept here):
CX_RASTER = [7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 43]
CY_RASTER = [10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 43, 46]
EXPECT_SPAWN = (49.0, 43.0)

CX_RIGHT = [46, 49, 52, 55, 58]           # right strip, task-specified
CY_TOP = [1, 4, 7]                        # top strip, task-specified
CY_BOT = [49, 52, 55, 58]                 # bottom strip, task-specified
CX_FULL = CX_RASTER + CX_RIGHT            # 18 values, "ALL cx" for top/bottom strips

GRIDS = [
    ("right", CX_RIGHT, CY_RASTER),   # 5 x 13 = 65
    ("top", CX_FULL, CY_TOP),         # 18 x 3 = 54
    ("bottom", CX_FULL, CY_BOT),      # 18 x 4 = 72
]
total_cells = sum(len(cx) * len(cy) for _, cx, cy in GRIDS)
print(f"candidate grids: {[(n, len(cx)*len(cy)) for n, cx, cy in GRIDS]} "
      f"total={total_cells} cells/phase x 21 phases = {total_cells*21} arms", flush=True)


def run_grid(pi, rowkey, root_sel_env, root_sel_obs, full_prefix, gname, cx_list, cy_list, tag0):
    grid_visited = {}
    grid_blocked = []
    grid_a5 = [0]

    def visit_and_test(env, o, ctx, walk_actions):
        c = get_center(o)
        bb = s_bbox(grid(o))
        if c is not None:
            grid_visited[c] = bb
        benv = copy.deepcopy(env)
        bo = step(benv, 5)
        grid_a5[0] += 1
        check_win(bo, f"{ctx} A5CLICK@{c}", full_prefix + walk_actions + [5])
        return o

    n_chunks = -(-len(cy_list) // CHUNK_ROWS)
    chunks_run = 0
    status = "COMPLETE"
    for ci in range(0, len(cy_list), CHUNK_ROWS):
        if time_left() < WRITEUP_RESERVE:
            print(f"[{tag0}] deadline approaching, stop before chunk {ci}", flush=True)
            status = "INCOMPLETE"
            break
        rows = cy_list[ci:ci + CHUNK_ROWS]
        walk_actions = []
        env = copy.deepcopy(root_sel_env)
        o = root_sel_obs
        o = nav_to(env, o, cx_list[0], rows[0], f"{tag0}-c{ci}-nav", walk_actions)
        if o is None:
            chunks_run += 1
            continue
        direction = 1
        for ri, cy in enumerate(rows):
            c = get_center(o)
            if c is None:
                break
            if c[1] != cy:
                o = nav_to(env, o, c[0], cy, f"{tag0}-c{ci}-r{ri}-y", walk_actions)
                if o is None:
                    break
            xs = cx_list if direction == 1 else list(reversed(cx_list))
            c = get_center(o)
            if c is not None and c[0] != xs[0]:
                o = nav_to(env, o, xs[0], cy, f"{tag0}-c{ci}-r{ri}-x0", walk_actions)
                if o is None:
                    break
            o = visit_and_test(env, o, f"{tag0}-c{ci}-r{ri}@{xs[0]},{cy}", walk_actions)
            for tx in xs[1:]:
                c = get_center(o)
                if c is None:
                    break
                if c[0] == tx:
                    o = visit_and_test(env, o, f"{tag0}-c{ci}-r{ri}@{tx},{cy}", walk_actions)
                    continue
                sign = 1 if tx > c[0] else -1
                o, moved, blocked = move_one(env, o, "x", sign, f"{tag0}-c{ci}-r{ri}", walk_actions)
                if o is None:
                    break
                if o.state == GameState.GAME_OVER:
                    break
                if blocked:
                    grid_blocked.append((tx, cy, "x"))
                    break
                o = visit_and_test(env, o, f"{tag0}-c{ci}-r{ri}@{get_center(o)}", walk_actions)
            if time_left() < WRITEUP_RESERVE:
                status = "INCOMPLETE"
                break
            if ri < len(rows) - 1:
                c = get_center(o)
                if c is None:
                    break
                o2 = nav_to(env, o, c[0], rows[ri + 1], f"{tag0}-c{ci}-r{ri}->next",
                            walk_actions, max_steps=5)
                if o2 is None:
                    break
                if get_center(o2) is not None and get_center(o2)[1] != rows[ri + 1]:
                    grid_blocked.append((c[0], rows[ri + 1], "y"))
                o = o2
                direction *= -1
        chunks_run += 1
        if status == "INCOMPLETE":
            break
    return {"grid": gname, "cx": cx_list, "cy": cy_list, "cells_total": len(cx_list) * len(cy_list),
            "status": status, "chunks_run": chunks_run, "chunks_total": n_chunks,
            "visited": len(grid_visited), "blocked": len(grid_blocked),
            "a5_branches": grid_a5[0], "blocked_cells": grid_blocked}


def run_phase(pi, rowkey, sp):
    tag0 = f"p{pi}(row={rowkey})"
    env0 = copy.deepcopy(sp["env"])
    o = sp["obs"]
    sel_actions = []
    sel_n = 0
    o = step(env0, 5); sel_actions.append(5); sel_n += 1
    check_win(o, f"{tag0} select1", sp["prefix"] + sel_actions)
    o = step(env0, 5); sel_actions.append(5); sel_n += 1
    check_win(o, f"{tag0} select2", sp["prefix"] + sel_actions)
    assert sel_n % 3 == 2, f"sel_n drift at {tag0}: {sel_n}"
    s_after = get_center(o)
    if s_after != EXPECT_SPAWN:
        print(f"  [{tag0}] WARNING spawn={s_after} != expected {EXPECT_SPAWN}", flush=True)
    root_sel_env = copy.deepcopy(env0)
    root_sel_obs = o
    full_prefix = sp["prefix"] + sel_actions

    subgrids = {}
    for gname, cx_list, cy_list in GRIDS:
        if time_left() < WRITEUP_RESERVE:
            subgrids[gname] = {"grid": gname, "status": "SKIPPED", "visited": 0, "blocked": 0,
                                "a5_branches": 0, "blocked_cells": [], "cells_total": len(cx_list) * len(cy_list)}
            continue
        subgrids[gname] = run_grid(pi, rowkey, root_sel_env, root_sel_obs, full_prefix,
                                    gname, cx_list, cy_list, f"{tag0}-{gname}")

    visited = sum(sg["visited"] for sg in subgrids.values())
    blocked = sum(sg["blocked"] for sg in subgrids.values())
    a5 = sum(sg["a5_branches"] for sg in subgrids.values())
    status = "COMPLETE" if all(sg["status"] == "COMPLETE" for sg in subgrids.values()) else "INCOMPLETE"
    return {"phase_idx": pi, "row0": rowkey, "band_presses": sp["presses"],
            "s_after_select": s_after, "status": status,
            "visited": visited, "blocked": blocked, "a5_branches": a5,
            "subgrids": subgrids}


print("\n=== PHASE SWEEP (nearest-entry-first) ===", flush=True)
CENSUS = {}
phases_completed_in_order = []
stopped_early_at = None
try:
    for oi, i in enumerate(ORDER):
        if time_left() < WRITEUP_RESERVE:
            print(f"deadline approaching, stopping before order-idx {oi} (phase {i})", flush=True)
            stopped_early_at = oi
            break
        rowkey, sp = phases_sorted[i]
        res = run_phase(i, rowkey, sp)
        CENSUS[i] = res
        phases_completed_in_order.append(i)
        print(f"phase {i} (row={rowkey}) -> visited={res['visited']} blocked={res['blocked']} "
              f"a5={res['a5_branches']} status={res['status']} t={elapsed():.1f}s", flush=True)
        if (oi + 1) % CHECKPOINT_EVERY == 0:
            with open("results/ar25-u6-checkpoint.json", "w") as f:
                json.dump({"census": CENSUS, "phases_done": phases_completed_in_order,
                           "order": ORDER, "elapsed_s": elapsed()}, f, indent=1, default=str)
            print(f"  checkpoint written after {oi + 1} phases", flush=True)
except Win as e:
    with open("results/ar25-u6-WIN-actions.json", "w") as f:
        f.write(str(e))
    print(f"WIN action sequence saved to results/ar25-u6-WIN-actions.json", flush=True)
    with open("results/ar25-u6-census.json", "w") as f:
        json.dump({"win": True, "census": CENSUS, "phases_done": phases_completed_in_order},
                   f, indent=1, default=str)
    raise

phases_missing = sorted(set(range(len(phases_sorted))) - set(phases_completed_in_order))
total_visited = sum(r["visited"] for r in CENSUS.values())
total_blocked = sum(r["blocked"] for r in CENSUS.values())
total_a5 = sum(r["a5_branches"] for r in CENSUS.values())
all_complete = all(r["status"] == "COMPLETE" for r in CENSUS.values()) and not phases_missing

verdict = "BOARD_CLOSED_NO_WIN" if all_complete else "INCOMPLETE"

print(f"\n=== SWEEP DONE t={elapsed():.1f}s === verdict={verdict} "
      f"phases_done={len(phases_completed_in_order)}/21 phases_missing={phases_missing} "
      f"total_visited={total_visited} total_blocked={total_blocked} total_a5={total_a5}",
      flush=True)

RESULT = {
    "win": False,
    "verdict": verdict,
    "elapsed_s": elapsed(),
    "n_down_presses": n_down,
    "n_up_presses": n_up,
    "phases_sorted_keys": [rk for rk, _ in phases_sorted],
    "entry_idx": entry_idx,
    "run_order": ORDER,
    "phases_done": phases_completed_in_order,
    "phases_missing": phases_missing,
    "candidate_grids": {gname: {"cx": cx, "cy": cy, "cells": len(cx) * len(cy)}
                         for gname, cx, cy in GRIDS},
    "total_candidate_cells_per_phase": total_cells,
    "total_visited": total_visited,
    "total_blocked": total_blocked,
    "total_a5_branches": total_a5,
    "census": CENSUS,
}
with open("results/ar25-u6-census.json", "w") as f:
    json.dump(RESULT, f, indent=1, default=str)
print("wrote results/ar25-u6-census.json", flush=True)
print("done", flush=True)
