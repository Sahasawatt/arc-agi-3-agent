"""sp80 probe 5 (level 2): can the player push the colour-8 blocks? wall map.

    ./.venv/Scripts/python.exe sp80_p5.py

Enters level 2 via the level-1 recipe (right x3, fire), then probes from level
resets. Player starts at (20,36); 8-blocks at (8,16) and (28,24).
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


def pos(g, colour):
    if g is None:
        return []
    ys, xs = np.nonzero(g == colour)
    if len(xs) == 0:
        return []
    # split into blobs by x-left of 12-wide runs: cheap -- report bbox list per row-band
    cells = set(zip(xs.tolist(), ys.tolist()))
    blobs = []
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
        blobs.append((min(bx), min(by), max(bx), max(by)))
    return sorted(blobs)


def to_level2(env, A):
    obs = env.reset()
    if obs.levels_completed == 1:
        return obs
    for a in RECIPE1:
        obs = env.step(A[a])
    assert obs.levels_completed == 1, f"recipe failed: lvl={obs.levels_completed}"
    return obs


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
obs = env.reset()
obs = env.step(A[1])
obs = to_level2(env, A)

print("== A: walk UP into the (28,24) 8-block (player x20-39 overlaps x28-39) ==")
for i in range(6):
    obs = env.step(A[1])
    g = grid(obs)
    print(f"  up#{i}: player={pos(g, 9)} eights={pos(g, 8)} state={obs.state.name}")
    if obs.state.name != "NOT_FINISHED":
        break

print("\n== B: walk LEFT into the (8,16) 8-block after climbing beside it ==")
obs = to_level2(env, A)
# player (20,36) -> go up to y16 row first at x20 (clear of both 8s? (8,16) spans x8-19 -- x20 clear)
seq = [1, 1, 1, 1, 1]  # y36 -> y16
for a in seq:
    obs = env.step(A[a])
g = grid(obs)
print(f"  after climb: player={pos(g, 9)} eights={pos(g, 8)} state={obs.state.name}")
for i in range(4):
    obs = env.step(A[3])
    g = grid(obs)
    print(f"  left#{i}: player={pos(g, 9)} eights={pos(g, 8)} state={obs.state.name}")
    if obs.state.name != "NOT_FINISHED":
        break

print("\n== C: level-2 wall map from start (20,36) ==")
for d, name in [(1, "up"), (2, "down"), (3, "left"), (4, "right")]:
    obs = to_level2(env, A)
    last = pos(grid(obs), 9)
    moves = 0
    for i in range(12):
        obs = env.step(A[d])
        g = grid(obs)
        if obs.state.name != "NOT_FINISHED":
            print(f"  {name}: terminal {obs.state.name} after {i+1} presses at {last}")
            break
        b = pos(g, 9)
        if b == last:
            print(f"  {name}: stops at {b} after {moves} moves")
            break
        last = b
        moves += 1
    else:
        print(f"  {name}: still moving at {last}")
sys.stdout.flush()
