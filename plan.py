"""Route the piece somewhere, using only what `discover.py` worked out.

`solver.py` does this for ls20 with its colours and its 5-cell step written in. Everything
here takes a `Model` instead, so it runs on a game nobody has read.
"""

from collections import deque

import numpy as np

from discover import locate, walkable
from perception import HUD_ROW, components, objects


def regions(frame, model, min_area=40):
    """Big areas that are neither the floor nor a wall.

    `perception.objects` treats any colour covering more than 400 cells as terrain and
    drops it, and any component over 200 cells as too big to be an object. That is right
    for the floor and wrong for a goal zone: `m0r0` ends up with zero candidate targets
    on a board whose objective is region-sized. Discovery already knows which colours the
    piece walks on and which stop it, so anything that is neither is worth visiting.
    """
    grid = np.array(frame)[-1][:model.rows]
    known = set(model.passable) | set(model.blocking)
    out = []
    for c in np.unique(grid):
        if int(c) in known:
            continue
        for x0, x1, y0, y1, area in components(grid, c):
            if area >= min_area:
                out.append({"colour": int(c), "x": [int(x0), int(x1)],
                            "y": [int(y0), int(y1)], "cells": int(area)})
    return out


def targets(frame, model, max_area=200):
    """Things worth walking onto: every object that is not the piece and not terrain.

    No idea which one ends the level — that is what trying them is for. Returned rarest
    first, because a unique object is a better guess at a goal than one of forty tiles.
    """
    objs, _ = objects(frame, max_area=max_area)
    at = locate(frame, model)
    parts = {(c, w, h) for c, w, h in model.parts}
    out = []
    for o in objs:
        w = o["x"][1] - o["x"][0] + 1
        h = o["y"][1] - o["y"][0] + 1
        if (o["colour"], w, h) in parts:
            continue                      # a piece part, here or elsewhere on the board
        if at and o["x"][0] == at[0] and o["y"][0] == at[1]:
            continue
        out.append(o)
    for r in regions(frame, model):
        if not any(o["x"][0] == r["x"][0] and o["y"][0] == r["y"][0] for o in out):
            out.append(r)
    counts = {}
    for o in out:
        counts[o["colour"]] = counts.get(o["colour"], 0) + 1
    out.sort(key=lambda o: (counts[o["colour"]], o["cells"]))
    return out


def footprints_touching(grid, model, o):
    """Positions of the piece that count as reaching `o`.

    Merely overlapping is not the same as arriving. A goal box on ls20 is 7x7 around a
    5x5 piece, and clipping its edge does nothing — the piece has to be inside it. So
    when the object is big enough to contain the footprint, containment is what counts;
    otherwise contact is all there is.
    """
    w, h = model.box
    inside, touching = set(), set()
    for y in range(0, model.rows - h + 1):
        for x in range(0, grid.shape[1] - w + 1):
            if not (x < o["x"][1] + 1 and x + w > o["x"][0]
                    and y < o["y"][1] + 1 and y + h > o["y"][0]):
                continue
            if not walkable(grid, model, x, y):
                continue
            touching.add((x, y))
            if (x >= o["x"][0] and x + w <= o["x"][1] + 1
                    and y >= o["y"][0] and y + h <= o["y"][1] + 1):
                inside.add((x, y))
    return inside or touching


def bfs(grid, model, start, goals):
    """Shortest action list from `start` to any position in `goals`, or None."""
    if not goals:
        return None
    if start in goals:
        return []
    seen = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        for act, (dx, dy) in model.dirs.items():
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in seen or not walkable(grid, model, nxt[0], nxt[1]):
                continue
            seen[nxt] = (act, cur)
            if nxt in goals:
                path, node = [], nxt
                while seen[node]:
                    act, node = seen[node]
                    path.append(act)
                return path[::-1]
            q.append(nxt)
    return None


def signature(o):
    """What an object is, independent of where it is."""
    return (o["colour"], o["x"][1] - o["x"][0] + 1, o["y"][1] - o["y"][0] + 1)


def bfs_all(grid, model, start):
    """Shortest action list to every reachable position -> {(x, y): [actions]}.

    Objects are a guess at where the goal is; positions are the whole space. Boards here
    have between 37 and 1024 reachable positions and the engine runs locally at ~2000
    FPS, so visiting all of them costs wall-clock and no score at all.
    """
    seen = {start: []}
    q = deque([start])
    while q:
        cur = q.popleft()
        for act, (dx, dy) in model.dirs.items():
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in seen or not walkable(grid, model, nxt[0], nxt[1]):
                continue
            seen[nxt] = seen[cur] + [act]
            q.append(nxt)
    return seen


def route_to(frame, model, o):
    """Action list that walks the piece onto object `o`, or None."""
    grid = np.array(frame)[-1][:model.rows or HUD_ROW]
    at = locate(frame, model)
    if at is None:
        return None
    return bfs(grid, model, (at[0], at[1]), footprints_touching(grid, model, o))
