"""ka59 g3 (2026-08-17) -- PHASE 1: the CROSSING TABLE survey.

Mission (per results/breadth-recon.md's last ka59 section -- the "MODEL
CORRECTION" entry -- and results/ka59-safe-route-20260817.md): a dot's
delivery phase is POSITION-DEPENDENT, drawn from its footprint's phase set.
For every achievable dot position (entry + measured kick/chain landings,
for all three dots), on a FRESH deepcopy: put the piece at the level-2
entry spawn, execute the kicks needed to reach that position (via
safe_route/safe_kick, reused verbatim from ka59_g2_safe_route.py), CLICK
that dot, and record: canonical landing cell, its phase, and an exhaustive
real-BFS census of the piece's post-click reachable component (size +
containment of the other two dots' approach cells, each box's interior at
the landing phase, and box2's interior at all).

This script is a SURVEY -- one row's failure must not kill the others, so
the harness's `fail()`-and-exit is replaced with `row_fail()` (raises
RowFailed, caught per-row) and `WinFound` (raises all the way out, in case
a stray click actually wins the level -- extremely unlikely mid-survey but
must not be silently swallowed).

    ./.venv/Scripts/python.exe ka59_g3_crossing_table.py > results/ka59-g3-run.txt
"""

import copy
import sys
import time
from collections import deque

import numpy as np

import arc_agi
from arcengine.enums import GameState

import ferry


# ============================================================================
# Harness (reused verbatim in spirit from ka59_g2_safe_route.py -- see
# results/ka59-safe-route-20260817.md for provenance -- adapted so a single
# row's failure does not kill the whole survey).
# ============================================================================

class RowFailed(Exception):
    pass


class WinFound(Exception):
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
    if o2.levels_completed > 1 or o2.state == GameState.WIN:
        raise WinFound(f"WIN at action {ACT_N[0]} ({tag})")
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
        if o2.levels_completed > 1 or o2.state == GameState.WIN:
            raise WinFound(f"WIN after settle ({tag})")
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
    """Exhaustive real BFS + positive control. Returns (seen, nodes, exhausted, ctrl_pass)."""
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


# ============================================================================
# Kick primitives (generalised from g2's leg1/leg2/leg4).
# ============================================================================

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


def chain_north(cur_e, cur_o, dot_now, protect_others, rounds, tag="chain-north"):
    """Repeat kick_north up to `rounds` times, re-locating the dot each round
    by nearest-component identity. Stops early if no safe approach or no
    movement. Returns (env, obs, final_dot_now, rounds_completed)."""
    cur = list(dot_now)
    completed = 0
    for i in range(rounds):
        prior = cur
        cur_e, cur_o, moved = kick_north_once(cur_e, cur_o, cur, protect_others, tag=f"{tag}-r{i}")
        if not moved:
            break
        completed += 1
        all_others = set()
        for oc in protect_others:
            all_others.add(oc)
        live = [c for c in dot_cells(grid(cur_o)) if c not in all_others]
        comps = components(live, adj=1)
        cur = nearest_component(comps, prior) if comps else prior
    return cur_e, cur_o, cur, completed


# ============================================================================
# Survey rows.
# ============================================================================

MD_PATH = "results/ka59-crossing-table-20260817.md"
mdf = open(MD_PATH, "w", encoding="utf-8")
mdf.write("# ka59 L2 -- CROSSING TABLE (2026-08-17)\n\n")
mdf.write("Phase 1 survey: for each (dot, position), a fresh deepcopy from level-2 entry, "
          "kicks reproduced via safe_route/safe_kick (harness from ka59_g2_safe_route.py), "
          "then click that dot and record the canonical landing + an exhaustive real-BFS "
          "census of the piece's post-click reachable component.\n\n")
mdf.write("| Dot | Setup | Actions | Landing | Phase | Reach(nodes/exh) | ctrl | "
          "dot0-appr | dot1-appr | dot2-appr | box0@ph | box1@ph | box3@ph | box2(any) | Notes |\n")
mdf.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
mdf.flush()


def dot_at_entry(cur_o):
    d = dot_cells(grid(cur_o))
    D0 = [c for c in d if 33 <= c[0] <= 35]
    D1 = [c for c in d if 40 <= c[0] <= 43]
    D2 = [c for c in d if c[0] >= 44]
    return D0, D1, D2


def approach_reachable(seen, other_dot_cells):
    if not other_dot_cells:
        return "n/a(consumed)"
    fp = dot_footprint(other_dot_cells)
    return any(c in seen for c in fp)


def box_at_phase_reachable(seen, box_name, ph):
    b = BOXES[box_name]
    cells = [(x, y) for x in range(b[0], b[2] + 1) for y in range(b[1], b[3] + 1) if phase((x, y)) == ph]
    hit = [c for c in cells if c in seen]
    return bool(hit), hit


def box_any_reachable(seen, box_name):
    b = BOXES[box_name]
    cells = [(x, y) for x in range(b[0], b[2] + 1) for y in range(b[1], b[3] + 1)]
    hit = [c for c in cells if c in seen]
    return bool(hit), hit


def run_row(label, setup_fn):
    t0 = time.time()
    ACT_N[0] = 0
    cur_e, cur_o = copy.deepcopy(ENV0), OBS0
    print(f"\n{'=' * 70}\nROW: {label}\n{'=' * 70}")
    sys.stdout.flush()
    try:
        cur_e, cur_o, click_target, other0, other1, note = setup_fn(cur_e, cur_o)
        # click_target: cells of the dot being clicked THIS row.
        cur_e, cur_o = guarded_step(cur_e, cur_o, f"{label}-CLICK",
                                     click=click_target[0], target_cells=click_target)
        landing = piece_xy(grid(cur_o))
        ph = phase(landing)
        print(f"landing={landing} phase={ph} actions={ACT_N[0]}")
        seen, nodes, exhausted, ctrl_pass = census(cur_e, cur_o)
        d0a = approach_reachable(seen, other0) if other0 is not None else "n/a"
        d1a = approach_reachable(seen, other1) if other1 is not None else "n/a"
        # third-dot placeholder filled by caller via note-encoded flag below
        b0ok, b0c = box_at_phase_reachable(seen, "box0", ph)
        b1ok, b1c = box_at_phase_reachable(seen, "box1", ph)
        b3ok, b3c = box_at_phase_reachable(seen, "box3", ph)
        b2ok, b2c = box_any_reachable(seen, "box2")
        print(f"census: nodes={nodes} size={len(seen)} exhausted={exhausted} ctrl={ctrl_pass}")
        print(f"  dot-approach reachable: {d0a} / {d1a}")
        print(f"  box0@phase{ph}: {b0ok} {b0c}")
        print(f"  box1@phase{ph}: {b1ok} {b1c}")
        print(f"  box3@phase{ph}: {b3ok} {b3c}")
        print(f"  box2(any): {b2ok} {b2c}")
        row = (label, note, ACT_N[0], landing, ph, f"{nodes}/{'EXH' if exhausted else 'CAP'}",
               ctrl_pass, d0a, d1a, "--", b0ok, b1ok, b3ok, b2ok, "OK")
    except (RowFailed, AssertionError) as ex:
        print(f"ROW FAILED: {ex}")
        row = (label, "", ACT_N[0], "--", "--", "--", "--", "--", "--", "--",
               "--", "--", "--", "--", f"FAILED: {ex}")
    dt = time.time() - t0
    print(f"row wall time: {dt:.1f}s")
    sys.stdout.flush()
    lbl, note, acts, landing, ph, reach, ctrl, d0a, d1a, d2a, b0ok, b1ok, b3ok, b2ok, status = row
    mdf.write(f"| {lbl} | {note} | {acts} | {landing} | {ph} | {reach} | {ctrl} | "
              f"{d0a} | {d1a} | {d2a} | {b0ok} | {b1ok} | {b3ok} | {b2ok} | {status} |\n")
    mdf.flush()
    return row


# ---- dot0 rows ----
def setup_dot0_entry(cur_e, cur_o):
    D0, D1, D2 = dot_at_entry(cur_o)
    return cur_e, cur_o, D0, D1, D2, "entry (no kick)"


def setup_dot0_west(cur_e, cur_o):
    D0, D1, D2 = dot_at_entry(cur_o)
    cur_e, cur_o = kick_west(cur_e, cur_o, D0, D1 + D2, tag="dot0-west")
    live = [c for c in dot_cells(grid(cur_o)) if c not in D1 and c not in D2]
    comps = components(live, adj=1)
    d0_now = nearest_component(comps, D0) if comps else D0
    return cur_e, cur_o, d0_now, D1, D2, f"west-kicked (from {D0})"


def setup_dot0_chain(cur_e, cur_o):
    D0, D1, D2 = dot_at_entry(cur_o)
    cur_e, cur_o = kick_west(cur_e, cur_o, D0, D1 + D2, tag="dot0-chain-west")
    live = [c for c in dot_cells(grid(cur_o)) if c not in D1 and c not in D2]
    comps = components(live, adj=1)
    d0_now = nearest_component(comps, D0) if comps else D0
    cur_e, cur_o, d0_now, rounds = chain_north(cur_e, cur_o, d0_now, D1 + D2, rounds=4, tag="dot0-chain-north")
    return cur_e, cur_o, d0_now, D1, D2, f"west+chain-north x{rounds}"


# ---- dot1 rows ----
def setup_dot1_entry(cur_e, cur_o):
    D0, D1, D2 = dot_at_entry(cur_o)
    return cur_e, cur_o, D1, D0, D2, "entry (no kick)"


def setup_dot1_west(cur_e, cur_o):
    D0, D1, D2 = dot_at_entry(cur_o)
    cur_e, cur_o = kick_west(cur_e, cur_o, D1, D0 + D2, tag="dot1-west")
    live = [c for c in dot_cells(grid(cur_o)) if c not in D0 and c not in D2]
    comps = components(live, adj=1)
    d1_now = nearest_component(comps, D1) if comps else D1
    return cur_e, cur_o, d1_now, D0, D2, f"west-kicked (from {D1})"


def setup_dot1_chain(cur_e, cur_o):
    D0, D1, D2 = dot_at_entry(cur_o)
    cur_e, cur_o = kick_west(cur_e, cur_o, D1, D0 + D2, tag="dot1-chain-west")
    live = [c for c in dot_cells(grid(cur_o)) if c not in D0 and c not in D2]
    comps = components(live, adj=1)
    d1_now = nearest_component(comps, D1) if comps else D1
    cur_e, cur_o, d1_now, rounds = chain_north(cur_e, cur_o, d1_now, D0 + D2, rounds=4, tag="dot1-chain-north")
    return cur_e, cur_o, d1_now, D0, D2, f"west+chain-north x{rounds}"


# ---- dot2 rows (west kick can compound-sweep dot0 -- identify by x-sort) ----
def setup_dot2_entry(cur_e, cur_o):
    D0, D1, D2 = dot_at_entry(cur_o)
    return cur_e, cur_o, D2, D0, D1, "entry (no kick)"


def kick_dot2_west_with_sweep(cur_e, cur_o, D0, D1, D2, tag="dot2-west"):
    """Mirrors g2 leg2 exactly: kicks dot2 west, declares D0 as a legit
    co-target (documented compound sweep), then re-identifies both by
    x-sort (smaller-x = dot0) since nearest-component is proven wrong here."""
    cur_e, cur_o = kick_west(cur_e, cur_o, D2, D1, extra_target=D0, tag=tag)
    west_dots = [c for c in dot_cells(grid(cur_o)) if c not in D1]
    comps = components(west_dots, adj=1)
    if len(comps) >= 2:
        comps_by_x = sorted(comps, key=lambda c: sum(p[0] for p in c) / len(c))
        d0_now, d2_now = comps_by_x[0], comps_by_x[-1]
        swept = True
    elif len(comps) == 1:
        d0_now, d2_now = D0, comps[0]
        swept = False
    else:
        raise RowFailed(f"{tag}: no dots found after kick")
    return cur_e, cur_o, d0_now, d2_now, swept


def setup_dot2_west(cur_e, cur_o):
    D0, D1, D2 = dot_at_entry(cur_o)
    cur_e, cur_o, d0_now, d2_now, swept = kick_dot2_west_with_sweep(cur_e, cur_o, D0, D1, D2)
    return cur_e, cur_o, d2_now, d0_now, D1, f"west-kicked (from {D2}; compound_sweep_of_dot0={swept})"


def setup_dot2_chain(cur_e, cur_o):
    D0, D1, D2 = dot_at_entry(cur_o)
    cur_e, cur_o, d0_now, d2_now, swept = kick_dot2_west_with_sweep(cur_e, cur_o, D0, D1, D2, tag="dot2-chain-west")
    cur_e, cur_o, d2_now, rounds = chain_north(cur_e, cur_o, d2_now, D0 + D1, rounds=4, tag="dot2-chain-north")
    return cur_e, cur_o, d2_now, d0_now, D1, f"west+chain-north x{rounds} (compound_sweep_of_dot0={swept})"


ROWS_TO_RUN = [
    ("dot0@entry", setup_dot0_entry),
    ("dot0@west", setup_dot0_west),
    ("dot0@chain-north", setup_dot0_chain),
    ("dot1@entry", setup_dot1_entry),
    ("dot1@west", setup_dot1_west),
    ("dot1@chain-north", setup_dot1_chain),
    ("dot2@entry", setup_dot2_entry),
    ("dot2@west", setup_dot2_west),
    ("dot2@chain-north", setup_dot2_chain),
]

RESULTS = []
for label, fn in ROWS_TO_RUN:
    try:
        RESULTS.append(run_row(label, fn))
    except WinFound as w:
        print(f"\n*** WIN FOUND MID-SURVEY: {w} *** (stopping survey)")
        mdf.write(f"\n**WIN FOUND MID-SURVEY at row {label}: {w}**\n")
        break

mdf.write(f"\nTotal rows attempted: {len(RESULTS)} / {len(ROWS_TO_RUN)}\n")
mdf.close()
print(f"\n=== SURVEY DONE: {len(RESULTS)} rows written to {MD_PATH} ===")
