"""sb26: no probed spot answers a click. Stop guessing spots -- sweep the
whole board: one episode per spot, click, diff (bar row excluded), record any
responder. Also try click SEQUENCES on the bottom blocks (top-row order and
bottom-row order) in single episodes, ACTION7 after each, since a selection
game may only draw once a valid sequence starts.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def changed(a, b, skip_row=53):
    if a is None or b is None:
        return -1
    m = a != b
    m[skip_row] = False
    return int(m.sum())


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
click = next(a for a in env.action_space if a.is_complex())
A = {a.value: a for a in env.action_space}

print("== full-grid click sweep, stride 2 ==")
hits = []
n = 0
for y in range(0, 64, 2):
    for x in range(0, 64, 2):
        obs = env.reset()
        g0 = grid_of(obs)
        click.set_data({"x": x, "y": y})
        obs = env.step(click)
        g1 = grid_of(obs)
        c = changed(g0, g1)
        n += 1
        if c > 0 or (obs is not None and obs.levels_completed > 0):
            hits.append((x, y, c, obs.levels_completed))
            print(f"  ({x},{y}): {c} cells lvl={obs.levels_completed}")
        if obs is None:
            print(f"  ({x},{y}): obs=None (engine rejected)")
print(f"swept {n} spots, {len(hits)} responders")

print("\n== click sequences on the bottom blocks ==")
BLOCK = {"e": (20, 58), "f": (28, 58), "9": (36, 58), "b": (44, 58)}
for label, order in [("top-row order 9,e,b,f", "9ebf"),
                     ("bottom-row order e,f,9,b", "ef9b")]:
    obs = env.reset()
    g0 = grid_of(obs)
    for ch in order:
        x, y = BLOCK[ch]
        click.set_data({"x": x, "y": y})
        obs = env.step(click)
    g1 = grid_of(obs)
    print(f"  {label}: {changed(g0, g1)} cells lvl={obs.levels_completed} "
          f"state={str(obs.state).split('.')[-1]}")
    obs = env.step(A[7])
    print(f"    then ACTION7: lvl={obs.levels_completed} "
          f"state={str(obs.state).split('.')[-1]}")
    sys.stdout.flush()
