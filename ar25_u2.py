"""ar25 u2 (2026-08-17, goal-directed session): drive the induced predicate
(colour-5 piece S docks on a colour-11 target) directly at L5, live, with
levels_completed read after every action -- and vary the BAND PHASE
(one-way-door candidate) before selecting S, since L3/L4's lesson is that a
control surface set BEFORE engaging the piece can be the whole answer.

    ./.venv/Scripts/python.exe ar25_u2.py > results/ar25-u2.txt
"""
import copy
import numpy as np

import arc_agi
from arcengine.enums import GameState
import mirror

A = None


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


def press(env, v, log, tag):
    o = step(env, v)
    if o is None:
        log.append(f"  {tag}: obs None")
        return None
    if o.state == GameState.WIN or o.levels_completed >= 5:
        log.append(f"  {tag}: *** WIN *** levels_completed={o.levels_completed}")
    if o.state == GameState.GAME_OVER:
        log.append(f"  {tag}: GAME_OVER")
    return o


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


print("=== reaching L5 root ===")
ROOT_ENV, ROOT_OBS = get_to_l5()
ROOT = copy.deepcopy(ROOT_ENV)
print("at L5 entry")

MARKERS = {"marker1(top-right of zigzag)": (37, 16), "marker2(bottom-left of zigzag)": (13, 40)}


def s_bbox(g):
    ys, xs = np.nonzero(g == 5)
    # exclude the row-63/col-63 HUD ticks
    keep = (xs < 62) & (ys < 62)
    ys, xs = ys[keep], xs[keep]
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()), len(xs))


def walk_to(env, o, target, budget, tag):
    """Greedy walk with BLOCKED-axis detection: if a press does not move the
    bbox, that axis is abandoned for the rest of this call (wall/edge)."""
    tx, ty = target
    blocked = set()
    path = []
    for i in range(budget):
        g = grid(o)
        bb = s_bbox(g)
        if bb is None:
            print(f"  [{tag}] i={i}: S unreadable, stop")
            break
        x0, x1, y0, y1, n = bb
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if abs(cx - tx) <= 2 and abs(cy - ty) <= 2:
            print(f"  [{tag}] i={i}: ARRIVED, bbox={bb}")
            return o, True
        ddx, ddy = tx - cx, ty - cy
        # MEASURED THIS SESSION (results/ar25-u2.txt ARM1/ARM2 raw paths):
        # act1=UP(dy-3) act2=DOWN(dy+3) act3=LEFT(dx-3) act4=RIGHT(dx+3) --
        # the OPPOSITE axis pairing from the historical breadth-recon note
        # (which had A1/A2 on x, A3/A4 on y). Corrected here.
        cand = []
        if abs(ddx) > 1 and "x" not in blocked:
            cand.append((abs(ddx), 3 if ddx < 0 else 4, "x"))
        if abs(ddy) > 1 and "y" not in blocked:
            cand.append((abs(ddy), 1 if ddy < 0 else 2, "y"))
        if not cand:
            print(f"  [{tag}] i={i}: no candidate axis left (blocked={blocked}), "
                  f"bbox={bb}, stop")
            break
        cand.sort(reverse=True)
        _, v, axis = cand[0]
        prev_bb = bb
        o = step(env, v)
        if o is None:
            print(f"  [{tag}] i={i}: obs None, stop")
            break
        if o.state == GameState.WIN or o.levels_completed >= 5:
            print(f"  [{tag}] i={i}: *** WIN *** levels_completed={o.levels_completed}")
            return o, True
        if o.state == GameState.GAME_OVER:
            print(f"  [{tag}] i={i}: GAME_OVER, stop")
            break
        new_bb = s_bbox(grid(o))
        if new_bb is not None and new_bb[:4] == prev_bb[:4]:
            blocked.add(axis)
            path.append(f"act={v} axis={axis} BLOCKED")
        else:
            path.append(f"act={v} axis={axis} bbox={new_bb}")
    print(f"  [{tag}] path: {path}")
    g = grid(o) if o is not None else None
    print(f"  [{tag}] final bbox={s_bbox(g) if g is not None else None} "
          f"levels_completed={o.levels_completed if o is not None else 'N/A'}")
    return o, False


print("\n=== ARM 1: entry band phase, select S (A5 x2), walk toward marker1 ===")
env = copy.deepcopy(ROOT)
log = []
o = press(env, 5, log, "select-1")
o = press(env, 5, log, "select-2")
g = grid(o)
print(f"  after select: S bbox = {s_bbox(g)}")
o, won1 = walk_to(env, o, MARKERS["marker1(top-right of zigzag)"], 40, "ARM1")
print(f"  ARM1 won={won1} levels_completed={o.levels_completed if o else 'N/A'} "
      f"state={o.state if o else 'N/A'}")

print("\n=== ARM 2: entry band phase, select S, walk toward marker2 ===")
env = copy.deepcopy(ROOT)
o = press(env, 5, [], "select-1")
o = press(env, 5, [], "select-2")
o, won2 = walk_to(env, o, MARKERS["marker2(bottom-left of zigzag)"], 40, "ARM2")
print(f"  ARM2 won={won2} levels_completed={o.levels_completed if o else 'N/A'} "
      f"state={o.state if o else 'N/A'}")

print("\n=== ARM 3: ONE-WAY-DOOR test -- shift band phase BEFORE selecting S, then repeat marker1 walk ===")
for band_presses, tag in [(3, "band+3"), (7, "band+7 (~1/3 of 21)"), (14, "band+14 (~2/3 of 21)")]:
    env = copy.deepcopy(ROOT)
    log = []
    o = ROOT_OBS
    for i in range(band_presses):
        o = press(env, 2, log, f"{tag} band-press {i}")  # drive band with A2 (right/down on band axis)
        if o is None or o.state == GameState.GAME_OVER:
            break
    if o is None:
        print(f"  [{tag}] died during band setup"); continue
    o = press(env, 5, log, f"{tag} select-1")
    o = press(env, 5, log, f"{tag} select-2")
    o, won3 = walk_to(env, o, MARKERS["marker1(top-right of zigzag)"], 30, tag)
    print(f"  [{tag}] won={won3} levels_completed={o.levels_completed if o else 'N/A'}")

print("\ndone")
