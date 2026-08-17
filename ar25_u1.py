"""ar25 u1 (2026-08-17, goal-directed session): induce the win predicate from
levels 1-4 by replaying each on a fresh env and diffing the board at the
win-instant against the action right before it.

    ./.venv/Scripts/python.exe ar25_u1.py > results/ar25-u1.txt
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


def components(mask):
    """4-connected components of a boolean mask -> list of (cells, bbox)."""
    from collections import deque
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        cells = []
        while q:
            y, x = q.popleft()
            cells.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] \
                        and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        ys_ = [c[0] for c in cells]
        xs_ = [c[1] for c in cells]
        out.append((len(cells), (min(xs_), max(xs_), min(ys_), max(ys_))))
    out.sort(reverse=True)
    return out


def diffcolours(g0, g1):
    out = {}
    for c in sorted(set(np.unique(g0)) | set(np.unique(g1))):
        n0 = int((g0 == c).sum())
        n1 = int((g1 == c).sum())
        if n0 != n1:
            out[int(c)] = (n0, n1)
    return out


def replay_all_transitions(line, tag):
    """Play the WHOLE line once. Return dict: level -> (frame_before, frame_at_win, i)."""
    env = arc_agi.Arcade().make("ar25")
    obs = env.reset()
    prev_g = grid(obs)
    seen = obs.levels_completed
    out = {}
    for i, e in enumerate(line):
        if isinstance(e, tuple):
            _, x, y, _ = e
            obs = step(env, 6, {"x": int(x), "y": int(y)})
        else:
            obs = step(env, int(e))
        if obs is None:
            print(f"  [{tag}] obs None at i={i}")
            return out
        g = grid(obs)
        if obs.levels_completed > seen:
            print(f"  [{tag}] level {seen}->{obs.levels_completed} at action i={i} "
                  f"(action={e})")
            out[obs.levels_completed] = (prev_g, g, i)
            seen = obs.levels_completed
        prev_g = g
    print(f"  [{tag}] final level={obs.levels_completed}")
    return out


def report(tag, before, after):
    if before is None:
        print(f"  [{tag}] NO CAPTURE\n")
        return
    d = diffcolours(before, after)
    print(f"  [{tag}] colour cell-count changes: {d}")
    for c, (n0, n1) in d.items():
        comps0 = components(before == c)
        comps1 = components(after == c)
        print(f"    colour {c}: before comps(top3)={comps0[:3]} "
              f"after comps(top3)={comps1[:3]}")
    print()


print("=== full L1-L4 replay, all transitions captured in ONE run ===")
FULL = (tuple(mirror.L1_LINE) + tuple(mirror.L2_LINE) + tuple(mirror.L3_LINE)
        + tuple(mirror.L4_LINE))
trans = replay_all_transitions(FULL, "L1-4")
for lvl in (1, 2, 3, 4):
    print(f"\n--- level {lvl - 1}->{lvl} board diff ---")
    if lvl in trans:
        b, a, i = trans[lvl]
        report(f"L{lvl}", b, a)
    else:
        print(f"  [L{lvl}] NOT REACHED in this line\n")

print("=== L5 entry board: colour-11 component census (candidate targets) ===")
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
print(f"reached L5 in {acts} actions, level={obs.levels_completed}")
ROOT = copy.deepcopy(env)
ENTRY = grid(obs)
for c in (5, 9, 10, 11):
    comps = components(ENTRY == c)
    print(f"  colour {c}: {len(comps)} components, top5 (cells,(x0,x1,y0,y1))={comps[:5]}")

print("\ndone")
