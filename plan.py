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


def step_to(model, pos, act, redirects=None):
    """Where an action leaves the piece: the square it aims at, unless that square sends it on.

    The redirect keys on the **destination**, not the source or the action — measured on
    `ls20` level 4, where pressing right from (14, 35) and pressing up from (19, 40) both aim
    at (19, 35) and both land at (19, 45). Keyed on source-and-action the table is one row per
    way of arriving and the router almost never has the row it needs; keyed on the
    destination it is one row per redirecting cell and every route through it gets that row.
    """
    # The cell rule first: "anything aiming at this square ends up there", which is what
    # `ls20` level 4 measured and what one sighting can generalise from. A per-button rule
    # is the narrower reading — one press from one square — and letting it outrank the cell
    # rule costs level 4.
    dx, dy = model.dirs[act]
    aim = (pos[0] + dx, pos[1] + dy)
    off = (redirects or {}).get(aim)
    if off is not None:
        return (aim[0] + off[0], aim[1] + off[1])
    # No rule for the square being aimed at. Fall back to what THIS button did from THIS
    # square, if it has been watched — one press from one place, which is less than the cell
    # rule knows (that one reading covers every approach) but more than nothing.
    exact = (redirects or {}).get((pos, act))
    return exact if exact is not None else aim


def bfs(grid, model, start, goals, redirects=None, came_from=None, sure=None):
    """Shortest action list from `start` to any position in `goals`, or None.

    The first action may not land back on `came_from`, the square the piece occupied one
    move ago. This refuses to undo the last move and nothing else — no route is removed,
    because any square reachable through the previous one is reachable without it. It is
    what stops `ls20` level 5 bouncing between two squares for twenty actions until it
    starves: a floor cell carries the piece back, the plain route walks into it again
    because it does not believe in the carry, and neither square is ever left.
    """
    if not goals:
        return None
    if start in goals:
        return []
    seen = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        for act in model.dirs:
            if sure is not None and (cur, act) not in sure:
                continue
            nxt = step_to(model, cur, act, redirects)
            if cur == start and nxt == came_from:
                continue
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


def bfs_all(grid, model, start, redirects=None):
    """Shortest action list to every reachable position -> {(x, y): [actions]}.

    Objects are a guess at where the goal is; positions are the whole space. Boards here
    have between 37 and 1024 reachable positions and the engine runs locally at ~2000
    FPS, so visiting all of them costs wall-clock and no score at all.
    """
    seen = {start: []}
    q = deque([start])
    while q:
        cur = q.popleft()
        for act in model.dirs:
            nxt = step_to(model, cur, act, redirects)
            if nxt is None or nxt in seen or not walkable(grid, model, nxt[0], nxt[1]):
                continue
            seen[nxt] = seen[cur] + [act]
            q.append(nxt)
    return seen


def route_to(frame, model, o, redirects=None, came_from=None, sure=None):
    """Action list that walks the piece onto object `o`, or None.

    A map of redirecting cells can only be as complete as the walking that built it, and an
    incomplete one **removes** routes: on `ls20` level 4, six cells learned by accident cut
    the reachable board from 67 squares to 57 and put both glyph-changers outside it — while
    the agent had demonstrably stood on both. So the map is used when it finds a way and
    ignored when it does not: walking the route the plain model believes in is what maps the
    cells along it, and those are exactly the cells this route needs.
    """
    grid = np.array(frame)[-1][:model.rows or HUD_ROW]
    at = locate(frame, model)
    if at is None:
        return None
    goals = footprints_touching(grid, model, o)
    here = (at[0], at[1])
    # Shortest of the routes the agent can actually BELIEVE — verified steps only, and the
    # map — rather than the first one that comes back non-None. Fewer actions is less fuel,
    # and on a board where a life is 21 actions that is the difference between arriving and
    # starving. The plain route stays last and is not part of the comparison: it is shorter
    # precisely because it does not believe in the carries, so walking it costs MORE than its
    # length says — the piece is taken somewhere else and the plan is dropped.
    believed = [r for r in (bfs(grid, model, here, goals, redirects, came_from, sure),
                            bfs(grid, model, here, goals, redirects, came_from))
                if r is not None]
    return min(believed, key=len) if believed else         bfs(grid, model, here, goals, came_from=came_from)


def slides(frame, grid, model, shut=()):
    """Cells the board MARKS as throwing the piece, read off one frame -> {cell: offset}.

    `ls20` level 4 and 5 draw a bar beside every such cell — one cell thick, one step long —
    and the piece entering that cell is thrown away from the bar until something blocks it.
    Eight of the eight cells found by walking level 5 come out of this rule exactly, given
    that a goal box whose display does not match is one of the things that blocks.

    Discovered by walking, the same map costs a few hundred actions and arrives late; read
    off the frame it is there before the first step. Nothing here is specific to a colour or
    a game: what is looked for is the SHAPE — a marker exactly one cell thick and one step
    long — and a rule that comes out wrong is dropped the moment a walk disagrees with it.
    """
    from perception import objects
    step = model.step or 5
    w, h = model.box
    out = {}
    objs, _ = objects(frame)
    for o in objs:
        ow = o["x"][1] - o["x"][0] + 1
        oh = o["y"][1] - o["y"][0] + 1
        if not ((ow == 1 and oh == step) or (oh == 1 and ow == step)):
            continue
        # The cell it marks is the one flush against it on the piece's own lattice, and the
        # throw is away from the marker along the marker's short axis.
        for d in ((step, 0), (-step, 0), (0, step), (0, -step)):
            if (oh == 1) != (d[0] == 0):
                continue                      # a flat bar throws vertically, and vice versa
            cell = (o["x"][0] - (d[0] and (d[0] // step) * 1) * 0 + (0 if d[0] == 0 else 0),
                    o["y"][0])
            cell = (o["x"][0] if d[0] == 0 else o["x"][0] + (1 if d[0] > 0 else -w),
                    o["y"][0] if d[1] == 0 else o["y"][0] + (1 if d[1] > 0 else -h))
            if not walkable(grid, model, cell[0], cell[1]):
                continue
            pos = cell
            for _ in range(model.rows // step + 2):
                nxt = (pos[0] + d[0], pos[1] + d[1])
                if nxt in shut or not walkable(grid, model, nxt[0], nxt[1]):
                    break
                pos = nxt
            if pos != cell:
                out[cell] = (pos[0] - cell[0], pos[1] - cell[1])
    return out
