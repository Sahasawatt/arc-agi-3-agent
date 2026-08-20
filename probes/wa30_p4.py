"""wa30 probe 4: is the 12x4 ring a frame for the three 4x4 boxes?

    ./.venv/Scripts/python.exe wa30_p4.py

Measured so far (`results/wa30-p2.txt`, `wa30-p3.txt`): action 5 beside a box
GRABS it -- its 12 ring cells become the piece's own edge colour and the piece's
bounding box grows 4x4 -> 4x8 -- the box then travels with the piece, and a
second press puts it down where it stands. So wa30 is a carry puzzle.

The board offers exactly three 4x4 boxes and one 12x4 colour-9 ring whose inner
is colour 2. Three 4x4 boxes side by side are 12x4. That is a hypothesis with a
number in it, so it is worth one drive: carry a box up to the ring and see what
the engine says.
"""

import sys

import numpy as np

import arc_agi

CHARS = "0123456789abcdef"


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def held(g):
    ys, xs = np.nonzero((g == 14) | (g == 0))
    if not len(xs):
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()),
            int(((g == 14) | (g == 0)).sum()))


def cens(g):
    return {c: int((g == c).sum()) for c in sorted(set(g.ravel().tolist()))}


def show(g, label, y0=22, y1=48, x0=10, x1=54):
    print(f"  -- {label} --")
    for y in range(y0, y1 + 1):
        row = "".join(CHARS[int(v) & 0xF] for v in g[y, x0:x1 + 1])
        if set(row) - {"1"}:
            print(f"    y={y:2d} {row}")


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["wa30"].game_id)
A = {a.value: a for a in env.action_space}
NAME = {1: "up", 2: "down", 3: "left", 4: "right", 5: "act5"}

obs = env.reset()
# grab B3 (32,36) from below, then drive the carried pair straight up at the ring
plan = [1, 1, 5, 1, 1, 1, 1]
for i, a in enumerate(plan):
    obs = env.step(A[a])
    g = grid_of(obs)
    if g is None:
        print(f"  {i:2d} {NAME[a]:5s}: empty frame state={obs.state}")
        break
    print(f"  {i:2d} {NAME[a]:5s}: carried={held(g)} lvl={obs.levels_completed} "
          f"census={cens(g)}")
    if obs.levels_completed > 0:
        print("  LEVEL CLEARED")
        break
show(g, "after driving the carried box at the ring")

print("\n== and with a DROP once it will not go further ==")
obs = env.step(A[5])
g2 = grid_of(obs)
print(f"  drop: carried={held(g2)} lvl={obs.levels_completed} census={cens(g2)}")
show(g2, "after the drop")
sys.stdout.flush()
