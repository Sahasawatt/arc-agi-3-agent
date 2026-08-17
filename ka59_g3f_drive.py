"""ka59 g3f (2026-08-17) -- PHASE 2+3, fourth attempt: g3e reached the chain-
kick with dot0 crossed and box3 filled, then hit a FALSE-POSITIVE safe-route
violation -- the kick target_cells listed only dot0's reference cell
(tx,ty), and when the kick moved dot0's OTHER footprint cell too, that cell
"vanishing" from an undeclared target tripped the guard. Fixed here: target
is dot0's full current cell list. Everything else unchanged from g3e:
g3d showed dot2's own
ENTRY canonical cell (44,48) phase (2,0) is a genuinely isolated 88-node
component (exhausted BFS) that cannot reach box3 -- so ANY early or
mid-line mint via unkicked dot2 strands the rest of the line, regardless
of ordering. Dropping the "mint-then-recycle" idea entirely.

New idea, simpler and closer to y11's own proven line: y11 filled box0 and
box1 (sacrificing box3's marker to do it) and then walked into box2 for
free (box2 was already reachable from box3's old marker cell). The only
gap was spending box3's OWN marker on box1. dot2 was untouched the whole
time in y11. So: swap y11's step G's object from "box3's marker" to
"dot2 itself" -- click dot2 (still live, untouched, at entry) from INSIDE
box1 instead. This fills box1 AND leaves box3 alone (still filled from its
own earlier crossing-click). The piece lands at dot2's stranding pocket
(44,48) phase (2,0) -- but that no longer matters if box2 itself has a
reachable cell in that exact 88-node component (untested until now: g3d's
census only reported the count, never checked box2 containment).

Line: (1) kick dot0 west. (2) kick dot1 west. (3) walk to box3, click dot1
-- crosses + fills box3. (4) chain-kick dot0 north. (5) walk to box0, click
dot0 -- fills box0. (6) walk to box1. (7) click dot2 (untouched) from
inside box1 -- fills box1, piece -> (44,48)-ish phase (2,0). (8) exhaustive
census + safe_route to box2 from there.

    ./.venv/Scripts/python.exe ka59_g3e_drive.py > results/ka59-g3e-run.txt
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


def region(x0, x1, y0, y1):
    return lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1


def in_box(c, bb):
    return bb[0] <= c[0] <= bb[2] and bb[1] <= c[1] <= bb[3]


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
# THE LINE.
# ============================================================================
cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: piece={piece_xy(grid(cur_o))} dot0={D0} dot1={D1} dot2={D2}")
record("0-entry", cur_o)

# --- 1. kick dot0 west --------------------------------------------------------
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(35, 39, 42, 46), protect=D1 + D2 + D0)
if p is None:
    fail("leg1: no safe route to dot0's approach", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "1-approach-dot0", target_cells=())
cur_e, cur_o, moved = safe_kick(cur_e, cur_o, 3, "1-kick-dot0-west", D0)
d0_now = [c for c in dot_cells(grid(cur_o)) if c[1] > 40 and c[0] < 30]
print(f"1 done: moved={moved} dot0 now at {sorted(d0_now)}")
record("1-dot0-kicked", cur_o)
if not moved or not d0_now:
    fail("leg1: dot0 did not kick west cleanly", cur_o)

# --- 2. kick dot1 west --------------------------------------------------------
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(48, 52, 33, 35), protect=d0_now + D1 + D2)
if p is None:
    fail("leg2: no safe route to dot1's approach", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "2-approach-dot1", target_cells=())
cur_e, cur_o, moved = safe_kick(cur_e, cur_o, 3, "2-kick-dot1-west", D1)
d1_now = [c for c in dot_cells(grid(cur_o)) if c not in d0_now and c[0] < 30]
print(f"2 done: moved={moved} dot1 now at {sorted(d1_now)}")
record("2-dot1-kicked", cur_o)
if not moved or not d1_now:
    fail("leg2: dot1 did not kick west cleanly", cur_o)

# --- 3. fill box3 via dot1, cross ---------------------------------------------
b3 = BOXES["box3"]
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(b3[0], b3[2], b3[1], b3[3]),
                      protect=d0_now + d1_now + D2, max_nodes=2000)
if p is None:
    fail("leg3: no safe route to box3", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "3-to-box3", target_cells=())
d1_now2 = [c for c in dot_cells(grid(cur_o)) if c not in d0_now and c not in D2]
if not d1_now2:
    fail(f"leg3: dot1 not found before box3 fill -- dots={dot_cells(grid(cur_o))}", cur_o)
cur_e, cur_o = guarded_step(cur_e, cur_o, "3-FILL-box3-dot1", click=d1_now2[0], target_cells=d1_now2)
record("3-box3-filled-crossed", cur_o)
piece_after_3 = piece_xy(grid(cur_o))
if not any(in_box(c, b3) for c in extra4(cur_o)):
    fail(f"leg3: box3 not filled after dot1 click -- extra4={extra4(cur_o)}", cur_o)
print(f"3 done: box3 filled, piece crossed to {piece_after_3} phase={phase(piece_after_3)}")

# --- 4. chain-kick dot0 north --------------------------------------------------
crossed = False
for round_i in range(4):
    d0_now2 = [c for c in dot_cells(grid(cur_o)) if not in_box(c, b3) and c not in D2]
    if not d0_now2:
        fail(f"leg4: dot0 lost before chain-kick round {round_i} -- dots={dot_cells(grid(cur_o))}", cur_o)
    tx, ty = d0_now2[0]
    if ty < BAND_Y[0]:
        crossed = True
        break
    tgt = region(tx - 1, tx + 4, ty + 3, ty + 8)
    p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, tgt, protect=[], max_nodes=1500)
    if p is None:
        print(f"4: round {round_i} no safe approach route -- stopping chain attempt")
        break
    cur_e, cur_o = safe_walk(cur_e, cur_o, p, f"4-approach-chain-r{round_i}", target_cells=())
    # BUGFIX vs g3e: target_cells must be dot0's FULL footprint (both cells of
    # its 1x2 shape), not just the reference cell (tx,ty) -- g3e's single-cell
    # target tripped a false-positive SAFE-ROUTE VIOLATION when the kick moved
    # BOTH cells (the second cell "vanished" from a target list that never
    # named it).
    cur_e, cur_o, moved = safe_kick(cur_e, cur_o, 1, f"4-chain-kick-dot0-r{round_i}", d0_now2)
    if not moved:
        print(f"4: round {round_i} kick did not move dot0 -- stopping chain attempt")
        break
record("4-dot0-chain-attempted", cur_o)
d0_now2 = [c for c in dot_cells(grid(cur_o)) if not in_box(c, b3) and c not in D2]
crossed = bool(d0_now2) and all(c[1] < BAND_Y[0] for c in d0_now2)
print(f"4 done: dot0 now at {sorted(d0_now2)}, crossed_band={crossed}")
if not crossed:
    seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
    fail(f"BROKE_AT_LEG_4: dot0 did not chain past the internal band -- "
         f"census {nodes} nodes {len(seen)} positions", cur_o)

# --- 5. fill box0 via dot0 ----------------------------------------------------
b0 = BOXES["box0"]
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(b0[0], b0[2], b0[1], b0[3]), protect=[], max_nodes=1500)
if p is None:
    fail("BROKE_AT_LEG_5: no safe route to box0 after dot0's north chain", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "5-to-box0", target_cells=())
d0_now2 = [c for c in dot_cells(grid(cur_o)) if not in_box(c, b3) and c not in D2]
if not d0_now2:
    fail(f"leg5: dot0 not found before box0 fill -- dots={dot_cells(grid(cur_o))}", cur_o)
cur_e, cur_o = guarded_step(cur_e, cur_o, "5-FILL-box0-dot0", click=d0_now2[0], target_cells=d0_now2)
record("5-box0-filled", cur_o)
if not any(in_box(c, b0) for c in extra4(cur_o)):
    fail(f"leg5: box0 not filled after dot0 click -- extra4={extra4(cur_o)}", cur_o)
piece_after_5 = piece_xy(grid(cur_o))
print(f"5 done: box0 filled, piece at {piece_after_5} phase={phase(piece_after_5)}")

# --- 6. walk into box1 --------------------------------------------------------
b1 = BOXES["box1"]
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(b1[0], b1[2], b1[1], b1[3]), protect=[], max_nodes=3000)
if p is None:
    seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
    fail(f"BROKE_AT_LEG_6: no safe route to box1 from {piece_after_5} phase={phase(piece_after_5)} -- "
         f"census {nodes} nodes {len(seen)} positions", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "6-to-box1", target_cells=())
record("6-standing-in-box1", cur_o)
print(f"6 done: standing at {piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))}")

# --- 7. THE SWAP: click dot2 (untouched) from inside box1 --------------------
d2_now = dot_cells(grid(cur_o))
print(f"7: dot2 sanity check -- live dots now: {d2_now} (expect == entry D2={D2}, untouched)")
if sorted(d2_now) != sorted(D2):
    print("  WARNING: dot2 does not match its entry position -- proceeding anyway with live cell")
if not d2_now:
    fail(f"leg7: dot2 not found before fill-box1 click -- dots={dot_cells(grid(cur_o))}", cur_o)
cur_e, cur_o = guarded_step(cur_e, cur_o, "7-FILL-box1-dot2", click=d2_now[0], target_cells=d2_now)
record("7-box1-filled", cur_o)
piece_after_7 = piece_xy(grid(cur_o))
phase_after_7 = phase(piece_after_7)
print(f"7 done: piece={piece_after_7} phase={phase_after_7}")
if not any(in_box(c, b1) for c in extra4(cur_o)):
    fail(f"leg7: box1 not filled after dot2 click -- extra4={extra4(cur_o)}", cur_o)
filled_after_7 = {
    "box0": any(in_box(c, b0) for c in extra4(cur_o)),
    "box1": any(in_box(c, b1) for c in extra4(cur_o)),
    "box3": any(in_box(c, b3) for c in extra4(cur_o)),
}
print(f"7 RESULT: extra4={extra4(cur_o)} boxes filled so far: {filled_after_7}")

# --- 8. is box2 reachable from dot2's stranding pocket? -----------------------
b2 = BOXES["box2"]
seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
exhausted = nodes < 15000
cells = [(x, y) for x in range(b2[0], b2[2] + 1) for y in range(b2[1], b2[3] + 1)]
reach_any = [c for c in cells if c in seen]
print(f"8 CENSUS: {nodes} nodes {len(seen)} positions ({'EXHAUSTED' if exhausted else 'CAP HIT'}), "
      f"box2 interior reachable (any phase): {reach_any}")
if reach_any:
    p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(b2[0], b2[2], b2[1], b2[3]),
                          protect=[], max_nodes=4000)
    if p is None:
        fail(f"leg8: census said box2 reachable but safe_route found no path -- reach={reach_any}", cur_o)
    cur_e, cur_o = safe_walk(cur_e, cur_o, p, "8-to-box2", target_cells=())
    record("8-final-in-box2", cur_o)
    final_piece = piece_xy(grid(cur_o))
    print(f"8 done: walked into box2, piece={final_piece} levels_completed={cur_o.levels_completed}")
else:
    print(f"\n8: box2 NOT reachable from dot2's stranding pocket -- LINE_COMPLETE_NO_WIN "
          f"(3 filled but piece cannot reach box2 from here)")
    record("8-box2-unreachable", cur_o)

final_piece = piece_xy(grid(cur_o))
final_extra4 = extra4(cur_o)
filled = {
    "box0": any(in_box(c, b0) for c in final_extra4),
    "box1": any(in_box(c, b1) for c in final_extra4),
    "box3": any(in_box(c, b3) for c in final_extra4),
}
piece_in_box2 = in_box(final_piece, b2) if final_piece else False
n_filled = sum(1 for v in filled.values() if v)
print(f"\n=== FINAL ===")
print(f"levels_completed={cur_o.levels_completed} state={cur_o.state}")
print(f"final piece: {final_piece} phase={phase(final_piece)}")
print(f"final extra4 census: {final_extra4}")
print(f"boxes filled: {filled}")
print(f"piece inside box2: {piece_in_box2}")
dump_legs()

if cur_o.levels_completed > 1 or cur_o.state == GameState.WIN:
    print("\nWIN WIN WIN -- LEVELS_COMPLETED > 1")
    verdict = "WIN"
else:
    verdict = ("LINE_COMPLETE_NO_WIN" if n_filled == 3 and piece_in_box2 else "LINE_COMPLETE_PARTIAL")
print(f"\n=== VERDICT: {verdict} -- {n_filled} of {{box0,box1,box3}} filled, "
      f"piece-in-box2={piece_in_box2}, levels_completed={cur_o.levels_completed} ===")
print(f"total actions: {ACT_N[0]}")
