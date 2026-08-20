"""bp35 ascent test: after event #1, at WHICH x does the next event fire?

Fresh episode per candidate: A4 x4 (fires event #1 at x44), then walk to a
target x and record whether an event fired en route and where the piece was
when it did. If the ascent hypothesis holds, exactly one x-column of the new
chamber is the passage, and events elsewhere only feed the flood -- the
tell apart is whether the TOWER (y0-36) changes.
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


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

for walk, label in [([3] * 6, "walk LEFT to the wall"),
                    ([4] * 3, "walk RIGHT to the wall")]:
    env = arc.make(envs["bp35"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    for _ in range(4):
        obs = env.step(A[4])
    g = grid_of(obs)
    tower0 = g[:37].copy()
    print(f"== after event #1 (piece x={piece_x(g)}): {label} ==")
    for i, v in enumerate(walk):
        px_before = piece_x(g)
        obs = env.step(A[v])
        g2 = grid_of(obs)
        n = int((g != g2).sum())
        tower_moved = not np.array_equal(tower0, g2[:37])
        if n > 100 or tower_moved:
            print(f"  A{v} from x={px_before}: {n} cells, tower_moved={tower_moved}, "
                  f"piece x={piece_x(g2)} lvl={obs.levels_completed}")
            tower0 = g2[:37].copy()
        g = g2
        if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
            print(f"  END: lvl={obs.levels_completed} "
                  f"state={str(obs.state).split('.')[-1]}")
            break
    print(f"  final piece x={piece_x(g)}")
    sys.stdout.flush()
