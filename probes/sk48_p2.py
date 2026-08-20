"""sk48 hypothesis 2: finish the recipe. After the 8-grab (`sk48-p1.txt`) the
machine holds 8 at its mouth and the two remaining blocks SLID LEFT to
x32-35 -- a dispenser queue. The HUD order is 8, 14, 9. Continue: down to
14's rows, extend, retract; then to 9's rows; watch for the level.

Machine arm rows after p1's trip: y20-21. 14 sits at y31-34 (arm rows 32-33 =
A2 x2), 9 at y25-28 (arm rows 26-27 = A2 x1 from there... driven by diffs,
not arithmetic -- print everything.)
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def diff(a, b):
    if a is None or b is None:
        return "EMPTY"
    ch = np.argwhere(a != b)
    if not len(ch):
        return "-"
    ys, xs = ch[:, 0], ch[:, 1]
    pairs = {}
    for y, x in ch:
        pairs[(int(a[y, x]), int(b[y, x]))] = pairs.get((int(a[y, x]), int(b[y, x])), 0) + 1
    top = " ".join(f"{u}->{v}:{n}" for (u, v), n in
                   sorted(pairs.items(), key=lambda kv: -kv[1])[:5])
    return f"{len(ch)}c x[{xs.min()}-{xs.max()}] y[{ys.min()}-{ys.max()}] {top}"


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sk48"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = grid_of(obs)
# p1's grab of 8, then: down 2 to 14's rows, extend 3, retract 3;
# up 1 to 9's rows, extend 3, retract 3.
SEQ = ([1, 1, 1, 4, 4, 4, 4, 3, 3, 3, 3]
       + [2, 2, 4, 4, 4, 3, 3, 3]
       + [1, 4, 4, 4, 3, 3, 3])
for i, v in enumerate(SEQ):
    obs = env.step(A[v])
    if obs is None:
        print(f"{i:2d} A{v}: obs=None")
        break
    g2 = grid_of(obs)
    print(f"{i:2d} A{v}: {diff(g, g2)}  lvl={obs.levels_completed} "
          f"state={str(obs.state).split('.')[-1]}")
    g = g2
    if obs.levels_completed > 0:
        print("LEVEL UP")
        break
    if str(obs.state) != "GameState.NOT_FINISHED":
        break
    sys.stdout.flush()

if g is not None:
    print("\nboard after, rows y12-45 x10-50:")
    for y in range(12, 46):
        print(f"  y{y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                       for v in g[y, 10:50]))
