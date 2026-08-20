"""bp35 twelfth pass: the ride has only ever been taken from ONE column.

Every ride measured so far went up from x44 -- the reset chute's column --
and landed on the same tape position T1, whose room has background above it
on the piece's own side (a dead end, climb1). At T0 the band above the room
holds FOUR blocks, at x31-35, 37-41, 43-47, 49-53, and the piece can stand
under any of them. A click rides only when it is over the piece (p13), so
each standing position is a different door and none but x44 has been tried.

E17  stand at x=32/38/44/50, click the block above THAT position, compare
     where the tape lands.
E18  ride DOWN past the starting room: A7 at the shaft column, twice.
"""
import sys

import numpy as np

import arc_agi


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


def block_over(g, px):
    """The colour-14 block whose x-span overlaps the piece, above the room."""
    for y in range(36, -1, -1):
        xs = np.nonzero(g[y] == 14)[0]
        hit = [x for x in xs if px - 4 <= x <= px + 8]
        if hit:
            return int(np.median(hit)), y
    return None


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def to_T0(env, A):
    obs = env.reset()
    for _ in range(4):
        obs = env.step(A[4])
    return obs


print("== E17: ride from each standing position at T0 ==")
for target in (32, 38, 44, 50):
    env = arc.make(envs["bp35"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = to_T0(env, A)
    g = grid_of(obs)
    walked = 0
    while piece_x(g) != target and walked < 6:
        obs = env.step(A[4] if piece_x(g) < target else A[3])
        g2 = grid_of(obs)
        if g2 is None or piece_x(g2) == piece_x(g):
            break
        g, walked = g2, walked + 1
    px = piece_x(g)
    b = block_over(g, px)
    if b is None:
        print(f"  x={px}: no block above")
        continue
    obs = env.step(A[6], data={"x": b[0], "y": b[1]})
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  x={px} click{b}: DEAD FRAME")
        continue
    n = int((g != g2).sum())
    print(f"  x={px} click{b}: n={n:5d} x->{piece_x(g2)} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
          f"{'  RIDE' if n > 600 else '  clear only'}")
    print(f"     bands: {bands(g2)}")
    sys.stdout.flush()

print("\n== E18: ride DOWN past the starting room ==")
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = to_T0(env, A)
g = grid_of(obs)
print(f"  T0     bands: {bands(g)}")
for k in range(6):
    obs = env.step(A[7])
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  A7 #{k}: DEAD FRAME")
        break
    n = int((g != g2).sum())
    print(f"  A7 #{k}: n={n:5d} x={piece_x(g2)} "
          f"cnt={int((g2[63] == 15).sum()):2d} lvl={obs.levels_completed} "
          f"st={str(obs.state).split('.')[-1]}{'  RIDE' if n > 600 else ''}")
    if n > 600:
        print(f"     bands: {bands(g2)}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]}")
        break
    # walk back to the shaft column if the ride moved the piece off it
    if piece_x(g) != 44:
        obs = env.step(A[4] if piece_x(g) < 44 else A[3])
        g2 = grid_of(obs)
        if g2 is None:
            break
        print(f"     walk back -> x={piece_x(g2)}")
        g = g2
    sys.stdout.flush()
