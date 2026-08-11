"""bp35 fourteenth pass: ride from the LEFT column, by hand.

p15 proved the walk reaches x=14 once the room's row band is cleared, and
climb3 then failed to ride there -- its picker chose a block two bands up
instead of the one over the piece. This spells the line out and dumps the
board after each ride, so what is above the piece is read rather than
guessed:

  A4 x4              ride 1 (reset -> T0)
  click(45,33)       ride 2 (T0 -> T1)
  click x15,21,27 y39   clear the row band that walls the room at x=32
  A3 x5              walk 44 -> 14
  click(15,33)       the block over the piece's own columns at T1

Budget at that point is 8 + about 8 per ride = 24 actions against 14 spent.
"""
import sys

import numpy as np

import arc_agi

PLAN = ([("m", 4)] * 4
        + [("c", 45, 33)]
        + [("c", 15, 39), ("c", 21, 39), ("c", 27, 39)]
        + [("m", 3)] * 5
        + [("c", 15, 33)])


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


def flood_top(g):
    ys, _ = np.nonzero(g[:63] == 15)
    return int(ys.min()) if len(ys) else None


def dump(g, label):
    print(f"  --- {label} ---")
    for y in range(0, 63):
        print("   y%2d " % y + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                       for v in g[y, 10:56]))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
for i, s in enumerate(PLAN):
    obs = (env.step(A[s[1]]) if s[0] == "m"
           else env.step(A[6], data={"x": s[1], "y": s[2]}))
    what = f"A{s[1]}" if s[0] == "m" else f"click({s[1]},{s[2]})"
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d} {what}: DEAD FRAME")
        break
    n = int((g != g2).sum())
    print(f"  i={i:2d} {what:14s} n={n:5d} x={piece_x(g2)} "
          f"cnt={int((g2[63] == 15).sum()):2d} flood={flood_top(g2)} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
          f"{'   RIDE' if n > 600 else ''}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]} after {i + 1} actions")
        break
    sys.stdout.flush()
dump(g, f"after the line, piece x={piece_x(g)} (x10-55 shown)")
