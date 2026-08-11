"""sb26: every single click is inert from reset and ACTION7 is too
(`sb26-p1.txt`) -- the only thing that answers is ACTION5, one cell of the
y53 row per press. The roster's own trap says a no-op is a statement about
the STARTING STATE, so drive the state forward with ACTION5 and re-ask
everything from each new state:

  * 20 ACTION5 presses, diffing OUTSIDE the y53 row (does anything else ever
    move?), watching state/level.
  * after k in {1, 2, 3, 5, 8, 13} presses: ACTION7, then a click on each
    bottom block -- does either start answering?
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def diff(a, b, skip_row=53):
    if a is None or b is None:
        return "EMPTY FRAME"
    m = a != b
    m[skip_row] = False
    ch = np.argwhere(m)
    if not len(ch):
        return "-"
    ys, xs = ch[:, 0], ch[:, 1]
    pairs = {}
    for y, x in ch:
        pairs[(int(a[y, x]), int(b[y, x]))] = pairs.get((int(a[y, x]), int(b[y, x])), 0) + 1
    return (f"{len(ch)} cells x[{xs.min()}-{xs.max()}] y[{ys.min()}-{ys.max()}] "
            + " ".join(f"{u}->{v}:{n}" for (u, v), n in sorted(pairs.items())))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
click = next(a for a in env.action_space if a.is_complex())
A = {a.value: a for a in env.action_space}

print("== 20x ACTION5, diff excluding the y53 bar ==")
obs = env.reset()
g = grid_of(obs)
for i in range(20):
    obs = env.step(A[5])
    g2 = grid_of(obs)
    d = diff(g, g2)
    if d != "-" or i < 3:
        print(f"  {i}: {d}  state={str(obs.state).split('.')[-1]} lvl={obs.levels_completed}")
    g = g2
    if str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  terminal at {i}")
        break

BLOCKS = [("e", 20, 58), ("f", 28, 58), ("9", 36, 58), ("b", 44, 58)]
for k in (1, 2, 3, 5, 8, 13):
    obs = env.reset()
    for _ in range(k):
        obs = env.step(A[5])
    g0 = grid_of(obs)
    obs7 = env.step(A[7])
    print(f"after {k}x A5 -> ACTION7: {diff(g0, grid_of(obs7))}  "
          f"lvl={obs7.levels_completed}")
    for name, x, y in BLOCKS:
        obs = env.reset()
        for _ in range(k):
            obs = env.step(A[5])
        gk = grid_of(obs)
        click.set_data({"x": x, "y": y})
        obsC = env.step(click)
        d = diff(gk, grid_of(obsC))
        if d != "-":
            print(f"  after {k}x A5, click {name}: {d}  lvl={obsC.levels_completed}")
    sys.stdout.flush()
print("done")
