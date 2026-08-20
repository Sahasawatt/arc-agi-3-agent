"""sp80 probe 10: level-2 budget, and can the env be deepcopied for BFS speed?

    ./.venv/Scripts/python.exe sp80_p10.py
"""

import copy
import sys
import time

import numpy as np

import arc_agi

RECIPE1 = [4, 4, 4, 5]


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
obs = env.reset()
obs = env.step(A[1])

print("== A: level-2 budget ==")
obs = env.reset()
for a in RECIPE1:
    obs = env.step(A[a])
g = grid(obs)
print("  L2 clock rows: y0 colours", sorted(set(g[0].tolist())),
      "y63 colours", sorted(set(g[63].tolist())))
bar0 = int((g == 14).sum())
print(f"  colour-14 cells at L2 start: {bar0}")
n = 0
while n < 200:
    obs = env.step(A[3 if n % 2 == 0 else 4])
    n += 1
    if obs.state.name != "NOT_FINISHED":
        break
print(f"  actions to terminal on L2: {n} (state={obs.state.name})")

print("\n== B: deepcopy the env -- legal? faithful? fast? ==")
obs = env.reset()
if obs.levels_completed == 0:
    for a in RECIPE1:
        obs = env.step(A[a])
t0 = time.time()
try:
    env2 = copy.deepcopy(env)
except Exception as e:
    print("  deepcopy FAILED:", type(e).__name__, e)
    sys.exit(0)
dt = time.time() - t0
print(f"  deepcopy ok in {dt * 1000:.1f} ms")
# faithful: same next-state for the same action?
o1 = env.step(A[4])
o2 = env2.step(A[4])
g1, g2 = grid(o1), grid(o2)
same = g1 is not None and g2 is not None and np.array_equal(g1, g2)
print(f"  same next frame after copy: {same}")
# and the copy diverges independently?
o3 = env2.step(A[4])
g3 = grid(o3)
print(f"  copy advanced independently: {not np.array_equal(g1, g3)}")
t0 = time.time()
for _ in range(100):
    e = copy.deepcopy(env)
print(f"  100 deepcopies: {time.time() - t0:.2f}s")
sys.stdout.flush()
