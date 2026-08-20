"""g50t probe 2: is the goal reachable at all while colour 8 counts as a wall?

    ./.venv/Scripts/python.exe g50t_p2.py

Probe 1 measured colour 8 to be a KEY: the piece covering the x39-41 column
consumed 16 of its cells and turned 24 wall cells into floor (`g50t-p1.txt`).
The live model meanwhile reads `block=[0, 8]` (`results/g50t-run1.txt`), so no
route it plans will ever aim at one. This asks the question that decides whether
that matters: with 8 as wall, can the piece reach the goal box at all?

Offline BFS on the reset frame only -- no engine steps, no scorecard.
"""

import sys
from collections import deque

import numpy as np

import arc_agi

STEP = 6          # measured, `results/g50t-acts.txt`
PW = PH = 5       # the piece's footprint, measured


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def blobs(g, colour, ymax=60, xmin=11):
    ys, xs = np.nonzero(g == colour)
    cells = {(int(x), int(y)) for x, y in zip(xs, ys) if y < ymax and x >= xmin}
    out = []
    while cells:
        stack, blob = [next(iter(cells))], set()
        while stack:
            p = stack.pop()
            if p in blob or p not in cells:
                continue
            blob.add(p)
            x, y = p
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) in cells:
                    stack.append((x + dx, y + dy))
        cells -= blob
        bx = [p[0] for p in blob]
        by = [p[1] for p in blob]
        out.append((min(bx), min(by), max(bx), max(by), len(blob)))
    return sorted(out)


def reach(g, start, passable):
    """Positions (x-left, y-top) the 5x5 piece can occupy, stepping by 6."""
    H, W = g.shape
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((0, -STEP), (0, STEP), (-STEP, 0), (STEP, 0)):
            n = (x + dx, y + dy)
            if n in seen or not (0 <= n[0] <= W - PW and 0 <= n[1] <= H - PH):
                continue
            foot = g[n[1]:n[1] + PH, n[0]:n[0] + PW]
            if not set(foot.ravel().tolist()) <= passable:
                continue
            seen.add(n)
            q.append(n)
    return seen


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["g50t"].game_id)
obs = env.reset()
g = grid_of(obs)

print("colour-8 blobs (the keys):")
for b in blobs(g, 8):
    print("  ", b)
print("colour-9 blobs off the clock row (piece + goal box + indicator):")
for b in blobs(g, 9, ymax=60, xmin=0):
    print("  ", b)

start = (14, 8)
GOAL = (43, 49, 49, 55)   # the ring of 9 at the bottom right, measured from the dump

for name, passable in (("8 is WALL (what the model believes)", {5, 9}),
                       ("8 is FLOOR (what probe 1 measured)", {5, 9, 8})):
    r = reach(g, start, passable)
    # a position "reaches the goal" if its footprint touches the goal ring
    touch = [p for p in r
             if p[0] <= GOAL[2] and p[0] + PW - 1 >= GOAL[0]
             and p[1] <= GOAL[3] and p[1] + PH - 1 >= GOAL[1]]
    onkey = [p for p in r if (g[p[1]:p[1] + PH, p[0]:p[0] + PW] == 8).any()]
    print(f"\n{name}: {len(r)} reachable positions")
    print(f"  positions whose footprint touches the goal box: {len(touch)} {touch[:6]}")
    print(f"  positions whose footprint covers a colour-8 cell: {len(onkey)} {onkey[:6]}")
sys.stdout.flush()
