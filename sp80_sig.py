"""sp80 rung safety measurement: what discriminates sp80's reset board from the
other sixteen, and does sp80 already trip cover's signature?

    ./.venv/Scripts/python.exe sp80_sig.py

Prints one row per playable game with every candidate feature, so the signature
is CHOSEN from the table rather than guessed and then defended.
"""

import sys

import numpy as np

import arc_agi
from compete import PLAYABLE
from cover import boxes

CHARS = "0123456789abcdef"


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def blobs(g, colour):
    ys, xs = np.nonzero(g == colour)
    cells = set(zip(xs.tolist(), ys.tolist()))
    out = []
    while cells:
        stack = [next(iter(cells))]
        blob = set()
        while stack:
            c = stack.pop()
            if c in blob or c not in cells:
                continue
            blob.add(c)
            x, y = c
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) in cells:
                    stack.append((x + dx, y + dy))
        cells -= blob
        bx = [c[0] for c in blob]
        by = [c[1] for c in blob]
        out.append((min(bx), min(by), max(bx), max(by), len(blob)))
    return out


def features(g):
    """Every candidate discriminator, measured -- no game named."""
    H, W = g.shape
    bg = int(np.bincount(g.ravel()).argmax())
    # full-width single-colour rows that are not background
    bars = [(y, int(g[y, 0])) for y in range(H)
            if len(set(g[y].tolist())) == 1 and int(g[y, 0]) != bg]
    # bars touching the top or bottom edge, as contiguous bands
    bands = []
    for y, c in bars:
        if bands and bands[-1][2] == c and bands[-1][1] == y - 1:
            bands[-1] = (bands[-1][0], y, c)
        else:
            bands.append((y, y, c))
    edge_bands = [b for b in bands if b[0] == 0 or b[1] == H - 1]
    # solid rectangular blobs, largest first
    rects = []
    for c in set(g.ravel().tolist()):
        if c == bg:
            continue
        for (x0, y0, x1, y1, n) in blobs(g, c):
            if n == (x1 - x0 + 1) * (y1 - y0 + 1) and n >= 16:
                rects.append((n, c, x0, y0, x1 - x0 + 1, y1 - y0 + 1))
    rects.sort(reverse=True)
    return {
        "bg": bg,
        "boxes": len(boxes(g)),
        "bars": bars,
        "edge_bands": edge_bands,
        "n_edge_bands": len(edge_bands),
        "rects": rects[:6],
        "n_rects": len(rects),
    }


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

print("game  acts        cover_boxes  edge_bands                 top_rects")
rows = {}
for name in PLAYABLE:
    try:
        env = arc.make(envs[name].game_id)
    except Exception as e:
        print(f"{name}  MAKE FAILED {type(e).__name__}")
        continue
    obs = env.reset()
    g = grid_of(obs)
    if g is None:
        print(f"{name}  EMPTY FRAME AT RESET")
        continue
    acts = sorted(a.value for a in env.action_space)
    cplx = sorted(a.value for a in env.action_space if a.is_complex())
    f = features(g)
    rows[name] = (acts, cplx, f)
    print(f"{name}  {str(acts):12s} {f['boxes']:>3d}         {str(f['edge_bands']):26s} "
          f"{[(n, c, w, h) for n, c, _, _, w, h in f['rects'][:3]]}")
    sys.stdout.flush()

print("\n== candidate signature: two opposite-edge single-colour bands + a solid "
      "rect >= 60 cells that is not part of them ==")
for name, (acts, cplx, f) in rows.items():
    top = any(b[0] == 0 for b in f["edge_bands"])
    bot = any(b[1] == 63 for b in f["edge_bands"])
    big = [r for r in f["rects"] if r[0] >= 60]
    hit = top and bot and bool(big) and 5 in acts
    print(f"  {name}: top={top} bottom={bot} big_rects={len(big)} has5={5 in acts} -> {hit}")

print("\n== cover.signature (boxes >= 4) per game -- does sp80 trip it? ==")
for name, (acts, cplx, f) in rows.items():
    print(f"  {name}: boxes={f['boxes']} cover_would_fire={f['boxes'] >= 4}")

print("\n== full detail ==")
for name, (acts, cplx, f) in rows.items():
    print(f"  {name}: acts={acts} complex={cplx} bg={f['bg']} bars={f['bars'][:6]} "
          f"n_rects={f['n_rects']} rects={f['rects']}")
sys.stdout.flush()
