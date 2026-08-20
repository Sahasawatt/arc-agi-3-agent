"""dc22: lay the bridges with the two buttons and walk to the marker.

What p1-p3 measured: the colour-4 field is void, blocks are the only walkable
ground, the checkered 9/4 pad is a wall and its solid twin is floor. The two
panel buttons are toggles that SWAP a pair each:

  8-button: colour-8 block   (12-17, 30-33) 6x4  <->  (18-21, 24-29) 4x6
  9-button: checkered pad    ( 8-11, 34-37)      <->  solid 9 block (18-21, 20-23)

So the route up is built, not found: press 9 to floor the pad, walk up and
right along the 8- and 13-blocks, press 8 to stand a bridge from y30 to y24,
climb it, press 9 again to floor the block at y20-23, climb that, and walk
right onto the colour-11 marker at (24-25, 20-21) -- the only object no button
touches, sitting in its own frame exactly as the piece does.

Each step is logged with the piece position, so a refusal shows up as a
position that does not move rather than as a silent failure.
"""
import sys

import numpy as np

import arc_agi

UP, DOWN, LEFT, RIGHT = 1, 2, 3, 4
BTN8, BTN9 = (48, 19), (48, 36)
LINE = ([("c", BTN9)] + [("m", UP)] * 5 + [("m", RIGHT)] * 4
        + [("c", BTN8)] + [("m", UP)] * 3
        + [("c", BTN9)] + [("m", UP)] * 2 + [("m", RIGHT)] * 3)


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece(g):
    ys, xs = np.nonzero(g == 14)
    return (int(xs.min()), int(ys.min())) if len(ys) else None


def show(g, label):
    print(f"  {label}")
    for y in range(16, 54):
        line = "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                       for v in g[y, 0:32])
        if set(line) != {"4"}:
            print(f"    y{y:2d} {line}")


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["dc22"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = grid_of(obs)
print(f"start piece={piece(g)}")
for i, s in enumerate(LINE):
    if s[0] == "c":
        obs = env.step(A[6], data={"x": s[1][0], "y": s[1][1]})
        what = f"click{s[1]}"
    else:
        obs = env.step(A[s[1]])
        what = f"A{s[1]}"
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  i={i:2d} {what}: DEAD FRAME")
        break
    print(f"  i={i:2d} {what:14s} n={int((g != g2).sum()):5d} piece={piece(g2)} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}"
          f"{'   REFUSED' if piece(g2) == piece(g) and s[0] == 'm' else ''}")
    g = g2
    if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
        print(f"  END lvl={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]} after {i + 1} actions")
        break
    sys.stdout.flush()
show(g, f"final board, piece={piece(g)}")
