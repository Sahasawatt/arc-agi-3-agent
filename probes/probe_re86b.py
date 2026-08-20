"""re86 probe B: direction map, board-edge behaviour, lattice parity.

    ./.venv/Scripts/python.exe probe_re86b.py

Parity is the whole question. Both crosses spawn on x%3==0, y%3==0; every B-box
inner is OFF that lattice, so no centre can ever land on one -- UNLESS the board
edge clamps a move to less than 3 and shifts the lattice.
"""

import numpy as np

import arc_agi

BOX_B = [(48, 16), (40, 24), (53, 24), (48, 35)]
BOX_P = [(15, 3), (6, 9), (24, 9), (15, 17)]


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def at(g):
    """The @ cell (colour 0) -- rides the ACTIVE cross's centre. (x, y) or None."""
    if g is None:
        return None
    ys, xs = np.nonzero(g == 0)
    return (int(xs[0]), int(ys[0])) if len(xs) else None


def census(g):
    if g is None:
        return {}
    v, c = np.unique(g, return_counts=True)
    return dict(zip(v.tolist(), c.tolist()))


arc = arc_agi.Arcade()
env = arc.make("re86")
A = {a.value: a for a in env.action_space}

# 1. direction map
print("== direction map ==")
for a in (1, 2, 3, 4):
    obs = env.reset()
    p0 = at(grid(obs))
    obs = env.step(A[a])
    p1 = at(grid(obs))
    print(f"  action {a}: {p0} -> {p1}  d={(p1[0] - p0[0], p1[1] - p0[1]) if p1 else None}")

# 2. push to each edge, 30 presses, log the tail
print("\n== edge behaviour (B-cross, 30 presses each way) ==")
for a in (1, 2, 3, 4):
    obs = env.reset()
    seen = []
    dead = None
    for i in range(30):
        obs = env.step(A[a])
        g = grid(obs)
        p = at(g)
        seen.append(p)
        if obs is not None and str(obs.state) != "GameState.NOT_FINISHED":
            dead = (i, str(obs.state))
            break
    print(f"  action {a}: last6={seen[-6:]} dead={dead}")
    print(f"           census@end={census(grid(obs))}")

# 3. after clamping on one axis, is the lattice shifted?
print("\n== parity after an edge push ==")
obs = env.reset()
for _ in range(30):
    obs = env.step(A[3])  # assume 3 = -x; corrected by the map above if not
    if obs is None or str(obs.state) != "GameState.NOT_FINISHED":
        break
p = at(grid(obs))
print("  after 30x action3:", p, "state", None if obs is None else str(obs.state))
if p:
    print("  x%3 =", p[0] % 3, " y%3 =", p[1] % 3, "(spawn was 36%3=0, 45%3=0)")
    print("  B-box inners reachable now:", [b for b in BOX_B if (b[0] - p[0]) % 3 == 0 and (b[1] - p[1]) % 3 == 0])
    print("  P-box inners reachable now:", [b for b in BOX_P if (b[0] - p[0]) % 3 == 0 and (b[1] - p[1]) % 3 == 0])
