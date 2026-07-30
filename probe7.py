"""Replay a prefix, then walk, printing one compact line per step.

    uv run python probe7.py ls20 <prefix-file> <actions>

`ls20` level 7 has no plates, so `probe6`'s reader — which prints panels and doors — has
nothing to say about it. What this board does instead is change SHAPE as the piece moves:
one step up destroys ninety floor cells at the bottom and grows terrain at the top, and
stepping back down restores them exactly. So the thing to write down per step is the
board's census, not its plates: where the piece is, how much floor there is and where it
reaches, and the count of every colour in the play area.
"""

import sys
from collections import Counter

import numpy as np

import arc_agi
from arcengine import GameState
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


def line(tag):
    grid = np.array(obs.frame)[-1][:60]
    piece = [(x0, y0) for x0, x1, y0, y1, n in components(grid, 12) if n >= 8 and y0 < 50]
    c = Counter(int(v) for v in grid.flatten())
    ys, xs = np.where(grid == 3)
    box = ("x%d-%d y%d-%d" % (xs.min(), xs.max(), ys.min(), ys.max())
           if len(xs) else "no floor")
    print("%-9s lvl=%d piece=%s floor=%d %s  c1=%d c11=%d c4=%d c5=%d hud=%s"
          % (tag, obs.levels_completed, piece[0] if piece else None,
             c.get(3, 0), box, c.get(1, 0), c.get(11, 0), c.get(4, 0), c.get(5, 0),
             {k: v for k, v in sorted(hud(obs.frame).items())}), flush=True)


line("start")
for i, a in enumerate(PROBE, start=1):
    obs = env.step(space[a])
    if np.array(obs.frame).size == 0:
        print("%3d act%d GAME OVER" % (i, a), flush=True)
        break
    line("%3d act%d" % (i, a))
