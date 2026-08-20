"""dc22 third pass: the 9-button unseals the room -- so where can the piece go?

p2 measured both panel buttons as TOGGLES: the 8-button swaps the colour-8
block between a 6x4 at (12-17, 30-33) and a 4x6 at (18-21, 24-29); the
9-button swaps the checkered 9/4 pad at (8-11, 34-37) with the solid 9 block
at (18-21, 20-23). And with the 9-button pressed the piece walks UP from y40
to y30 instead of stopping at y38 -- recon's "the room is sealed, all nine
positions probed in all four directions" was measured with the checkered pad
still in place, which is this game's wall.

E8   after the 9-button, walk up and dump the board: what is up there.
E9   the reachable set under each of the four button combinations, walked as
     a snake (up/right/down/left, six of each, positions recorded).
E10  is there anything that looks like a goal -- the colour-13 block and the
     colour-11 marker are the two objects no button has touched.
"""
import sys

import numpy as np

import arc_agi

BTN8, BTN9 = (48, 19), (48, 36)


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


def run(presses, walk):
    env = arc.make(envs["dc22"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    for b in presses:
        obs = env.step(A[6], data={"x": b[0], "y": b[1]})
    g = grid_of(obs)
    trail = [piece(g)]
    for v in walk:
        obs = env.step(A[v])
        g2 = grid_of(obs)
        if g2 is None:
            break
        g = g2
        trail.append(piece(g))
        if obs.levels_completed or str(obs.state) != "GameState.NOT_FINISHED":
            break
    return g, trail, obs


print("== E8: after the 9-button, walk up ==")
g, trail, obs = run([BTN9], [1] * 6)
print(f"  trail: {trail}  lvl={obs.levels_completed}")
show(g, "board after")
sys.stdout.flush()

print("\n== E9: reachable set per button combination ==")
SNAKE = [1] * 6 + [4] * 6 + [2] * 6 + [3] * 6 + [1] * 6
for presses, label in (([], "none (control)"), ([BTN9], "9"), ([BTN8], "8"),
                       ([BTN8, BTN9], "8 then 9")):
    g, trail, obs = run(presses, SNAKE)
    seen = sorted({t for t in trail if t})
    print(f"  {label:14s}: {len(seen):2d} distinct positions "
          f"x{min(p[0] for p in seen)}-{max(p[0] for p in seen)} "
          f"y{min(p[1] for p in seen)}-{max(p[1] for p in seen)} "
          f"lvl={obs.levels_completed} st={str(obs.state).split('.')[-1]}")
    sys.stdout.flush()

print("\n== E10: the objects no button touches ==")
env = arc.make(envs["dc22"].game_id)
obs = env.reset()
g = grid_of(obs)
for col in (11, 13, 2):
    ys, xs = np.nonzero(g == col)
    if len(ys):
        print(f"  colour {col:2d}: x{int(xs.min())}-{int(xs.max())} "
              f"y{int(ys.min())}-{int(ys.max())} cells={len(ys)}")
