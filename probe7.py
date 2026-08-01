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


def line(tag):
    grid = np.array(obs.frame)[-1][:60]
    piece = [(x0, y0) for x0, x1, y0, y1, n in components(grid, 12) if n >= 8 and y0 < 50]
    c = Counter(int(v) for v in grid.flatten())
    ys, xs = np.where(grid == 3)
    box = ("x%d-%d y%d-%d" % (xs.min(), xs.max(), ys.min(), ys.max())
           if len(xs) else "no floor")
    full = np.array(obs.frame)[-1]
    # The indicator keeps its place but walks its INK along 12 -> 9 -> 14 -> 8, so a
    # scan pinned to colour 12 reports "none" the moment the ink changer is pressed —
    # which is exactly the earlier probe trap. Scan the glyph's own corner for any of
    # the game's four inks instead.
    gl = [(int(x), int(y)) for y in range(50, full.shape[0]) for x in range(0, 20)
          if int(full[y][x]) in (12, 9, 14, 8)]
    if gl:
        x0 = min(p[0] for p in gl); x1 = max(p[0] for p in gl)
        y0 = min(p[1] for p in gl); y1 = max(p[1] for p in gl)
        bits = "/".join("".join("#" if (x, y) in gl else "." for x in range(x0, x1 + 1))
                        for y in range(y0, y1 + 1))
    else:
        bits = "none"
    print("   glyph %s" % bits, flush=True)
    # The x55-57 patroller's live position, when its column is inside the window:
    # the five-cell cross is colours 0 and 1 on an otherwise floor/wall column.
    pys = sorted({int(y) for y in range(60) for x in range(54, 59)
                  if int(grid[y][x]) in (0, 1)})
    print("%-9s lvl=%d piece=%s floor=%d %s  c1=%d c11=%d c4=%d c5=%d pat=%s hud=%s"
          % (tag, obs.levels_completed, piece[0] if piece else None,
             c.get(3, 0), box, c.get(1, 0), c.get(11, 0), c.get(4, 0), c.get(5, 0),
             pys, {k: v for k, v in sorted(hud(obs.frame).items())}), flush=True)


def remember():
    """Fold this frame's window into the world map, skipping the piece's own footprint.

    The windows stitch because the coordinates are fixed (measured: consecutive frames
    match best at dx=dy=0). What must NOT be folded in is anything the piece is standing
    on or made of — remembering those paints a trail of piece-coloured cells across the
    fog, which is the same mistake as reading a display the piece is covering.
    """
    grid = np.array(obs.frame)[-1][:60]
    # Only the PIECE, which is colour 12 over colour 9 — not every large colour-12
    # component. The level's big L glyph is drawn in the piece's own colour, and
    # skipping it too is how it went missing from the first map that was stitched.
    ps = [(x0, x1, y0, y1) for x0, x1, y0, y1, n in components(grid, 12)
          if n >= 8 and (grid[y1 + 1:y1 + 4, x0:x1 + 1] == 9).any()]
    for y in range(60):
        for x in range(64):
            c = int(grid[y][x])
            if c == 5:
                continue
            if any(x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 5 for x0, x1, y0, y1 in ps):
                continue
            # A cell that comes back DIFFERENT is the only thing on this board that can
            # be a lock's indicator: the window explains a cell going to 5 and back, and
            # the piece explains its own footprint, so anything left is the board acting.
            if world.get((x, y), c) != c:
                changed.setdefault((x, y), []).append((world[(x, y)], c))
            world[(x, y)] = c


world, changed = {}, {}
line("start")
if "-map" in sys.argv:
    remember()
for i, a in enumerate(PROBE, start=1):
    obs = env.step(space[a])
    if np.array(obs.frame).size == 0 or obs.state == GameState.GAME_OVER:
        print("%3d act%d GAME OVER, reset" % (i, a), flush=True)
        obs = env.reset()
        continue
    line("%3d act%d" % (i, a))
    if "-map" in sys.argv:
        remember()

if "-map" in sys.argv:
    print("\nstitched world: %d cells" % len(world))
    for y in range(60):
        row = "".join("%X" % (world[(x, y)] % 16) if (x, y) in world else "."
                      for x in range(64))
        if row.strip("."):
            print("%2d %s" % (y, row))
    # The question stitching exists to answer: is there anything to walk TO that no
    # single window ever shows whole? `plates` is the reader that finds a door.
    comp = np.full((64, 64), 5)
    for (x, y), c in world.items():
        comp[y][x] = c
    print("\nplates on the stitched world:")
    for box, (ink, ic) in sorted(plates([comp.tolist()]).items()):
        print("   %s ink=%s %s" % (box, ink, ic))
    print("colours present:", sorted(Counter(world.values()).items()))
    print("\ncells that came back DIFFERENT: %d" % len(changed))
    for (x, y), hist in sorted(changed.items(), key=lambda kv: -len(kv[1]))[:20]:
        print("   (%2d,%2d) x%d  %s" % (x, y, len(hist), hist[:6]))
