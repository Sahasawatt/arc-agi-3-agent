"""dc22 with an AIMED click.

breadth-recon records dc22 as "63 single clicks all eventually answer zero
changed cells" -- every one of them sent through `set_data`, which the local
wrapper ignores (results/click-probe.txt). dc22's game tolerates the missing
key instead of raising, so those clicks landed wherever an empty data dict
lands, and the zero was real but was not a reading about the objects.

This clicks the actual objects: every colour component in the frame, one per
fresh episode, centre of its box. Control: a click on the emptiest corner in
the same sweep.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def components(g):
    out = []
    bg = int(np.bincount(g.ravel()).argmax())
    seen = np.zeros(g.shape, dtype=bool)
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            if seen[y, x] or g[y, x] == bg:
                continue
            col = g[y, x]
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
                        int(col), len(cells)))
    return out


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["dc22"].game_id)
obs = env.reset()
g0 = grid_of(obs)
cands = sorted(components(g0), key=lambda c: c[3])
print(f"dc22 reset: {len(cands)} components")

live = 0
for cx, cy, col, size in cands[:40]:
    env = arc.make(envs["dc22"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    g = grid_of(obs)
    obs = env.step(A[6], data={"x": cx, "y": cy})
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  ({cx:2d},{cy:2d}) colour{col:3d} size{size:5d}: DEAD FRAME")
        continue
    n = int((g != g2).sum())
    if n:
        live += 1
    print(f"  ({cx:2d},{cy:2d}) colour{col:3d} size{size:5d}: n={n:5d} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
          f"{'   RESPONDS' if n else ''}")
    sys.stdout.flush()
print(f"live responders: {live} of {min(40, len(cands))}")
