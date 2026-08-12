"""ka59: the piece carries (its ring travels, n=18-19 per move vs 8-9 bare)
and the dot is off the board -- find the DROP.

From the ferried state (kick east, click the landing), click every
distinctive target on the board, one fresh episode each, and read what
changes. Targets: the right slot interior and walls, the empty ring left in
the corridor, the left slot interior, the piece itself, the bar, open floor
in both rooms. Additionally, the same sweep from a state standing INSIDE the
right slot -- a drop may be position-gated.
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


def ferried(park=None):
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
    if park:
        obs = walk_to(env, A, obs, park[0], park[1])
    return env, A, obs


TARGETS = [
    (46, 28, "right slot interior"),
    (47, 26, "right slot top wall"),
    (25, 31, "the empty ring in the corridor"),
    (12, 34, "left slot interior"),
    (35, 31, "the colour-15 bar"),
    (50, 35, "right room open floor"),
    (12, 25, "left room open floor"),
]

for park, plabel in ((None, "standing at the landing (43,31)"),
                     ((46, 28), "standing IN the right slot")):
    print(f"== drop sweep, {plabel} ==")
    for x, y, what in TARGETS:
        env, A, obs = ferried(park)
        g = grid_of(obs)
        p0 = piece(g)
        obs = env.step(A[6], data={"x": x, "y": y})
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  ({x:2d},{y:2d}) {what}: DEAD FRAME")
            continue
        n = int((g != g2).sum())
        tag = ""
        if n > 1:
            ys, xs = np.nonzero(g != g2)
            tag = f"  changed y{ys.min()}-{ys.max()} x{xs.min()}-{xs.max()}"
        print(f"  ({x:2d},{y:2d}) {what:30s}: n={n:3d} piece {p0} -> "
              f"{piece(g2)} dot={dot(g2)} lvl={obs.levels_completed}{tag}")
        sys.stdout.flush()
    print()
