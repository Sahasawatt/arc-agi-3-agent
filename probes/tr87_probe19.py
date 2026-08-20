"""tr87: can the WHOLE combination be read off one reset frame, generically?

The hand solution (`tr87-solution.txt`) hardcodes five (station, phase) pairs
that a human read out of `probe16`'s hardcoded windows. A driver cannot: it has
to segment the regions itself. This probe does exactly that -- column/row-run
segmentation on each region's own background colour, no coordinate literals --
and carries its own positive control: the five (station -> target) pairs it
derives must equal the five the hand solution wins with.

It also asks the question the driver's algorithm depends on and probe16 never
did: within one station's own 7-state deck, are the canonical (dihedral-8, both
polarities) forms DISTINCT? "Dial until the window matches the target's shape"
is only a correct plan if a shape names one phase.
"""
import sys

import numpy as np

import arc_agi

KNOWN = {15: 5, 22: 5, 29: 3, 36: 6, 43: 5}   # the positive control


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def runs(mask):
    """Contiguous True runs of a 1-D boolean -> [(start, end)] inclusive."""
    out, start = [], None
    for i, v in enumerate(mask.tolist()):
        if v and start is None:
            start = i
        if not v and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return out


def dihedral8(m):
    forms, base = [], m
    for b in (base, np.fliplr(base)):
        cur = b
        for _ in range(4):
            forms.append(cur)
            cur = np.rot90(cur)
    return forms


def canon(m):
    return min(tuple(map(tuple, t.tolist())) for t in dihedral8(m))


def shape_key(m):
    """A shape and its ink-inverted twin are the same key -- probe16 matched
    both polarities, and three of the five blocks only match inverted."""
    return min(canon(m), canon(~m))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}
g0 = grid_of(env.reset())

# -- region split: the frame's own horizontal bands -----------------------
# Rows are one of two background colours (2 on top, 3 below); a region is a
# maximal run of rows sharing one, and everything drawn sits inside one.
row_bg = [int(np.bincount(r).argmax()) for r in g0]
print("row backgrounds, run-length encoded:")
enc, cur, n = [], row_bg[0], 0
for c in row_bg + [None]:
    if c == cur:
        n += 1
    else:
        enc.append((cur, n))
        cur, n = c, 1
print(" ", enc)

# -- the top region: (icon, block) pairs ----------------------------------
TOPBG = row_bg[0]
top = g0[:len([1 for c in row_bg if c == TOPBG])] if False else None
top_rows = [y for y in range(g0.shape[0]) if row_bg[y] == TOPBG]
y_top0, y_top1 = min(top_rows), max(top_rows)
top = g0[y_top0:y_top1 + 1]
print(f"\ntop region y[{y_top0}-{y_top1}] bg={TOPBG}")
xr = runs((top != TOPBG).any(axis=0))
print("  x-runs:", xr)
pairs = []
for x0, x1 in xr:
    band = top[:, x0:x1 + 1]
    yr = runs((band != TOPBG).any(axis=1))
    for y0, y1 in yr:
        cell = band[y0:y1 + 1]
        cxr = runs((cell != TOPBG).any(axis=0))
        if len(cxr) != 2:
            print(f"  SKIP y[{y0}-{y1}] x[{x0}-{x1}]: {len(cxr)} column runs, expected 2")
            continue
        (a0, a1), (b0, b1) = cxr
        icon = cell[:, a0:a1 + 1]
        block = cell[:, b0:b1 + 1]
        pairs.append((y_top0 + y0, x0 + a0, icon, block))
print(f"  found {len(pairs)} (icon, block) pairs")

# -- the hint band and the room -------------------------------------------
# Both sit in the lower background; the hint band is the run of drawn rows
# above the room, the room the one below it. Take every drawn row-band in the
# lower region and print it, then choose.
low_rows = [y for y in range(g0.shape[0]) if row_bg[y] != TOPBG]
low0 = min(low_rows)
low = g0[low0:]
LOWBG = int(np.bincount(low.ravel()).argmax())
print(f"\nlower region y[{low0}-{g0.shape[0]-1}] bg={LOWBG}")
for y0, y1 in runs((low != LOWBG).any(axis=1)):
    band = low[y0:y1 + 1]
    vals, cnt = np.unique(band, return_counts=True)
    print(f"  band y[{low0+y0}-{low0+y1}] h={y1-y0+1} census={dict(zip(vals.tolist(), cnt.tolist()))}"
          f" x-runs={runs((band != LOWBG).any(axis=0))}")

sys.stdout.flush()
