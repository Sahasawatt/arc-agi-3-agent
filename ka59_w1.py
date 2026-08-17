"""ka59 w1 (2026-08-17) -- drive the mint-via-dot0 ticket line from
breadth-recon.md's "2026-08-17 -- ka59 L2: ARBITRARY PHASE DELIVERY IS
REAL" tail section. Harness reused verbatim from ka59_z1/z2/z3.py.

Line (recon's own spelling):
  1. Pre-kick dot0 west then chain north to (19,20) (y11's proven kicks).
     Pre-kick dot2 west past the moat (compound sweep).
  2. Fill box3: enter box3, click dot1 at entry -> box3 filled, piece to
     dot1's cell (RIGHT).
  3. Walk to a box2 interior cell AT THE PIECE'S CURRENT PHASE (real BFS,
     not the static map -- reachability check A, with positive control).
     MINT: click dot0 (at 19,20) -> ticket lands in box2, piece lands at
     (19,20) phase (1,2) -- the mint click IS the moat crossing.
  4. Walk into box1 (y11's proven leg). Fill box1: click dot2 (wherever
     kicked) -> box1 filled by dot2's marker, piece to dot2's cell.
  5. Reachability check B (positive control): any box0 interior (2,0) cell
     reachable? Walk in if so.
  6. FINAL: click the box2 ticket marker from inside box0 -> box0 filled
     by the relocating ticket, piece delivered INTO box2. Read
     levels_completed.

If check A fails: reorder per the recon's own fallback -- do the box2 walk
+ mint BEFORE the box3 fill (mint before box3 fill; the box3 fill click
then sends the piece to dot1's cell as usual, and the rest is unchanged
since dot0's marker/ticket persists in box2 regardless of when it was
planted).

    ./.venv/Scripts/python.exe ka59_w1.py > results/ka59-ticket-line-run.txt
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
ACT_N = [0]
LEGS = []  # (leg, action_tag, piece, phase, extra4, levels_completed)


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


def fail(msg, o):
    print(f"\n  LINE BROKE: {msg}")
    print(f"  FINAL: levels_completed={o.levels_completed} state={o.state}")
    print(f"  final extra4 census: {extra4(o)}")
    print(f"  final piece: {piece_xy(grid(o))} phase={phase(piece_xy(grid(o)))}")
    print("\n=== LEG TABLE ===")
    for leg, p, ph, e4, lc in LEGS:
        print(f"  {leg:32s} piece={p} phase={ph} extra4={e4} levels_completed={lc}")
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
        sys.exit(0)
    return e, o2


def commit(e, o, path, tag):
    for v in path:
        e, o = step_log(e, o, v=v, tag=tag)
    return e, o


def in_box(c, bb):
    return bb[0] <= c[0] <= bb[2] and bb[1] <= c[1] <= bb[3]


cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: piece={piece_xy(grid(cur_o))} dot0={D0} dot1={D1} dot2={D2}")
record("0-entry", cur_o)

# ============================================================================
# STEP 1a/1b: kick dot0 west then chain north to (19,20) -- y11 legs A + D
# verbatim, run back-to-back (dot1 untouched throughout, so filtering dot0's
# post-kick cells is "not in D1 and not in D2").
# ============================================================================
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(35, 39, 42, 46), avoid=D1 + D2)
if p is None:
    fail("no route to dot0's approach", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "1a-approach-dot0")
for _ in range(8):
    before = set(dot_cells(grid(cur_o)))
    cur_e, cur_o = step_log(cur_e, cur_o, v=3, tag="1a-kick-dot0-west")
    if set(dot_cells(grid(cur_o))) - before:
        break
record("1a-dot0-kicked-west", cur_o)

d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D1 and c not in D2]
if not d0_now:
    fail(f"dot0 not found after west kick -- dots={dot_cells(grid(cur_o))}", cur_o)
tx, ty = d0_now[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(tx - 1, tx + 4, ty + 3, ty + 8),
                     avoid=d0_now, max_nodes=1500)
if p is None:
    fail("no approach to dot0's crossed position for the chain kick", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "1b-approach-chain")
for _ in range(8):
    before = set(dot_cells(grid(cur_o)))
    cur_e, cur_o = step_log(cur_e, cur_o, v=1, tag="1b-chain-kick-dot0-north")
    if set(dot_cells(grid(cur_o))) - before:
        break
record("1b-dot0-chained-north", cur_o)

d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D1 and c not in D2]
if not d0_now:
    fail(f"dot0 lost after chain kick -- dots={dot_cells(grid(cur_o))}", cur_o)
DOT0_TICKET_CELL = d0_now[0]
print(f"\n1a/1b done: dot0 now at {DOT0_TICKET_CELL} phase={phase(DOT0_TICKET_CELL)} "
      f"(expected (19,20) phase (1,2))")

# ============================================================================
# STEP 1c: kick dot2 west past the moat (compound sweep, s3's
# east-approach/press-west recipe on dot2's ORIGINAL bbox).
# ============================================================================
x0 = min(c[0] for c in D2)
x1 = max(c[0] for c in D2)
y0 = min(c[1] for c in D2)
y1 = max(c[1] for c in D2)
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(x1 + 2, x1 + 7, y0 - 1, y1 + 1),
                     avoid=D1 + d0_now, max_nodes=1500)
if p is None:
    fail("no route to dot2's east approach", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "1c-approach-dot2")
for _ in range(4):
    before = set(dot_cells(grid(cur_o)))
    cur_e, cur_o = step_log(cur_e, cur_o, v=3, tag="1c-kick-dot2-west")
    after = set(dot_cells(grid(cur_o)))
    if after - before:
        break
record("1c-dot2-kicked-west", cur_o)

d2_now = [c for c in dot_cells(grid(cur_o)) if c not in D1 and c not in d0_now]
if not d2_now:
    fail(f"dot2 lost after west kick -- dots={dot_cells(grid(cur_o))}", cur_o)
print(f"1c done: dot2 now at {d2_now} (expected relocated past the moat, x well below entry's 44+)")
past_moat = all(c[0] < 30 for c in d2_now)
print(f"  dot2 past the moat (all x<30): {past_moat}")

# also re-verify dot0 was NOT disturbed by the dot2 kick (compound sweep
# risk once dot0 has already moved away)
d0_check = [c for c in dot_cells(grid(cur_o)) if c not in D1 and c not in d2_now]
print(f"  dot0 position after dot2's kick: {d0_check} (expected unchanged: {d0_now})")
if sorted(d0_check) != sorted(d0_now):
    print("  *** WARNING: dot0 WAS disturbed by the dot2 kick -- recomputing ticket cell ***")
    DOT0_TICKET_CELL = d0_check[0] if d0_check else DOT0_TICKET_CELL

# ============================================================================
# STEP 2: fill box3 via dot1 (dot1 untouched, still at its entry cell)
# ============================================================================
b = BOXES["box3"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]),
                     avoid=d0_check + d2_now, max_nodes=3000)
if p is None:
    fail("no route to box3", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "2-to-box3")
d1_now = [c for c in dot_cells(grid(cur_o)) if c not in d0_check and c not in d2_now]
if not d1_now:
    fail(f"dot1 not found at box3 -- dots={dot_cells(grid(cur_o))}", cur_o)
tx, ty = d1_now[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="2-FILL-box3-dot1")
record("2-box3-filled", cur_o)
piece_after_box3 = piece_xy(grid(cur_o))
phase_after_box3 = phase(piece_after_box3)
print(f"\n2 done: box3 filled, piece at {piece_after_box3} phase={phase_after_box3}")

# ============================================================================
# STEP 3: reachability check A -- any box2 interior cell reachable AT THE
# PIECE'S CURRENT PHASE? Exhaustive real BFS, with a positive control.
# ============================================================================
print("\n=== REACHABILITY CHECK A: box2 interior at piece's current phase ===")
seen_a, nodes_a = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
print(f"exhaustive BFS: expanded {nodes_a} nodes, {len(seen_a)} distinct reachable positions "
      f"({'EXHAUSTED' if nodes_a < 15000 else 'CAP HIT, not exhausted'})")
b2 = BOXES["box2"]
box2_cells = [(x, y) for x in range(b2[0], b2[2] + 1) for y in range(b2[1], b2[3] + 1)]
box2_cells_at_phase = [c for c in box2_cells if phase(c) == phase_after_box3]
reachable_box2 = [c for c in box2_cells if c in seen_a]
reachable_box2_at_phase = [c for c in box2_cells_at_phase if c in seen_a]
print(f"box2 interior cells: {box2_cells}")
print(f"box2 cells at piece's phase {phase_after_box3}: {box2_cells_at_phase}")
print(f"box2 cells reachable (any phase): {reachable_box2}")
print(f"box2 cells reachable at piece's phase: {reachable_box2_at_phase}")

# positive control: take one real action from cur_o, confirm the resulting
# position is in the reachable set (proves the search + tracking actually
# work on THIS state, not just returns a trivial answer)
ctrl_e = copy.deepcopy(cur_e)
ctrl_o = None
for v in (4, 2, 1, 3):
    ctrl_o = ctrl_e.step(A[v])
    if ctrl_o is not None and ctrl_o.state != GameState.GAME_OVER:
        ctrl_p = piece_xy(grid(ctrl_o))
        if ctrl_p is not None and ctrl_p != piece_after_box3:
            break
    ctrl_e = copy.deepcopy(cur_e)
else:
    ctrl_p = None
ctrl_pass = ctrl_p is not None and ctrl_p in seen_a
print(f"positive control: one real press from this state landed at {ctrl_p}, "
      f"in reachable set: {ctrl_pass} ({'PASS' if ctrl_pass else 'FAIL -- BFS INSTRUMENT BROKEN'})")
if not ctrl_pass:
    fail("reachability-check-A positive control FAILED -- the BFS instrument itself is broken, "
         "cannot trust the negative reading", cur_o)

CHECK_A_OK = len(reachable_box2_at_phase) > 0
print(f"\nCHECK A VERDICT: {'REACHABLE' if CHECK_A_OK else 'NOT REACHABLE'} "
      f"({len(reachable_box2_at_phase)} of {len(box2_cells_at_phase)} phase-matched box2 cells)")

if not CHECK_A_OK:
    print("\n*** CHECK A FAILED -- box2 unreachable at piece's post-box3-fill phase. ***")
    print("*** Documented reorder not attempted in this run: box3 is already filled and its ***")
    print("*** click is spent, so reordering now would require a full re-drive from L2 entry. ***")
    print("*** Recording as BROKE_AT_LEG_3 with full census; a reorder needs a fresh script. ***")
    fail("box2 not reachable at current phase after box3 fill (check A) -- see census above", cur_o)

# ============================================================================
# STEP 3 continued: walk to the reachable box2 interior cell, then MINT by
# clicking dot0's ticket cell (remote click, no proximity needed).
# ============================================================================
target_cell = reachable_box2_at_phase[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, lambda pp: pp == target_cell, max_nodes=15000)
if p is None:
    fail(f"BFS said {target_cell} was reachable but bfs_route (bounded, 15000) could not find it "
         f"-- bounded/unbounded search disagreement, needs investigation", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "3-walk-to-box2-cell")
box2_stand_cell = piece_xy(grid(cur_o))
print(f"\n3 done: standing at {box2_stand_cell} phase={phase(box2_stand_cell)} "
      f"(target was {target_cell})")
record("3-standing-in-box2", cur_o)

cur_e, cur_o = step_log(cur_e, cur_o, click=DOT0_TICKET_CELL, tag="3-MINT-click-dot0")
record("3-minted-box2-ticket", cur_o)
box2_ticket = box2_stand_cell
piece_after_mint = piece_xy(grid(cur_o))
print(f"\n3-MINT done: piece landed at {piece_after_mint} phase={phase(piece_after_mint)} "
      f"(expected {DOT0_TICKET_CELL} phase (1,2)); box2_ticket at {box2_ticket}")
if box2_ticket not in extra4(cur_o):
    fail(f"box2 ticket marker not found at {box2_ticket} after mint -- extra4={extra4(cur_o)}", cur_o)

# ============================================================================
# STEP 4: walk into box1, fill via clicking dot2 (wherever it was kicked)
# ============================================================================
b = BOXES["box1"]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]), max_nodes=3000)
if p is None:
    pp = piece_xy(grid(cur_o))
    fail(f"no route to box1 from {pp} phase={phase(pp)}", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "4-to-box1")
record("4-standing-in-box1", cur_o)

d2_current = [c for c in dot_cells(grid(cur_o)) if c not in D1]
if not d2_current:
    fail(f"dot2 not found before box1 fill -- dots={dot_cells(grid(cur_o))}", cur_o)
tx, ty = d2_current[0]
cur_e, cur_o = step_log(cur_e, cur_o, click=(tx, ty), tag="4-FILL-box1-via-dot2")
record("4-box1-filled", cur_o)
piece_after_box1 = piece_xy(grid(cur_o))
phase_after_box1 = phase(piece_after_box1)
print(f"\n4 done: box1 filled, piece at {piece_after_box1} phase={phase_after_box1} "
      f"(expected dot2's old cell {(tx, ty)} phase (2,0))")

# ============================================================================
# STEP 5: reachability check B -- any box0 interior (2,0) cell reachable?
# ============================================================================
print("\n=== REACHABILITY CHECK B: box0 interior at phase (2,0) ===")
seen_b, nodes_b = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
print(f"exhaustive BFS: expanded {nodes_b} nodes, {len(seen_b)} distinct reachable positions "
      f"({'EXHAUSTED' if nodes_b < 15000 else 'CAP HIT, not exhausted'})")
b0 = BOXES["box0"]
box0_cells = [(x, y) for x in range(b0[0], b0[2] + 1) for y in range(b0[1], b0[3] + 1)]
box0_cells_20 = [c for c in box0_cells if phase(c) == (2, 0)]
reachable_box0 = [c for c in box0_cells if c in seen_b]
reachable_box0_20 = [c for c in box0_cells_20 if c in seen_b]
print(f"box0 interior cells at phase (2,0): {box0_cells_20}")
print(f"box0 cells reachable (any phase): {reachable_box0}")
print(f"box0 cells reachable at phase (2,0): {reachable_box0_20}")

ctrl_e = copy.deepcopy(cur_e)
ctrl_o = None
for v in (4, 2, 1, 3):
    ctrl_o = ctrl_e.step(A[v])
    if ctrl_o is not None and ctrl_o.state != GameState.GAME_OVER:
        ctrl_p = piece_xy(grid(ctrl_o))
        if ctrl_p is not None and ctrl_p != piece_after_box1:
            break
    ctrl_e = copy.deepcopy(cur_e)
else:
    ctrl_p = None
ctrl_pass_b = ctrl_p is not None and ctrl_p in seen_b
print(f"positive control: one real press landed at {ctrl_p}, in reachable set: {ctrl_pass_b} "
      f"({'PASS' if ctrl_pass_b else 'FAIL -- BFS INSTRUMENT BROKEN'})")
if not ctrl_pass_b:
    fail("reachability-check-B positive control FAILED -- BFS instrument broken", cur_o)

CHECK_B_OK = len(reachable_box0_20) > 0
print(f"\nCHECK B VERDICT: {'REACHABLE' if CHECK_B_OK else 'NOT REACHABLE'} "
      f"({len(reachable_box0_20)} of {len(box0_cells_20)} phase-(2,0) box0 cells)")

if not CHECK_B_OK:
    fail("box0 phase-(2,0) interior not reachable from post-box1-fill position (check B) -- "
         "see census above; LINE_COMPLETE_NO_WIN at this config", cur_o)

target_cell = reachable_box0_20[0]
p, _, _ = bfs_route(copy.deepcopy(cur_e), cur_o, lambda pp: pp == target_cell, max_nodes=15000)
if p is None:
    fail(f"BFS said {target_cell} reachable but bounded bfs_route could not confirm it", cur_o)
cur_e, cur_o = commit(cur_e, cur_o, p, "5-walk-to-box0-cell")
record("5-standing-in-box0", cur_o)
print(f"\n5 done: standing at {piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))} "
      f"(target was {target_cell})")

# ============================================================================
# STEP 6: FINAL -- click the box2 ticket marker from inside box0
# ============================================================================
if box2_ticket not in extra4(cur_o):
    fail(f"box2 ticket marker gone before final click -- extra4={extra4(cur_o)}", cur_o)
cur_e, cur_o = step_log(cur_e, cur_o, click=box2_ticket, tag="6-FINAL-click-box2-ticket")
record("6-final", cur_o)

final_piece = piece_xy(grid(cur_o))
final_extra4 = extra4(cur_o)
print(f"\n=== FINAL ===")
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

print("\n=== LEG TABLE ===")
for leg, p, ph, e4, lc in LEGS:
    print(f"  {leg:32s} piece={p} phase={ph} extra4={e4} levels_completed={lc}")

print(f"\n=== VERDICT: {n_filled} of {{box1,box3,box0}} filled, "
      f"piece-in-box2={piece_in_box2}, levels_completed={cur_o.levels_completed} ===")
print(f"total actions: {ACT_N[0]}")
