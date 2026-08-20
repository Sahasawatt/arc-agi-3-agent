"""sp80 probe 4: auto-sweep every level -- fire from each reachable spot, chain wins.

    ./.venv/Scripts/python.exe sp80_p4.py

Mechanic from p1-p3: block moves in steps of 4 (1=up 2=down 3=left 4=right),
ACTION5 fires (5th fire in a life = GAME_OVER, so max 4 per attempt), a fire from
the right position completes the level. Budget 30 actions/life; env.reset() after
>=1 action = LEVEL reset, so each attempt replays this level only.

Per level: dump the board, then try every (x,y) block position in cheap-first
order, firing up to 4 times. On level-up, record the recipe and sweep the next
board. Stops at WIN, or when a full sweep finds nothing.
"""

import sys

import numpy as np

import arc_agi

CHARS = "0123456789abcdef"


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def blk(g):
    if g is None:
        return None
    ys, xs = np.nonzero(g == 9)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()))  # x-left, y-top


def dump(g, label):
    print(f"-- board: {label} --")
    if g is None:
        print("  (empty frame)")
        return
    vals, cnt = np.unique(g, return_counts=True)
    print("  census:", dict(zip(vals.tolist(), cnt.tolist())))
    for y in range(g.shape[0]):
        print(f"  y={y:2d} " + "".join(CHARS[v & 0xF] for v in g[y]))


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}

recipes = []  # (moves, shots) per cleared level, replayable from a game reset


def ensure_level(env, obs, lvl):
    """reset() can fall back to a full game reset after a GAME_OVER; replay there."""
    if obs.levels_completed == lvl:
        return obs
    for moves, shots in recipes:
        for a in moves:
            obs = env.step(A[a])
        for _ in range(shots):
            obs = env.step(A[5])
    if obs.levels_completed != lvl:
        print(f"  REPLAY FAILED: at {obs.levels_completed}, wanted {lvl}")
    return obs


obs = env.reset()
obs = env.step(A[1])  # one real action so reset() scopes to the level from now on
obs = env.reset()

MAXLVL = 12
lvl = obs.levels_completed
while lvl < MAXLVL:
    g0 = grid(obs)
    dump(g0, f"level index {lvl}")
    b0 = blk(g0)
    print(f"  block start: {b0}")
    if b0 is None:
        print("  no colour-9 block on this board -- sweep logic does not apply, stopping")
        break
    x0, y0 = b0

    # candidate targets: every lattice-aligned position, cheap-first
    cands = []
    for tx in range(0, 61, 4):
        for ty in range(0, 61, 4):
            dist = abs(tx - x0) // 4 + abs(ty - y0) // 4
            cands.append((dist, tx, ty))
    cands.sort()

    won = None
    tried = 0
    unreachable = 0
    for dist, tx, ty in cands:
        moves = []
        dx = (tx - x0) // 4
        dy = (ty - y0) // 4
        moves += [4] * max(dx, 0) + [3] * max(-dx, 0)
        moves += [2] * max(dy, 0) + [1] * max(-dy, 0)
        if len(moves) + 4 > 29:
            continue
        obs = env.reset()
        obs = ensure_level(env, obs, lvl)
        dead = False
        for a in moves:
            obs = env.step(A[a])
            if obs.state.name != "NOT_FINISHED":
                dead = True
                break
        if dead:
            continue
        here = blk(grid(obs))
        if here != (tx, ty):
            unreachable += 1
            continue
        tried += 1
        for shot in range(4):
            obs = env.step(A[5])
            st = obs.state.name
            nl = obs.levels_completed
            if nl > lvl or st == "WIN":
                won = (tx, ty, shot + 1, moves)
                break
            if st != "NOT_FINISHED":
                break
        if won:
            break
        obs = env.reset()

    if not won:
        print(f"  SWEEP EXHAUSTED at level index {lvl}: {tried} positions fired, "
              f"{unreachable} unreachable -- no single-position win")
        break
    tx, ty, shots, moves = won
    recipes.append((moves, shots))
    print(f"  LEVEL CLEARED from block=({tx},{ty}) with {shots} shot(s), "
          f"{len(moves)} moves, state={obs.state.name} lvl={obs.levels_completed}")
    lvl = obs.levels_completed
    if obs.state.name == "WIN":
        print("  GAME WIN")
        break
    # obs now sits at the next level's start
    g = grid(obs)
    if g is None:
        # engine can hand back an empty frame on the transition; take a free look
        obs = env.reset()

print(f"\nfinal: state={obs.state.name} levels_completed={obs.levels_completed}")
sys.stdout.flush()
