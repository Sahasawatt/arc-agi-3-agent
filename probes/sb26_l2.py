"""sb26 level 2 by hand: two machines, seven blocks, one order.

The L2 board (results/l2-peek.txt): a seven-colour recipe row (c,f,8,9,e,b,6
at y1-6), seven stock blocks (8,f,e,c,6,9,b at y57-60), and TWO machines --
an upper one with three slot marks (y22-23) and a lower one with four
(y36-37), joined by a colour-14 pipe. The sorter's level-1 line was
select-then-slot in recipe order, run with A5.

Slot orders to try, one fresh episode each (level 1 is replayed by the known
9-action line first):
  A  upper machine left-to-right, then lower left-to-right
  B  lower first, then upper
  C  interleaved by x across both rows (global left-to-right)
Each arm loads all seven, then presses A5, then A7 if A5 does nothing.
"""
import sys

import numpy as np

import arc_agi

L1 = [("c", 35, 58), ("c", 22, 29), ("c", 19, 58), ("c", 28, 29),
      ("c", 43, 58), ("c", 34, 29), ("c", 27, 58), ("c", 40, 29), ("m", 5)]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def runs_row(g, y, skip=(4, 5, 0)):
    out, run = [], None
    for x in range(g.shape[1]):
        c = int(g[y, x])
        if c not in skip and (run is None or run[2] != c):
            if run:
                out.append(tuple(run))
            run = [x, x, c]
        elif c not in skip and run:
            run[1] = x
        else:
            if run:
                out.append(tuple(run))
            run = None
    if run:
        out.append(tuple(run))
    return out


def slot_marks(g, y):
    """Colour-2 marks in one row."""
    return [( (a + b) // 2, y) for a, b, c in runs_row(g, y) if c == 2]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def to_l2():
    env = arc.make(envs["sb26"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    for s in L1:
        obs = (env.step(A[6], data={"x": s[1], "y": s[2]}) if s[0] == "c"
               else env.step(A[s[1]]))
    return env, A, obs


env, A, obs = to_l2()
g = grid_of(obs)
# y1 is each recipe box's solid top edge -- one run per box. y3 cuts
# through the hollow interior and reads every box twice (two wall runs).
recipe = [c for _, _, c in runs_row(g, 1) if c != 5]
stock = {c: (a + b) // 2 for a, b, c in runs_row(g, 58)}
upper = slot_marks(g, 22)
lower = slot_marks(g, 36)
print(f"recipe {recipe}")
print(f"stock  {stock}")
print(f"upper slots {upper}")
print(f"lower slots {lower}")
sys.stdout.flush()

ORDERS = {
    "A upper then lower": upper + lower,
    "B lower then upper": lower + upper,
    "C global left-to-right": sorted(upper + lower),
}

for label, slots in ORDERS.items():
    env, A, obs = to_l2()
    g = grid_of(obs)
    print(f"== {label} ==")
    if len(slots) < len(recipe):
        print(f"  only {len(slots)} slots for {len(recipe)} colours -- skip")
        continue
    for i, c in enumerate(recipe):
        if c not in stock:
            print(f"  colour {c} not in stock -- stop")
            break
        for x, y in ((stock[c], 58), slots[i]):
            obs = env.step(A[6], data={"x": x, "y": y})
            g2 = grid_of(obs)
            if g2 is None:
                print("  DEAD FRAME")
                break
            g = g2
    for v in (5, 7):
        obs = env.step(A[v])
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  A{v}: DEAD FRAME")
            break
        print(f"  A{v}: n={int((g != g2).sum()):5d} lvl={obs.levels_completed} "
              f"st={str(obs.state).split('.')[-1]}")
        g = g2
        if obs.levels_completed >= 2:
            print("  ** LEVEL 2 **")
            break
    sys.stdout.flush()
