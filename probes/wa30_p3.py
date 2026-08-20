"""wa30 probe 3: action 5 beside a box GRABS it -- then what?

    ./.venv/Scripts/python.exe wa30_p3.py

Measured in `results/wa30-p2.txt` A: standing under the box at (32,36) and
pressing action 5 turns its 12 ring cells from the highlight colour 3 into
colour 0 -- the piece's own edge colour -- and the piece's (14|0) bounding box
grows from 4x4 to 4x8. Nothing in `wa30-acts.txt` could see that, because there
action 5 was only ever pressed from the start square.

Asks the obvious follow-ups: does the grabbed box travel with the piece, can a
second one be grabbed, does the big 12x4 colour-9 ring with the colour-2 inner
take them, and does a press release.
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


def show(g, label, y0=20, y1=56, x0=8, x1=56):
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
plan = [1, 1, 5,            # under B3, grab it
        2, 3, 1,            # try to carry it around
        5,                  # press again: release?
        1, 3, 3, 3, 5]      # head for the big ring and press
for i, a in enumerate(plan):
    obs = env.step(A[a])
    g = grid_of(obs)
    if g is None:
        print(f"  {i:2d} {NAME[a]:5s}: empty frame state={obs.state}")
        break
    print(f"  {i:2d} {NAME[a]:5s}: piece={held(g)} lvl={obs.levels_completed} "
          f"census={cens(g)}")
    if obs.levels_completed > 0:
        print("  LEVEL CLEARED")
        break

show(g, "board after the drive")
sys.stdout.flush()
