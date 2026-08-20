"""ka59 g1 (2026-08-17) -- GUIDED SEARCH, composed line #1.

Mission (per results/breadth-recon.md's clean-settle+composition-analysis tail):
box3-last / mint-via-dot0 and box3-last / mint-via-dot2 are BOTH exhausted
(results/ka59-clean-settle-20260817.md). The remaining space is ORDERINGS
composing two never-driven mechanics: (a) the return-click fill (click dot1,
still at entry, from inside an unfilled box -> fills it AND returns the
piece to dot1's RIGHT entry cell) and (b) markers inherit their origin dot's
kick geometry.

Key re-derivation (main-thread, this session): y11 (ka59_y11.py) already
PROVED dot0's own north-chain (kick west -> chain-kick north -> box0 fill
-> lands piece at box1, phase (1,2)) works -- its only cost was spending
dot1 AND box3's fill to cross RIGHT<->LEFT twice. If a DIFFERENT dot (dot2)
is used for the RIGHT->LEFT crossing + box3 fill instead of dot1, dot1 stays
completely untouched and free for the return-click fill of box1 -- which
means box3 need NEVER be un-filled. This composed line:

  A. [RIGHT] kick dot0 west -> LEFT-BOTTOM (raw).                 (y11 leg A, verbatim)
  B. [RIGHT] kick dot2 west -> LEFT-BOTTOM (raw).                 (new: dot2 instead of dot1)
  C. box3, click dot2 -> box3 FILLED, piece crosses LEFT to dot2's cell.
  D. [LEFT] chain-kick dot0 north -> phase (1,2), LEFT-TOP.        (y11 leg D, verbatim)
  E. box0, click dot0 -> box0 FILLED, piece crosses to dot0's cell, phase (1,2).
  F. walk into box1 (phase match, per y11).
  G. click dot1 (STILL UNTOUCHED, RIGHT entry) from inside box1 -> box1 FILLED,
     piece returns to dot1's RIGHT entry cell.                     (NOVEL -- the mission's
     untested "return-click fill" mechanic)
  H. walk into box2 directly (box2's interior spans all 9 phases per x3 --
     may not need a ticket/mint at all).

If ALL of A-H succeed: box0+box1+box3 filled AND piece in box2 simultaneously
-- a configuration NO prior session has reached (y2 filled 3 but stranded
outside box2; y11 reached box2 with only 2 filled).

Before the composed line: a CHEAP priority-1 check on a throwaway branch --
does dot1's MARKER (not the raw dot) obey the same slide-until-blocked,
multiple-of-3 kick physics already measured for dot2's marker? Not used by
the composed line itself (which only clicks dot1 raw), but load-bearing for
any FALLBACK that needs to re-position dot1 after it becomes a marker.

    ./.venv/Scripts/python.exe ka59_g1_composed_line.py > results/ka59-g1-run.txt
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


def region(x0, x1, y0, y1):
    return lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1


BOXES = {"box1": (9, 9, 11, 14), "box3": (54, 39, 59, 41),
         "box0": (6, 42, 11, 47), "box2": (51, 51, 53, 53)}
BAND_Y = (24, 29)
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


def record(leg, o):
    p = piece_xy(grid(o))
    LEGS.append((leg, p, phase(p), extra4(o), o.levels_completed))


def dump_legs():
    print("\n=== LEG TABLE ===")
    for leg, p, ph, e4, lc in LEGS:
        print(f"  {leg:32s} piece={p} phase={ph} extra4={e4} levels_completed={lc}")


def fail(msg, o):
    print(f"\n  LINE BROKE: {msg}")
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
        # dot-avoiding settle, reused verbatim from ka59_s4_clean_settle.py.
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


def commit(e, o, path, tag):
    for v in path:
        e, o = step_log(e, o, v=v, tag=tag)
    return e, o


def in_box(c, bb):
    return bb[0] <= c[0] <= bb[2] and bb[1] <= c[1] <= bb[3]


def reach_check(cur_e, cur_o, tag, box_name, phase_filter, ref_p_for_ctrl):
    print(f"\n=== {tag}: {box_name} interior at phase {phase_filter} ===")
    seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
    print(f"exhaustive BFS: expanded {nodes} nodes, {len(seen)} distinct reachable positions "
          f"({'EXHAUSTED' if nodes < 15000 else 'CAP HIT, not exhausted'})")
    b = BOXES[box_name]
    cells = [(x, y) for x in range(b[0], b[2] + 1) for y in range(b[1], b[3] + 1)]
    cells_at_phase = [c for c in cells if phase(c) == phase_filter]
    reachable = [c for c in cells if c in seen]
    reachable_at_phase = [c for c in cells_at_phase if c in seen]
    print(f"{box_name} interior cells: {cells}")
    print(f"{box_name} cells reachable (any phase): {reachable}")
    print(f"{box_name} cells reachable at required phase: {reachable_at_phase}")

    ctrl_e = copy.deepcopy(cur_e)
    ctrl_o, ctrl_p = None, None
    for v in (4, 2, 1, 3):
        ctrl_o = ctrl_e.step(A[v])
        if ctrl_o is not None and ctrl_o.state != GameState.GAME_OVER:
            cp = piece_xy(grid(ctrl_o))
            if cp is not None and cp != ref_p_for_ctrl:
                ctrl_p = cp
                break
        ctrl_e = copy.deepcopy(cur_e)
    ctrl_pass = ctrl_p is not None and ctrl_p in seen
    print(f"positive control: one real press from this state landed at {ctrl_p}, "
          f"in reachable set: {ctrl_pass} ({'PASS' if ctrl_pass else 'FAIL -- BFS INSTRUMENT BROKEN'})")
    if not ctrl_pass:
        fail(f"{tag} positive control FAILED -- BFS instrument broken", cur_o)

    ok = len(reachable_at_phase) > 0 if phase_filter is not None else len(reachable) > 0
    print(f"\n{tag} VERDICT: {'REACHABLE' if ok else 'NOT REACHABLE'}, "
          f"nodes={nodes}, exhausted={nodes < 15000}")
    return ok, (reachable_at_phase if phase_filter is not None else reachable), nodes


# ============================================================================
# PRIORITY 1 (cheap, throwaway branch): does dot1's MARKER inherit the same
# slide-until-blocked / multiple-of-3 kick physics measured for dot2's marker?
# Not used by the composed line (which clicks dot1 RAW, never marker-ized) --
# this is a load-bearing check for any fallback line that needs to recycle
# dot1 after spending it, so it is answered up front, cheaply, before the
# main line spends any of its own action budget.
# ============================================================================
print("=== PRIORITY 1: dot1's marker kick-geometry check (throwaway branch) ===")
p1_e, p1_o = copy.deepcopy(ENV0), OBS0
p1_dots0 = dot_cells(grid(p1_o))
P1_D1 = [c for c in p1_dots0 if 40 <= c[0] <= 43]
P1_OTHER = [c for c in p1_dots0 if c not in P1_D1]
p1_n = [0]


def p1_step(e, o, v=None, click=None, tag=""):
    p1_n[0] += 1
    o2 = e.step(A[6], data={"x": int(click[0]), "y": int(click[1])}) if click else e.step(A[v])
    ok = o2 is not None and o2.state != GameState.GAME_OVER
    p = piece_xy(grid(o2)) if ok else None
    print(f"  p1#{p1_n[0]:3d} {tag:24s} {'CLICK' + str(click) if click else 'v=' + str(v):12s} "
          f"ok={ok} piece={p} dots={dot_cells(grid(o2)) if ok else None}")
    return (e, o2) if ok else (e, o)


# 1a. walk into box3, click dot1 raw -> box3 filled with dot1's marker.
b = BOXES["box3"]
p, _, _ = bfs_route(copy.deepcopy(p1_e), p1_o, region(b[0], b[2], b[1], b[3]), avoid=P1_OTHER)
if p is None:
    print("  PRIORITY 1: no route to box3 -- SKIPPING (not load-bearing for the main line)")
else:
    for v in p:
        p1_e, p1_o = p1_step(p1_e, p1_o, v=v, tag="p1-to-box3")
    d1c = [c for c in dot_cells(grid(p1_o)) if c in P1_D1 or (40 <= c[0] <= 43)]
    if not d1c:
        print("  PRIORITY 1: dot1 not found near box3 -- SKIPPING")
    else:
        fill_target = d1c[0]
        p1_e, p1_o = p1_step(p1_e, p1_o, click=fill_target, tag="p1-FILL-box3-dot1")
        # settle if needed (piece_xy None after click near a wall)
        if piece_xy(grid(p1_o)) is None:
            for sv in (1, 4, 3, 2):
                e3 = copy.deepcopy(p1_e)
                o3 = e3.step(A[sv])
                if o3 is not None and o3.state != GameState.GAME_OVER and piece_xy(grid(o3)) is not None:
                    p1_e, p1_o = p1_step(p1_e, p1_o, v=sv, tag="p1-settle")
                    break
        marker_now = [c for c in extra4(p1_o) if in_box(c, b)]
        print(f"  PRIORITY 1: box3 marker cells after fill: {marker_now}")
        if marker_now:
            fc = marker_now[0]
            halo = (fc[0] - 1, fc[1] - 1)
            print(f"  PRIORITY 1: ejecting via halo click at {halo} (fill cell {fc} - (1,1))")
            approach_cell = piece_xy(grid(p1_o))
            p1_e, p1_o = p1_step(p1_e, p1_o, click=halo, tag="p1-EJECT-halo")
            if piece_xy(grid(p1_o)) is None:
                for sv in (1, 4, 3, 2):
                    e3 = copy.deepcopy(p1_e)
                    o3 = e3.step(A[sv])
                    if o3 is not None and o3.state != GameState.GAME_OVER and piece_xy(grid(o3)) is not None:
                        p1_e, p1_o = p1_step(p1_e, p1_o, v=sv, tag="p1-settle2")
                        break
            marker_ejected = [c for c in extra4(p1_o) if not in_box(c, b)]
            print(f"  PRIORITY 1: ejected marker (extra4 outside box3): {marker_ejected}")
            if marker_ejected:
                mk_before = set(marker_ejected)
                # approach the ejected marker from the east (it reads as colour 4,
                # not colour 5 -- if it's not adjacent-kickable the piece will just
                # walk normally; watch extra4 for any movement).
                mx, my = marker_ejected[0]
                p2, _, _ = bfs_route(copy.deepcopy(p1_e), p1_o, region(mx + 2, mx + 6, my - 1, my + 1),
                                      max_nodes=1200)
                if p2 is None:
                    print("  PRIORITY 1: no approach route to ejected marker -- INCONCLUSIVE")
                else:
                    for v in p2:
                        p1_e, p1_o = p1_step(p1_e, p1_o, v=v, tag="p1-approach-marker")
                    moved = False
                    for _try in range(8):
                        before4 = set(extra4(p1_o))
                        p1_e, p1_o = p1_step(p1_e, p1_o, v=3, tag="p1-KICK-marker-west")
                        after4 = set(extra4(p1_o))
                        if after4 != before4:
                            moved = True
                            new_marker = sorted(after4 - mk_before) or sorted(after4)
                            dx = (new_marker[0][0] - mx) if new_marker else None
                            print(f"  PRIORITY 1 RESULT: marker MOVED. before={sorted(mk_before)} "
                                  f"after={sorted(after4)} dx={dx} "
                                  f"({'multiple of 3' if dx is not None and dx % 3 == 0 else 'NOT mult-3' if dx is not None else '?'})")
                            break
                    if not moved:
                        print("  PRIORITY 1 RESULT: marker did NOT move under 8 west presses from this approach "
                              "(may need a different approach side, or is not kickable from open floor)")
            else:
                print("  PRIORITY 1: halo click did not eject a marker onto open floor -- INCONCLUSIVE")
        else:
            print("  PRIORITY 1: box3 fill via dot1 did not register -- INCONCLUSIVE")
print(f"=== PRIORITY 1 done ({p1_n[0]} throwaway actions, discarded) ===\n")
sys.stdout.flush()

# ============================================================================
# MAIN LINE: composed line #1 (see module docstring).
# ============================================================================
cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: piece={piece_xy(grid(cur_o))} dot0={D0} dot1={D1} dot2={D2}")
record("0-entry", cur_o)

# --- A. kick dot0 west (y11 leg A, verbatim) ----------------------------------
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(35, 39, 42, 46), avoid=D1 + D2)
if p is None:
    fail("no route to dot0's approach", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "A-approach-dot0")
for _ in range(8):
    before = set(dot_cells(grid(cur_o)))
    cur_e, cur_o = step_log(cur_e, cur_o, v=3, tag="A-kick-dot0-west")
    if set(dot_cells(grid(cur_o))) - before:
        break
record("A-dot0-kicked", cur_o)

# --- B. kick dot2 west (NEW: dot2 instead of dot1) ----------------------------
d0_now = [c for c in dot_cells(grid(cur_o)) if c[1] > 40 and c[0] < 30]
y0d = min(c[1] for c in D2); y1d = max(c[1] for c in D2)
x1d = max(c[0] for c in D2)
p = None
for lo, hi in ((y0d, y1d), (y0d - 1, y1d + 1), (y0d, y0d), (y1d, y1d)):
    p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(x1d + 2, x1d + 12, lo, hi),
                         avoid=D1 + d0_now, max_nodes=3000)
    if p is not None:
        print(f"B: approach region y=[{lo},{hi}] SUCCEEDED")
        break
    print(f"B: approach region y=[{lo},{hi}] no route, trying next")
if p is None:
    fail("no route to dot2's east approach (avoiding dot0/dot1)", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "B-approach-dot2")
before_all = set(dot_cells(grid(cur_o)))
for _ in range(8):
    before = set(dot_cells(grid(cur_o)))
    cur_e, cur_o = step_log(cur_e, cur_o, v=3, tag="B-kick-dot2-west")
    if set(dot_cells(grid(cur_o))) - before:
        break
after_all = set(dot_cells(grid(cur_o)))
d0_check = [c for c in after_all if c[1] > 40 and c[0] < 30]
print(f"B done: dot0 still at {sorted(d0_check)} (expect unchanged from A: {sorted(d0_now)}) "
      f"-- untouched={sorted(d0_check) == sorted(d0_now)}")
record("B-dot2-kicked", cur_o)

# --- C. box3, click dot2 -> box3 FILLED, piece crosses LEFT ------------------
b = BOXES["box3"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]), avoid=d0_now + D1)
if p is None:
    fail("no route to box3", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "C-to-box3")
d2_now = [c for c in dot_cells(grid(cur_o)) if c not in d0_now and c not in D1]
if not d2_now:
    fail(f"dot2 not found before box3 fill -- dots={dot_cells(grid(cur_o))}", cur_o)
tx, ty = d2_now[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="C-FILL-box3-dot2")
record("C-box3-filled-crossed", cur_o)
if not any(in_box(c, b) for c in extra4(cur_o)):
    fail(f"box3 not filled after dot2 click -- extra4={extra4(cur_o)}", cur_o)
print(f"C done: box3 filled, piece crossed to {piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))}")

# --- D. chain-kick dot0 north (y11 leg D, verbatim shape; looped like s4 CHECK B') ---
crossed = False
for round_i in range(4):
    d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D1 and not in_box(c, BOXES["box3"])]
    if not d0_now:
        fail(f"dot0 lost before chain-kick round {round_i} -- dots={dot_cells(grid(cur_o))}", cur_o)
    tx, ty = d0_now[0]
    if ty < BAND_Y[0]:
        crossed = True
        break
    p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(tx - 1, tx + 4, ty + 3, ty + 8),
                         avoid=d0_now, max_nodes=1500)
    if p is None:
        break
    cur_e, cur_o = commit(cur_e, cur_o, p, f"D-approach-chain-r{round_i}")
    moved = False
    for _try in range(8):
        before = set(dot_cells(grid(cur_o)))
        cur_e, cur_o = step_log(cur_e, cur_o, v=1, tag=f"D-chain-kick-dot0-r{round_i}")
        if set(dot_cells(grid(cur_o))) - before:
            moved = True
            break
    if not moved:
        break
record("D-dot0-chain-attempted", cur_o)
d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D1 and not in_box(c, BOXES["box3"])]
crossed = bool(d0_now) and all(c[1] < BAND_Y[0] for c in d0_now)
print(f"D done: dot0 now at {sorted(d0_now)}, crossed_band={crossed}")
if not crossed:
    print("\n*** D BROKE: dot0 did not chain past the internal band. Census of what IS reachable: ***")
    seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
    seen = {c for c in seen if c is not None}
    print(f"exhaustive BFS: {nodes} nodes, {len(seen)} positions "
          f"({'EXHAUSTED' if nodes < 15000 else 'CAP HIT'})")
    for bn in ("box0", "box1", "box3"):
        bb = BOXES[bn]
        cells = [(x, y) for x in range(bb[0], bb[2] + 1) for y in range(bb[1], bb[3] + 1)]
        reach = [c for c in cells if c in seen]
        print(f"  {bn} interior cells reachable (any phase): {reach}")
    fail("dot0 did not chain past the internal band after crossing via dot2/box3 (LEG D) -- "
         "composed-line-1 broken here", cur_o)

# --- E. box0, click dot0 (y11 leg E, verbatim shape) --------------------------
b = BOXES["box0"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]), max_nodes=1500)
if p is None:
    fail("no route to box0 after dot0's north chain", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "E-to-box0")
d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D1 and not in_box(c, BOXES["box3"])]
if not d0_now:
    fail(f"dot0 not found before box0 fill -- dots={dot_cells(grid(cur_o))}", cur_o)
tx, ty = d0_now[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="E-FILL-box0-dot0")
record("E-box0-filled", cur_o)
if not any(in_box(c, b) for c in extra4(cur_o)):
    fail(f"box0 not filled after dot0 click -- extra4={extra4(cur_o)}", cur_o)
piece_after_e = piece_xy(grid(cur_o))
print(f"E done: box0 filled, piece at {piece_after_e} phase={phase(piece_after_e)}")

# --- F. walk into box1 --------------------------------------------------------
b = BOXES["box1"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]), max_nodes=3000)
if p is None:
    ok_d, reach_d, nodes_d = reach_check(cur_e, cur_o, "CHECK-F-census", "box1", None, piece_after_e)
    fail(f"no route to box1 from {piece_after_e} phase={phase(piece_after_e)} -- "
         f"census REACHABLE={ok_d} reach={reach_d}", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "F-to-box1")
record("F-standing-in-box1", cur_o)
print(f"F done: standing at {piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))}")

# --- G. click dot1 (STILL UNTOUCHED) from inside box1 -- NOVEL return-click fill ---
d1_now = [c for c in dot_cells(grid(cur_o))]
print(f"G: dot1 sanity check -- live dots now: {d1_now} (expect == entry D1={D1}, untouched)")
if sorted(d1_now) != sorted(D1):
    print("  WARNING: dot1 does not match its entry position -- proceeding anyway with live cell")
if not d1_now:
    fail(f"dot1 not found before return-click -- dots={dot_cells(grid(cur_o))}", cur_o)
tx, ty = d1_now[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="G-RETURN-CLICK-box1-dot1")
record("G-box1-filled-returned", cur_o)
piece_after_g = piece_xy(grid(cur_o))
phase_after_g = phase(piece_after_g)
print(f"G done: piece={piece_after_g} phase={phase_after_g} (expect ~dot1 canonical entry, RIGHT)")
if not any(in_box(c, BOXES["box1"]) for c in extra4(cur_o)):
    fail(f"box1 not filled after return-click -- extra4={extra4(cur_o)}", cur_o)
print(f"G RESULT: box1 filled AND piece returned -- extra4={extra4(cur_o)} "
      f"boxes filled so far: box0={any(in_box(c, BOXES['box0']) for c in extra4(cur_o))} "
      f"box1={any(in_box(c, BOXES['box1']) for c in extra4(cur_o))} "
      f"box3={any(in_box(c, BOXES['box3']) for c in extra4(cur_o))}")

# --- H. walk into box2 directly -----------------------------------------------
b = BOXES["box2"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]), max_nodes=4000)
if p is None:
    ok_h, reach_h, nodes_h = reach_check(cur_e, cur_o, "CHECK-H-census", "box2", None, piece_after_g)
    fail(f"no direct route to box2 from {piece_after_g} phase={phase_after_g} -- "
         f"census REACHABLE={ok_h} reach={reach_h} (no ticket/mint was planted in this line)", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "H-to-box2")
record("H-final", cur_o)

final_piece = piece_xy(grid(cur_o))
final_extra4 = extra4(cur_o)
print("\n=== FINAL ===")
print(f"levels_completed={cur_o.levels_completed} state={cur_o.state}")
print(f"final piece: {final_piece} phase={phase(final_piece)}")
print(f"final extra4 census: {final_extra4}")

b1, b3, b0, b2 = BOXES["box1"], BOXES["box3"], BOXES["box0"], BOXES["box2"]
filled = {
    "box1": any(in_box(c, b1) for c in final_extra4),
    "box3": any(in_box(c, b3) for c in final_extra4),
    "box0": any(in_box(c, b0) for c in final_extra4),
    "box2": any(in_box(c, b2) for c in final_extra4),
}
piece_in_box2 = in_box(final_piece, b2) if final_piece else False
print(f"boxes filled: {filled}")
print(f"piece inside box2: {piece_in_box2}")
n_filled = sum(1 for k in ("box0", "box1", "box3") if filled[k])

dump_legs()

if cur_o.levels_completed > 1:
    print("\nWIN WIN WIN -- LEVELS_COMPLETED > 1")
print(f"\n=== VERDICT: {n_filled} of {{box0,box1,box3}} filled, "
      f"piece-in-box2={piece_in_box2}, levels_completed={cur_o.levels_completed} ===")
print(f"total actions (main line, excludes PRIORITY 1's {p1_n[0]} throwaway actions): {ACT_N[0]}")
