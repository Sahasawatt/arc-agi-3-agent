"""ka59: the cheap remaining hypotheses, one run each.

A  kick the dot east and DO NOT follow -- park the piece in the left slot,
   its own ring, the dot's ring; hold each through several actions. (Two
   objects, two stations: maybe the level wants the dot resting east and the
   piece somewhere specific.)
B  carrying, walk INTO each wall of the right slot repeatedly (a drop by
   bump, the wa30 crate law).
C  carrying, walk into the LEFT slot and bump its walls.
D  kick, follow, and then HOLD through a full timer (100+ actions) -- the
   death was only ever measured in the left room, and the y63 bar may be a
   level clock (the re86 lesson) rather than a death everywhere.
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


def kicked():
    env = arc.make(envs["ka59"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    g = grid_of(obs)
    d = dot(g)
    obs = walk_to(env, A, obs, d[0] - 1, d[1])
    obs = env.step(A[4])
    return env, A, obs


print("== A: kick, don't follow, park somewhere ==")
for tx, ty, what in ((12, 34, "left slot interior"),
                     (19, 31, "the piece's own ring"),
                     (28, 31, "the dot's old ring")):
    env, A, obs = kicked()
    obs = walk_to(env, A, obs, tx, ty)
    g = grid_of(obs)
    lvl0 = obs.levels_completed
    for k in range(8):
        obs = env.step(A[1] if k % 2 else A[2])
        if obs is None or obs.levels_completed:
            break
    print(f"  park {what:22s}: piece={piece(g)} dot={dot(g)} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
    sys.stdout.flush()

print("\n== B: carrying, bump every right-slot wall ==")
env = arc.make(envs["ka59"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
d = dot(g)
obs = walk_to(env, A, obs, d[0] - 1, d[1])
obs = env.step(A[4])
g = grid_of(obs)
d2 = dot(g)
obs = env.step(A[6], data={"x": d2[0], "y": d2[1]})
for tx, ty, v, what in ((46, 31, 1, "bump north into the slot's south wall"),
                        (41, 28, 4, "bump east into its west wall"),
                        (52, 28, 3, "bump west into its east wall"),
                        (46, 23, 2, "bump south into its north wall")):
    obs = walk_to(env, A, obs, tx, ty)
    for _ in range(3):
        obs = env.step(A[v])
        if obs is None or obs.levels_completed:
            break
    g = grid_of(obs)
    print(f"  {what:38s}: piece={piece(g)} dot={dot(g)} "
          f"lvl={obs.levels_completed}")
    if obs.levels_completed:
        break
    sys.stdout.flush()

print("\n== D: ferried, hold through a full timer ==")
env, A, obs = kicked()
g = grid_of(obs)
d2 = dot(g)
obs = env.step(A[6], data={"x": d2[0], "y": d2[1]})
deaths = 0
for k in range(230):
    obs = env.step(A[1] if k % 2 else A[2])
    if obs is None:
        print("  obs None")
        break
    g = grid_of(obs)
    if obs.levels_completed:
        print(f"  LEVEL at extra action {k + 1}")
        break
    if str(obs.state) == "GameState.GAME_OVER":
        deaths += 1
        print(f"  GAME_OVER #{deaths} at extra action {k + 1}; resetting on")
        obs = env.reset()
        if deaths >= 2:
            break
print(f"  end: lvl={obs.levels_completed} deaths={deaths} "
      f"st={str(obs.state).split('.')[-1]}")
