"""Turn a 64x64 colour grid into a short object list.

A 4096-char grid is unreadable for a small model. Connected components of the
rare colours are: the piece you move, the goal marker, pickups, HUD. Terrain is
whatever fills most of the screen, and is described by area rather than listed.
"""

from math import gcd

import numpy as np

HUD_ROW = 60  # rows below this are the budget bar / lives, not the play area


def components(grid, colour):
    """Connected components (4-neighbour) of one colour. Returns [(x0,x1,y0,y1,n)]."""
    mask = grid == colour
    seen = np.zeros_like(mask)
    out = []
    for sy, sx in zip(*np.nonzero(mask & ~seen)):
        if seen[sy, sx]:
            continue
        stack, cells = [(sy, sx)], []
        seen[sy, sx] = True
        while stack:
            y, x = stack.pop()
            cells.append((y, x))
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < grid.shape[0] and 0 <= nx < grid.shape[1] \
                        and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        ys, xs = zip(*cells)
        out.append((min(xs), max(xs), min(ys), max(ys), len(cells)))
    return out


def objects(frame, max_area=200):
    """Objects in the play area, rarest colour first. Bulk terrain is skipped."""
    grid = np.array(frame)[-1][:HUD_ROW]
    colours, counts = np.unique(grid, return_counts=True)
    terrain = {int(c) for c, n in zip(colours, counts) if n > 400}
    objs = []
    for c, n in sorted(zip(colours, counts), key=lambda cn: cn[1]):
        if int(c) in terrain:
            continue
        for x0, x1, y0, y1, area in components(grid, c):
            if area <= max_area:
                objs.append({"colour": int(c), "x": [int(x0), int(x1)],
                             "y": [int(y0), int(y1)], "cells": int(area)})
    return objs, sorted(terrain)


def hud(frame):
    """The strip below the play area: budget bar length and lives. Objects() drops it,
    but it is the only oracle for "did that pickup give me anything"."""
    grid = np.array(frame)[-1]
    strip = grid[HUD_ROW:]
    colours, counts = np.unique(strip, return_counts=True)
    return {int(c): int(n) for c, n in zip(colours, counts)}


def icon(frame, x0, x1, y0, y1, ink=9):
    """The shape drawn inside a panel, as a comparable string.

    The pattern indicator and the goal marker are both an `ink`-coloured glyph on a dark
    plate. Comparing cell COUNTS conflates different glyphs of equal area, so compare the
    bitmap. Trimmed to the glyph's own bounding box, so the two plates' sizes don't matter.
    """
    grid = np.array(frame)[-1]
    m = grid[y0:y1 + 1, x0:x1 + 1] == ink
    if not m.any():
        return "(empty)"
    ys, xs = np.nonzero(m)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    # The two plates draw the same glyph at different scales (the indicator is 2x), so it
    # has to be divided back down. Collapsing runs of identical adjacent rows and columns
    # does that and is scale-invariant, but it is not injective: a glyph that genuinely
    # repeats a row — `#.#/#.#/###` — collapses onto a different two-row glyph, and the
    # door then reads as open when it is shut. Dividing by the scale the glyph is actually
    # drawn at keeps both properties.
    g = _scale(m)
    m = m[::g, ::g]
    return "/".join("".join("#" if v else "." for v in row) for row in m)


def _scale(m):
    """The integer scale a bitmap is drawn at: the gcd of every run length in it.

    A glyph drawn at 2x has every run of set and unset cells twice as long, in both
    directions, so the gcd is 2 and dividing by it recovers the glyph. Anything irregular
    gives 1 and the bitmap is left alone.
    """
    g = 0
    for line in list(m) + list(m.T):
        n = 1
        for i in range(1, len(line)):
            if line[i] == line[i - 1]:
                n += 1
            else:
                g, n = gcd(g, n), 1
        g = gcd(g, n)
        if g == 1:
            return 1
    return max(g, 1)


def describe(objs, terrain):
    lines = [f"terrain colours (bulk fill, not objects): {terrain}"]
    for o in objs:
        w, h = o["x"][1] - o["x"][0] + 1, o["y"][1] - o["y"][0] + 1
        lines.append(f"  colour {o['colour']}: {w}x{h} box at "
                     f"x{o['x'][0]}-{o['x'][1]} y{o['y'][0]}-{o['y'][1]} ({o['cells']} cells)")
    return "\n".join(lines)


def movement(before, after):
    """Match objects across a step; report what shifted. Generic, no game rules."""
    events = []
    used = set()
    for a in after:
        best, bi = None, None
        for i, b in enumerate(before):
            if i in used or b["colour"] != a["colour"] or b["cells"] != a["cells"]:
                continue
            d = abs(b["x"][0] - a["x"][0]) + abs(b["y"][0] - a["y"][0])
            if best is None or d < best:
                best, bi = d, i
        if bi is None:
            events.append(f"colour {a['colour']} appeared at x{a['x'][0]} y{a['y'][0]}")
            continue
        used.add(bi)
        b = before[bi]
        dx, dy = a["x"][0] - b["x"][0], a["y"][0] - b["y"][0]
        if dx or dy:
            events.append(f"colour {a['colour']} moved dx={dx} dy={dy}")
    for i, b in enumerate(before):
        if i not in used and not any(o["colour"] == b["colour"] and o["cells"] == b["cells"]
                                     for o in after):
            events.append(f"colour {b['colour']} disappeared")
    return events or ["nothing moved"]
