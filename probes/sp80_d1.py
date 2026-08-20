"""Is D1 real? Does a clock death corrupt the arrow mapping swap.py learned?

    ./.venv/Scripts/python.exe sp80_d1.py

`Swap.act` reads the mapping from `moved(self.prev, g)` BEFORE it asks whether a
life just ended. When the life ended on the CLOCK the last action was a
direction, so the pair being compared straddles the engine's reset -- and the
block coming back to the level's start IS a rigid translation of the driven
colour. Read from the code that predicts `dirs[last]` is overwritten with a
bogus vector. This drives the real class with synthetic frames to find out.

No engine, no network: the question is about a frame PAIR, which is the layer
the defect lives on.
"""

import sys

import numpy as np

from swap import Swap

BG, MINE, CLOCK, FLOOR = 12, 9, 14, 1
H = W = 64


def board(x, y=16, bar=64, w=20, h=4):
    g = np.full((H, W), BG, dtype=int)
    g[0, :bar] = CLOCK
    g[0, bar:] = 0
    g[H - 4:H, :] = FLOOR
    g[y:y + h, x:x + w] = MINE
    return g


def learned():
    sw = Swap([1, 2, 3, 4, 5])
    sw.mine = MINE
    sw.dirs = {1: (0, -4), 2: (0, 4), 3: (-4, 0), 4: (4, 0)}
    sw.mag = 4
    return sw


ALL_BUT_ONE = {(x, y) for x in range(0, 45, 4) for y in range(0, 61, 4)} - {(44, 44)}

print("== the mapping before and after a CLOCK death (last action = a direction) ==")
sw = learned()
sw.act(board(12, bar=64), 0)          # level init + latch
sw.fired = set(ALL_BUT_ONE)           # everything tested but one far target: it WALKS
sw.shots = 0
# a walk step: the driver emits a direction and remembers this frame
out = sw.act(board(12, y=20, bar=40), 0)
print(f"  walk round emitted {out}, dirs now {dict(sw.dirs)}")
# positive control: the whole question is about a pair whose FIRST half ended on a
# direction. If the driver fired here, the probe is measuring nothing.
assert out in (1, 2, 3, 4), f"probe did not set up a walk: emitted {out}"
before = dict(sw.dirs)
# ...that action drained the clock. compete.play resets; the block is back at the
# level start with a full bar, and THIS is the next frame the driver is handed.
sw.act(board(12, y=16, bar=64), 0)
after = dict(sw.dirs)
print(f"  after the post-death frame: {after}")
bad = {a: (before.get(a), after[a]) for a in after if before.get(a) != after[a]}
print(f"  CORRUPTED entries: {bad}" if bad else "  mapping intact")

print("\n== control: the SAME walk answered honestly (no death, clock keeps burning) ==")
sw2 = learned()
sw2.act(board(12, bar=64), 0)
sw2.fired = set(ALL_BUT_ONE)
sw2.shots = 0
out2 = sw2.act(board(12, y=20, bar=40), 0)
assert out2 in (1, 2, 3, 4), f"control did not set up a walk: emitted {out2}"
b2 = dict(sw2.dirs)
# the honest answer to that press: the block moved by exactly that action's vector
dx, dy = b2[out2]
sw2.act(board(12 + dx, y=20 + dy, bar=38), 0)
after2 = {a: tuple(int(v) for v in d) for a, d in sw2.dirs.items()}
print(f"  emitted {out2}; dirs {b2} -> {after2}")
print("  control clean:", after2 == b2)

print("\n== what a corrupt entry does to the sweep's lattice ==")
sw3 = learned()
sw3.dirs[4] = (-32, 0)                # the shape of the corruption above
print("  targets with a clean stride:",
      len(learned()._targets(board(12), (12, 16, 20, 4))))
print("  targets with the corrupt stride:",
      len(sw3._targets(board(12), (12, 16, 20, 4))))
sys.stdout.flush()
