"""Replay a prefix, then probe, printing what the GATE reader sees — piece, panel, doors.

    uv run python probe6.py ls20 <prefix-file> <probe-actions>

`walk.py`'s readers predate the gate: its `block()` takes the first colour-12 component
(a decoy on level 6) and its plate reader cannot parse the indicator panel. This one
reads plates with `gate.plates` — the reader the agent itself trusts — and prints every
colour-12 component so the piece is found by eye, not by a guess baked into the tool.
"""

import sys

import numpy as np

import arc_agi
from arcengine import GameState
from gate import plates
from perception import components, hud

GAME = sys.argv[1]
PREFIX = [int(a) for a in open(sys.argv[2]).read().strip().split(",")]
PROBE = [int(a) for a in sys.argv[3].split(",")] if len(sys.argv) > 3 else []

arc = arc_agi.Arcade()
env = arc.make(GAME)
obs = env.reset()
space = {a.value: a for a in env.action_space}

for a in PREFIX:
    obs = env.step(space[a])
    if np.array(obs.frame).size == 0 or obs.state == GameState.GAME_OVER:
        obs = env.reset()


def show(tag):
    grid = np.array(obs.frame)[-1]
    twelves = ["x%d-%d y%d-%d (%d)" % (x0, x1, y0, y1, n)
               for x0, x1, y0, y1, n in components(grid, 12)]
    print("%s lvl=%d hud=%s" % (tag, obs.levels_completed, hud(obs.frame)))
    print("   piece12: %s" % "; ".join(twelves))
    # every small non-terrain component in the play area: the movers live here
    small = []
    for c in (0, 1, 8, 9, 14):
        for x0, x1, y0, y1, n in components(grid[:60], c):
            if n <= 12:
                small.append("c%d x%d-%d y%d-%d" % (c, x0, x1, y0, y1))
    print("   small: %s" % "; ".join(sorted(small)))
    for box, (ink, ic) in sorted(plates(obs.frame).items()):
        print("   plate%s ink=%s %s" % (box, ink, ic))


def dump():
    grid = np.array(obs.frame)[-1]
    for y in range(0, 60):
        print("   %2d %s" % (y, "".join("%X" % (c % 16) if c else "." for c in grid[y])))


show("start")
if "-g" in sys.argv:
    dump()
for i, a in enumerate(PROBE, start=1):
    obs = env.step(space[a])
    if np.array(obs.frame).size == 0:
        print("%3d act%d GAME OVER" % (i, a))
        break
    show("%3d act%d" % (i, a))
    if "-g" in sys.argv:
        dump()
