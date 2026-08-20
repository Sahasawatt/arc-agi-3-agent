"""sp80 probe 2: ACTION5 semantics, ACTION6 targets, wall map, castle contact.

    ./.venv/Scripts/python.exe sp80_p2.py

Budget is 30 actions/life; every test gets its own reset (level reset, >=1 action
taken since the last transition -- the env has acted before every reset here).
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


def blk(g):
    """bbox of the colour-9 block, or None."""
    if g is None:
        return None
    ys, xs = np.nonzero(g == 9)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()))


def census(g):
    if g is None:
        return {}
    vals, cnt = np.unique(g, return_counts=True)
    return dict(zip(vals.tolist(), cnt.tolist()))


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}

print("== A: is the ACTION5 death counter consecutive or per-life total? ==")
# seq 5,5,5,5,1,5 -- if consecutive, the 1 resets it and press 6 survives
obs = env.reset()
for i, a in enumerate([5, 5, 5, 5, 1, 5]):
    obs = env.step(A[a])
    print(f"  press {i} (action {a}): state={obs.state}")
    if obs.state.name != "NOT_FINISHED":
        break

print("\n== A2: 5x5 with the block moved first (position-dependent?) ==")
obs = env.reset()
env.step(A[3]); env.step(A[3])
dead = False
for i in range(5):
    obs = env.step(A[5])
    if obs.state.name != "NOT_FINISHED":
        print(f"  died at press {i} (state={obs.state})")
        dead = True
        break
if not dead:
    print("  survived 5 presses after moving")

print("\n== B: does ACTION5 modify the NEXT action? [5,d] vs [d] displacement ==")
for d in [1, 2, 3, 4]:
    obs = env.reset()
    b0 = blk(grid(obs))
    obs = env.step(A[d])
    b_plain = blk(grid(obs))
    obs = env.reset()
    env.step(A[5])
    obs = env.step(A[d])
    b_mod = blk(grid(obs))
    print(f"  d={d}: start={b0} plain={b_plain} after5={b_mod} same={b_plain == b_mod}")

print("\n== C: ACTION6 clicks on each object ==")
targets = [("4-block", 38, 2), ("6-block", 38, 5), ("tower L1", 18, 53),
           ("gap L1", 21, 53), ("base L1", 21, 57), ("bottom band", 32, 61),
           ("bar", 10, 0), ("tower R1", 42, 53), ("gap R2", 45, 53)]
for name, x, y in targets:
    obs = env.reset()
    prev = grid(obs)
    obs = env.step(A[6], data={"x": x, "y": y})
    cur = grid(obs)
    if prev is None or cur is None:
        print(f"  {name} ({x},{y}): frame empty")
        continue
    ys, xs = np.nonzero(prev != cur)
    keep = [(int(xx), int(yy)) for yy, xx in zip(ys, xs) if yy != 0]
    print(f"  {name} ({x},{y}): {len(xs)} cells changed, non-bar: {keep[:8]}  state={obs.state}")

print("\n== D: wall map -- how far does the block go each way? ==")
for d, name in [(1, "up"), (2, "down"), (3, "left"), (4, "right")]:
    obs = env.reset()
    last = blk(grid(obs))
    moves = 0
    for i in range(12):
        obs = env.step(A[d])
        g = grid(obs)
        if obs.state.name != "NOT_FINISHED":
            print(f"  {name}: terminal {obs.state} after {i+1} presses at {last}")
            break
        b = blk(g)
        if b == last:
            print(f"  {name}: stops at {b} after {moves} moves ({i+1} presses)")
            break
        last = b
        moves += 1
    else:
        print(f"  {name}: still moving at {last} after 12 presses")

print("\n== E: park ON the castle top and on the gap column -- consumption? ==")
# castle L at x16-27 y52-59, gap x20-23 y52-55. floor for block = y44-47.
# park block at y44-47 with x s.t. it spans the gap: default x12-31 already spans.
obs = env.reset()
c0 = census(grid(obs))
for i in range(7):
    obs = env.step(A[2])
b = blk(grid(obs))
c1 = census(grid(obs))
print(f"  parked at {b} state={obs.state}")
print(f"  census delta: {[(k, c1.get(k, 0) - c0.get(k, 0)) for k in sorted(set(c0) | set(c1)) if c1.get(k, 0) != c0.get(k, 0)]}")
# sit there a few actions (refused downs) and watch
for i in range(3):
    obs = env.step(A[2])
c2 = census(grid(obs))
print(f"  after 3 more downs: state={obs.state} census delta vs parked: "
      f"{[(k, c2.get(k, 0) - c1.get(k, 0)) for k in sorted(set(c1) | set(c2)) if c2.get(k, 0) != c1.get(k, 0)]}")
sys.stdout.flush()
