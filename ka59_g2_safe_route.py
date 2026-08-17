"""ka59 g2 (2026-08-17) -- SAFE-ROUTE harness fix + composed line #1, re-driven.

Mission (per results/breadth-recon.md's last two ka59 sections and
results/ka59-guided-search-20260817.md): composed line #1 (kick dot0 west,
kick dot2 west, box3+click dot2 crosses LEFT, chain-kick dot0 north, box0+
click dot0, walk box1, return-click dot1 fills box1 + returns piece RIGHT,
walk box2 directly) has now broken THREE times from the SAME contamination
class: a routed BFS walk brushing adjacent to a live dot/marker and kicking
it silently, before the script's own "kick" phase believes it has started
(settle press, approach-walk x2). This script builds `safe_route` first --
every routed leg is BFS'd with an explicit forbidden zone (8-neighbourhood
+ footprint of every live dot/loose-marker cell not this leg's own kick
target), plus a belt-and-braces per-press assert that aborts the leg loudly,
naming which press moved what, the moment any OTHER protected object's
footprint changes -- then re-drives the composed line with it.

    ./.venv/Scripts/python.exe ka59_g2_safe_route.py > results/ka59-g2-run.txt
"""

import copy
import sys
from collections import deque

import numpy as np

import arc_agi
from arcengine.enums import GameState

import ferry


# ============================================================================
# Harness (reused verbatim from ka59_g1_composed_line.py -- see
# results/ka59-guided-search-20260817.md for provenance).
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


def record(leg, o, note="asserts=PASS (script sys.exit(0)s loudly on any violation)"):
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
# THE HARNESS FIX: safe_route + guarded_step.
#
# safe_route: BFS routing that FORBIDS landing on the 8-neighbourhood+
# footprint of every cell in `protect` (live dots/loose markers this leg has
# no business touching), UNLESS the landing cell satisfies is_target (the
# leg's own destination -- which is how a deliberate kick-approach still
# gets to stand adjacent to ITS OWN target: the caller simply omits that
# object from `protect` in the first place, or includes it and lets
# is_target admit only the exact staging cell(s), whichever is stricter).
#
# guarded_step / safe_walk: belt-and-braces. After EVERY press, diff the
# full live dot+marker cell set against before. Any cell that VANISHED
# (an object moved off it) that is not in this press's own declared
# `target_cells` is a contamination -- abort the leg loudly, print exactly
# which press (act# already printed by step_log) and which cells moved.
# ============================================================================

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
    """Which connected component (by cell-adjacency) sits closest to a
    reference cell cluster -- used to re-identify dot0 vs dot2 by IDENTITY
    after a compound sweep, instead of a fixed x/y geography filter that a
    compound sweep can put either object through."""
    if not comps:
        return []
    rx = sum(c[0] for c in ref_cells) / len(ref_cells)
    ry = sum(c[1] for c in ref_cells) / len(ref_cells)

    def dist(comp):
        cx = sum(c[0] for c in comp) / len(comp)
        cy = sum(c[1] for c in comp) / len(comp)
        return (cx - rx) ** 2 + (cy - ry) ** 2

    return min(comps, key=dist)


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
    """Every live dot + marker cell (colour 5 and colour 4-beyond-frame),
    including settled box fills -- cheap to over-protect since a fill only
    moves via a deliberate halo click, never handled here."""
    return set(dot_cells(grid(o))) | set(extra4(o))


def guarded_step(e, o, tag, v=None, click=None, target_cells=()):
    """One press/click with the belt-and-braces object-position assert."""
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
    """Walk a BFS path one press at a time, asserting after every press."""
    for v in path:
        e, o = guarded_step(e, o, tag, v=v, target_cells=target_cells)
    return e, o


def safe_kick(e, o, v, tag, target_cells_now, max_presses=8):
    """Press `v` up to max_presses times to kick the object currently at
    target_cells_now. Every press is asserted (only that object may vanish
    from its old cell); stops as soon as the target's old cells are gone
    from the live set (it moved)."""
    moved = False
    for i in range(max_presses):
        e, o = guarded_step(e, o, f"{tag}-p{i + 1}", v=v, target_cells=target_cells_now)
        if not (set(target_cells_now) & live_objects(o)):
            moved = True
            break
    return e, o, moved


# ============================================================================
# THE LINE (composed line #1, re-driven with safe_route).
# ============================================================================
cur_e, cur_o = copy.deepcopy(ENV0), OBS0
dots0 = dot_cells(grid(cur_o))
D0 = [c for c in dots0 if 33 <= c[0] <= 35]
D1 = [c for c in dots0 if 40 <= c[0] <= 43]
D2 = [c for c in dots0 if c[0] >= 44]
print(f"L2 entry: piece={piece_xy(grid(cur_o))} dot0={D0} dot1={D1} dot2={D2}")
record("0-entry", cur_o)

# --- 1. kick dot0 west (safe_route to approach; protect dot1+dot2 fully) -----
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(35, 39, 42, 46), protect=D1 + D2)
if p is None:
    fail("leg1: no safe route to dot0's approach (avoiding dot1/dot2 8-nbhd)", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "1-approach-dot0", target_cells=())
d0_now = D0
cur_e, cur_o, moved = safe_kick(cur_e, cur_o, 3, "1-kick-dot0-west", d0_now)
d0_now = [c for c in dot_cells(grid(cur_o)) if c[1] > 40 and c[0] < 30]
print(f"1 done: moved={moved} dot0 now at {sorted(d0_now)} "
      f"(expect (19,44)/(19,45) or (13,44)-family)")
record("1-dot0-kicked", cur_o)
if not moved or not d0_now:
    fail("leg1: dot0 did not kick west cleanly", cur_o)

# --- 2. kick dot2 west from its OWN approach, disturbing nothing -------------
y0d = min(c[1] for c in D2)
y1d = max(c[1] for c in D2)
x1d = max(c[0] for c in D2)
p = None
for lo, hi in ((y0d, y1d), (y0d - 1, y1d + 1), (y0d, y0d), (y1d, y1d)):
    # protect D1 + current dot0 fully, AND protect dot2 itself (so the approach
    # cannot brush it) -- is_target admits only the staging region itself.
    tgt = region(x1d + 2, x1d + 12, lo, hi)
    p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, tgt, protect=D1 + d0_now + D2, max_nodes=3000)
    if p is not None:
        print(f"2: safe approach region y=[{lo},{hi}] SUCCEEDED ({len(p)} steps)")
        break
    print(f"2: safe approach region y=[{lo},{hi}] no route, trying next")
if p is None:
    fail("leg2: no safe route to dot2's east approach (protecting dot0/dot1/dot2 8-nbhd)", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "2-approach-dot2", target_cells=())
d2_before = [c for c in dot_cells(grid(cur_o)) if c not in d0_now and c not in D1]
if not d2_before:
    fail(f"leg2: dot2 not found after safe approach -- dots={dot_cells(grid(cur_o))}", cur_o)
d0_before_kick = d0_now
# The known-good "compound sweep" (mission text: kicking west can sweep dot0+dot2
# TOGETHER -- dot0->(13,44), dot2->(17,47)-family -- and that is documented as
# fine, not contamination). So both objects are declared as legitimate targets
# of this specific kick; anything else moving is still a violation.
cur_e, cur_o, moved = safe_kick(cur_e, cur_o, 3, "2-kick-dot2-west", d2_before + d0_before_kick)
# Re-identify dot0 vs dot2 by IDENTITY (nearest connected component to their
# PRE-kick position), not a fixed x/y geography filter -- a compound sweep
# can land dot2 in the same region the geography filter used to mean "dot0"
# (measured: (17,47)-family also satisfies x<30,y>40, which broke the old
# filter's classification outright).
west_dots = [c for c in dot_cells(grid(cur_o)) if c not in D1]
comps = components(west_dots, adj=1)
if len(comps) >= 2:
    # Documented fact (results/breadth-recon.md, known-good legs): the compound
    # sweep lands dot0 -> (13,44)-family (smaller x) and dot2 -> (17,47)-family
    # (larger x). Nearest-to-old-position is the WRONG discriminator here --
    # measured directly: it picked (17,47) as "dot0" because it happens to sit
    # geometrically closer to dot0's PRE-sweep cell than (13,44) does, which is
    # backwards from the documented identity. Sort by x instead.
    comps_by_x = sorted(comps, key=lambda c: sum(p[0] for p in c) / len(c))
    d0_now, d2_now = comps_by_x[0], comps_by_x[-1]
elif len(comps) == 1:
    # no compound sweep -- only dot2 moved; dot0 stayed at its pre-kick cell.
    d0_now, d2_now = d0_before_kick, comps[0]
else:
    d0_now, d2_now = d0_before_kick, []
went_west = bool(d2_now) and max(c[0] for c in d2_now) < min(c[0] for c in d2_before)
compound = sorted(d0_now) != sorted(d0_before_kick)
print(f"2 done: moved={moved} dot2 before={sorted(d2_before)} after={sorted(d2_now)} "
      f"went_west={went_west} dot0 before={sorted(d0_before_kick)} dot0 after={sorted(d0_now)} "
      f"compound_sweep_fired={compound} (documented-fine if it fired)")
record("2-dot2-kicked", cur_o)
if not moved or not went_west:
    fail(f"leg2: dot2 did not kick WEST cleanly (before={d2_before} after={d2_now})", cur_o)

# --- 3. fill box3 via dot2, cross piece LEFT ---------------------------------
b = BOXES["box3"]
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]),
                      protect=d0_now + D1)
if p is None:
    fail("leg3: no safe route to box3 (protecting dot0/dot1 8-nbhd)", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "3-to-box3", target_cells=())
d2_now = [c for c in dot_cells(grid(cur_o)) if c not in d0_now and c not in D1]
if not d2_now:
    fail(f"leg3: dot2 not found before box3 fill -- dots={dot_cells(grid(cur_o))}", cur_o)
cur_e, cur_o = guarded_step(cur_e, cur_o, "3-FILL-box3-dot2", click=d2_now[0], target_cells=d2_now)
record("3-box3-filled-crossed", cur_o)
piece_after_3 = piece_xy(grid(cur_o))
if not any(in_box(c, b) for c in extra4(cur_o)):
    fail(f"leg3: box3 not filled after dot2 click -- extra4={extra4(cur_o)}", cur_o)
print(f"3 done: box3 filled, piece crossed to {piece_after_3} phase={phase(piece_after_3)}")

# --- 3b. gate check: can we reach dot0's SOUTH approach from here? -----------
# (per mission fallback clause -- probe leg 4's own approach shape now, with a
# real exhaustive census + positive control, before committing to leg 4.)
tx0, ty0 = d0_now[0]
south_region = region(tx0 - 1, tx0 + 4, ty0 + 3, ty0 + 8)
piece_now = piece_xy(grid(cur_o))
print(f"\n3b: piece phase after crossing = {phase(piece_now)} (mission's own line names '(2,0) LEFT' "
      f"as the expected phase for a dot2-vehicle crossing -- differs here because dot2's actual "
      f"crossing cell moved from the compound sweep; recorded, not treated as a wall by itself).")
probe_p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, south_region, protect=D1, max_nodes=1500)
if probe_p is None:
    print("3b: one-shot safe_route probe to dot0's south approach found no path directly -- "
          "running census+control, then giving leg 4's own per-round retry loop its shot anyway "
          "(it recomputes the approach region fresh each round; this probe used a fixed window)")
    ok3b, reach3b, nodes3b = reach_check(cur_e, cur_o, "CHECK-3b", "box0", None, piece_after_3)
    print(f"3b CENSUS: safe_route-to-fixed-south-window={probe_p is not None}, "
          f"box0-interior-reachable-at-all={ok3b} (any phase) nodes={nodes3b}")
    record("3b-south-approach-probe-negative", cur_o,
           note=f"one-shot probe FAILED; box0-reachable-any-phase={ok3b} (see leg 4 for the real test)")
else:
    print(f"3b: safe route to dot0's south approach found directly ({len(probe_p)} steps) -- proceeding")
    record("3b-south-approach-probe-positive", cur_o)

# --- 4. chain-kick dot0 north (y11 leg D shape, safe_route + per-press assert) ---
crossed = False
for round_i in range(4):
    d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D1 and not in_box(c, BOXES["box3"])]
    if not d0_now:
        fail(f"leg4: dot0 lost before chain-kick round {round_i} -- dots={dot_cells(grid(cur_o))}", cur_o)
    tx, ty = d0_now[0]
    if ty < BAND_Y[0]:
        crossed = True
        break
    tgt = region(tx - 1, tx + 4, ty + 3, ty + 8)
    p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, tgt, protect=D1 + [c for c in d0_now if c != (tx, ty)],
                          max_nodes=1500)
    if p is None:
        print(f"4: round {round_i} no safe approach route -- stopping chain attempt")
        break
    cur_e, cur_o = safe_walk(cur_e, cur_o, p, f"4-approach-chain-r{round_i}", target_cells=())
    cur_e, cur_o, moved = safe_kick(cur_e, cur_o, 1, f"4-chain-kick-dot0-r{round_i}", [(tx, ty)])
    if not moved:
        print(f"4: round {round_i} kick did not move dot0 -- stopping chain attempt")
        break
record("4-dot0-chain-attempted", cur_o)
d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D1 and not in_box(c, BOXES["box3"])]
crossed = bool(d0_now) and all(c[1] < BAND_Y[0] for c in d0_now)
print(f"4 done: dot0 now at {sorted(d0_now)}, crossed_band={crossed}")
if not crossed:
    print("\n*** 4 BROKE: dot0 did not chain past the internal band. Census of what IS reachable: ***")
    seen, nodes = exhaustive(copy.deepcopy(cur_e), cur_o, max_nodes=15000)
    seen = {c for c in seen if c is not None}
    print(f"exhaustive BFS: {nodes} nodes, {len(seen)} positions "
          f"({'EXHAUSTED' if nodes < 15000 else 'CAP HIT'})")
    for bn in ("box0", "box1", "box3"):
        bb = BOXES[bn]
        cells = [(x, y) for x in range(bb[0], bb[2] + 1) for y in range(bb[1], bb[3] + 1)]
        reach = [c for c in cells if c in seen]
        print(f"  {bn} interior cells reachable (any phase): {reach}")
    fail("BROKE_AT_LEG_4: dot0 did not chain past the internal band after crossing via "
         "dot2/box3 -- composed-line-1 broken here", cur_o)

# --- 5. fill box0 via dot0 (census + control on the piece's lattice) ---------
b = BOXES["box0"]
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]),
                      protect=D1, max_nodes=1500)
if p is None:
    ok5, reach5, nodes5 = reach_check(cur_e, cur_o, "CHECK-5-census", "box0", None,
                                       piece_xy(grid(cur_o)))
    fail(f"BROKE_AT_LEG_5: no safe route to box0 after dot0's north chain -- "
         f"census REACHABLE={ok5} reach={reach5}", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "5-to-box0", target_cells=())
d0_now = [c for c in dot_cells(grid(cur_o)) if c not in D1 and not in_box(c, BOXES["box3"])]
if not d0_now:
    fail(f"leg5: dot0 not found before box0 fill -- dots={dot_cells(grid(cur_o))}", cur_o)
cur_e, cur_o = guarded_step(cur_e, cur_o, "5-FILL-box0-dot0", click=d0_now[0], target_cells=d0_now)
record("5-box0-filled", cur_o)
if not any(in_box(c, b) for c in extra4(cur_o)):
    fail(f"leg5: box0 not filled after dot0 click -- extra4={extra4(cur_o)}", cur_o)
piece_after_5 = piece_xy(grid(cur_o))
print(f"5 done: box0 filled, piece at {piece_after_5} phase={phase(piece_after_5)}")

# --- 6. walk into box1 -------------------------------------------------------
b = BOXES["box1"]
p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]),
                      protect=D1, max_nodes=3000)
if p is None:
    ok6, reach6, nodes6 = reach_check(cur_e, cur_o, "CHECK-6-census", "box1", None, piece_after_5)
    fail(f"BROKE_AT_LEG_6: no safe route to box1 from {piece_after_5} phase={phase(piece_after_5)} -- "
         f"census REACHABLE={ok6} reach={reach6}", cur_o)
cur_e, cur_o = safe_walk(cur_e, cur_o, p, "6-to-box1", target_cells=())
record("6-standing-in-box1", cur_o)
print(f"6 done: standing at {piece_xy(grid(cur_o))} phase={phase(piece_xy(grid(cur_o)))}")

# --- 7. return-click fill: click dot1 (still untouched) from inside box1 ----
d1_now = dot_cells(grid(cur_o))
print(f"7: dot1 sanity check -- live dots now: {d1_now} (expect == entry D1={D1}, untouched)")
if sorted(d1_now) != sorted(D1):
    print("  WARNING: dot1 does not match its entry position -- proceeding anyway with live cell")
if not d1_now:
    fail(f"leg7: dot1 not found before return-click -- dots={dot_cells(grid(cur_o))}", cur_o)
cur_e, cur_o = guarded_step(cur_e, cur_o, "7-RETURN-CLICK-box1-dot1", click=d1_now[0],
                             target_cells=d1_now)
record("7-box1-filled-returned", cur_o)
piece_after_7 = piece_xy(grid(cur_o))
phase_after_7 = phase(piece_after_7)
print(f"7 done: piece={piece_after_7} phase={phase_after_7} (expect ~dot1 canonical entry, RIGHT)")
if not any(in_box(c, BOXES["box1"]) for c in extra4(cur_o)):
    fail(f"leg7: box1 not filled after return-click -- extra4={extra4(cur_o)}", cur_o)
filled_after_7 = {
    "box0": any(in_box(c, BOXES["box0"]) for c in extra4(cur_o)),
    "box1": any(in_box(c, BOXES["box1"]) for c in extra4(cur_o)),
    "box3": any(in_box(c, BOXES["box3"]) for c in extra4(cur_o)),
}
print(f"7 RESULT: extra4={extra4(cur_o)} boxes filled so far: {filled_after_7}")

# --- 8. exhaustive census: is ANY box2 interior cell reachable from here? ----
b = BOXES["box2"]
ok8, reach8, nodes8 = reach_check(cur_e, cur_o, "CHECK-8-box2", "box2", None, piece_after_7)
if ok8:
    p, _, _ = safe_route(copy.deepcopy(cur_e), cur_o, region(b[0], b[2], b[1], b[3]),
                          protect=[], max_nodes=4000)
    if p is None:
        fail(f"leg8: census said box2 REACHABLE but safe_route found no path (protect=[]) -- "
             f"reach8={reach8}", cur_o)
    cur_e, cur_o = safe_walk(cur_e, cur_o, p, "8-to-box2", target_cells=())
    record("8-final-in-box2", cur_o)
    final_piece = piece_xy(grid(cur_o))
    print(f"8 done: walked into box2, piece={final_piece} levels_completed={cur_o.levels_completed}")
    if cur_o.levels_completed > 1:
        print("\nWIN WIN WIN -- LEVELS_COMPLETED > 1")
else:
    print(f"\n8: box2 NOT reachable with fills {filled_after_7} (nodes={nodes8}) -- "
          f"LINE_COMPLETE_NO_WIN, falsifying '3 filled + piece in box2'")
    record("8-box2-unreachable", cur_o)

# ============================================================================
# 9. bonus arm -- only if leg 8 failed and time remains. NOT attempted in
# this run unless leg 8 fails; if it fails, this line documents NOT RUN
# rather than fabricating an attempt.
# ============================================================================
if not ok8:
    print("\n9: bonus arm (pre-park dot1's marker as a box2 ticket before leg 7) -- NOT RUN "
          "(time budget; would require re-planning the mint before leg 7, which already ran).")

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
verdict = "WIN" if cur_o.levels_completed > 1 else (
    "LINE_COMPLETE_NO_WIN" if n_filled == 3 and piece_in_box2 else "LINE_COMPLETE_PARTIAL")
print(f"\n=== VERDICT: {verdict} -- {n_filled} of {{box0,box1,box3}} filled, "
      f"piece-in-box2={piece_in_box2}, levels_completed={cur_o.levels_completed} ===")
print(f"total actions: {ACT_N[0]}")
