"""sp80 probe 1: what do ACTION5 and ACTION6 do, what kills the run, bar budget.

    ./.venv/Scripts/python.exe sp80_p1.py

Tests, each from a fresh reset (level reset semantics: >=1 action taken before):
  A. ACTION5 once, then ACTION1 x4 -- full-board diff per step (autonomous movers?)
  B. ACTION5 x5 -- confirm the GAME_OVER, print state per press (guarded reads)
  C. ACTION6 (complex) at (32,32) and at (20,17) -- diff
  D. alternate ACTION3/4 until GAME_OVER -- bar cells vs actions = the budget
"""

import sys

import numpy as np

import arc_agi


def grid(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def diff(a, b, label):
    if a is None or b is None:
        print(f"  {label}: frame empty (a={a is not None} b={b is not None})")
        return
    ys, xs = np.nonzero(a != b)
    if len(xs) == 0:
        print(f"  {label}: no change")
        return
    print(f"  {label}: {len(xs)} cells x[{xs.min()}-{xs.max()}] y[{ys.min()}-{ys.max()}]")
    # group by (old,new) colour pair
    pairs = {}
    for y, x in zip(ys.tolist(), xs.tolist()):
        k = (int(a[y, x]), int(b[y, x]))
        pairs.setdefault(k, []).append((x, y))
    for k, cells in sorted(pairs.items()):
        sample = cells[:6]
        print(f"    {k[0]}->{k[1]}: {len(cells)} cells  e.g. {sample}")


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
for a in env.action_space:
    print(f"action {a.value}: complex={a.is_complex()}")

print("\n== A: ACTION5 once, then ACTION1 x4 ==")
obs = env.reset()
prev = grid(obs)
obs = env.step(A[5])
cur = grid(obs)
diff(prev, cur, "after 5")
print(f"    state={obs.state} lvl={obs.levels_completed}")
prev = cur
for i in range(4):
    obs = env.step(A[1])
    cur = grid(obs)
    diff(prev, cur, f"after 1 (#{i})")
    print(f"    state={obs.state}")
    prev = cur

print("\n== B: ACTION5 x5 from reset ==")
obs = env.reset()
prev = grid(obs)
for i in range(5):
    obs = env.step(A[5])
    cur = grid(obs)
    diff(prev, cur, f"press {i}")
    print(f"    state={obs.state} lvl={obs.levels_completed}")
    prev = cur
    if obs.state.name == "GAME_OVER":
        print("    GAME_OVER hit at press", i)
        break

print("\n== C: ACTION6 ==")
obs = env.reset()
prev = grid(obs)
obs = env.step(A[6], data={"x": 32, "y": 32})
cur = grid(obs)
diff(prev, cur, "6 at (32,32)")
print(f"    state={obs.state}")
prev = cur
obs = env.step(A[6], data={"x": 20, "y": 17})
cur = grid(obs)
diff(prev, cur, "6 at (20,17) on the 9-block")
print(f"    state={obs.state}")

print("\n== D: bar budget -- alternate 3/4 until GAME_OVER (cap 200) ==")
obs = env.reset()
g = grid(obs)
bar0 = int((g[0] == 14).sum()) if g is not None else -1
print(f"  bar at reset: {bar0} cells of colour 14")
n = 0
while n < 200:
    obs = env.step(A[3 if n % 2 == 0 else 4])
    n += 1
    g = grid(obs)
    bar = int((g[0] == 14).sum()) if g is not None else -1
    if n <= 3 or n % 10 == 0 or (obs.state.name != "NOT_FINISHED"):
        print(f"  action {n}: bar={bar} state={obs.state}")
    if obs.state.name != "NOT_FINISHED":
        break
print(f"  total actions to terminal: {n}")
sys.stdout.flush()
