"""tr87: dump the room's full 7-state cycle at station 1, look for a state
that is monochrome (colour-5 count == 0) inside the crate footprint --
would be the natural 'solved/cleared' reading. Then check station 2 (no
detected crate) and station 4 (the 5x3 crate) for the same period and
whether THEY have a monochrome state too.
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def dump(g, x0, x1, y0=51, y1=58):
    sub = g[y0:y1, x0:x1]
    for row in sub:
        print("    " + "".join(str(int(v)) for v in row))
    vals, cnt = np.unique(sub, return_counts=True)
    print("    census:", dict(zip(vals.tolist(), cnt.tolist())))


print("== station 1 (x15-19), full crate footprint x16-19 -- 7 states ==")
obs = env.reset()
g = grid_of(obs)
print(" state0 (reset):")
dump(g, 15, 20)
for i in range(1, 8):
    obs = env.step(A[1])
    g = grid_of(obs)
    print(f" state{i}:")
    dump(g, 15, 20)
    if obs.levels_completed:
        print("  LEVEL UP")
        break

print("\n== station 4 (x36-40, the 5x3 crate) -- move there then cycle 7 ==")
obs = env.reset()
for _ in range(3):
    obs = env.step(A[4])  # 15->22->29->36
g = grid_of(obs)
print(" state0:")
dump(g, 36, 41)
for i in range(1, 8):
    obs = env.step(A[1])
    g = grid_of(obs)
    print(f" state{i}:")
    dump(g, 36, 41)
    if obs.levels_completed:
        print("  LEVEL UP")
        break

sys.stdout.flush()
