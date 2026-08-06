"""re86 probe C: what is the colour-15 -> colour-1 bar, and what happens at zero?

    ./.venv/Scripts/python.exe probe_re86c.py

Probe B found 19 of the 64 colour-15 HUD cells flip to colour 1 after 30 presses,
identically for every direction. Either a per-action budget or something else --
this measures the curve, locates the cells, and drives it to zero.
"""

import numpy as np

import arc_agi

CHARS = "0123456789abcdef"


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def at(g):
    if g is None:
        return None
    ys, xs = np.nonzero(g == 0)
    return (int(xs[0]), int(ys[0])) if len(xs) else None


def bar(g):
    return -1 if g is None else int((g == 1).sum())


def show(g, rows=None):
    for y in rows if rows else range(g.shape[0]):
        print(f"  y={y:2d} " + "".join(CHARS[v & 0xF] for v in g[y]))


arc = arc_agi.Arcade()
env = arc.make("re86")
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = grid(obs)
r15 = [y for y in range(64) if (g[y] == 15).all()]
print("solid colour-15 rows at reset:", r15)
print("colour-15 cells by row:", {y: int((g[y] == 15).sum()) for y in range(64) if (g[y] == 15).any()})

# curve: bar vs action count, per action kind
print("\n== bar vs presses ==")
for a in (1, 5, 3):
    env.reset()
    marks = []
    for i in range(1, 41):
        o = env.step(A[a])
        marks.append(bar(grid(o)))
    print(f"  action {a}: {marks}")

# where do the colour-1 cells sit?
env.reset()
for _ in range(10):
    o = env.step(A[1])
g = grid(o)
print("\ncolour-1 cells by row:", {y: int((g[y] == 1).sum()) for y in range(64) if (g[y] == 1).any()})
print("colour-1 x range:", np.nonzero(g == 1)[1].min(), np.nonzero(g == 1)[1].max())
show(g, r15)

# drive it to zero: alternate right/left so the cross returns to spawn each pair
print("\n== to zero (alternating 4/3) ==")
env.reset()
last = None
for i in range(1, 301):
    o = env.step(A[4 if i % 2 else 3])
    g = grid(o)
    b, st = bar(g), (None if o is None else str(o.state))
    if b != last or st != "GameState.NOT_FINISHED":
        print(f"  i={i:3d} bar={b:2d} @={at(g)} state={st} lvl={None if o is None else o.levels_completed}")
        last = b
    if st is not None and st != "GameState.NOT_FINISHED":
        break

# the action-2 mystery from probe B: no @ at all after 30 downs
print("\n== 30x action 2 ==")
env.reset()
for i in range(30):
    o = env.step(A[2])
g = grid(o)
v, c = np.unique(g, return_counts=True)
print("  census:", dict(zip(v.tolist(), c.tolist())), "state", str(o.state))
show(g, [y for y in range(64) if (g[y] != 5).any()])
