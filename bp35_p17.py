"""bp35 fifteenth pass: there is a colour-7 object, and it is the first thing
in this game that looks like a goal.

p16's third ride (from the left column, after clearing the room's row band)
put a room at y19-29 holding a small colour-7 diamond at x20-22 -- a colour
no earlier probe has seen on this board. The piece rides into the room above
when it clicks a block over its own columns, so: ride once more, then walk
onto the 7.

Continues p16's line exactly, then walks toward whatever colour-7 cells the
frame holds, one action at a time, and reports the level after every step.
"""
import sys

import numpy as np

import arc_agi

P16 = ([("m", 4)] * 4 + [("c", 45, 33)]
       + [("c", 15, 39), ("c", 21, 39), ("c", 27, 39)]
       + [("m", 3)] * 5 + [("c", 15, 33)])


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


def where(g, colour):
    ys, xs = np.nonzero(g == colour)
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())) if len(ys) else None


def blocks_above(g, ceil=36):
    out = []
    for y in range(ceil, -1, -1):
        xs = np.nonzero(g[y] == 14)[0]
        if not len(xs):
            continue
        run = [int(xs[0])]
        for x in list(xs[1:]) + [None]:
            if x is not None and x == run[-1] + 1:
                run.append(int(x))
                continue
            out.append((run[0], run[-1], y))
            if x is None:
                break
            run = [int(x)]
        if out:
            return out          # lowest band only
    return out


def step(env, A, s):
    return (env.step(A[s[1]]) if s[0] == "m"
            else env.step(A[6], data={"x": s[1], "y": s[2]}))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
n_act = 0
for s in P16:
    obs = step(env, A, s)
    g = grid_of(obs)
    n_act += 1
print(f"after p16's line ({n_act} actions): x={piece_x(g)} "
      f"colour7 at {where(g, 7)} lvl={obs.levels_completed}")
sys.stdout.flush()

for i in range(28):
    px = piece_x(g)
    if px is None:
        print("  piece lost")
        break
    above = blocks_above(g)
    over = [b for b in above if b[0] - 4 <= px <= b[1]]
    if over:
        b = over[0]
        s = ("c", (b[0] + b[1]) // 2, b[2])
    elif above:
        # walk toward the nearest block that could be a door
        tgt = min(above, key=lambda b: abs((b[0] + b[1]) // 2 - px))
        s = ("m", 4 if (tgt[0] + tgt[1]) // 2 > px else 3)
    else:
        seven = where(g, 7)
        if seven is None:
            print("  nothing above and no colour 7 in view")
            break
        s = ("m", 4 if seven[0] > px else 3)
    obs = step(env, A, s)
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d}: DEAD FRAME")
        break
    n = int((g != g2).sum())
    what = f"A{s[1]}" if s[0] == "m" else f"click({s[1]},{s[2]})"
    ys, _ = np.nonzero(g2[:63] == 15)
    print(f"  i={i:2d} {what:14s} n={n:5d} x={piece_x(g2)} "
          f"cnt={int((g2[63] == 15).sum()):2d} "
          f"flood={int(ys.min()) if len(ys) else None} c7={where(g2, 7)} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
          f"{'   RIDE' if n > 600 else ''}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]} after {n_act + i + 1} actions")
        break
    sys.stdout.flush()
