"""ka59: the piece can stand ON the dot -- what does stepping off do?

The click is not a teleport: it answers only when aimed at the dot or its
ring, and it puts the PIECE on the dot's square (results/ka59-p2.txt). That
is a state the 74-state keyboard BFS never contained, because the keyboard
can only walk INTO the dot, which kicks it east to the fixed landing at
(43,31).

If stepping OFF the dot drags or kicks it by direction, the dot can finally
be moved somewhere other than east. One fresh episode per direction:
click onto the dot, then press the direction, then read both positions --
and remember the occlusion law: the piece standing on the dot HIDES it, so
the dot's true position is only readable after stepping away.

Then the two candidate endgames, whichever direction works:
  E9  dot into the LEFT slot interior (10-14, 32-36)
  E10 kick east first (walk into it), click onto it at (43,31), and step
      off toward the right slot interior (45-47, 27-29).
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def piece(g):
    ys, xs = np.nonzero(g[:63] == 0)
    return (int(xs.min()), int(ys.min())) if len(ys) else None


def dot(g):
    ys, xs = np.nonzero(g[:63] == 5)
    return (int(xs.min()), int(ys.min())) if len(ys) else None


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}


def fresh():
    env = arc.make(envs["ka59"].game_id)
    return env, {a.value: a for a in env.action_space}, env.reset()


print("== E8: click onto the dot, then step off in each direction ==")
for v, name in ((1, "UP"), (2, "DOWN"), (3, "LEFT"), (4, "RIGHT")):
    env, A, obs = fresh()
    g = grid_of(obs)
    d0 = dot(g)
    obs = env.step(A[6], data={"x": d0[0], "y": d0[1]})
    g = grid_of(obs)
    obs = env.step(A[v])
    g2 = grid_of(obs)
    if g2 is None:
        print(f"  {name}: DEAD FRAME")
        continue
    print(f"  {name:5s}: piece {piece(g)} -> {piece(g2)}  "
          f"dot {d0} -> {dot(g2)}  lvl={obs.levels_completed} "
          f"st={str(obs.state).split('.')[-1]}")
    sys.stdout.flush()
