"""bp35 probe: full frames at every event of one shuttle run, plus what the
first event actually rearranges (reset vs event #1, cell by cell, as row
ranges). The band fingerprint hid sub-band structure; this does not."""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def dump(g, label):
    print(label)
    for y in range(64):
        print(f"  y{y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                       for v in g[y]))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = grid_of(obs)
dump(g, "== RESET ==")
events = 0
plan = [4] * 5 + [3, 4] * 12
for i, v in enumerate(plan):
    obs = env.step(A[v])
    g2 = grid_of(obs)
    n = int((g != g2).sum())
    if n > 100:
        events += 1
        dump(g2, f"== EVENT #{events} (i={i}, A{v}) ==")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"end: lvl={obs.levels_completed} state={str(obs.state).split('.')[-1]} "
              f"after {events} events")
        break
    sys.stdout.flush()
