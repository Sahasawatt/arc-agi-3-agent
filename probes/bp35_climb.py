"""bp35: climb level 1 by hand, forward-only.

The model all ten probes now agree on:
  * the shaft is the colour-10 column at x43-47; the piece rides it with A4
    when a shaft section sits ABOVE the chamber and with A7 when one sits
    BELOW (p12 E15: A7 at x44 fired 1343 cells with the piece not moving).
  * a ride travels until a colour-14 block stops it -- clearing the block
    over the chute before riding doubled the trip, +18 -> +36 (p10 E13).
  * a click turns a block into floor (p12 E16: `3eee35` -> `aaaaa5`).
  * the flood is an ACTION timer: with no tape event it starts at action 8
    and kills at 16; each event buys about 8 (p8 E7/E8).

So the line is: stand in the shaft column, clear whatever is above, ride,
repeat. This drives that loop from the frame rather than from a recipe, and
stops on a level, a game over, or the budget.
"""
import sys

import numpy as np

import arc_agi

SHAFT = (43, 47)
CEIL = 36          # the piece's chamber starts just under this
BUDGET = 40


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


def block_above(g):
    """Lowest colour-14 block overlapping the shaft column, above the ceiling."""
    rowsy = [y for y in range(CEIL, -1, -1)
             if (g[y, SHAFT[0]:SHAFT[1] + 1] == 14).any()]
    if not rowsy:
        return None
    y = rowsy[0]
    xs = np.nonzero(g[y] == 14)[0]
    xs = [x for x in xs if SHAFT[0] - 2 <= x <= SHAFT[1] + 2]
    return (int(np.median(xs)), y) if xs else None


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


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
print(f"start x={piece_x(g)} bands: {bands(g)}")

line, last_ride, stuck = [], None, 0
for i in range(BUDGET):
    px = piece_x(g)
    if px is None:
        print("  piece lost")
        break
    if px < 44:
        what, obs = "A4->shaft", env.step(A[4])
    elif px > 44:
        what, obs = "A3->shaft", env.step(A[3])
    else:
        b = block_above(g)
        if b is not None and stuck < 2:
            what, obs = f"click{b}", env.step(A[6], data={"x": b[0], "y": b[1]})
        elif last_ride != 4:
            what, obs = "A4 ride up", env.step(A[4])
        else:
            what, obs = "A7 ride down", env.step(A[7])
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d} {what}: DEAD FRAME")
        break
    n = int((g != g2).sum())
    if n > 600:
        last_ride = 4 if "A4" in what else (7 if "A7" in what else last_ride)
        stuck = 0
    elif "ride" in what:
        stuck += 1
        last_ride = 4 if last_ride != 4 else 7
    line.append(what)
    print(f"  i={i:2d} {what:16s} n={n:5d} x={piece_x(g2)} "
          f"cnt={int((g2[63] == 15).sum()):2d} flood={flood_top(g2)} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
          f"{'   RIDE' if n > 600 else ''}")
    if n > 600:
        print(f"       bands: {bands(g2)}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]} after {i + 1} actions")
        break
    sys.stdout.flush()
print(f"line: {line}")
