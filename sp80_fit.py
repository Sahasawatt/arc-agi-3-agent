"""sp80: fit the transfer-legality predicate against the p12+p13 maps.

    ./.venv/Scripts/python.exe sp80_fit.py

Data: two measured maps (active body -> did ACTION5 transfer). Search: single
half-plane predicates p*dx + q*dy + r >= 0 over every (active corner, target
corner) pair, small integer coefficients, optionally OR'd with left-wall /
ceiling contact. Also cones (conjunction of two half-planes over the same
corner pair). A predicate must explain EVERY cell of BOTH maps.
"""

import itertools
import sys

# (map rows, y range, x range, active w/h, target x,y,w,h)
P12 = ("""
2 2 2 2 2 2 2 2 2 2 2 2
2 2 2 2 2 2 2 - - - - -
2 2 2 2 2 2 - - - - - -
2 2 2 2 - - - - - - - -
2 2 2 - - - - - - - - -
2 2 2 - - - - - - - - -
2 2 - - - - - - - - - -
2 - - - - - - - - - - -
2 - - - - - - - - - - -
""", 16, 48, 0, 44, 20, 4, 28, 24, 12, 4)

P13 = ("""
P P P P P P P P P P P P P P
P P P P P P P P P - - - - -
P P P P P P P - - - - - - -
P P P P P P - - - - - - - -
P P P P P - - - - - - - - -
P P P P - - - - - - - - - -
P P P P - - - - - - - - - -
P P P - - - - - - - - - - -
P P P - - - - - - - - - - -
""", 16, 48, 0, 52, 12, 4, 20, 24, 20, 4)


def cells(spec):
    rows, y0, y1, x0, x1, aw, ah, tx, ty, tw, th = spec
    out = []
    lines = [ln.split() for ln in rows.strip().splitlines()]
    for iy, ln in enumerate(lines):
        y = y0 + 4 * iy
        for ix, ch in enumerate(ln):
            x = x0 + 4 * ix
            out.append((x, y, aw, ah, tx, ty, tw, th, ch != "-"))
    return out


DATA = cells(P12) + cells(P13)
print(f"{len(DATA)} labelled cells")


def corners(x, y, w, h):
    return [(x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1),
            (x + w // 2, y + h // 2)]


COEF = range(-3, 4)
CIDX = range(5)

hits = []
for ai, ti in itertools.product(CIDX, CIDX):
    for p, q in itertools.product(COEF, COEF):
        if p == q == 0:
            continue
        for r in range(-24, 25, 2):
            for use_wall in (False, True):
                for use_ceil in (False, True):
                    ok = True
                    for (x, y, aw, ah, tx, ty, tw, th, lab) in DATA:
                        ax, ay = corners(x, y, aw, ah)[ai]
                        tcx, tcy = corners(tx, ty, tw, th)[ti]
                        dx, dy = tcx - ax, tcy - ay
                        pred = (p * dx + q * dy + r) >= 0
                        if use_wall and x == 0:
                            pred = True
                        if use_ceil and y == 16:
                            pred = True
                        if pred != lab:
                            ok = False
                            break
                    if ok:
                        hits.append((ai, ti, p, q, r, use_wall, use_ceil))

print(f"single half-plane fits: {len(hits)}")
for h in hits[:20]:
    print("  ", h)

if not hits:
    # cones: two half-planes AND'ed, same corner pair, wall/ceiling override
    print("trying cones...")
    cone_hits = []
    planes = [(p, q, r) for p in COEF for q in COEF for r in range(-24, 25, 2)
              if not (p == 0 and q == 0)]
    for ai, ti in itertools.product(CIDX, CIDX):
        # precompute dx,dy per cell for this corner pair
        pts = []
        for (x, y, aw, ah, tx, ty, tw, th, lab) in DATA:
            ax, ay = corners(x, y, aw, ah)[ai]
            tcx, tcy = corners(tx, ty, tw, th)[ti]
            pts.append((tcx - ax, tcy - ay, x == 0, y == 16, lab))
        # planes that keep every positive point (with overrides): candidates
        pos = [(dx, dy) for dx, dy, w, c, lab in pts if lab and not w and not c]
        cand = [pl for pl in planes
                if all(pl[0] * dx + pl[1] * dy + pl[2] >= 0 for dx, dy in pos)]
        for i, pl1 in enumerate(cand):
            for pl2 in cand[i:]:
                ok = True
                for dx, dy, w, c, lab in pts:
                    pred = (pl1[0] * dx + pl1[1] * dy + pl1[2] >= 0 and
                            pl2[0] * dx + pl2[1] * dy + pl2[2] >= 0)
                    if w or c:
                        pred = True
                    if pred != lab:
                        ok = False
                        break
                if ok:
                    cone_hits.append((ai, ti, pl1, pl2))
        if len(cone_hits) > 50:
            break
    print(f"cone fits: {len(cone_hits)}")
    for h in cone_hits[:20]:
        print("  ", h)
sys.stdout.flush()
