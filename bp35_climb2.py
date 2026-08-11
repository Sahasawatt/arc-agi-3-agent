"""bp35: dig, don't ride. Second climber.

climb1 (results/bp35-climb1.txt) oscillated between two tape states forever
because it only ever looked at the x43-47 shaft: click the block over the
ceiling -> ride up, A7 -> ride down, repeat, 40 actions and no level. What
the frame says instead (p11's state-S dump, p12 E16):

  * a click turns a colour-14 block into colour-10 FLOOR;
  * the piece walks the connected floor region and rides whenever that
    region opens upward -- so the game is DUG, not steered;
  * at S the way up is on the LEFT (blocks at x13-30 fill y30-47), behind a
    block wall the piece cannot walk past.

So: flood-fill the floor the piece stands on, take the blocks TOUCHING it,
prefer the highest one, walk under it if need be, click it, repeat. The
budget is real (8 actions + ~8 per tape event), so every action is logged
with the flood.
"""
import sys
from collections import deque

import numpy as np

import arc_agi

FLOOR, BLOCK = 10, 14
BUDGET = 45


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_box(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    if not len(ys):
        return None
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def region(g, seed):
    """4-connected floor the piece stands on (its own cells count as floor)."""
    walk = (g == FLOOR) | (g == 9) | (g == 11)
    seen = set()
    q = deque([seed])
    while q:
        y, x = q.popleft()
        if (y, x) in seen or not (0 <= y < 63 and 0 <= x < 64):
            continue
        if not walk[y, x]:
            continue
        seen.add((y, x))
        q.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])
    return seen


def components(g, colour):
    mask = g == colour
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if not mask[y, x] or seen[y, x]:
                continue
            stack, cells = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1]
                            and mask[ny, nx] and not seen[ny, nx]):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            out.append(cells)
    return out


def touching(g, floor):
    """Blocks with a cell orthogonally adjacent to the floor region."""
    out = []
    for cells in components(g, BLOCK):
        if any((cy + dy, cx + dx) in floor
               for cy, cx in cells for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            out.append(((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2,
                        min(ys), min(xs), max(xs)))
    return out


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
line = []
for i in range(BUDGET):
    box = piece_box(g)
    if box is None:
        print("  piece lost")
        break
    x0, x1, y0, y1 = box
    floor = region(g, (y1, (x0 + x1) // 2))
    cands = touching(g, floor)
    if not cands:
        print(f"  i={i:2d} nothing touches the floor region -- stopping")
        break
    # highest block first; among equals, the one nearest the piece
    cx, cy, top, bx0, bx1 = min(cands, key=lambda c: (c[2], abs(c[0] - x0)))
    obs = env.step(A[6], data={"x": cx, "y": cy})
    what = f"click({cx},{cy})"
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d} {what}: DEAD FRAME")
        break
    n = int((g != g2).sum())
    line.append((6, cx, cy))
    ys, _ = np.nonzero(g2[:63] == 15)
    print(f"  i={i:2d} {what:14s} n={n:5d} block_top=y{top} "
          f"floor={len(floor):4d} cnt={int((g2[63] == 15).sum()):2d} "
          f"flood={int(ys.min()) if len(ys) else None} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
          f"{'   RIDE' if n > 600 else ''}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]} after {i + 1} actions")
        break
    sys.stdout.flush()
print(f"line: {line}")
