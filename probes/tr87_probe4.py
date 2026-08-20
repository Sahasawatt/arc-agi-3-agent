"""tr87: exact cell diffs from ACTION1/ACTION2, and whether the edited region
tracks the piece's current column or is fixed/global. Also: period of the
ACTION1-alone cycle, and whether moving to a different crate column changes
which cells respond.
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


def diff(a, b):
    ys, xs = np.nonzero(a != b)
    return sorted((int(x), int(y), int(a[y, x]), int(b[y, x])) for x, y in zip(xs, ys))


print("== ACTION1 pressed 8x alone from reset: period? exact diff each time ==")
obs = env.reset()
g = grid_of(obs)
for i in range(8):
    prev = g.copy()
    obs = env.step(A[1])
    g = grid_of(obs)
    d = diff(prev, g)
    xs = [c[0] for c in d if c[1] != 63]  # exclude budget-bar row
    print(f"  press{i}: n={len(d)} x-range={min(xs) if xs else None}-{max(xs) if xs else None} "
          f"lvl={obs.levels_completed}")
same_as_reset = np.array_equal(g, grid_of(env.reset()))
print("  (env re-reset for compare only, ignore its own side effect)")

print("\n== move to x22 (1x ACTION4) then ACTION1 x2: does a DIFFERENT region change? ==")
obs = env.reset()
obs = env.step(A[4])
g = grid_of(obs)
print("piece now at x:", np.nonzero(grid_of(obs) == 0)[1].min())
for i in range(2):
    prev = g.copy()
    obs = env.step(A[1])
    g = grid_of(obs)
    d = diff(prev, g)
    xs = [c[0] for c in d if c[1] != 63]
    print(f"  press{i}: n={len(d)} x-range={min(xs) if xs else None}-{max(xs) if xs else None}")

print("\n== reset baseline, ACTION1 once, exact (x,y,old,new) diff list (bar excluded) ==")
obs = env.reset()
g0 = grid_of(obs)
obs = env.step(A[1])
g1 = grid_of(obs)
d = diff(g0, g1)
for x, y, a, b in d:
    if y == 63:
        continue
    print(f"  ({x},{y}) {a}->{b}")

sys.stdout.flush()
