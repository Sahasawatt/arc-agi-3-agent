"""ka59: the click TELEPORTS -- so what are its rules, and does the right
room open?

E1 measured a click on the dot moving the PIECE there: (19,31) went to
background and (28,31) went to the piece's colour. If that is a general
teleport, the 74-state keyboard graph was never the state space, and the
right room -- which the piece has never entered in 2,000 competition actions
-- is one click away.

E5  teleport targets across the map, one fresh episode each: left room,
    corridor, ON the bar, right room floor, right slot interior, left slot
    interior, void outside the rooms. Readout: where the piece ends up.
E6  if the right room takes, drive the whole endgame: kick the dot east
    first (walk into it), then teleport beside its landing spot and push it
    the last cells into the right slot.
E7  or the cheap win: teleport the piece INTO each slot interior and see if
    standing there is the level.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece(g):
    ys, xs = np.nonzero(g[:63] == 0)
    if not len(ys):
        return None
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


def dot(g):
    ys, xs = np.nonzero(g[:63] == 5)
    return (int(xs.min()), int(ys.min())) if len(ys) else None


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def fresh():
    env = arc.make(envs["ka59"].game_id)
    return env, {a.value: a for a in env.action_space}, env.reset()


print("== E5: teleport targets across the map ==")
TARGETS = [
    (12, 25, "left room, open floor"),
    (27, 31, "corridor (the dot's own ring)"),
    (35, 31, "ON the colour-15 bar"),
    (46, 35, "right room, open floor"),
    (46, 28, "right slot interior"),
    (12, 34, "left slot interior"),
    (5, 10, "void outside the rooms"),
]
for x, y, what in TARGETS:
    env, A, obs = fresh()
    g = grid_of(obs)
    p0 = piece(g)
    obs = env.step(A[6], data={"x": x, "y": y})
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  ({x:2d},{y:2d}) {what}: DEAD FRAME")
        continue
    n = int((g != g2).sum())
    print(f"  ({x:2d},{y:2d}) {what:28s}: n={n:3d} piece {p0} -> {piece(g2)} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
    sys.stdout.flush()

print("\n== E7: park in each slot -- is standing there the level? ==")
for x, y, what in ((12, 34, "left slot"), (46, 28, "right slot")):
    env, A, obs = fresh()
    g = grid_of(obs)
    obs = env.step(A[6], data={"x": x, "y": y})
    g = grid_of(obs)
    print(f"  teleport to {what}: piece {piece(g)} lvl={obs.levels_completed}")
    for k in range(6):
        obs = env.step(A[1])      # nudge; any action ticks the clock
        g = grid_of(obs)
        if g is None:
            break
        if obs.levels_completed:
            print(f"    LEVEL after {k + 1} extra actions")
            break
    print(f"    after nudges: lvl={obs.levels_completed} "
          f"st={str(obs.state).split('.')[-1]}")
    sys.stdout.flush()
