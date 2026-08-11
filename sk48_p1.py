"""sk48 hypothesis 1: a grabber rides the left track (A1 = up 6px), its arm
(the 12-cell woven strip at y38-39) extends right with A4 and retracts with
A3, and the right wall holds three 4x4 blocks -- 8 at y19-22, 9 at y25-28,
14 at y31-34, all at x42-45 -- while the bottom HUD names an ORDER
(8, then 14, then 9). Baseline 61.

Drive: A1 x3 (arm rows y38-39 -> y20-21, inside 8's rows), A4 x4 (tip to
x41-46, overlapping 8's box), then A3 x4 back. Print a diff line per press.
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
SEQ = [1, 1, 1, 4, 4, 4, 4, 3, 3, 3, 3]
for i, v in enumerate(SEQ):
    obs = env.step(A[v])
    g2 = grid_of(obs)
    print(f"{i:2d} A{v}: {diff(g, g2)}  lvl={obs.levels_completed} "
          f"state={str(obs.state).split('.')[-1]}")
    g = g2
    sys.stdout.flush()

print("\nboard after the trip, rows y12-45 x10-50:")
for y in range(12, 46):
    print(f"  y{y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                   for v in g[y, 10:50]))
