"""ka59 g4 (2026-08-17) -- THE ONE MEASURABLE QUESTION: can dot2 be kicked so
its CANONICAL CELL (piece landing cell when clicked) lies inside box2's
interior (51,51)-(53,53)? Reuses ka59_g3f_drive.py's harness verbatim
(reach_l2/grid/piece_xy/dot_cells/marker_cells/phase/region/in_box/step_log)
and ka59_g2_safe_route.py's safe_route/guarded_step/safe_kick/exhaustive.

z4 (results/ka59-z4.txt) measured dot2's raw FOOTPRINT after single-direction
kicks (not the canonical click-landing cell, and not routed through the
safe-route harness): east kick -> footprint (59-60,47-48), south kick ->
footprint (44-45,59-60). Both overshoot box2 (51-53,51-53) because neither
kick's fixed OTHER axis (y=47-48 for east, x=44-45 for south) ever passes
through box2's row/column, so nothing stops the slide near it. This script:
(1) re-measures both kicks through safe_route/guarded_step (protecting
dot0+dot1), (2) reads the CANONICAL cell via an aimed click (A[6], not
proximity-gated -- g3f's leg 7 already proved clicks work at range) for the
entry position AND every landing, (3) chains a second kick from each landing
(south-after-east, east-after-south) to see whether the chain's second axis
happens to land within box2's row/column band this time.

    ./.venv/Scripts/python.exe ka59_g4_dot2_canon.py > results/ka59-g4-canon.txt
"""

import copy
import sys
from collections import deque

import numpy as np

import arc_agi
from arcengine.enums import GameState

import ferry


# ============================================================================
# Harness, reused verbatim from ka59_g2_safe_route.py / ka59_g3f_drive.py.
# ============================================================================

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
    return c is not None and bb[0] <= c[0] <= bb[2] and bb[1] <= c[1] <= bb[3]


BOXES = {"box1": (9, 9, 11, 14), "box3": (54, 39, 59, 41),
         "box0": (6, 42, 11, 47), "box2": (51, 51, 53, 53)}
ACT_N = [0]
LEGS = []


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


def record(leg, o, note="asserts=PASS"):
    p = piece_xy(grid(o))
    LEGS.append((leg, p, phase(p), extra4(o), o.levels_completed, note))


def dump_legs():
    print("\n=== LEG TABLE ===")
    hdr = f"  {'leg':32s} {'piece':10s} {'phase':8s} {'extra4':28s} {'lvl':4s} asserts"
    print(hdr)
    for leg, p, ph, e4, lc, note in LEGS:
        print(f"  {leg:32s} {str(p):10s} {str(ph):8s} {str(e4):28s} {lc:<4d} {note}")


def fail(msg, o):
    print(f"\n  ABORT: {msg}")
    print(f"  FINAL: levels_completed={o.levels_completed} state={o.state}")
    print(f"  final extra4 census: {extra4(o)}")
    print(f"  final piece: {piece_xy(grid(o))} phase={phase(piece_xy(grid(o)))}")
    dump_legs()
    sys.exit(0)


def step_log(e, o, v=None, click=None, tag=""):
    ACT_N[0] += 1
    o2 = e.step(A[6], data={"x": int(click[0]), "y": int(click[1])}) if click else e.step(A[v])
    if o2 is None or o2.state == GameState.GAME_OVER:
        print(f"  act#{ACT_N[0]:3d} {tag:28s} DIED")
        fail(f"death at action {ACT_N[0]} ({tag})", o if o2 is None else o2)
    p = piece_xy(grid(o2))
    print(f"  act#{ACT_N[0]:3d} {tag:28s} {'CLICK' + str(click) if click else 'v=' + str(v):14s} "
          f"piece={p} phase={phase(p)} extra4={extra4(o2)} "
          f"levels_completed={o2.levels_completed} state={o2.state}")
    sys.stdout.flush()
    if o2.levels_completed > 1 or o2.state == GameState.WIN:
        print("\n  *** LEVELS_COMPLETED > 1 -- WIN FIRED, STOPPING ***")
        print(f"  final extra4 census: {extra4(o2)}")
        record("WIN", o2)
        dump_legs()
        sys.exit(0)
    if click is not None and p is None:
        print(f"  act#{ACT_N[0]:3d} {'':28s} piece_xy=None after click -- SETTLING (known transient)")
        dots_before = set(dot_cells(grid(o2)))
        trials = []
        for sv in (1, 4, 3, 2):
            e3 = copy.deepcopy(e)
            o3 = e3.step(A[sv])
            if o3 is None or o3.state == GameState.GAME_OVER:
                print(f"  act#{ACT_N[0]:3d} {'':28s} settle-trial v={sv} DIED (rejected)")
                continue
            p3 = piece_xy(grid(o3))
            resolved = p3 is not None
            dots_after = set(dot_cells(grid(o3)))
            disturbed = dots_after != dots_before
            trials.append((sv, e3, o3, resolved, dots_after, disturbed))
            extra = (f" dots_before={sorted(dots_before)} dots_after={sorted(dots_after)}"
                     if disturbed else "")
            print(f"  act#{ACT_N[0]:3d} {'':28s} settle-trial v={sv} resolved={resolved} "
                  f"dots_disturbed={disturbed}{extra}")

        clean = [t for t in trials if t[3] and not t[5]]
        if clean:
            chosen = clean[0]
            print(f"  act#{ACT_N[0]:3d} {'':28s} settle choice: v={chosen[0]} "
                  f"(CLEAN -- resolves AND touches no dot)")
        else:
            resolved_only = [t for t in trials if t[3]]
            if not resolved_only:
                fail(f"piece_xy stayed None after click AND all 4 settle attempts ({tag})", o2)
            chosen = min(resolved_only, key=lambda t: len(t[4].symmetric_difference(dots_before)))
            print(f"  act#{ACT_N[0]:3d} {'':28s} settle choice: v={chosen[0]} "
                  f"(NO CLEAN OPTION -- least-disturbance fallback)")

        sv, e3, o3, resolved, dots_after, disturbed = chosen
        ACT_N[0] += 1
        e, o2 = e3, o3
        p = piece_xy(grid(o2))
        print(f"  act#{ACT_N[0]:3d} {tag + '-SETTLE':28s} v={sv:<13} "
              f"piece={p} phase={phase(p)} extra4={extra4(o2)} "
              f"levels_completed={o2.levels_completed} state={o2.state}")
        sys.stdout.flush()
        if o2.levels_completed > 1 or o2.state == GameState.WIN:
            print("\n  *** LEVELS_COMPLETED > 1 -- WIN FIRED, STOPPING ***")
            record("WIN", o2)
            dump_legs()
            sys.exit(0)
    return e, o2


def dot_footprint(cells):
    fp = set()
    for (cx, cy) in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                fp.add((cx + dx, cy + dy))
    return fp


def safe_route(env, obs, is_target, protect, avoid=(), action_values=(1, 2, 3, 4), max_nodes=3000):
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


def live_objects(o):
    return set(dot_cells(grid(o))) | set(extra4(o))


def guarded_step(e, o, tag, v=None, click=None, target_cells=()):
    before = live_objects(o)
    e, o2 = step_log(e, o, v=v, click=click, tag=tag)
    after = live_objects(o2)
    vanished = before - after
    bad = vanished - set(target_cells)
    if bad:
        fail(f"SAFE-ROUTE VIOLATION in leg '{tag}': this press moved/removed cell(s) "
             f"{sorted(bad)} that were NOT the declared target {sorted(target_cells)} "
             f"(objects before={sorted(before)} after={sorted(after)})", o2)
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


# ============================================================================
# THE QUESTION.
# ============================================================================
dots0 = dot_cells(grid(OBS0))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: dot0={D0} dot1={D1} dot2={D2}")
BOX2 = BOXES["box2"]
print(f"box2 interior: {BOX2}")


def in_box2(p):
    return in_box(p, BOX2)


def candidates_side(cells, side, sizes=(2, 4, 6, 8, 10, 14, 18, 24)):
    """Multiple candidate approach windows on the given side of `cells`,
    widening/receding until one clears safe_route (mirrors g2 leg2's
    multi-window retry -- geometry near a fresh landing spot is unmeasured)."""
    x0 = min(c[0] for c in cells)
    x1 = max(c[0] for c in cells)
    y0 = min(c[1] for c in cells)
    y1 = max(c[1] for c in cells)
    out = []
    if side == "west":  # approach west of cells -> press east to kick east
        for s in sizes:
            out.append(region(x0 - s - 5, x0 - s, y0 - 2, y1 + 2))
    elif side == "north":  # approach north of cells -> press south to kick south
        for s in sizes:
            out.append(region(x0 - 2, x1 + 2, y0 - s - 5, y0 - s))
    return out


def do_kick(env, obs, dot_cells_list, protect, side, press_v, tag, max_presses=8):
    cands = candidates_side(dot_cells_list, side)
    p = None
    for i, cand in enumerate(cands):
        p, _, _ = safe_route(copy.deepcopy(env), obs, cand, protect=protect, max_nodes=3000)
        if p is not None:
            print(f"{tag}: approach candidate {i} succeeded ({len(p)} steps)")
            break
        print(f"{tag}: approach candidate {i} failed, trying next")
    if p is None:
        print(f"{tag}: NO SAFE ROUTE to any approach candidate on side={side}")
        return env, obs, None, False
    e, o = safe_walk(copy.deepcopy(env), obs, p, f"{tag}-approach", target_cells=())
    e, o, moved = safe_kick(e, o, press_v, tag, dot_cells_list, max_presses=max_presses)
    if not moved:
        print(f"{tag}: kick did not move the object (blocked immediately)")
        return e, o, None, False
    new_cells = sorted([c for c in dot_cells(grid(o)) if c not in D0 and c not in D1])
    print(f"{tag}: landed at {new_cells}")
    return e, o, new_cells, True


def measure_canonical(env, obs, dot_cells_list, tag):
    """Aimed click (range, per g3f leg 7 -- no proximity needed) on the given
    dot's own cell; reads the piece's landing cell = the canonical cell."""
    e = copy.deepcopy(env)
    e, o2 = guarded_step(e, obs, tag, click=dot_cells_list[0], target_cells=dot_cells_list)
    p = piece_xy(grid(o2))
    ib2 = in_box2(p)
    print(f"{tag}: canonical piece={p} phase={phase(p)} in_box2={ib2}")
    return p, phase(p), ib2, e, o2


TABLE = []  # (label, kicked, landing, canonical, canon_phase, in_box2)

# --- 0. entry (unkicked) canonical -------------------------------------------
ep, eph, eib2, _, _ = measure_canonical(copy.deepcopy(ENV0), OBS0, D2, "0-entry-canonical")
TABLE.append(("entry (unkicked)", "n/a", D2, ep, eph, eib2))

# --- A. east kick (approach west, press east=4) ------------------------------
e_east, o_east, east_landing, east_moved = do_kick(
    copy.deepcopy(ENV0), OBS0, D2, D0 + D1, "west", 4, "A-east-kick")
TABLE.append(("east kick", east_moved, east_landing, None, None, None))
if east_moved:
    ap, aph, aib2, _, _ = measure_canonical(e_east, o_east, east_landing, "A-east-canonical")
    TABLE[-1] = ("east kick", east_moved, east_landing, ap, aph, aib2)

# --- B. south kick (approach north, press south=2) ---------------------------
e_south, o_south, south_landing, south_moved = do_kick(
    copy.deepcopy(ENV0), OBS0, D2, D0 + D1, "north", 2, "B-south-kick")
TABLE.append(("south kick", south_moved, south_landing, None, None, None))
if south_moved:
    bp, bph, bib2, _, _ = measure_canonical(e_south, o_south, south_landing, "B-south-canonical")
    TABLE[-1] = ("south kick", south_moved, south_landing, bp, bph, bib2)

# --- C. chain: east landing -> kick south -------------------------------------
if east_moved:
    e_es, o_es, es_landing, es_moved = do_kick(
        copy.deepcopy(e_east), o_east, east_landing, D0 + D1, "north", 2, "C-east-then-south-kick")
    TABLE.append(("east then south kick", es_moved, es_landing, None, None, None))
    if es_moved:
        cp, cph, cib2, _, _ = measure_canonical(e_es, o_es, es_landing, "C-east-then-south-canonical")
        TABLE[-1] = ("east then south kick", es_moved, es_landing, cp, cph, cib2)
else:
    TABLE.append(("east then south kick", "SKIPPED (east kick failed)", None, None, None, None))

# --- D. chain: south landing -> kick east -------------------------------------
if south_moved:
    e_se, o_se, se_landing, se_moved = do_kick(
        copy.deepcopy(e_south), o_south, south_landing, D0 + D1, "west", 4, "D-south-then-east-kick")
    TABLE.append(("south then east kick", se_moved, se_landing, None, None, None))
    if se_moved:
        dp, dph, dib2, _, _ = measure_canonical(e_se, o_se, se_landing, "D-south-then-east-canonical")
        TABLE[-1] = ("south then east kick", se_moved, se_landing, dp, dph, dib2)
else:
    TABLE.append(("south then east kick", "SKIPPED (south kick failed)", None, None, None, None))

# ============================================================================
# VERDICT
# ============================================================================
print("\n=== DOT2 KICK / CANONICAL TABLE ===")
hdr = f"  {'label':24s} {'kicked':30s} {'landing':40s} {'canonical':12s} {'phase':8s} {'in_box2':8s}"
print(hdr)
for label, kicked, landing, canon, cph, ib2 in TABLE:
    print(f"  {label:24s} {str(kicked):30s} {str(landing):40s} {str(canon):12s} {str(cph):8s} {str(ib2):8s}")

any_hit = any(row[5] is True for row in TABLE)
print(f"\n=== VERDICT: {'HIT -- at least one dot2 position has canonical INSIDE box2' if any_hit else 'NO_HIT -- no measured dot2 position lands its canonical inside box2'} ===")
print(f"total actions this script: {ACT_N[0]}")
dump_legs()
