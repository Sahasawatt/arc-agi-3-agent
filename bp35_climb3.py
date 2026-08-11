"""bp35 third climber: clear the wall, walk to the new column, ride there.

p15 broke the dead end: clearing the three blocks in the room's own row band
lets the walk run 44 -> 14 (the control, uncleared, stops at 32). What
failed after that was the picker, not the game -- it took the median of
every colour-14 cell near the piece and landed BETWEEN two blocks, so the
click cleared a neighbour instead of riding. A block is the door only when
it sits over the piece's own five columns; pick by OVERLAP.

The loop: ride if a block overlaps the piece from above, else clear a block
that is boxing the walk in, else walk toward the side with blocks overhead.
Every action is logged with the flood, since the budget is 8 actions plus
about 8 per ride.
"""
import sys

import numpy as np

import arc_agi

BUDGET = 45
CEIL = 36


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    if not len(ys):
        return None
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def flood_top(g):
    ys, _ = np.nonzero(g[:63] == 15)
    return int(ys.min()) if len(ys) else None


def blocks(g, y0, y1):
    """(x0, x1, y0, y1) of every colour-14 run inside the row window."""
    out = []
    for y in range(y0, y1 + 1):
        xs = np.nonzero(g[y] == 14)[0]
        if not len(xs):
            continue
        start = prev = xs[0]
        for x in list(xs[1:]) + [None]:
            if x is not None and x == prev + 1:
                prev = x
                continue
            out.append((int(start), int(prev), y))
            if x is None:
                break
            start = prev = x
    merged = {}
    for x0, x1, y in out:
        merged.setdefault((x0, x1), []).append(y)
    return [(x0, x1, min(ys), max(ys)) for (x0, x1), ys in merged.items()]


def overlap(a0, a1, b0, b1):
    return max(0, min(a1, b1) - max(a0, b0) + 1)


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
line = []
for i in range(BUDGET):
    p = piece(g)
    if p is None:
        print("  piece lost")
        break
    px0, px1, py0, py1 = p
    above = blocks(g, 0, CEIL - 1)
    door = max((b for b in above if overlap(px0, px1, b[0], b[1]) >= 3),
               key=lambda b: (b[3], overlap(px0, px1, b[0], b[1])), default=None)
    side = [b for b in blocks(g, py0, py1) if b[1] < px0 or b[0] > px1]
    if door is not None:
        cx, cy = (door[0] + door[1]) // 2, (door[2] + door[3]) // 2
        what, obs = f"ride click({cx},{cy})", env.step(A[6], data={"x": cx, "y": cy})
    elif side:
        # clear the one nearest the piece so the walk can widen
        b = min(side, key=lambda b: min(abs(b[1] - px0), abs(b[0] - px1)))
        cx, cy = (b[0] + b[1]) // 2, (b[2] + b[3]) // 2
        what, obs = f"clear click({cx},{cy})", env.step(A[6], data={"x": cx, "y": cy})
    else:
        # nothing overhead, nothing beside: walk toward the nearest block above
        tgt = min(above, key=lambda b: abs((b[0] + b[1]) // 2 - px0), default=None)
        step = 4 if tgt is None or (tgt[0] + tgt[1]) // 2 > px0 else 3
        what, obs = f"walk A{step}", env.step(A[step])
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d} {what}: DEAD FRAME")
        break
    n = int((g != g2).sum())
    p2 = piece(g2)
    line.append(what)
    print(f"  i={i:2d} {what:22s} n={n:5d} x={p2[0] if p2 else None} "
          f"cnt={int((g2[63] == 15).sum()):2d} flood={flood_top(g2)} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
          f"{'   RIDE' if n > 600 else ''}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]} after {i + 1} actions")
        break
    sys.stdout.flush()
print(f"line: {line}")
