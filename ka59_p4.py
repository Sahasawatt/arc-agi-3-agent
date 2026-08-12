"""ka59: the click PICKS THE DOT UP -- so carry it to a slot and drop it.

E8 measured: after clicking onto the dot the dot is gone from the frame even
once the piece steps away, so the piece is carrying it. The drop is the
remaining unknown; candidates are a second click (on the piece, or on a
destination), or simply standing in a slot.

E11  carry to the LEFT slot interior (12,34), then: stand, click self, click
     the slot centre -- one arm each, level read after every action.
E12  the same at the RIGHT slot interior (46,28) -- reachable now, since a
     carried dot needs no corridor. The piece walks with step 3, so the walk
     is driven by coordinates, not by a fixed press count.
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
    """Greedy coordinate walk; returns (obs, ok)."""
    g = grid_of(obs)
    for _ in range(budget):
        p = piece(g)
        if p is None:
            return obs, False
        if abs(p[0] - tx) <= 1 and abs(p[1] - ty) <= 1:
            return obs, True
        dx, dy = tx - p[0], ty - p[1]
        v = (4 if dx > 0 else 3) if abs(dx) >= abs(dy) else (2 if dy > 0 else 1)
        obs = env.step(A[v])
        g2 = grid_of(obs)
        if g2 is None or obs.levels_completed or \
                str(obs.state) != "GameState.NOT_FINISHED":
            return obs, True
        if piece(g2) == p:
            # refused: try the other axis
            v = (2 if dy > 0 else 1) if abs(dx) >= abs(dy) else (4 if dx > 0 else 3)
            obs = env.step(A[v])
            g2 = grid_of(obs)
            if g2 is None:
                return obs, False
        g = g2
    return obs, False


for tx, ty, label in ((12, 34, "LEFT slot"), (46, 28, "RIGHT slot")):
    for drop, dname in ((None, "just stand"), ("self", "click the piece"),
                        ("slot", "click the slot centre")):
        env = arc.make(envs["ka59"].game_id)
        A = {a.value: a for a in env.action_space}
        obs = env.reset()
        g = grid_of(obs)
        d0 = dot(g)
        obs = env.step(A[6], data={"x": d0[0], "y": d0[1]})   # pick up
        obs, ok = walk_to(env, A, obs, tx, ty)
        g = grid_of(obs)
        p = piece(g) if g is not None else None
        if drop == "self" and p:
            obs = env.step(A[6], data={"x": p[0], "y": p[1]})
        elif drop == "slot":
            obs = env.step(A[6], data={"x": tx, "y": ty})
        g2 = grid_of(obs)
        print(f"  {label:10s} + {dname:22s}: piece={piece(g2) if g2 is not None else '?'} "
              f"dot={dot(g2) if g2 is not None else '?'} "
              f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
        sys.stdout.flush()
