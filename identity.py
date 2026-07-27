"""Follow objects across frames.

The previous scheme keyed objects on `(colour, cell_count)` and looked them up in a dict.
That has two failure modes and both were live: two objects sharing the key in one frame
collided and one was silently discarded — 55 objects across the 9 MAZE_LIKE games at
reset alone, 19 of `dc22`'s 31 — and an object whose colour or size changed lost its key
entirely, which the caller then read as "it did not move".

Identity cannot be a key, because every attribute of an object can change. It has to be
the cheapest consistent explanation of one frame given the last: each track predicts
where it should be, every object is scored against every track, and the pairs are taken
best-first. Colour, area and position all contribute, so any one of them can drift.
"""

from dataclasses import dataclass, field
from math import hypot

BOARD_DIAG = hypot(64, 60)
GATE = 20.0          # cells; nothing on this board moves further in one step
W_POSITION = 1.0
W_COLOUR = 1.0
W_AREA = 1.0


@dataclass
class Track:
    id: int
    colour: int
    area: int
    box: tuple                      # (x, y, w, h) as last seen
    velocity: tuple = (0, 0)        # last observed displacement, used to predict
    missed: int = 0
    hits: int = field(default=1)


def _box(o):
    return (o["x"][0], o["y"][0], o["x"][1] - o["x"][0] + 1, o["y"][1] - o["y"][0] + 1)


def cost(t: Track, o, gate=GATE):
    """How badly `o` fits `t`. None means the pair is impossible."""
    px, py = t.box[0] + t.velocity[0], t.box[1] + t.velocity[1]
    d = hypot(o["x"][0] - px, o["y"][0] - py)
    if d > gate:
        return None
    return (W_POSITION * d / BOARD_DIAG
            + W_COLOUR * (0.0 if o["colour"] == t.colour else 1.0)
            + W_AREA * abs(o["cells"] - t.area) / max(o["cells"], t.area, 1))


def match(tracks, objs, gate=GATE):
    """{object index: track id}, best-first greedy over the gated cost matrix.

    Greedy rather than Hungarian: the boards top out around 200 objects, the costs are
    well separated once colour and area are in them, and scipy is not a dependency.
    """
    pairs = []
    for ti, t in enumerate(tracks):
        for oi, o in enumerate(objs):
            c = cost(t, o, gate)
            if c is not None:
                pairs.append((c, ti, oi))
    pairs.sort(key=lambda p: (p[0], p[1], p[2]))

    used_t, used_o, out = set(), set(), {}
    for _, ti, oi in pairs:
        if ti in used_t or oi in used_o:
            continue
        used_t.add(ti)
        used_o.add(oi)
        out[oi] = tracks[ti].id
    return out


def update(tracks, objs, next_id, gate=GATE, max_missed=2):
    """Advance every track one frame. Returns (tracks, {object index: track id}, next_id).

    A track that goes unmatched is kept for `max_missed` frames before being dropped:
    one frame of not seeing something is not proof it is gone, and the caller needs to
    tell "absent" from "stationary" to know whether a move was blocked.
    """
    assign = match(tracks, objs, gate)
    by_id = {t.id: t for t in tracks}
    matched = set()

    for oi, tid in assign.items():
        t, b = by_id[tid], _box(objs[oi])
        t.velocity = (b[0] - t.box[0], b[1] - t.box[1])
        t.box, t.colour, t.area = b, objs[oi]["colour"], objs[oi]["cells"]
        t.missed, t.hits = 0, t.hits + 1
        matched.add(tid)

    for t in tracks:
        if t.id not in matched:
            t.missed += 1

    kept = [t for t in tracks if t.missed <= max_missed]
    for oi, o in enumerate(objs):
        if oi not in assign:
            kept.append(Track(id=next_id, colour=o["colour"], area=o["cells"], box=_box(o)))
            assign[oi] = next_id
            next_id += 1
    return kept, assign, next_id
