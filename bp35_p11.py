"""bp35 ninth pass: stop hand-picking coordinates -- find the blocks and ask
each one, from the state where the climb has stalled.

State S = A4 x4 (climb, tape +18) then click(45,33) (tape +24). From S the
shuttle is silent and re-clicking that spot answers 1 cell (p10). So S is a
new wall, and what to press next is a question about the board, not about
the recipe: enumerate every colour-14 block and every narrow colour-10 stub
(a chute reads as one), then spend ONE fresh episode per candidate.

Readouts per candidate: cells changed, tape shift, whether a climb becomes
possible afterwards (A3 out, A4 back in -- silent means still walled), and
the level. A candidate that answers 1 cell is inert; the control is that S
itself is reproduced identically in every episode (its band string is
printed each time and must match).
"""
import sys

import numpy as np

import arc_agi

S_PLAN = [("move", 4)] * 4 + [("click", 45, 33)]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


def bands(g):
    out = []
    for y0 in range(0, 60, 6):
        band = g[y0:y0 + 6]
        codes = []
        for x0, x1 in ((13, 30), (31, 53)):
            sub = band[:, x0:x1 + 1]
            n10, n14 = int((sub == 10).sum()), int((sub == 14).sum())
            codes.append(f"{n14 // 21 or 1}G" if n14 > 20 else "B" if n10 > 60
                         else "b" if n10 > 10 else ".")
        out.append(codes[0] + "/" + codes[1])
    return " ".join(out)


def shift(a, b):
    best = (None, 0.0)
    for dy in range(-36, 37, 6):
        rows = [y for y in range(max(0, -dy), min(63, 63 - dy))]
        if len(rows) < 20:
            continue
        frac = float((a[rows, 13:54] == b[[y + dy for y in rows], 13:54]).mean())
        if frac > best[1]:
            best = (dy, frac)
    return best


def blocks(g, colour=14):
    """Axis-aligned components of one colour, as (cx, cy, w, h)."""
    mask = (g == colour)
    seen = np.zeros_like(mask, dtype=bool)
    out = []
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if not mask[y, x] or seen[y, x]:
                continue
            stack, cells = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1]
                            and mask[ny, nx] and not seen[ny, nx]):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            out.append(((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2,
                        max(xs) - min(xs) + 1, max(ys) - min(ys) + 1))
    return out


def to_state(env, A):
    obs = env.reset()
    for s in S_PLAN:
        obs = (env.step(A[s[1]]) if s[0] == "move"
               else env.step(A[6], data={"x": s[1], "y": s[2]}))
    return obs


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = to_state(env, A)
gS = grid_of(obs)
S_BANDS = bands(gS)
print(f"== state S: x={piece_x(gS)} bands: {S_BANDS} ==")
for y in range(64):
    print("  y%2d " % y + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                  for v in gS[y]))

cands = [(cx, cy, f"block {w}x{h}") for cx, cy, w, h in blocks(gS, 14)]
print(f"\n== {len(cands)} colour-14 blocks at S; one fresh episode each ==")
sys.stdout.flush()

for cx, cy, what in cands:
    env = arc.make(envs["bp35"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = to_state(env, A)
    g = grid_of(obs)
    if bands(g) != S_BANDS:
        print(f"  ({cx:2d},{cy:2d}) SETUP DRIFTED -- reading discarded")
        continue
    obs = env.step(A[6], data={"x": cx, "y": cy})
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  ({cx:2d},{cy:2d}) {what}: DEAD FRAME")
        continue
    n = int((g != g2).sum())
    dy, frac = shift(g, g2) if n > 200 else (0, 1.0)
    # does a climb open up afterwards?
    obs = env.step(A[3])
    g3 = grid_of(obs)
    obs = env.step(A[4])
    g4 = grid_of(obs)
    climb = int((g3 != g4).sum()) if g4 is not None else -1
    print(f"  ({cx:2d},{cy:2d}) {what:12s} n={n:5d} tape dy={dy:+3d} "
          f"then A3/A4 -> n={climb:5d}{'  CLIMB' if climb > 200 else ''} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
    if n > 200:
        print(f"        bands: {bands(g2)}")
    sys.stdout.flush()
