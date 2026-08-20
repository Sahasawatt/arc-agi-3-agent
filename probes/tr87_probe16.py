"""tr87: the six colour-7 "blocks" paired with the six top icons are NOT
solid (probe15 found ink=5 texture in all six, counts 16/15/14/15/19/15).
Print them, crop the 5x5 interior the same way every other region here
crops (1-cell border on all sides), and check EXACT + shape (dihedral-8,
both polarities) matches against: the 5 hint-band icons, all 35 dial
states, and the six top ink-icons themselves.
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}
STATIONS = [15, 22, 29, 36, 43]
ROWS = [4, 13, 22]
ICON_X = [12, 35]
BLOCK_X = [22, 45]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def deck_at(x0, moves_to_station):
    obs = env.reset()
    for _ in range(moves_to_station):
        obs = env.step(A[4])
    g = grid_of(obs)
    d = [(g[51:58, x0:x0 + 5] == 5)[1:6, :]]
    for i in range(6):
        obs = env.step(A[1])
        g = grid_of(obs)
        d.append((g[51:58, x0:x0 + 5] == 5)[1:6, :])
    return d


def dihedral8(mask):
    forms = []
    for base in (mask, np.fliplr(mask)):
        cur = base
        for _ in range(4):
            forms.append(cur)
            cur = np.rot90(cur)
    return forms


def canon(mask):
    return min(tuple(map(tuple, t.tolist())) for t in dihedral8(mask))


obs = env.reset()
g0 = grid_of(obs)

print("== six blocks, raw 7x7 ==")
blocks = {}
for r_i, y0 in enumerate(ROWS):
    for c_i, x0 in enumerate(BLOCK_X):
        sub = g0[y0:y0 + 7, x0:x0 + 7]
        blocks[(r_i, c_i)] = sub
        print(f"  block row={r_i} col={c_i} @({x0},{y0}):")
        for row in sub:
            print("    " + "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in row))

print("\n== crop interior 5x5 (rows/cols 1:6), ink=5 mask, cell counts ==")
block_masks = {}
for k, sub in blocks.items():
    m = (sub[1:6, 1:6] == 5)
    block_masks[k] = m
    print(f"  block{k}: {m.sum()} cells")

icon_masks = {}
for r_i, y0 in enumerate(ROWS):
    for c_i, x0 in enumerate(ICON_X):
        sub = g0[y0:y0 + 7, x0:x0 + 7]
        icon_masks[(r_i, c_i)] = (sub[1:6, 1:6] == 5)

hints = {}
for x0 in STATIONS:
    hints[x0] = (g0[40:47, x0:x0 + 5] == 5)[1:6, :]

decks = {}
for st_idx, x0 in enumerate(STATIONS):
    decks[x0] = deck_at(x0, st_idx)

print("\n== block vs {hint, dial-state, top-icon} -- EXACT match (direct + inverted) ==")
hit = False
for bk, bm in block_masks.items():
    for hx, hm in hints.items():
        if np.array_equal(bm, hm):
            print(f"  EXACT: block{bk} == hint@{hx}"); hit = True
        if np.array_equal(bm, ~hm):
            print(f"  EXACT(inv): block{bk} == ~hint@{hx}"); hit = True
    for dx, deck in decks.items():
        for i, s in enumerate(deck):
            if np.array_equal(bm, s):
                print(f"  EXACT: block{bk} == deck@{dx} state{i}"); hit = True
            if np.array_equal(bm, ~s):
                print(f"  EXACT(inv): block{bk} == ~deck@{dx} state{i}"); hit = True
    for ik, im in icon_masks.items():
        if bk != ik and np.array_equal(bm, im):
            print(f"  EXACT: block{bk} == top-icon{ik}"); hit = True
if not hit:
    print("  none")

print("\n== block vs {hint, dial-state, top-icon} -- SHAPE match (dihedral-8, direct+inverted) ==")
hit2 = False
for bk, bm in block_masks.items():
    cb = canon(bm)
    cbi = canon(~bm)
    for hx, hm in hints.items():
        ch = canon(hm)
        if cb == ch or cbi == ch:
            print(f"  SHAPE: block{bk} ~ hint@{hx}"); hit2 = True
    for dx, deck in decks.items():
        for i, s in enumerate(deck):
            cs = canon(s)
            if cb == cs or cbi == cs:
                print(f"  SHAPE: block{bk} ~ deck@{dx} state{i}"); hit2 = True
    for ik, im in icon_masks.items():
        if bk == ik:
            continue
        ci = canon(im)
        if cb == ci or cbi == ci:
            print(f"  SHAPE: block{bk} ~ top-icon{ik}"); hit2 = True
if not hit2:
    print("  none")

print("\n== also: do the six TOP ICONS match each other, the hints, or the deck states "
      "(exact + shape)? ==")
hit3 = False
for ik, im in icon_masks.items():
    ci = canon(im)
    cii = canon(~im)
    for hx, hm in hints.items():
        if np.array_equal(im, hm) or np.array_equal(im, ~hm):
            print(f"  EXACT: top-icon{ik} <-> hint@{hx}"); hit3 = True
        elif canon(hm) in (ci, cii):
            print(f"  SHAPE: top-icon{ik} ~ hint@{hx}"); hit3 = True
    for dx, deck in decks.items():
        for i, s in enumerate(deck):
            if np.array_equal(im, s) or np.array_equal(im, ~s):
                print(f"  EXACT: top-icon{ik} <-> deck@{dx} state{i}"); hit3 = True
if not hit3:
    print("  none")

sys.stdout.flush()
