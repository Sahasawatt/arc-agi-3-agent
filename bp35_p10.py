"""bp35 eighth pass: play it WITH the click, which now lands.

Known after p7/p8/p9:
  * the flood is an ACTION TIMER, not a crossing budget -- with no tape
    event it starts at action 8 and the run is GAME_OVER at 16; one tape
    event moves both by 8 (E7/E8, results/bp35-p7.txt, bp35-p8.txt).
  * a tape event is A4 INTO x44 (tape down 18) or A7 OUT of x44 (tape up
    18); returning to x44 from either side never fires again (E7).
  * a click on an e-block changes ~26-36 cells; a click on the 4-block
    group sitting above the ceiling after event #1 changed 1343 (p9).

E11  what the 1343-cell click DID -- bands and tape shift either side.
E12  can the piece climb AGAIN once that click has been paid?
E13  clear the block over the chute BEFORE the first climb, then climb.
Each arm prints the flood/counter per action, so a line that spends the
timer is visible as it happens rather than at the game over.
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


def flood_top(g):
    ys, _ = np.nonzero(g[:63] == 15)
    return int(ys.min()) if len(ys) else None


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


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def run(label, steps):
    """steps: list of ('move', v) or ('click', x, y)."""
    print(f"== {label} ==")
    env = arc.make(envs["bp35"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    g = grid_of(obs)
    print(f"  start  x={piece_x(g)}  bands: {bands(g)}")
    for i, s in enumerate(steps):
        if s[0] == "move":
            obs = env.step(A[s[1]])
            what = f"A{s[1]}"
        else:
            obs = env.step(A[6], data={"x": s[1], "y": s[2]})
            what = f"click({s[1]},{s[2]})"
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  i={i:2d} {what:14s} DEAD FRAME")
            break
        n = int((g != g2).sum())
        tag = ""
        if n > 200:
            dy, frac = shift(g, g2)
            tag = f"  TAPE dy={dy:+d} fit={frac:.2f}"
        print(f"  i={i:2d} {what:14s} n={n:5d} x={piece_x(g2)} "
              f"cnt={int((g2[63] == 15).sum()):2d} flood={flood_top(g2)} "
              f"lvl={obs.levels_completed} "
              f"st={str(obs.state).split('.')[-1]}{tag}")
        if n > 200:
            print(f"       bands: {bands(g2)}")
        g = g2
        if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
            print(f"  END lvl={obs.levels_completed} "
                  f"state={str(obs.state).split('.')[-1]}")
            break
        sys.stdout.flush()
    print()


# E11/E12: climb, click the blocking group, try to climb again.
run("E11+E12: climb -> click the group above -> try to climb again",
    [("move", 4)] * 4 + [("click", 45, 33)]
    + [("move", 3), ("move", 4)] * 3)

# E13: clear the block over the chute BEFORE walking in.
run("E13: click the block over the chute first, then walk in",
    [("click", 45, 15), ("move", 4), ("move", 4), ("move", 4), ("move", 4),
     ("move", 3), ("move", 4)])

# E14: how many times can the same group be clicked -- is it a pump?
run("E14: climb, then click the same spot repeatedly",
    [("move", 4)] * 4 + [("click", 45, 33)] * 6)
