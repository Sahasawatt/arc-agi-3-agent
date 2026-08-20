"""sb26: a click SELECTS -- so what commits?

p1 measured the click as a cursor: the first click draws a 0-border around a
bottom block (20 cells), each later click moves that border (40 = one erased,
one drawn), and neither the top row's order nor its reverse wins anything.

breadth-recon's readings of the other two actions were taken when nothing
could be selected, because no click had ever landed:
  * ACTION5 = a pure timer burn, one cell of the y53 row per press, GAME_OVER
    at press 64, nothing else ever changes;
  * ACTION7 = free and silent, 70 presses change nothing.
Both were measured with an EMPTY selection. This asks them again with a block
selected.

E4  select each block, then press 7; and select each block, then press 5.
E5  the top row's order, committing after each selection with whichever of
    the two answered in E4.
Control: press 7 and 5 with nothing selected, in the same invocation.
"""
import sys

import numpy as np

import arc_agi

BOTTOM_ROW = 58


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


def dump(g, label, y0, y1):
    print(f"    {label}")
    for y in range(y0, y1 + 1):
        line = "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in g[y])
        if len(set(line)) > 1:
            print(f"      y{y:2d} {line}")


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def fresh():
    env = arc.make(envs["sb26"].game_id)
    return env, {a.value: a for a in env.action_space}, env.reset()


env, A, obs = fresh()
g0 = grid_of(obs)
where = {c: x for x, c in boxes(g0, BOTTOM_ROW)}
order = [c for _, c in boxes(g0, 6) if c in where]
print(f"blocks: {where}   top-row order: {order}")

print("\n== control: 7 and 5 with nothing selected ==")
for v in (7, 5):
    env, A, obs = fresh()
    g = grid_of(obs)
    obs = env.step(A[v])
    g2 = grid_of(obs)
    print(f"  A{v}: n={int((g != g2).sum())} lvl={obs.levels_completed} "
          f"st={str(obs.state).split('.')[-1]}")

print("\n== E4: select a block, then press 7 / 5 ==")
for c in order:
    for v in (7, 5):
        env, A, obs = fresh()
        g = grid_of(obs)
        obs = env.step(A[6], data={"x": where[c], "y": BOTTOM_ROW})
        g1 = grid_of(obs)
        obs = env.step(A[v])
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  select {c}, A{v}: DEAD FRAME")
            continue
        n = int((g1 != g2).sum())
        print(f"  select colour {c:2d}, then A{v}: n={n:5d} "
              f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
        if n > 1:
            ys, xs = np.nonzero(g1 != g2)
            dump(g2, f"after (changed y{ys.min()}-{ys.max()})",
                 int(ys.min()), int(ys.max()))
        sys.stdout.flush()

print("\n== E5: select-and-commit down the top row's order ==")
for commit in (7, 5):
    env, A, obs = fresh()
    g = grid_of(obs)
    print(f"  committing with A{commit}")
    for c in order:
        obs = env.step(A[6], data={"x": where[c], "y": BOTTOM_ROW})
        g2 = grid_of(obs)
        if g2 is None:
            print("    dead frame on select")
            break
        g = g2
        obs = env.step(A[commit])
        g2 = grid_of(obs)
        if g2 is None:
            print("    dead frame on commit")
            break
        print(f"    colour {c:2d}: commit n={int((g != g2).sum()):5d} "
              f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
        g = g2
        if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
            print(f"    END lvl={obs.levels_completed} "
                  f"state={str(obs.state).split('.')[-1]}")
            break
    sys.stdout.flush()
