"""ka59 with an AIMED click.

The standing wall: keyboard BFS exhausts 74 states with no win; the grey dot
kicked east lands at (43,31), three cells short of the right slot, and
nothing can reach it there. "Clicks are inert -- a 440-point full-grid sweep
changed zero cells" was measured through the un-aimed call, so the click
channel has never actually been asked.

The aimed sweep found the dot's own cells answer n=3 (results/
click-sweep-all.txt). Three cells is the dot MOVING one step. So:

E1  what a click on the dot does -- board before/after, exact cells.
E2  can repeated clicks WALK the dot? Click it, find it again, click again.
E3  the endgame the geometry forbids: kick the dot east (it lands at 43,31),
    then click it the last cells into the right slot interior (45-47,27-29).
E4  and if clicks move it freely, skip the kick: click it all the way west
    into the LEFT slot (10-14,32-36) -- nearer, and the level may want either.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def dot(g):
    """The grey dot: colour-5 cells outside the HUD row, as a box."""
    ys, xs = np.nonzero(g[:63] == 5)
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())) if len(ys) else None


def piece(g):
    """The piece: colour-0 cells off the HUD row y63."""
    ys, xs = np.nonzero(g[:63] == 0)
    return (int(xs.min()), int(ys.min())) if len(ys) else None


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def fresh():
    env = arc.make(envs["ka59"].game_id)
    return env, {a.value: a for a in env.action_space}, env.reset()


print("== E1: one aimed click on the dot ==")
env, A, obs = fresh()
g = grid_of(obs)
d = dot(g)
print(f"  dot at {d}, piece at {piece(g)}")
cx, cy = (d[0] + d[1]) // 2, (d[2] + d[3]) // 2
obs = env.step(A[6], data={"x": cx, "y": cy})
g2 = grid_of(obs)
ys, xs = np.nonzero(g != g2)
print(f"  click({cx},{cy}): n={int((g != g2).sum())} "
      f"changed {[(int(x), int(y), int(g[y, x]), int(g2[y, x])) for y, x in zip(ys, xs)]}")
print(f"  dot now {dot(g2)} lvl={obs.levels_completed}")
sys.stdout.flush()

print("\n== E2: walk the dot by clicking, 12 presses ==")
env, A, obs = fresh()
g = grid_of(obs)
for k in range(12):
    d = dot(g)
    if d is None:
        print(f"  press {k}: dot gone")
        break
    cx, cy = (d[0] + d[1]) // 2, (d[2] + d[3]) // 2
    obs = env.step(A[6], data={"x": cx, "y": cy})
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  press {k}: DEAD FRAME")
        break
    print(f"  press {k}: click({cx},{cy}) n={int((g != g2).sum()):3d} "
          f"dot {d} -> {dot(g2)} lvl={obs.levels_completed} "
          f"st={str(obs.state).split('.')[-1]}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed}")
        break
    sys.stdout.flush()
