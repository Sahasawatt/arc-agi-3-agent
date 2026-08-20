"""bp35 eleventh pass: does a click RIDE, or only the click over the piece?

At T0 (reset + A4 x4) four blocks sit in the band above the room, at
x31-35, 37-41, 43-47, 49-53. Clicking the one over the piece (x43-47)
answered 1343 cells = a ride, and the tape then oscillated forever
(climb1). If a click AWAY from the piece's column merely clears, the band
can be opened wide before riding -- and how far a ride travels is what
level 1 is made of.

Arms, each a fresh episode from T0:
  A  click x33 (far from the piece) -- ride or clear?
  B  click x33, x39, x51 (all but the piece's own), then A4
  C  clear all four, then A4
  D  control: click x45 alone, which is already known to ride
Every arm prints the band string after each action, so a clear and a ride
are told apart by the board and not by the cell count alone.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


def bands(g):
    out = []
    for y0 in range(0, 60, 6):
        band = g[y0:y0 + 6]
        codes = []
        for x0, x1 in ((13, 30), (31, 53)):
            sub = band[:, x0:x1 + 1]
            n10, n14 = int((sub == 10).sum()), int((sub == 14).sum())
            codes.append(f"{n14 // 21 or 1}G" if n14 > 20 else "B" if n10 > 60
                         else "b" if n10 > 10 else ".")
        out.append(codes[0] + "/" + codes[1])
    return " ".join(out)


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

ARMS = [
    ("A: one click far from the piece", [("c", 33, 33)]),
    ("B: clear the other three, then ride",
     [("c", 33, 33), ("c", 39, 33), ("c", 51, 33), ("m", 4)]),
    ("C: clear all four, then ride",
     [("c", 33, 33), ("c", 39, 33), ("c", 51, 33), ("c", 45, 33), ("m", 4)]),
    ("D: control -- the click over the piece alone", [("c", 45, 33)]),
]

for label, steps in ARMS:
    env = arc.make(envs["bp35"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    for _ in range(4):
        obs = env.step(A[4])
    g = grid_of(obs)
    print(f"== {label} ==")
    print(f"  T0 x={piece_x(g)} bands: {bands(g)}")
    for i, s in enumerate(steps):
        obs = (env.step(A[6], data={"x": s[1], "y": s[2]}) if s[0] == "c"
               else env.step(A[s[1]]))
        what = f"click({s[1]},{s[2]})" if s[0] == "c" else f"A{s[1]}"
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  {what:14s} DEAD FRAME")
            break
        n = int((g != g2).sum())
        print(f"  {what:14s} n={n:5d} x={piece_x(g2)} "
              f"cnt={int((g2[63] == 15).sum()):2d} lvl={obs.levels_completed} "
              f"st={str(obs.state).split('.')[-1]}{'  RIDE' if n > 600 else ''}")
        print(f"                 bands: {bands(g2)}")
        g = g2
        if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
            print(f"  END lvl={obs.levels_completed} "
                  f"state={str(obs.state).split('.')[-1]}")
            break
        sys.stdout.flush()
    print()
