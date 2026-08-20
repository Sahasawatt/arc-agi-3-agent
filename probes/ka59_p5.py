"""ka59: the dot is a FERRY -- kick it over the bar, then click it to follow.

The click moves the piece onto the dot wherever the dot is (ka59-p2/p3), and
the kick sends the dot east over the bar to (43,31) (the standing recon). So
the right room, unreachable by walking in every earlier probe, is reachable
in two moves: kick, then click the landing spot. Nothing about the piece's
side of the bar is in the way of either.

E13  kick east (walk into the dot), read where it lands, click it, and
     confirm the piece is in the right room.
E14  from there, drive the endgame candidates in one run each:
     a) walk into the dot from the west -- another kick, now aimed at the
        right slot's row? read where it goes;
     b) pick it up (click) and walk into the right slot interior;
     c) just walk the piece into the right slot interior, leaving the dot.
Every arm prints piece, dot and level after each action group.
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
    return (int(xs.min()), int(ys.min())) if len(ys) else None


def dot(g):
    ys, xs = np.nonzero(g[:63] == 5)
    return (int(xs.min()), int(ys.min())) if len(ys) else None


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
DIRS = {1: (0, -3), 2: (0, 3), 3: (-3, 0), 4: (3, 0)}


def walk_to(env, A, obs, tx, ty, budget=30):
    g = grid_of(obs)
    for _ in range(budget):
        p = piece(g)
        if p is None or (abs(p[0] - tx) <= 1 and abs(p[1] - ty) <= 1):
            return obs
        dx, dy = tx - p[0], ty - p[1]
        v = (4 if dx > 0 else 3) if abs(dx) >= abs(dy) else (2 if dy > 0 else 1)
        obs = env.step(A[v])
        g2 = grid_of(obs)
        if g2 is None or obs.levels_completed or \
                str(obs.state) != "GameState.NOT_FINISHED":
            return obs
        if piece(g2) == p:
            v = (2 if dy > 0 else 1) if abs(dx) >= abs(dy) else (4 if dx > 0 else 3)
            obs = env.step(A[v])
            g2 = grid_of(obs)
            if g2 is None:
                return obs
        g = g2
    return obs


def ferried(label):
    """Fresh episode driven to: dot kicked east, piece clicked across."""
    env = arc.make(envs["ka59"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    g = grid_of(obs)
    d = dot(g)
    obs = walk_to(env, A, obs, d[0] - 1, d[1])     # stand west of the dot
    obs = env.step(A[4])                            # kick east
    g = grid_of(obs)
    d2 = dot(g)
    obs = env.step(A[6], data={"x": d2[0], "y": d2[1]})   # follow it
    g = grid_of(obs)
    print(f"  [{label}] kick: dot {d} -> {d2}; click: piece={piece(g)} "
          f"dot={dot(g)} lvl={obs.levels_completed}")
    return env, A, obs


print("== E13/E14a: kick, follow, kick again ==")
env, A, obs = ferried("a")
g = grid_of(obs)
p = piece(g)
# the piece now stands where the dot was; the dot may be underneath (occluded)
# or picked up. Step west then walk back east INTO that square to re-kick.
obs = env.step(A[3])
g = grid_of(obs)
print(f"    step west: piece={piece(g)} dot={dot(g)}")
obs = env.step(A[4])
g = grid_of(obs)
print(f"    walk back east: piece={piece(g)} dot={dot(g)} "
      f"lvl={obs.levels_completed}")
sys.stdout.flush()

print("\n== E14b: follow, then carry into the right slot interior ==")
env, A, obs = ferried("b")
obs = walk_to(env, A, obs, 46, 28)
g = grid_of(obs)
print(f"    at slot: piece={piece(g)} dot={dot(g)} lvl={obs.levels_completed} "
      f"st={str(obs.state).split('.')[-1]}")
sys.stdout.flush()

print("\n== E14c: leave the dot at its landing, walk the piece to the slot ==")
env = arc.make(envs["ka59"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
d = dot(g)
obs = walk_to(env, A, obs, d[0] - 1, d[1])
obs = env.step(A[4])
g = grid_of(obs)
d2 = dot(g)
obs = env.step(A[6], data={"x": d2[0], "y": d2[1]})       # cross the bar
obs = env.step(A[2])                                       # step OFF the dot
g = grid_of(obs)
print(f"    after stepping off: piece={piece(g)} dot={dot(g)}")
obs = walk_to(env, A, obs, 46, 28)
g = grid_of(obs)
print(f"    at slot: piece={piece(g)} dot={dot(g)} lvl={obs.levels_completed} "
      f"st={str(obs.state).split('.')[-1]}")
