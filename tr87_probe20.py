"""tr87: derive the whole combination from the reset frame with NO coordinate
literals, and ask whether "dial until the room window matches the target's
shape" is a correct plan.

Segmentation, all from the frame's own structure (`tr87-probe19.txt` and the
raw dumps behind it):

  * rows split into background runs; the top region is the first, the rest
    holds the hint band, the clamp's two brackets, the room and the bar.
  * the HINT band and the ROOM are the two 7-row drawn bands; each is a strip
    with a frame colour and one ink colour, and the five stations are the
    5-wide windows on its 7-pitch lattice.
  * the CLAMP is the 2-row band of a colour neither strip uses; its x-run is
    the station it is parked at.
  * a top band holds two 7x7 tiles: the one framed in the HINT band's colour
    is an ICON (it names a station), the one framed in the ROOM's colour is a
    BLOCK (it names that station's target phase). Same palette, same meaning
    -- which is the rule that pairs them without hardcoding x.

Controls in this same invocation: the derived (station -> phase) map must
equal the hand solution's, and the shape keys within one station's deck must
be DISTINCT, or "dial until it matches" would stop at the wrong phase.
"""
import sys

import numpy as np

import arc_agi

KNOWN = {15: 5, 22: 5, 29: 3, 36: 6, 43: 5}


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def runs(mask):
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


def canon(m):
    forms, out = [], []
    for b in (m, np.fliplr(m)):
        cur = b
        for _ in range(4):
            out.append(tuple(map(tuple, cur.tolist())))
            cur = np.rot90(cur)
    return min(out)


def shape_key(m):
    return min(canon(m), canon(~m))


def read_board(g):
    """-> dict of everything the driver needs, or None."""
    row_bg = [int(np.bincount(r).argmax()) for r in g]
    top_bg = row_bg[0]
    top_end = max(y for y in range(len(row_bg)) if row_bg[y] == top_bg
                  and all(row_bg[k] == top_bg for k in range(y + 1)))
    low = g[top_end + 1:]
    low_bg = int(np.bincount(low.ravel()).argmax())
    bands = [(top_end + 1 + a, top_end + 1 + b)
             for a, b in runs((low != low_bg).any(axis=1))]
    strips = [(y0, y1) for y0, y1 in bands if y1 - y0 + 1 == 7]
    if len(strips) != 2:
        return None
    (hy0, hy1), (ry0, ry1) = strips[0], strips[1]

    def frame_ink(y0, y1):
        sub = g[y0:y1 + 1]
        vals, cnt = np.unique(sub[sub != low_bg], return_counts=True)
        if len(vals) != 2:
            return None, None
        order = np.argsort(-cnt)
        return int(vals[order[0]]), int(vals[order[1]])   # frame, ink

    hframe, hink = frame_ink(hy0, hy1)
    rframe, rink = frame_ink(ry0, ry1)
    if hframe is None or rframe is None:
        return None
    rx = runs((g[ry0:ry1 + 1] != low_bg).any(axis=0))
    if len(rx) != 1:
        return None
    x0, x1 = rx[0]
    stations = list(range(x0 + 1, x1, 7))

    clamp = None
    for y0, y1 in bands:
        sub = g[y0:y1 + 1]
        cols = runs((sub != low_bg).any(axis=0))
        drawn = set(np.unique(sub[sub != low_bg]).tolist())
        if len(cols) == 1 and not (drawn & {hframe, hink, rframe, rink}) \
                and cols[0][0] in stations:
            clamp = cols[0][0]
    return {"hint": (hy0, hy1), "room": (ry0, ry1), "stations": stations,
            "hframe": hframe, "hink": hink, "rframe": rframe, "rink": rink,
            "clamp": clamp, "top_end": top_end, "top_bg": top_bg}


def window(g, y0, x0, ink):
    return g[y0 + 1:y0 + 6, x0:x0 + 5] == ink


def top_pairs(g, b):
    """[(icon 5x5 mask, block 5x5 mask)] -- a tile framed in the hint band's
    colour beside one framed in the room's colour."""
    top = g[:b["top_end"] + 1]
    bg = b["top_bg"]
    out = []
    # A pair is one row-band of one COLUMN run -- both tiles live side by side
    # inside the same run, and every band crosses two runs, so scanning by band
    # alone keeps one pair of the two and silently drops the other.
    for x0, x1 in runs((top != bg).any(axis=0)):
        col = top[:, x0:x1 + 1]
        for y0, y1 in runs((col != bg).any(axis=1)):
            band = col[y0:y1 + 1]
            icon = block = None
            for xa in range(band.shape[1] - 6):
                tile = band[:, xa:xa + 7]
                if tile.shape != (7, 7):
                    continue
                border = set(np.unique(np.concatenate(
                    [tile[0], tile[-1], tile[:, 0], tile[:, -1]])).tolist())
                if border == {b["hframe"]}:
                    icon = tile[1:6, 1:6] == b["hink"]
                elif border == {b["rframe"]}:
                    block = tile[1:6, 1:6] == b["rink"]
            if icon is not None and block is not None:
                out.append((icon, block))
    return out


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}
g0 = grid_of(env.reset())

b = read_board(g0)
print("board:", {k: v for k, v in b.items() if k != "top_bg"})

hints = {x: shape_key(window(g0, b["hint"][0], x, b["hink"])) for x in b["stations"]}
print("hint keys distinct across stations:", len(set(hints.values())) == len(hints))

pairs = top_pairs(g0, b)
print(f"top (icon, block) pairs found: {len(pairs)}")
targets = {}
for icon, block in pairs:
    k = shape_key(icon)
    hit = [x for x, hk in hints.items() if hk == k]
    print(f"  icon -> stations {hit}")
    if len(hit) == 1:
        targets[hit[0]] = shape_key(block)
print("stations with a target:", sorted(targets))

# -- build each station's real deck, and score the plan --------------------
print("\nstation  deck-keys-distinct  target-matches-at-phase")
derived = {}
for i, x in enumerate(b["stations"]):
    obs = env.reset()
    for _ in range(i):
        obs = env.step(A[4])
    keys = []
    for p in range(7):
        if p:
            obs = env.step(A[1])
        keys.append(shape_key(window(grid_of(obs), b["room"][0], x, b["rink"])))
    match = [p for p, k in enumerate(keys) if k == targets.get(x)]
    derived[x] = match[0] if len(match) == 1 else None
    print(f"  {x:3d}      {len(set(keys)) == 7!s:5s}               {match}")

print("\nderived:", derived)
print("known:  ", KNOWN)
ok = derived == KNOWN
print("VERDICT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
