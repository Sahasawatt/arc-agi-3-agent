"""bp35 thirteenth pass: does clearing the blocks BESIDE the room widen it?

At T1 the piece's room is x31-53 and the walk left stops at x=32 (p12 E15).
The colour-14 blocks at x13-29 in the same rows become floor when clicked
(p12 E16) but are separated from the room by one background column at x30,
which no click reaches. Whether that column is a wall is a question about
the game's own walk rule, not about the pixels -- so ask the game.

Arm 1: at T1 clear both blocks in the room's row band, then walk left as far
       as it goes (before: x=32).
Arm 2: clear the row band AND the band below it, then walk left.
Arm 3: control -- walk left at T1 with nothing cleared.
If the walk gets past x=32, the left column's own doors (blocks at x13-29
above the ceiling) become reachable and the tape's reachable set is not the
three positions p14 measured.
"""
import sys

import numpy as np

import arc_agi

S_PLAN = [("m", 4)] * 4 + [("c", 45, 33)]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


def to_T1(env, A):
    obs = env.reset()
    for s in S_PLAN:
        obs = (env.step(A[s[1]]) if s[0] == "m"
               else env.step(A[6], data={"x": s[1], "y": s[2]}))
    return obs


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

ARMS = [
    ("1: clear the room's own row band (x15,21,27 at y39)",
     [(15, 39), (21, 39), (27, 39)]),
    ("2: clear that band and the one below (y45)",
     [(15, 39), (21, 39), (27, 39), (15, 45), (21, 45), (27, 45)]),
    ("3: control -- clear nothing", []),
]

for label, clicks in ARMS:
    env = arc.make(envs["bp35"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = to_T1(env, A)
    g = grid_of(obs)
    print(f"== {label} ==")
    for cx, cy in clicks:
        obs = env.step(A[6], data={"x": cx, "y": cy})
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  click({cx},{cy}): DEAD FRAME")
            break
        print(f"  click({cx},{cy}): n={int((g != g2).sum()):5d} "
              f"st={str(obs.state).split('.')[-1]}")
        g = g2
    xs = [piece_x(g)]
    for _ in range(7):
        obs = env.step(A[3])
        g2 = grid_of(obs)
        if g2 is None:
            break
        g = g2
        xs.append(piece_x(g))
        if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
            break
    print(f"  walk left: {xs}  lvl={obs.levels_completed} "
          f"st={str(obs.state).split('.')[-1]}")
    # if it got past the old wall, is there now a block above to ride?
    px = piece_x(g)
    if px is not None and px < 32:
        for y in range(36, -1, -1):
            hit = [x for x in np.nonzero(g[y] == 14)[0] if px - 4 <= x <= px + 8]
            if hit:
                cx = int(np.median(hit))
                obs = env.step(A[6], data={"x": cx, "y": y})
                g2 = grid_of(obs)
                n = int((g != g2).sum()) if g2 is not None else -1
                print(f"  then click({cx},{y}) over the piece: n={n} "
                      f"{'RIDE' if n > 600 else 'clear only'} "
                      f"lvl={obs.levels_completed}")
                break
    print()
    sys.stdout.flush()
