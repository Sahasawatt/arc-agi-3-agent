"""ka59 t1 (2026-08-17) -- drive the CORRECTED 7-step ticket line from
breadth-recon.md's "2026-08-17 -- ka59 L2: ticket line BROKE AT LEG 1 --
and the break narrows the construction to ONE order" tail section.

Harness reused verbatim from ka59_w1.py (grid/piece_xy/dot_cells/marker_cells/
phase/bfs_route/exhaustive/region/BOXES/reach_l2/extra4/record/fail/step_log/
commit/in_box). New: `components()` for identifying dot0 vs dot2 after the
compound sweep by cluster size (not by hand-picked coordinates).

Corrected line (recon tail, verbatim):
  1. Kick dot0 west (19,44) + dot2 west (17,47) -- ONE compound-sweep press
     near dot2 relocates both. dot1 stays at entry (41,34) RIGHT.
  2. Fill box3: stand in box3 (RIGHT), click dot1 -> box3 filled, piece to
     dot1's cell (0,1). No crossing.
  3. CHECK A: walk to a box2 interior cell on the (0,1) lattice. MINT: click
     dot0 (west) -> ticket lands in box2, piece lands (19,44)-ish, phase
     (1,2) -- the mint IS the crossing.
  4. CHECK B: chain-kick dot2 north past the internal band (y=24-29),
     approached from the south.
  5. CHECK C: reach a box0 (1,2) interior cell, click dot2 (north) -> box0
     filled, piece to dot2's cell north of the band, phase (2,0).
  6. CHECK D: reach a box1 interior cell on the (2,0) lattice.
  7. FINAL: from box1, click the TICKET (planted at leg 3) -> box1 filled by
     the relocating ticket, piece delivered into box2. Read levels_completed.

    ./.venv/Scripts/python.exe ka59_t1.py > results/ka59-corrected-ticket-run.txt
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
    """Connected components at Chebyshev distance <= adj (touching-blob
    definition -- distinguishes two nearby-but-separate dot objects from one
    contiguous one)."""
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
    just drains the queue. Returns (reachable_set, nodes_expanded)."""
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
BAND_Y = (24, 29)  # internal band, per brief
ACT_N = [0]
LEGS = []  # (leg, piece, phase, extra4, levels_completed)


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
    return e, o2


def commit(e, o, path, tag):
    for v in path:
        e, o = step_log(e, o, v=v, tag=tag)
    return e, o


def in_box(c, bb):
    return bb[0] <= c[0] <= bb[2] and bb[1] <= c[1] <= bb[3]


def reach_check(cur_e, cur_o, tag, box_name, phase_filter, ref_p_for_ctrl):
    """CHECK A-D pattern: exhaustive real BFS + positive control, filtered to
    a named box's interior at a required phase."""
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


cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: piece={piece_xy(grid(cur_o))} dot0={D0} dot1={D1} dot2={D2}")
record("0-entry", cur_o)

# ============================================================================
# LEG 1: compound sweep -- approach dot2 from the east on a route that avoids
# dot0's own cells (r24/r25's recipe), press west once/a few times, and
# expect BOTH dot0 and dot2 to relocate together.
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
print(f"1 done: dot0 now at {d0_now} (expected ~(19,44)), dot2 now at {d2_now} (expected ~(17,47))")
print(f"  dot0 past moat (x<30): {all(c[0] < 30 for c in d0_now)}; "
      f"dot2 past moat (x<30): {all(c[0] < 30 for c in d2_now)}")
DOT0_TICKET_CELL = d0_now[0]

# ============================================================================
# LEG 2: fill box3 via dot1 (untouched, still at its entry cells).
# ============================================================================
b = BOXES["box3"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]),
                     avoid=d0_now + d2_now, max_nodes=3000)
if p is None:
    fail("no route to box3", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "2-to-box3")
d1_now = [c for c in dot_cells(grid(cur_o)) if c not in d0_now and c not in d2_now]
if not d1_now:
    fail(f"dot1 not found at box3 approach -- dots={dot_cells(grid(cur_o))}", cur_o)
tx, ty = d1_now[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="2-FILL-box3-dot1")
record("2-box3-filled", cur_o)
piece_after_box3 = piece_xy(grid(cur_o))
phase_after_box3 = phase(piece_after_box3)
print(f"\n2 done: box3 filled, piece at {piece_after_box3} phase={phase_after_box3} "
      f"(expected ~(41,34) phase (0,1))")

# ============================================================================
# LEG 3: CHECK A -- box2 interior reachable at piece's current phase?
# ============================================================================
ok_a, reach_a, nodes_a = reach_check(cur_e, cur_o, "CHECK A", "box2", phase_after_box3,
                                      piece_after_box3)
if not ok_a:
    print("\n*** CHECK A FAILED. Fallback (i) per brief: re-fill box3 from a different stand ***")
    print("*** cell -- but the post-click landing phase is FIXED by dot1's own cell (0,1),  ***")
    print("*** independent of the stand cell used, so this fallback is structurally inert.  ***")
    print("*** Recording BROKE_AT_LEG_3 with full census.                                    ***")
    fail("box2 not reachable at piece's post-box3-fill phase (check A)", cur_o)

target_cell = reach_a[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, lambda pp: pp == target_cell, max_nodes=15000)
if p is None:
    fail(f"CHECK A said {target_cell} reachable but bounded bfs_route (15000) could not confirm it",
         cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "3-walk-to-box2-cell")
box2_stand_cell = piece_xy(grid(cur_o))
print(f"\n3 done: standing at {box2_stand_cell} phase={phase(box2_stand_cell)} (target {target_cell})")
record("3-standing-in-box2", cur_o)

cur_e, cur_o = step_log(cur_e, cur_o, click=DOT0_TICKET_CELL, tag="3-MINT-click-dot0")
record("3-minted-box2-ticket", cur_o)
box2_ticket = box2_stand_cell
piece_after_mint = piece_xy(grid(cur_o))
phase_after_mint = phase(piece_after_mint)
print(f"\n3-MINT done: piece landed at {piece_after_mint} phase={phase_after_mint} "
      f"(expected ~(19,44) phase (1,2)); box2_ticket at {box2_ticket}")
if box2_ticket not in extra4(cur_o):
    fail(f"box2 ticket marker not found at {box2_ticket} after mint -- extra4={extra4(cur_o)}", cur_o)

# ============================================================================
# LEG 4: CHECK B -- chain-kick dot2 north past the internal band. Approach
# from the south (dot1's chained analogue: (17,34)->(17,19) south-approached).
# ============================================================================
print(f"\n=== CHECK B: does dot2 chain north past the internal band y={BAND_Y}? ===")
d2_before = list(d2_now)
attempts = []
for label, ax0, ax1, ay0, ay1, dirv in (
    ("south-approach-press-north", d2_now[0][0] - 2, d2_now[-1][0] + 2, d2_now[-1][1] + 3, d2_now[-1][1] + 8, 1),
):
    p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(ax0, ax1, ay0, ay1),
                         avoid=d1_now, max_nodes=1500)
    if p is None:
        attempts.append((label, "NO ROUTE TO APPROACH"))
        continue
    trial_e, trial_o = commit(cur_e, cur_o, p, f"4-approach-dot2-{label}")
    moved = False
    for _ in range(8):
        before = set(dot_cells(grid(trial_o)))
        trial_e, trial_o = step_log(trial_e, trial_o, v=dirv, tag=f"4-CHAIN-KICK-dot2-{label}")
        after = set(dot_cells(grid(trial_o)))
        if after - before:
            moved = True
            break
    d2_after = [c for c in dot_cells(grid(trial_o)) if c not in d1_now and c not in d0_now]
    crossed = moved and d2_after and all(c[1] < BAND_Y[0] for c in d2_after)
    attempts.append((label, f"moved={moved} d2_after={d2_after} crossed_band={crossed}"))
    if crossed:
        cur_e, cur_o = trial_e, trial_o
        d2_now = d2_after
        break
else:
    crossed = False

print("CHECK B attempts:")
for label, result in attempts:
    print(f"  {label}: {result}")

if not crossed:
    print("\n*** CHECK B: dot2 did not chain past the internal band on south-approach. ***")
    print("*** Fallback (ii) per brief (role-swap: mint via dot2, fill box0 via dot0) ***")
    print("*** is a full re-derivation from LEG 1 and is NOT attempted in this run --  ***")
    print("*** recording BROKE_AT_LEG_4 with full census instead.                     ***")
    record("4-chain-kick-FAILED", cur_o)
    fail("dot2 did not chain north past the internal band (check B) -- see attempts above", cur_o)

record("4-dot2-chained-north", cur_o)
print(f"\n4 done: dot2 chained north to {d2_now}, piece at {piece_xy(grid(cur_o))} "
      f"phase={phase(piece_xy(grid(cur_o)))} (expected still (1,2), kicks preserve phase)")

# ============================================================================
# LEG 5: CHECK C -- box0 interior reachable at phase (1,2)? Then fill via dot2.
# ============================================================================
piece_now = piece_xy(grid(cur_o))
ok_c, reach_c, nodes_c = reach_check(cur_e, cur_o, "CHECK C", "box0", (1, 2), piece_now)
if not ok_c:
    fail("box0 phase-(1,2) interior not reachable after dot2's north chain (check C)", cur_o)

target_cell = reach_c[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, lambda pp: pp == target_cell, max_nodes=15000)
if p is None:
    fail(f"CHECK C said {target_cell} reachable but bounded bfs_route could not confirm it", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "5-walk-to-box0-cell")
record("5-standing-in-box0", cur_o)
print(f"\n5 done: standing at {piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))} "
      f"(target {target_cell})")

d2_current = [c for c in dot_cells(grid(cur_o)) if c not in d1_now and c not in d0_now]
if not d2_current:
    fail(f"dot2 not found before box0 fill -- dots={dot_cells(grid(cur_o))}", cur_o)
tx, ty = d2_current[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="5-FILL-box0-dot2")
record("5-box0-filled", cur_o)
piece_after_box0 = piece_xy(grid(cur_o))
phase_after_box0 = phase(piece_after_box0)
print(f"\n5 done: box0 filled, piece at {piece_after_box0} phase={phase_after_box0} "
      f"(expected dot2's old cell {(tx, ty)} phase (2,0))")

# ============================================================================
# LEG 6: CHECK D -- box1 interior reachable at phase (2,0)?
# ============================================================================
ok_d, reach_d, nodes_d = reach_check(cur_e, cur_o, "CHECK D", "box1", (2, 0), piece_after_box0)
if not ok_d:
    fail("box1 phase-(2,0) interior not reachable after box0 fill (check D) -- "
         "LINE_COMPLETE_NO_WIN at this config (box3+box0 filled, ticket in box2, piece here)", cur_o)

target_cell = reach_d[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, lambda pp: pp == target_cell, max_nodes=15000)
if p is None:
    fail(f"CHECK D said {target_cell} reachable but bounded bfs_route could not confirm it", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "6-walk-to-box1-cell")
record("6-standing-in-box1", cur_o)
print(f"\n6 done: standing at {piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))} "
      f"(target {target_cell})")

# ============================================================================
# LEG 7: FINAL -- click the box2 ticket from inside box1.
# ============================================================================
if box2_ticket not in extra4(cur_o):
    fail(f"box2 ticket marker gone before final click -- extra4={extra4(cur_o)}", cur_o)
cur_e, cur_o = step_log(cur_e, cur_o, click=box2_ticket, tag="7-FINAL-click-box2-ticket")
record("7-final", cur_o)

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
n_filled = sum(1 for k in ("box1", "box3", "box0") if filled[k])

dump_legs()

print(f"\n=== VERDICT: {n_filled} of {{box1,box3,box0}} filled, "
      f"piece-in-box2={piece_in_box2}, levels_completed={cur_o.levels_completed} ===")
print(f"total actions: {ACT_N[0]}")
