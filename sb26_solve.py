"""sb26: drag the blocks into the machine's slots, in the top row's order.

p3 found the other half of the click: select a bottom block, then click one of
the machine's four colour-2 slot marks at y29-30 (x21-22, 27-28, 33-34, 39-40)
and the block moves into it (n=53, y28-61). The top row names the order --
9, 14, 11, 15 -- and the blocks sit in a different one, 14, 15, 9, 11, which
is the whole puzzle.

Two arms, each a fresh episode and each printing the level after every action:
  A  the top row's order, left slot to right slot
  B  control -- the blocks' own left-to-right order, which should not win
Level-1 baseline is 18; each placement is two actions, so the line is eight.
"""
import sys

import numpy as np

import arc_agi

ROW = 58
SLOT_Y = 29


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def boxes(g, row):
    bg = int(np.bincount(g.ravel()).argmax())
    out, run = [], None
    for x in range(g.shape[1]):
        c = int(g[row, x])
        if c != bg and (run is None or run[2] != c):
            if run:
                out.append(((run[0] + run[1]) // 2, run[2]))
            run = [x, x, c]
        elif c != bg:
            run[1] = x
        elif run:
            out.append(((run[0] + run[1]) // 2, run[2]))
            run = None
    if run:
        out.append(((run[0] + run[1]) // 2, run[2]))
    return out


def slots(g):
    """The machine's slot marks: runs of colour 2 in the slot row."""
    out, run = [], None
    for x in range(g.shape[1]):
        if g[SLOT_Y, x] == 2:
            run = [x, x] if run is None else [run[0], x]
        elif run:
            out.append((run[0] + run[1]) // 2)
            run = None
    if run:
        out.append((run[0] + run[1]) // 2)
    return out


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def run(order, label):
    env = arc.make(envs["sb26"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    g = grid_of(obs)
    where = {c: x for x, c in boxes(g, ROW)}
    sl = slots(g)
    print(f"== {label}: order {order} into slots {sl} ==")
    for i, c in enumerate(order):
        if i >= len(sl):
            break
        for x, y, what in ((where[c], ROW, f"select {c}"),
                           (sl[i], SLOT_Y, f"place in slot {i}")):
            obs = env.step(A[6], data={"x": x, "y": y})
            g2 = grid_of(obs)
            if g2 is None:
                print(f"  {what}: DEAD FRAME")
                return
            print(f"  {what:16s} click({x:2d},{y:2d}) "
                  f"n={int((g != g2).sum()):5d} lvl={obs.levels_completed} "
                  f"st={str(obs.state).split('.')[-1]}")
            g = g2
            if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
                print(f"  END lvl={obs.levels_completed} "
                      f"state={str(obs.state).split('.')[-1]}")
                return
        sys.stdout.flush()


env = arc.make(envs["sb26"].game_id)
g0 = grid_of(env.reset())
top = [c for _, c in boxes(g0, 6) if c in {c2 for _, c2 in boxes(g0, ROW)}]
bottom = [c for _, c in boxes(g0, ROW)]
run(top, "A: the top row's order")
print()
run(bottom, "B: control -- the blocks' own order")
