"""sp80 probe 8: is ACTION5 a control transfer? Who moves after the swap?

    ./.venv/Scripts/python.exe sp80_p8.py

From the level-2 start, run scripted sequences and print the 9/8 blob maps after
every step. Blob detector accumulates nothing -- occlusion caveat applies, so
every reading that matters is taken with bodies apart.
"""

import sys

import numpy as np

import arc_agi

RECIPE1 = [4, 4, 4, 5]


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def blobs(g, colour):
    if g is None:
        return []
    ys, xs = np.nonzero(g == colour)
    cells = set(zip(xs.tolist(), ys.tolist()))
    out = []
    while cells:
        stack = [next(iter(cells))]
        blob = set()
        while stack:
            c = stack.pop()
            if c in blob or c not in cells:
                continue
            blob.add(c)
            x, y = c
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) in cells:
                    stack.append((x + dx, y + dy))
        cells -= blob
        bx = [c[0] for c in blob]
        by = [c[1] for c in blob]
        out.append((min(bx), min(by), max(bx), max(by), len(blob)))
    return sorted(out)


def show(g, tag):
    print(f"  {tag}: 9={blobs(g, 9)} 8={blobs(g, 8)}")


def fresh_l2(env, A):
    obs = env.reset()
    if obs.levels_completed == 0:
        for a in RECIPE1:
            obs = env.step(A[a])
    assert obs.levels_completed == 1
    return obs


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
obs = env.reset()
obs = env.step(A[1])

print("== S1: walk to (0,28), fire, then press RIGHT twice -- who moves? ==")
obs = fresh_l2(env, A)
for a in [3, 3, 3, 3, 3, 1, 1]:
    obs = env.step(A[a])
show(grid(obs), "at (0,28) pre-fire")
obs = env.step(A[5])
show(grid(obs), "post-fire")
obs = env.step(A[4])
show(grid(obs), "after RIGHT 1")
obs = env.step(A[4])
show(grid(obs), "after RIGHT 2")
obs = env.step(A[5])
show(grid(obs), "after fire 2")
obs = env.step(A[4])
show(grid(obs), "after RIGHT 3")
print(f"  state={obs.state.name} lvl={obs.levels_completed}")

print("\n== S2: boundary pairs -- fire at (24,20) vs (28,20), (20,24) vs (24,24) ==")
for route, name in [([4, 1, 1, 1, 1], "(24,20)"),
                    ([4, 4, 1, 1, 1, 1], "(28,20)"),
                    ([1, 1, 1], "(20,24)"),
                    ([4, 1, 1, 1], "(24,24)")]:
    obs = fresh_l2(env, A)
    for a in route:
        obs = env.step(A[a])
    pre = grid(obs)
    show(pre, f"{name} pre")
    obs = env.step(A[5])
    cur = grid(obs)
    d = (pre != cur) if cur is not None else np.zeros((64, 64), bool)
    d[63, :] = False
    n = int(d.sum())
    show(cur, f"{name} post (diff={n})")

print("\n== S3: double fire at one spot -- does it swap back? ==")
obs = fresh_l2(env, A)
for a in [3, 3, 3, 3, 3, 1, 1]:
    obs = env.step(A[a])
obs = env.step(A[5])
show(grid(obs), "fire 1")
obs = env.step(A[5])
show(grid(obs), "fire 2")
obs = env.step(A[5])
show(grid(obs), "fire 3")
print(f"  state={obs.state.name}")
sys.stdout.flush()
