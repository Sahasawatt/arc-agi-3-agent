"""sp80 probe 12: the complete transfer map of level 2 -- position -> target body.

    ./.venv/Scripts/python.exe sp80_p12.py

For every reachable player position: fire once, read WHICH body holds colour 9
after (full blob compare, not 8-cell samples). Output one line per row of the
lattice, symbol per column: '.' unreachable, '-' no transfer, '1' block-1,
'2' block-2, '?' other.
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


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
obs = env.reset()
obs = env.step(A[1])

X0, Y0 = 20, 36
B1 = (8, 16)
B2 = (28, 24)
rows = {}
for ty in range(12, 53, 4):
    line = []
    for tx in range(0, 61, 4):
        obs = env.reset()
        if obs.levels_completed == 0:
            for a in RECIPE1:
                obs = env.step(A[a])
        dx = (tx - X0) // 4
        dy = (ty - Y0) // 4
        moves = [4] * max(dx, 0) + [3] * max(-dx, 0) + [2] * max(dy, 0) + [1] * max(-dy, 0)
        if len(moves) + 1 > 44:
            line.append(".")
            continue
        dead = False
        for a in moves:
            obs = env.step(A[a])
            if obs.state.name != "NOT_FINISHED":
                dead = True
                break
        if dead:
            line.append(".")
            continue
        g = grid(obs)
        nines = blobs(g, 9)
        if not (len(nines) == 1 and nines[0][:2] == (tx, ty)):
            line.append(".")
            continue
        obs = env.step(A[5])
        g = grid(obs)
        nines = blobs(g, 9)
        if obs.levels_completed > 1:
            line.append("W")
        elif len(nines) == 1 and nines[0][:2] == (tx, ty) and nines[0][4] == 80:
            line.append("-")
        elif len(nines) == 1 and nines[0][:2] == B1:
            line.append("1")
        elif len(nines) == 1 and nines[0][:2] == B2:
            line.append("2")
        else:
            line.append("?")
    rows[ty] = "".join(line)

print("transfer map (x-left 0..60 step 4, per row y-top):")
print("        x: " + " ".join(f"{x:>2d}" for x in range(0, 61, 4)))
for ty in sorted(rows):
    print(f"  y={ty:2d}   {'  '.join(rows[ty])}")
sys.stdout.flush()
