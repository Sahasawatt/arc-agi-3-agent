"""dc22 first pass with an AIMED click.

breadth-recon's §dc22 verdict -- "clicks are INERT on this level, 6 floor/panel
spots, all 20 object centres, double-clicks, pairs: zero play-area cells
changed, ever" -- was measured through `set_data`, which the local wrapper
ignores, so all of those clicks arrived at the same empty-dict destination
(results/click-probe.txt). Aimed, exactly two of 35 components answer:
(48,19) with 129 cells and (48,36) with 97 (results/dc22-click.txt).

E1  what each of the two does: the board before and after, as rows.
E2  is it a toggle, a cycle or a one-shot -- click the same one four times.
E3  do the two interact -- A then B, and B then A, in fresh episodes.
E4  does anything else wake up once one has been pressed -- re-sweep every
    component after clicking (48,19).
Control in every arm: a click on the background corner, which must stay at
the HUD tick (1 cell) that recon already identified.
"""
import sys

import numpy as np

import arc_agi

A_TGT, B_TGT = (48, 19), (48, 36)


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def rows(g, y0, y1, x0=0, x1=63):
    return [f"y{y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                  for v in g[y, x0:x1 + 1])
            for y in range(y0, y1 + 1)]


def diff_box(a, b):
    ys, xs = np.nonzero(a != b)
    if not len(ys):
        return None
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def components(g):
    bg = int(np.bincount(g.ravel()).argmax())
    seen = np.zeros(g.shape, dtype=bool)
    out = []
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            if seen[y, x] or g[y, x] == bg:
                continue
            col = int(g[y, x])
            stack, cells = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < g.shape[0] and 0 <= nx < g.shape[1]
                            and not seen[ny, nx] and g[ny, nx] == col):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            out.append(((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2,
                        col, len(cells)))
    return out


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def fresh():
    env = arc.make(envs["dc22"].game_id)
    A = {a.value: a for a in env.action_space}
    return env, A, env.reset()


def click(env, A, xy):
    return env.step(A[6], data={"x": xy[0], "y": xy[1]})


print("== E1: what each target does ==")
for tgt in (A_TGT, B_TGT):
    env, A, obs = fresh()
    g = grid_of(obs)
    obs = click(env, A, tgt)
    g2 = grid_of(obs)
    box = diff_box(g, g2)
    print(f"  click{tgt}: n={int((g != g2).sum())} box={box} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
    if box:
        x0, x1, y0, y1 = box
        for a, b in zip(rows(g, y0, y1, x0, x1), rows(g2, y0, y1, x0, x1)):
            print(f"    {a}  |  {b}")
    sys.stdout.flush()

print("\n== E2: same target four times ==")
for tgt in (A_TGT, B_TGT):
    env, A, obs = fresh()
    g = grid_of(obs)
    seen = {}
    for k in range(4):
        obs = click(env, A, tgt)
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  click{tgt} #{k}: DEAD FRAME")
            break
        key = g2.tobytes()
        tag = f"  <-- same board as press {seen[key]}" if key in seen else ""
        seen[key] = k
        print(f"  click{tgt} #{k}: n={int((g != g2).sum()):5d} "
              f"lvl={obs.levels_completed}{tag}")
        g = g2
    sys.stdout.flush()

print("\n== E3: the two together ==")
for order in ((A_TGT, B_TGT), (B_TGT, A_TGT)):
    env, A, obs = fresh()
    g = grid_of(obs)
    for tgt in order:
        obs = click(env, A, tgt)
        g2 = grid_of(obs)
        print(f"  click{tgt}: n={int((g != g2).sum()):5d} "
              f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
        g = g2
    print(f"  order {order[0]}->{order[1]} done")
    sys.stdout.flush()

print("\n== E4: re-sweep every component after clicking A ==")
env, A, obs = fresh()
obs = click(env, A, A_TGT)
base = grid_of(obs)
live = 0
for cx, cy, col, size in sorted(components(base), key=lambda c: c[3]):
    env2, A2, obs2 = fresh()
    obs2 = click(env2, A2, A_TGT)
    g = grid_of(obs2)
    obs2 = click(env2, A2, (cx, cy))
    g2 = grid_of(obs2)
    if g2 is None:
        print(f"  ({cx:2d},{cy:2d}) c{col} s{size}: DEAD FRAME")
        continue
    n = int((g != g2).sum())
    if n > 1:
        live += 1
        print(f"  ({cx:2d},{cy:2d}) colour{col:3d} size{size:5d}: n={n:5d} "
              f"lvl={obs2.levels_completed}   RESPONDS")
    sys.stdout.flush()
print(f"  responders after A (excluding the 1-cell HUD tick): {live}")
