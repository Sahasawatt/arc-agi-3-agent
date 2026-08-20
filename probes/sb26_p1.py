"""sb26 with an AIMED click.

breadth-recon §sb26 closed this game as "every input channel is dead at every
reachable state" -- including "a stride-2 full-grid sweep, 1,024 spots, one
episode each, changes zero cells" and "a click does not even tick the clock,
so it is swallowed before the game logic". Every one of those clicks went
through `set_data` and arrived with no coordinates (results/click-probe.txt).

Aimed, exactly four things answer, and they are the four bottom blocks:
(19,58) colour 14, (27,58) colour 15, (35,58) colour 9, (43,58) colour 11,
20 cells each (results/click-sweep-all.txt). That is precisely the reading
the recon guessed and could not test: the top row's boxes run 9, 14, 11, 15
and the bottom blocks run 14, 15, 9, 11, so the level looks like "click the
blocks in the top row's order".

E1  the board, and what one click does.
E2  the top row's order, clicked.
E3  control: a deliberately wrong order, in a fresh episode.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def dump(g, label, y0=0, y1=63):
    print(f"  {label}")
    for y in range(y0, y1 + 1):
        line = "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                       for v in g[y])
        if len(set(line)) > 1:
            print(f"    y{y:2d} {line}")


def boxes(g, row):
    """(centre x, colour) of each run of non-background in one row."""
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


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def fresh():
    env = arc.make(envs["sb26"].game_id)
    return env, {a.value: a for a in env.action_space}, env.reset()


env, A, obs = fresh()
g = grid_of(obs)
print("== E1: the board ==")
dump(g, "reset")
top = [b for b in boxes(g, 6)]
bottom = [b for b in boxes(g, 58)]
print(f"  top row (y6):    {top}")
print(f"  bottom row (y58): {bottom}")
obs = env.step(A[6], data={"x": 19, "y": 58})
g2 = grid_of(obs)
print(f"  one click at (19,58): n={int((g != g2).sum())} "
      f"lvl={obs.levels_completed}")
ys, xs = np.nonzero(g != g2)
if len(ys):
    print(f"    changed y{ys.min()}-{ys.max()} x{xs.min()}-{xs.max()}")
    dump(g2, "after", int(ys.min()), int(ys.max()))
sys.stdout.flush()

print("\n== E2: click the bottom blocks in the TOP row's colour order ==")
env, A, obs = fresh()
g = grid_of(obs)
where = {c: x for x, c in boxes(g, 58)}
# the top row is drawn with colour-5 separators between the boxes; the
# ORDER is the colours that actually have a block to click
order = [c for _, c in boxes(g, 6) if c in where]
print(f"  order wanted: {order}; bottom positions: {where}")
for c in order:
    if c not in where:
        print(f"  colour {c} has no bottom block -- stopping")
        break
    obs = env.step(A[6], data={"x": where[c], "y": 58})
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  click colour {c}: DEAD FRAME")
        break
    print(f"  click colour {c:2d} at x={where[c]:2d}: n={int((g != g2).sum()):5d} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]}")
        break
sys.stdout.flush()

print("\n== E3: control -- the reverse order in a fresh episode ==")
env, A, obs = fresh()
g = grid_of(obs)
for c in reversed(order):
    obs = env.step(A[6], data={"x": where[c], "y": 58})
    g2 = grid_of(obs)
    if g2 is None:
        break
    print(f"  click colour {c:2d}: n={int((g != g2).sum()):5d} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]}")
        break
