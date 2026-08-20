"""ar25 u4 (2026-08-17): JOINT sweep of L5's docking family -- band phase x S
dock position.  Builds up to 21 band-phase save points by driving the band
(colour-10 comb) DOWN then UP from L5 entry, deepcopy-ing at every distinct
phase; from EACH save point, selects S (A5 x2) and walks it to marker1,
marker2 and the zigzag's interior center, then tries one A5-click branch.
levels_completed is read after every real press.  Reuses get_to_l5() and the
axis pairing (A1=up dy-3, A2=down dy+3, A3=left dx-3, A4=right dx+3) proven
in ar25_u2.py / ar25_u3_zigzag_sweep.py.

    PYTHONUTF8=1 ./.venv/Scripts/python.exe ar25_u4_joint_sweep.py > results/ar25-u4-run.txt
"""
import copy
import time
import json
from collections import deque

import numpy as np

import arc_agi
from arcengine.enums import GameState
import mirror

T0 = time.time()
DEADLINE = T0 + 35 * 60
RESERVE = 5 * 60
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


def s_center(g):
    bb = s_bbox(g)
    if bb is None:
        return None
    return ((bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2)


def components(mask):
    H, W = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(H):
        for x in range(W):
            if mask[y, x] and not seen[y, x]:
                cells, q = [], deque([(y, x)])
                seen[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    cells.append((cy, cx))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if (0 <= ny < H and 0 <= nx < W and mask[ny, nx]
                                and not seen[ny, nx]):
                            seen[ny, nx] = True
                            q.append((ny, nx))
                ys = [c[0] for c in cells]
                xs = [c[1] for c in cells]
                out.append({"n": len(cells), "bbox": (min(ys), max(ys), min(xs), max(xs))})
    out.sort(key=lambda c: -c["n"])
    return out


def band_row(g):
    """Band = colour-10 fragments with row-span <=2 (<=3 rows tall) --
    combines fragments the zigzag splits the comb into.  Excludes any tall
    static colour-10 object by construction (its bbox height is large)."""
    if g is None:
        return None
    mask = (g == 10).copy()
    mask[:, 62:] = False
    mask[62:, :] = False
    parts = [c for c in components(mask) if (c["bbox"][1] - c["bbox"][0]) <= 2]
    if not parts:
        return None
    y0 = min(p["bbox"][0] for p in parts)
    y1 = max(p["bbox"][1] for p in parts)
    n = sum(p["n"] for p in parts)
    return (y0, y1, n, len(parts))


def check_win(o, ctx):
    if o is not None and (o.state == GameState.WIN or o.levels_completed >= 5):
        msg = f"{ctx} levels_completed={o.levels_completed} state={o.state}"
        print(f"*** WIN *** {msg}", flush=True)
        raise Win(msg)


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
ROOT_ENV, ROOT_OBS = get_to_l5()
ROOT = copy.deepcopy(ROOT_ENV)
ENTRY_BAND = band_row(grid(ROOT_OBS))
ENTRY_S = s_center(grid(ROOT_OBS))
print(f"L5 entry t={elapsed():.1f}s: band={ENTRY_BAND} S_center={ENTRY_S}", flush=True)

# ---------------------------------------------------------------- PHASE 1 ---
# Build band-phase save points: drive DOWN (act=2) then UP (act=1) from ROOT,
# deepcopy at every DISTINCT phase (keyed by band row0), stop each direction
# when 1 press produces no change (clamp).
SAVE = {}
ENTRY_ROW0 = ENTRY_BAND[0] if ENTRY_BAND is not None else 0
SAVE[ENTRY_ROW0] = {"env": copy.deepcopy(ROOT), "obs": ROOT_OBS, "presses": 0,
                     "row_predicted": ENTRY_ROW0, "row_observed": ENTRY_BAND, "prefix": []}


def frames_equal(g1, g2):
    """Full-frame byte equality, HUD ticks (row/col 63) excluded -- robust
    blocked-press detector even once the band visually merges (4-connects)
    with the tall static colour-10 column and component decomposition
    (band_row()) can no longer isolate it (measured live: band_row() reads
    None from the very first UP press and from down-press 11 onward, yet
    consecutive raw frames keep differing there -- band_row() is blind
    past that point, not the band itself)."""
    if g1 is None or g2 is None or g1.shape != g2.shape:
        return False
    d = (g1 != g2)
    d[:, 63:] = False
    d[63:, :] = False
    return not d.any()


def build_direction(v_action, max_steps, sign, tag):
    """Clamp = a press that changes NOTHING on the board (full-frame
    byte-identical, HUD excluded) -- the same 'blocked press' law CLAUDE.md
    already documents for this repo. Phase KEY is the PREDICTED row
    (entry_row0 + 3*sign*n), trusted from the context's own '3px/press'
    fact; band_row()'s component-based reading is recorded alongside for
    cross-check whenever it resolves, but is not load-bearing for the key."""
    env = copy.deepcopy(ROOT)
    o = ROOT_OBS
    prev_frame = grid(ROOT_OBS)
    prefix = []
    n = 0
    for i in range(max_steps):
        o2 = step(env, v_action)
        if o2 is None:
            print(f"  [{tag}] obs None at step {i}", flush=True)
            break
        check_win(o2, f"band-build {tag} step{i}")
        if o2.state == GameState.GAME_OVER:
            print(f"  [{tag}] GAME_OVER at step {i}", flush=True)
            break
        new_frame = grid(o2)
        if frames_equal(prev_frame, new_frame):
            print(f"  [{tag}] CLAMPED at step {i} (n={n} presses so far): "
                  f"press produced zero board change", flush=True)
            break
        n += 1
        prefix = prefix + [v_action]
        prev_frame = new_frame
        row_obs = band_row(new_frame)
        pred_row0 = ENTRY_BAND[0] + 3 * sign * n
        key = pred_row0
        if key not in SAVE:
            SAVE[key] = {"env": copy.deepcopy(env), "obs": o2, "presses": sign * n,
                         "row_predicted": pred_row0, "row_observed": row_obs,
                         "prefix": list(prefix)}
        o = o2
    return n


try:
    n_down = build_direction(2, 30, +1, "down")
    n_up = build_direction(1, 30, -1, "up")
except Win as e:
    print(f"WIN DURING BAND-PHASE CONSTRUCTION: {e}", flush=True)
    raise

print(f"down real presses={n_down} up real presses={n_up} "
      f"distinct band phases reached (incl entry)={len(SAVE)}", flush=True)

phases_sorted = sorted(SAVE.items(), key=lambda kv: kv[0])
for pi, (rowkey, sp) in enumerate(phases_sorted):
    print(f"  phase{pi}: row0_predicted={rowkey} row_observed={sp['row_observed']} "
          f"presses_from_entry={sp['presses']}", flush=True)

# ---------------------------------------------------------------- PHASE 2 ---
DOCKS = [("marker1", (37, 16)), ("marker2", (13, 40)), ("zigzag_center", (25, 28))]


def walk_dock(env, o, target, budget, tag, actions_out):
    tx, ty = target
    blocked = set()
    for i in range(budget):
        c = s_center(grid(o))
        if c is None:
            return o, "UNREADABLE"
        cx, cy = c
        if abs(cx - tx) <= 2 and abs(cy - ty) <= 2:
            return o, "ARRIVED"
        ddx, ddy = tx - cx, ty - cy
        cand = []
        if abs(ddx) > 1 and "x" not in blocked:
            cand.append((abs(ddx), 3 if ddx < 0 else 4, "x"))
        if abs(ddy) > 1 and "y" not in blocked:
            cand.append((abs(ddy), 1 if ddy < 0 else 2, "y"))
        if not cand:
            return o, "BLOCKED_BOTH_AXES"
        cand.sort(reverse=True)
        _, v, axis = cand[0]
        prev = s_bbox(grid(o))
        o2 = step(env, v)
        if o2 is None:
            return o, "OBS_NONE"
        check_win(o2, f"{tag} walk i={i}")
        if o2.state == GameState.GAME_OVER:
            return o2, "GAME_OVER"
        actions_out.append(v)
        new_bb = s_bbox(grid(o2))
        if new_bb is not None and prev is not None and new_bb[:4] == prev[:4]:
            blocked.add(axis)
        o = o2
    return o, "BUDGET_EXCEEDED"


CENSUS = []
A5_BRANCH_COUNT = 0
print(f"\n=== PHASE 2: dock walk at {len(phases_sorted)} band phases x {len(DOCKS)} docks ===",
      flush=True)

stopped_early = False
try:
    for pi, (rowkey, sp) in enumerate(phases_sorted):
        if time_left() < RESERVE:
            print(f"deadline approaching, stopping before phase {pi}/{len(phases_sorted)}",
                  flush=True)
            stopped_early = True
            break
        for dname, target in DOCKS:
            tag = f"phase{pi}(row={rowkey})-{dname}"
            env = copy.deepcopy(sp["env"])
            o = sp["obs"]
            arm_actions = list(sp["prefix"])
            sel_n = 0
            o = step(env, 5); sel_n += 1
            check_win(o, f"{tag} select1")
            arm_actions.append(5)
            o = step(env, 5); sel_n += 1
            check_win(o, f"{tag} select2")
            arm_actions.append(5)
            assert sel_n % 3 == 2, f"sel_n bookkeeping broken at {tag}: n={sel_n}"
            s_after_select = s_center(grid(o))
            o, status = walk_dock(env, o, target, 20, tag, arm_actions)
            arrival = s_center(grid(o)) if o is not None else None
            arrival_bbox = s_bbox(grid(o)) if o is not None else None
            if o is not None and o.state != GameState.GAME_OVER:
                benv = copy.deepcopy(env)
                bo = step(benv, 5)
                A5_BRANCH_COUNT += 1
                check_win(bo, f"{tag} A5-branch")
            CENSUS.append({
                "phase_idx": pi, "band_row0_predicted": rowkey,
                "band_row_observed": sp["row_observed"],
                "band_presses_from_entry": sp["presses"], "dock": dname,
                "target": list(target), "s_after_select": s_after_select,
                "status": status, "arrival_center": arrival, "arrival_bbox": arrival_bbox,
            })
        print(f"  phase {pi} done, t={elapsed():.1f}s", flush=True)
except Win as e:
    with open("results/ar25-u4-WIN-actions.json", "w") as f:
        json.dump({"win_msg": str(e), "actions_from_entry": arm_actions}, f, indent=1)
    print(f"WIN action sequence saved to results/ar25-u4-WIN-actions.json: {arm_actions}",
          flush=True)
    raise

print(f"\n=== SWEEP DONE t={elapsed():.1f}s === "
      f"phases={len(phases_sorted)} arms={len(CENSUS)} a5_branches={A5_BRANCH_COUNT} "
      f"stopped_early={stopped_early}", flush=True)

verdict = "JOINT_SWEPT_NO_WIN" if not stopped_early and len(phases_sorted) > 0 else \
    "INCOMPLETE"
RESULT = {
    "win": False,
    "verdict": verdict,
    "elapsed_s": elapsed(),
    "entry_band": ENTRY_BAND,
    "entry_s_center": ENTRY_S,
    "n_down_presses": n_down,
    "n_up_presses": n_up,
    "phases": [{"idx": pi, "row0_predicted": rk, "row_observed": sp["row_observed"],
                "presses": sp["presses"]}
               for pi, (rk, sp) in enumerate(phases_sorted)],
    "distinct_phases": len(phases_sorted),
    "docks": DOCKS,
    "arms_run": len(CENSUS),
    "a5_branch_count": A5_BRANCH_COUNT,
    "stopped_early": stopped_early,
    "census": CENSUS,
}
with open("results/ar25-u4-result.json", "w") as f:
    json.dump(RESULT, f, indent=1, default=str)
print("wrote results/ar25-u4-result.json", flush=True)
print("done", flush=True)
