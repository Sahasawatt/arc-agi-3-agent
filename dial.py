"""The combination-lock family: dial each station to the phase the board
itself names, and the level opens when all of them hold at once.

`tr87` is the family on the public roster. The board is three regions stacked
vertically, and the whole level is readable from one frame:

  * a ROOM strip -- a frame colour and one ink colour -- divided by a 7-pitch
    lattice into 5-wide station windows. Each station is an independent
    7-state cycle; one action dials the station under the clamp, its partner
    is the exact inverse (`results/tr87-probe4.txt`, `tr87-probe5.txt`).
  * a HINT band above it, same shape, same lattice: one icon per station,
    naming it.
  * a TOP region of (icon, block) pairs. The icon is framed in the HINT
    band's colour and the block in the ROOM's, which is what pairs them to a
    meaning without any coordinate being hardcoded: the icon says WHICH
    station, the block says WHICH phase of that station's own deck.

A pair's icon matches its hint under the dihedral-8 canon, in either ink
polarity -- two of tr87's five match byte-exactly and three only up to
rotation/reflection (`results/tr87-probe16.txt`), so an exact comparison reads
three of the five stations as unlabelled. The five (station, phase) pairs this
derives are the hand solution's exactly (`results/tr87-probe20.txt`, which
carries that comparison as its control), and within one station's deck all
seven shape keys are DISTINCT -- which is what makes "dial until the window
matches the target" stop at the right phase rather than at a lookalike.

The drive needs no route and no arithmetic: if the clamp is parked at a
station that is not yet at its target, dial; otherwise slide it on. The slide
wraps, so one action covers every station whichever way it turns out to go --
the direction is never assumed, because it is never needed. Everything is
re-read from the live frame each round, so a death (the budget bar burns one
cell per action, a life is ~64) costs the plan nothing.
"""

import sys

import numpy as np

DIAL = 1          # dial the station under the clamp; its partner is the inverse
SLIDE = 4         # slide the clamp one station along the lattice, wrapping
CYCLE = 7         # states in a station's deck -- a full turn teaches everything
STRIP_H = 7       # the hint band and the room are both 7 rows tall


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


def canon(m):
    """The lexicographically smallest of a mask's eight dihedral forms."""
    out, cur = [], m
    for b in (m, np.fliplr(m)):
        cur = b
        for _ in range(4):
            out.append(tuple(map(tuple, cur.tolist())))
            cur = np.rot90(cur)
    return min(out)


def shape_key(m):
    """Canon over both ink polarities -- a block names its deck state through
    whichever of the two the artist drew it in."""
    return min(canon(m), canon(~m))


def read_board(g):
    """Everything the driver needs, read off one frame -> dict or None."""
    if g is None or g.ndim < 2 or g.size == 0:
        return None
    row_bg = [int(np.bincount(r).argmax()) for r in g]
    top_bg = row_bg[0]
    top_end = 0
    while top_end + 1 < len(row_bg) and row_bg[top_end + 1] == top_bg:
        top_end += 1
    low = g[top_end + 1:]
    if low.size == 0:
        return None
    low_bg = int(np.bincount(low.ravel()).argmax())
    bands = [(top_end + 1 + a, top_end + 1 + b)
             for a, b in runs((low != low_bg).any(axis=1))]
    strips = [(y0, y1) for y0, y1 in bands if y1 - y0 + 1 == STRIP_H]
    if len(strips) != 2:
        return None
    (hy0, hy1), (ry0, ry1) = strips

    def frame_ink(y0, y1):
        sub = g[y0:y1 + 1]
        vals, cnt = np.unique(sub[sub != low_bg], return_counts=True)
        if len(vals) != 2:
            return None, None
        order = np.argsort(-cnt)
        return int(vals[order[0]]), int(vals[order[1]])

    hframe, hink = frame_ink(hy0, hy1)
    rframe, rink = frame_ink(ry0, ry1)
    if hframe is None or rframe is None:
        return None
    rx = runs((g[ry0:ry1 + 1] != low_bg).any(axis=0))
    if len(rx) != 1:
        return None
    x0, x1 = rx[0]
    stations = list(range(x0 + 1, x1, CYCLE))
    if len(stations) < 2:
        return None
    # The clamp is the band that draws in none of the two strips' colours --
    # read by what it is NOT, so nothing has to know its colour.
    clamp = None
    for y0, y1 in bands:
        sub = g[y0:y1 + 1]
        cols = runs((sub != low_bg).any(axis=0))
        drawn = set(np.unique(sub[sub != low_bg]).tolist())
        if len(cols) == 1 and not (drawn & {hframe, hink, rframe, rink}) \
                and cols[0][0] in stations:
            clamp = cols[0][0]
    return {"hint": hy0, "room": ry0, "stations": stations, "clamp": clamp,
            "hframe": hframe, "hink": hink, "rframe": rframe, "rink": rink,
            "top_end": top_end, "top_bg": top_bg}


def window(g, y0, x0, ink):
    """A station's 5x5 glyph -- the strip's interior at that lattice slot."""
    return g[y0 + 1:y0 + 6, x0:x0 + 5] == ink


def top_pairs(g, b):
    """[(icon mask, block mask)] from the top region. A pair is one row-band
    of one COLUMN run: every band crosses both runs, so scanning by band alone
    keeps one pair of each two and drops the other silently."""
    top, bg, out = g[:b["top_end"] + 1], b["top_bg"], []
    for x0, x1 in runs((top != bg).any(axis=0)):
        col = top[:, x0:x1 + 1]
        for y0, y1 in runs((col != bg).any(axis=1)):
            band = col[y0:y1 + 1]
            if band.shape[0] != STRIP_H:
                continue
            icon = block = None
            for xa in range(band.shape[1] - STRIP_H + 1):
                tile = band[:, xa:xa + STRIP_H]
                border = set(np.unique(np.concatenate(
                    [tile[0], tile[-1], tile[:, 0], tile[:, -1]])).tolist())
                if border == {b["hframe"]}:
                    icon = tile[1:6, 1:6] == b["hink"]
                elif border == {b["rframe"]}:
                    block = tile[1:6, 1:6] == b["rink"]
            if icon is not None and block is not None:
                out.append((icon, block))
    return out


def combination(g, b):
    """{station x -> target shape key}. A pair whose icon names no station, or
    names more than one, is dropped rather than guessed -- tr87's sixth pair
    is exactly that (`results/breadth-recon.md` §tr87)."""
    hints = {x: shape_key(window(g, b["hint"], x, b["hink"])) for x in b["stations"]}
    out = {}
    for icon, block in top_pairs(g, b):
        k = shape_key(icon)
        hit = [x for x, hk in hints.items() if hk == k]
        if len(hit) == 1:
            out[hit[0]] = shape_key(block)
    return out


def signature(g):
    """A board this driver can read at all, with at least two stations whose
    target is named -- tr87 alone of the seventeen playable games at reset
    (`results/dial-sig.txt`)."""
    b = read_board(g)
    return bool(b) and len(combination(g, b)) >= 2


class Dial:
    """Constructed once if the reset frame matches; asked first every round;
    answers None the moment it has nothing to do, so the rungs take over."""

    def __init__(self, values):
        self.on = {DIAL, SLIDE} <= set(values)
        self.lvl = None
        self.targets = None
        self.presses = {}     # station -> dial presses spent on it this level
        self.done = False

    def act(self, g, lvl):
        if not self.on or self.done:
            return None
        b = read_board(g)
        if b is None:
            return None       # an empty or mid-transition frame, not a verdict
        if lvl != self.lvl:
            self.lvl, self.targets, self.presses = lvl, None, {}
        if self.targets is None:
            self.targets = combination(g, b)
            if len(self.targets) < 2:
                self.done = True
                return None
        if b["clamp"] is None:
            self.done = True
            return None

        wrong = [x for x, t in self.targets.items()
                 if shape_key(window(g, b["room"], x, b["rink"])) != t]
        # A station a full turn of dialing has not answered is a misread, not a
        # station: skip it, and give up only once every one of them is.
        live = [x for x in wrong if self.presses.get(x, 0) <= CYCLE]
        if not live:
            self.done = not not wrong
            return None
        if b["clamp"] in live:
            self.presses[b["clamp"]] = self.presses.get(b["clamp"], 0) + 1
            return DIAL
        return SLIDE


if __name__ == "__main__":   # offline harness: play with nothing else in the loop
    import arc_agi

    want = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    env = arc_agi.Arcade().make(sys.argv[1] if len(sys.argv) > 1 else "tr87")
    A = {a.value: a for a in env.action_space}
    obs = env.reset()

    def grid(o):
        if o is None:
            return None
        f = np.array(o.frame)
        return None if f.ndim < 2 or f.size == 0 else f[-1]

    dl = Dial([a.value for a in env.action_space if not a.is_complex()])
    print("signature:", signature(grid(obs)))
    per, spent, done = [], 0, obs.levels_completed
    for i in range(want):
        v = dl.act(grid(obs), obs.levels_completed)
        if v is None:
            print(f"i={i} out of ideas at level {obs.levels_completed + 1}")
            break
        obs = env.step(A[v])
        spent += 1
        if obs is None or grid(obs) is None or str(obs.state) != "GameState.NOT_FINISHED":
            if obs is None:
                break
            obs = env.reset()
            if obs is None or grid(obs) is None:
                break
            continue
        if obs.levels_completed > done:
            per.append(spent)
            spent, done = 0, obs.levels_completed
            print(f"  level {done} cleared, actions={per[-1]} (i={i})")
    print("levels completed:", 0 if obs is None else obs.levels_completed, per)
