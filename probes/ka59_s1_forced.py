"""ka59 s1 (2026-08-17) -- drive REDESIGN 4 (the FORCED assignment) from
breadth-recon.md's last ka59 section: "BROKE_AT_LEG_5 -- box1 needs (1,2),
so the dot ASSIGNMENT is now forced."

Harness reused verbatim from ka59_u1.py (grid/piece_xy/dot_cells/
marker_cells/phase/components/bfs_route/exhaustive/region/BOXES/reach_l2/
extra4/record/fail/step_log/commit/in_box/reach_check) -- copied in rather
than imported because ka59_u1.py executes its drive at import time.

Redesign 4 -- swap which dot mints (dot2, not dot0) and which dot chain-
kicks (dot0, not dot2), because box1 has only ever succeeded at phase
(1,2), which is dot0's own canonical NORTH delivery:
  1. Compound sweep: dot0 -> (13,44), dot2 -> (17,47); dot1 stays RIGHT.
  2. Walk into box2 (proven reachable here). MINT via dot2 -> ticket in
     box2, piece to dot2's canonical cell LEFT-BOTTOM phase (2,0).
     CHECK A': is that LEFT (2,0) component non-isolated -- are dot0's
     kick-approach cells reachable from there?
  3. CHECK B': chain-kick dot0 north from (13,44) past the internal band.
  4. CHECK C': box0 (2,0)-lattice interior reachable? Fill via dot0.
  5. CHECK D': box1 at phase (1,2) reachable (y11's proven leg shape)?
  6. Fill box1 FROM AFAR via dot1 (RIGHT, untouched).
  7. CHECK E': box3 (0,1) interior reachable?
  8. FINAL: click the box2 ticket from inside box3.

    ./.venv/Scripts/python.exe ka59_s1_forced.py > results/ka59-forced-run.txt
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
    """Authoritative instrument per this game's own law: targets nothing,
    just drains the queue."""
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
        # Measured (ka59_u2.py): a click that teleports the piece next to a
        # box wall leaves ONE transient frame where colour-0 spans >2 cells
        # and find_cell bails. One more real action resolves it.
        print(f"  act#{ACT_N[0]:3d} {'':28s} piece_xy=None after click -- SETTLING (known transient)")
        for sv in (1, 4, 3, 2):
            e3 = copy.deepcopy(e)
            o3 = e3.step(A[sv])
            if o3 is not None and o3.state != GameState.GAME_OVER and piece_xy(grid(o3)) is not None:
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
                break
        else:
            fail(f"piece_xy stayed None after click AND all 4 settle attempts ({tag})", o2)
    return e, o2


def commit(e, o, path, tag):
    for v in path:
        e, o = step_log(e, o, v=v, tag=tag)
    return e, o


def in_box(c, bb):
    return bb[0] <= c[0] <= bb[2] and bb[1] <= c[1] <= bb[3]


def reach_check(cur_e, cur_o, tag, box_name, phase_filter, ref_p_for_ctrl):
    """CHECK pattern: exhaustive real BFS + positive control, filtered to a
    named box's interior at a required phase."""
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
    print(f"{box_name} cells at required phase {phase_filter}: {cells_at_phase}")
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
        fail(f"{tag} positive control FAILED -- BFS instrument broken, cannot trust the negative reading",
             cur_o)

    ok = len(reachable_at_phase) > 0
    print(f"\n{tag} VERDICT: {'REACHABLE' if ok else 'NOT REACHABLE'} "
          f"({len(reachable_at_phase)} of {len(cells_at_phase)} phase-matched cells), "
          f"nodes={nodes}, exhausted={nodes < 15000}")
    return ok, reachable_at_phase, nodes


def region_reach_check(cur_e, cur_o, tag, region_name, cells, ref_p_for_ctrl):
    """Same CHECK pattern as reach_check, but against an arbitrary named
    cell list (a kick-approach region) instead of a BOXES entry -- used for
    CHECK A' (is dot0's kick-approach region reachable from the piece's
    post-mint LEFT (2,0) landing?)."""
    print(f"\n=== {tag}: {region_name} ({len(cells)} cells) ===")
    seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
    print(f"exhaustive BFS: expanded {nodes} nodes, {len(seen)} distinct reachable positions "
          f"({'EXHAUSTED' if nodes < 15000 else 'CAP HIT, not exhausted'})")
    if seen:
        xs = [c[0] for c in seen if c is not None]
        ys = [c[1] for c in seen if c is not None]
        print(f"reachable bbox: x=[{min(xs)},{max(xs)}] y=[{min(ys)},{max(ys)}]")
    reachable = [c for c in cells if c in seen]
    print(f"{region_name} cells: {cells}")
    print(f"{region_name} cells reachable: {reachable}")

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
        fail(f"{tag} positive control FAILED -- BFS instrument broken, cannot trust the negative reading",
             cur_o)

    ok = len(reachable) > 0
    print(f"\n{tag} VERDICT: {'REACHABLE' if ok else 'NOT REACHABLE'} "
          f"({len(reachable)} of {len(cells)} region cells), nodes={nodes}, exhausted={nodes < 15000}")
    return ok, reachable, nodes, seen


cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: piece={piece_xy(grid(cur_o))} dot0={D0} dot1={D1} dot2={D2}")
record("0-entry", cur_o)

# ============================================================================
# LEG 1: compound sweep (identical recipe to t1/t2/u1).
# ============================================================================
x0 = min(c[0] for c in D2); x1 = max(c[0] for c in D2)
y0 = min(c[1] for c in D2); y1 = max(c[1] for c in D2)
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(x1 + 2, x1 + 7, y0 - 1, y1 + 1),
                     avoid=D0 + D1, max_nodes=1500)
if p is None:
    fail("no route to dot2's east approach (avoiding dot0)", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "1-approach-dot2-east")
for _ in range(4):
    before = set(dot_cells(grid(cur_o)))
    cur_e, cur_o = step_log(cur_e, cur_o, v=3, tag="1-COMPOUND-SWEEP-west")
    after = set(dot_cells(grid(cur_o)))
    if after - before:
        break
record("1-compound-swept", cur_o)

remaining = [c for c in dot_cells(grid(cur_o)) if c not in D1]
comps = components(remaining)
print(f"1 done: remaining (non-dot1) dot cells={remaining}  components={comps}")
d0_now = next((c for c in comps if len(c) == len(D0)), None)
d2_now = next((c for c in comps if len(c) == len(D2) and c != d0_now), None)
if d0_now is None or d2_now is None:
    fail(f"could not identify dot0/dot2 by cluster size after sweep -- comps={comps}, "
         f"|D0|={len(D0)} |D2|={len(D2)}", cur_o)
print(f"1 done: dot0 now at {d0_now} (expected ~(13,44)), dot2 now at {d2_now} (expected ~(17,47))")
print(f"  dot0 past moat (x<30): {all(c[0] < 30 for c in d0_now)}; "
      f"dot2 past moat (x<30): {all(c[0] < 30 for c in d2_now)}")
DOT2_TICKET_CELL = d2_now[0]
d1_now = list(D1)  # dot1 untouched by the sweep

# ============================================================================
# LEG 2: walk into box2 (t2/u1 PROVED reachable right after the sweep).
# MINT via dot2 -> ticket in box2, piece to dot2's canonical cell.
# (REDESIGN 4: dot2 mints, not dot0 -- box1 forces dot0 to be the box0
# filler whose click delivers phase (1,2), so dot0 must stay unspent here.)
# ============================================================================
b = BOXES["box2"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]),
                     avoid=d1_now, max_nodes=3000)
if p is None:
    fail("no route to box2 -- contradicts t2/u1's proven-reachable census", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "2-walk-to-box2")
box2_stand_cell = piece_xy(grid(cur_o))
print(f"\n2 done: standing in box2 at {box2_stand_cell} phase={phase(box2_stand_cell)}")
record("2-standing-in-box2", cur_o)

cur_e, cur_o = step_log(cur_e, cur_o, click=DOT2_TICKET_CELL, tag="2-MINT-click-dot2")
record("2-minted-box2-ticket", cur_o)
box2_ticket = box2_stand_cell
piece_after_mint = piece_xy(grid(cur_o))
phase_after_mint = phase(piece_after_mint)
print(f"\n2-MINT done: piece landed at {piece_after_mint} phase={phase_after_mint} "
      f"(expected ~dot2's canonical cell {DOT2_TICKET_CELL}, phase (2,0)); "
      f"box2_ticket planted at {box2_ticket}")
if box2_ticket not in extra4(cur_o):
    fail(f"box2 ticket marker not found at {box2_ticket} after mint -- extra4={extra4(cur_o)}", cur_o)

# INSTRUMENT FACT (measured, this session): the auto-settle press after the
# MINT click's transient corrupted frame is a REAL action chosen from a
# fixed direction order (1,4,3,2) regardless of what else it touches -- and
# it can WALK INTO dot0, kicking it, as an unintended side effect. Measured:
# dot0 moved (13,44)/(13,45) -> (1,44)/(1,45) during THIS settle (a westward
# press). d0_now must therefore be RE-DERIVED from the live board here, not
# read from the stale post-sweep (pre-mint) value -- using the stale value
# silently targets an empty cell and reads as "cannot chain" for the wrong
# reason (verified: a first pass of this script using the stale value found
# 0/4 kick directions moved anything, because none of the approach regions
# were anywhere near dot0's REAL post-settle position).
d0_now = [c for c in dot_cells(grid(cur_o)) if c not in d1_now]
if not d0_now:
    fail(f"dot0 not found (as live colour5) right after MINT+settle -- dots={dot_cells(grid(cur_o))}",
         cur_o)
print(f"\nINSTRUMENT: dot0 after MINT+settle: {d0_now} "
      f"(pre-mint it was at ~(13,44)/(13,45) -- moved by the settle press's side effect)")

# ============================================================================
# CHECK A': is the LEFT (2,0) landing component non-isolated -- are dot0's
# kick-approach cells reachable from here?  (The z3 isolation was measured
# for dot2-at-ENTRY; this is a different component, unmeasured.)
# ============================================================================
dax0 = min(c[0] for c in d0_now); dax1 = max(c[0] for c in d0_now)
day0 = min(c[1] for c in d0_now); day1 = max(c[1] for c in d0_now)
APPROACH_CELLS_A = []
for ax0, ax1, ay0, ay1 in (
        (dax0 - 2, dax1 + 2, day1 + 3, day1 + 8),   # south-approach (press north)
        (dax0 - 2, dax1 + 2, day0 - 8, day0 - 3),   # north-approach (press south)
        (dax0 - 8, dax0 - 3, day0 - 2, day1 + 2),   # west-approach (press east)
        (dax1 + 3, dax1 + 8, day0 - 2, day1 + 2)):  # east-approach (press west)
    APPROACH_CELLS_A += [(x, y) for x in range(ax0, ax1 + 1) for y in range(ay0, ay1 + 1)]

ok_a, reach_a, nodes_a, seen_a = region_reach_check(
    cur_e, cur_o, "CHECK A'", "dot0-kick-approach region", APPROACH_CELLS_A, piece_after_mint)
if not ok_a:
    print("\n*** CHECK A' FAILED: the LEFT (2,0) landing component after minting via dot2 ***")
    print("*** cannot reach ANY of dot0's kick-approach cells. Full census below.          ***")
    for bn in ("box0", "box1", "box3"):
        bb = BOXES[bn]
        cells = [(x, y) for x in range(bb[0], bb[2] + 1) for y in range(bb[1], bb[3] + 1)]
        reach = [c for c in cells if c in seen_a]
        print(f"  {bn} interior cells reachable (any phase): {reach}")
    fail("dot0's kick-approach region unreachable from the post-mint-via-dot2 landing (CHECK A') -- "
         "the ticket-construction is exhausted across all measurement-consistent assignments", cur_o)

record("2A-check-A-passed", cur_o)

# ============================================================================
# CHECK B' / LEG 3: chain-kick dot0 north from (13,44) past the internal
# band (y=24-29). Geometry unmeasured at this x -- try all 4 directions,
# chase up to 6 real kicks per direction (2 kicks were needed for dot2 at
# its x; dot0 sits at a different x, so this is a genuinely new reading).
# ============================================================================
print(f"\n=== CHECK B': does dot0 chain past the internal band y={BAND_Y}, any direction? ===")
dx0 = min(c[0] for c in d0_now); dx1 = max(c[0] for c in d0_now)
dy0 = min(c[1] for c in d0_now); dy1 = max(c[1] for c in d0_now)
attempts = []
crossed = False
KICK_ARMS = (
    ("south-approach-press-north", dx0 - 2, dx1 + 2, dy1 + 3, dy1 + 8, 1),
    ("north-approach-press-south", dx0 - 2, dx1 + 2, dy0 - 8, dy0 - 3, 2),
    ("west-approach-press-east", dx0 - 8, dx0 - 3, dy0 - 2, dy1 + 2, 4),
    ("east-approach-press-west", dx1 + 3, dx1 + 8, dy0 - 2, dy1 + 2, 3),
)
for label, ax0, ax1, ay0, ay1, dirv in KICK_ARMS:
    fresh_e = copy.deepcopy(cur_e)  # each of the 4 arms is an INDEPENDENT trial from the
    p, _, _ = bfs_route(copy.deepcopy(fresh_e), cur_o, region(ax0, ax1, ay0, ay1),
                         avoid=d1_now, max_nodes=1500)  # same starting state, not chained
    if p is None:
        attempts.append((label, "NO ROUTE TO APPROACH"))
        continue
    trial_e, trial_o = commit(fresh_e, cur_o, p, f"3-approach-dot0-{label}")
    moved_total = 0
    d0_after = [c for c in dot_cells(grid(trial_o)) if c not in d1_now and c not in d2_now]
    for _ in range(6):
        before = set(dot_cells(grid(trial_o)))
        moved_this = False
        for _try in range(8):
            trial_e, trial_o = step_log(trial_e, trial_o, v=dirv, tag=f"3-CHAIN-KICK-dot0-{label}")
            after = set(dot_cells(grid(trial_o)))
            if after - before:
                moved_this = True
                break
        if not moved_this:
            break
        moved_total += 1
        d0_after = [c for c in dot_cells(grid(trial_o)) if c not in d1_now and c not in d2_now]
        if d0_after and all(c[1] < BAND_Y[0] for c in d0_after):
            break
    moved = moved_total > 0
    this_crossed = moved and d0_after and all(c[1] < BAND_Y[0] for c in d0_after)
    attempts.append((label, f"moved={moved} kicks={moved_total} d0_after={d0_after} "
                             f"crossed_band={this_crossed}"))
    if this_crossed and not crossed:
        cur_e, cur_o = trial_e, trial_o
        d0_now = d0_after
        crossed = True

print("CHECK B' attempts (all 4 kick directions):")
for label, result in attempts:
    print(f"  {label}: {result}")

if not crossed:
    print("\n*** CHECK B': dot0 did not chain past the internal band in any of 4 directions. ***")
    record("3-chain-kick-FAILED", cur_o)
    seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
    seen = {c for c in seen if c is not None}
    print(f"\ncensus of what IS reachable from this state: {nodes} nodes expanded, "
          f"{len(seen)} distinct positions ({'EXHAUSTED' if nodes < 15000 else 'CAP HIT'})")
    if seen:
        xs = [c[0] for c in seen]; ys = [c[1] for c in seen]
        print(f"reachable bbox: x=[{min(xs)},{max(xs)}] y=[{min(ys)},{max(ys)}]")
    for bn in ("box0", "box1", "box3"):
        bb = BOXES[bn]
        cells = [(x, y) for x in range(bb[0], bb[2] + 1) for y in range(bb[1], bb[3] + 1)]
        reach = [c for c in cells if c in seen]
        print(f"  {bn} interior cells reachable (any phase): {reach}")
    fail("dot0 did not chain past the internal band in any of 4 kick directions (CHECK B') -- "
         "the ticket-construction is exhausted across all measurement-consistent assignments", cur_o)

record("3-dot0-chained", cur_o)
print(f"\n3 done: dot0 now at {d0_now}, piece at {piece_xy(grid(cur_o))} "
      f"phase={phase(piece_xy(grid(cur_o)))}")

# ============================================================================
# LEG 4: CHECK C' -- box0 interior reachable at phase (2,0)-lattice? Fill
# via dot0. Expected piece afterward -> dot0's north cell, phase (1,2).
# ============================================================================
piece_now = piece_xy(grid(cur_o))
ok_c, reach_c, nodes_c = reach_check(cur_e, cur_o, "CHECK C'", "box0", (2, 0), piece_now)
if not ok_c:
    fail("box0 phase-(2,0) interior not reachable after dot0's chain (CHECK C') -- "
         "LINE_COMPLETE_NO_WIN at this config (ticket in box2, piece here)", cur_o)

target_cell = reach_c[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, lambda pp: pp == target_cell, max_nodes=15000)
if p is None:
    fail(f"CHECK C' said {target_cell} reachable but bounded bfs_route could not confirm it", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "4-walk-to-box0-cell")
record("4-standing-in-box0", cur_o)
print(f"\n4 done: standing at {piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))} "
      f"(target {target_cell})")

d0_current = [c for c in dot_cells(grid(cur_o)) if c not in d1_now and c not in d2_now]
if not d0_current:
    fail(f"dot0 not found before box0 fill -- dots={dot_cells(grid(cur_o))}", cur_o)
tx, ty = d0_current[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="4-FILL-box0-dot0")
record("4-box0-filled", cur_o)
piece_after_box0 = piece_xy(grid(cur_o))
phase_after_box0 = phase(piece_after_box0)
print(f"\n4 done: box0 filled, piece at {piece_after_box0} phase={phase_after_box0} "
      f"(expected dot0's old cell {(tx, ty)} phase (1,2))")
if not any(in_box(c, BOXES["box0"]) for c in extra4(cur_o)):
    fail(f"box0 not filled after dot0 click -- extra4={extra4(cur_o)}", cur_o)

# ============================================================================
# LEG 5: CHECK D' -- box1 interior reachable at phase (1,2)? (y11's proven
# leg shape -- the whole reason for this redesign.) Walk in.
# ============================================================================
ok_d, reach_d, nodes_d = reach_check(cur_e, cur_o, "CHECK D'", "box1", (1, 2), piece_after_box0)
if not ok_d:
    fail("box1 phase-(1,2) interior not reachable after box0 fill (CHECK D') -- "
         "LINE_COMPLETE_NO_WIN at this config (box0 filled, ticket in box2, piece here) -- "
         "the ticket-construction is exhausted across all measurement-consistent assignments", cur_o)

target_cell = reach_d[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, lambda pp: pp == target_cell, max_nodes=15000)
if p is None:
    fail(f"CHECK D' said {target_cell} reachable but bounded bfs_route could not confirm it", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "5-walk-to-box1-cell")
record("5-standing-in-box1", cur_o)
box1_stand_cell = piece_xy(grid(cur_o))
print(f"\n5 done: standing at {box1_stand_cell} phase={phase(box1_stand_cell)} (target {target_cell})")

# ============================================================================
# LEG 6: fill box1 FROM AFAR -- click dot1 (still at entry, RIGHT, wholly
# untouched; no proximity requirement) while standing inside box1.
# ============================================================================
d1_current = [c for c in dot_cells(grid(cur_o)) if c not in d0_now and c not in d2_now]
if not d1_current:
    fail(f"dot1 not found before box1-from-afar fill -- dots={dot_cells(grid(cur_o))}", cur_o)
DOT1_CLICK_CELL = d1_current[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=DOT1_CLICK_CELL, tag="6-FILL-box1-dot1-AFAR")
record("6-box1-filled", cur_o)
piece_after_box1 = piece_xy(grid(cur_o))
phase_after_box1 = phase(piece_after_box1)
print(f"\n6 done: box1 filled, piece at {piece_after_box1} phase={phase_after_box1} "
      f"(expected dot1's canonical cell ~(41,34) phase (0,1) RIGHT)")
if not any(in_box(c, BOXES["box1"]) for c in extra4(cur_o)):
    fail(f"box1 not filled after afar-click -- extra4={extra4(cur_o)}", cur_o)

# ============================================================================
# LEG 7: CHECK E' -- box3 interior reachable at phase (0,1)? Walk in.
# ============================================================================
ok_e, reach_e, nodes_e = reach_check(cur_e, cur_o, "CHECK E'", "box3", (0, 1), piece_after_box1)
if not ok_e:
    fail("box3 phase-(0,1) interior not reachable after box1-from-afar fill (CHECK E') -- "
         "LINE_COMPLETE_NO_WIN at this config (box0+box1 filled, ticket in box2, piece here) -- "
         "the ticket-construction is exhausted across all measurement-consistent assignments", cur_o)

target_cell = reach_e[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, lambda pp: pp == target_cell, max_nodes=15000)
if p is None:
    fail(f"CHECK E' said {target_cell} reachable but bounded bfs_route could not confirm it", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "7-walk-to-box3-cell")
record("7-standing-in-box3", cur_o)
print(f"\n7 done: standing at {piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))} "
      f"(target {target_cell})")

# ============================================================================
# LEG 8: FINAL -- click the box2 ticket from inside box3.
# ============================================================================
if box2_ticket not in extra4(cur_o):
    fail(f"box2 ticket marker gone before final click -- extra4={extra4(cur_o)}", cur_o)
cur_e, cur_o = step_log(cur_e, cur_o, click=box2_ticket, tag="8-FINAL-click-box2-ticket")
record("8-final", cur_o)

final_piece = piece_xy(grid(cur_o))
final_extra4 = extra4(cur_o)
print("\n=== FINAL ===")
print(f"levels_completed={cur_o.levels_completed} state={cur_o.state}")
print(f"final piece: {final_piece} phase={phase(final_piece)} (predicted: inside box2, {box2_ticket})")
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
print(f"total actions: {ACT_N[0]}")
