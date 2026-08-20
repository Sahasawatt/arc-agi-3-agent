"""bp35 sixth pass.

p3(b) fired a SECOND tower event -- A7 from x44 -- and its fingerprint shifts
the tape the OTHER way (up 3 bands) from event #1 (down 3 bands). Every
x44 case measured so far:

  A4 38->44 (heading R, moving R)  EVENT, tape DOWN
  A7 44->38 (heading R, moving L)  EVENT, tape UP
  A4 44->50, A3 50->44, A3 44->38, A7 50->44   all silent

E7  RATCHET. Nobody has yet returned to x44 FROM THE LEFT after event #1:
    p6 walked away and stopped, E2/p4 always came back from x50. Loop
    [A3 out, A4 in] and ask whether each A4 fires again, and which way.
E8  FLOOD LAW. probe_acts' A3 run flooded on action 8; E2's flooded on
    action 16. Press one action into a wall and read the y63 counter and
    the flood top per action -- is it an action timer at all?
E9  A6 (the complex action) at the chute -- never probed there.

Tape direction is measured by matching the tower against itself at every
6-row offset, so "DOWN 18" is a fit, not an eyeball; the fit reports its
own match fraction and a no-shift control.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


def flood_top(g):
    ys, _ = np.nonzero(g[:63] == 15)
    return int(ys.min()) if len(ys) else None


def counter(g):
    return int((g[63] == 15).sum())


def shift(a, b):
    """Best dy such that a[y] == b[y+dy] over the tape columns x13-53.

    Positive dy = content moved DOWN the screen. Returns (dy, fraction).
    """
    best = (None, 0.0)
    for dy in range(-36, 37, 6):
        ys = range(max(0, -dy), min(63, 63 - dy))
        rows = [y for y in ys]
        if len(rows) < 20:
            continue
        A = a[rows, 13:54]
        B = b[[y + dy for y in rows], 13:54]
        frac = float((A == B).mean())
        if frac > best[1]:
            best = (dy, frac)
    return best


def fresh():
    env = arc.make(envs["bp35"].game_id)
    return env, {a.value: a for a in env.action_space}, None


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

# ---------------------------------------------------------------- E7
print("== E7: ratchet -- leave x44 by A3 (silent), return by A4 ==")
env, A, _ = fresh()
obs = env.reset()
g = grid_of(obs)
plan = [4] * 4 + [3, 4] * 9
for i, v in enumerate(plan):
    xb = piece_x(g)
    obs = env.step(A[v])
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d} A{v}: EMPTY FRAME")
        break
    n = int((g != g2).sum())
    tag = ""
    if n > 600:
        dy, frac = shift(g, g2)
        tag = f"  TAPE dy={dy:+d} fit={frac:.2f}"
    print(f"  i={i:2d} A{v} x {xb}->{piece_x(g2)} n={n:5d} "
          f"cnt={counter(g2):2d} flood={flood_top(g2)} "
          f"st={str(obs.state).split('.')[-1]} lvl={obs.levels_completed}{tag}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]}")
        break
    sys.stdout.flush()
# control: the shift fit must report 0 for a frame against itself
print(f"  control shift(g,g) = {shift(g, g)} (expect dy=0, fit=1.00)")

# ---------------------------------------------------------------- E8
print("\n== E8: flood law -- press A3 into the left wall, 30 actions ==")
env, A, _ = fresh()
obs = env.reset()
g = grid_of(obs)
for i in range(30):
    obs = env.step(A[3])
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d}: EMPTY FRAME")
        break
    n = int((g != g2).sum())
    if n > 1 or i < 3:
        print(f"  i={i:2d} A3 x={piece_x(g2)} n={n:4d} cnt={counter(g2):2d} "
              f"flood={flood_top(g2)} st={str(obs.state).split('.')[-1]}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END at action {i + 1}: lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]}")
        break
    sys.stdout.flush()

# ---------------------------------------------------------------- E9
print("\n== E9: A6 (complex) at the chute and away from it ==")
for pre, label in [([4] * 4, "at x44 (after event #1)"), ([], "at reset x20")]:
    env, A, _ = fresh()
    obs = env.reset()
    for v in pre:
        obs = env.step(A[v])
    g = grid_of(obs)
    print(f"  {label}: x={piece_x(g)}")
    for k in range(3):
        obs = env.step(A[6])
        g2 = grid_of(obs)
        if g2 is None:
            print(f"    A6 #{k}: EMPTY FRAME")
            break
        print(f"    A6 #{k}: n={int((g != g2).sum()):5d} x={piece_x(g2)} "
              f"cnt={counter(g2):2d} st={str(obs.state).split('.')[-1]}")
        g = g2
    sys.stdout.flush()
