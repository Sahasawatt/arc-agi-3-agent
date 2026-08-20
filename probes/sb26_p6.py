"""sb26: clicks do not even TICK the clock (every real action burns the y53
bar; a click leaves it alone), so either they are swallowed for the whole
level or they unlock at a state not yet reached. Two instruments:

  * one episode: at every bar length, click all four blocks + the machine +
    press ACTION7 (all free), burn one, repeat to death. Any response at any
    state gets caught.
  * do clicks return the SAME frame object or a fresh identical one, and does
    obs.frame ever hold more than one animation layer after any action?
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
click = next(a for a in env.action_space if a.is_complex())
A = {a.value: a for a in env.action_space}

SPOTS = [(20, 58), (28, 58), (36, 58), (44, 58), (32, 29)]

obs = env.reset()
layers = {len(np.array(obs.frame))}
g = grid_of(obs)
found = False
for burn in range(63):
    for x, y in SPOTS:
        click.set_data({"x": x, "y": y})
        obs = env.step(click)
        if obs is None:
            print(f"burn={burn} click({x},{y}): obs=None")
            continue
        layers.add(len(np.array(obs.frame)))
        g2 = grid_of(obs)
        if not np.array_equal(g, g2) or obs.levels_completed:
            print(f"burn={burn} click({x},{y}): RESPONSE "
                  f"cells={int((g != g2).sum())} lvl={obs.levels_completed}")
            found, g = True, g2
    obs = env.step(A[7])
    layers.add(len(np.array(obs.frame)))
    g2 = grid_of(obs)
    if not np.array_equal(g, g2) or obs.levels_completed:
        print(f"burn={burn} ACTION7: RESPONSE cells={int((g != g2).sum())} "
              f"lvl={obs.levels_completed}")
        found, g = True, g2
    obs = env.step(A[5])
    if obs is None or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"terminal at burn {burn}: "
              f"{'None' if obs is None else str(obs.state).split('.')[-1]}")
        break
    g = grid_of(obs)

print("any response ever:", found)
print("frame layer counts seen:", sorted(layers))
sys.stdout.flush()
