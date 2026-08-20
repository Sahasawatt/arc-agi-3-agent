"""sp80 foundation probe: determinism-under-replay, step rate, full board census.

    ./.venv/Scripts/python.exe probe_sp80.py

Same three questions as probe_re86.py, for sp80:
  1. does reset() + a fixed action sequence reproduce the SAME frame in-process?
  2. how many steps/sec (offline-probe budget)?
  3. what is on the board at reset (census, non-background rows, layers)?
"""

import hashlib
import sys
import time

import numpy as np

import arc_agi

CHARS = "0123456789abcdef"
SEQ = [1, 4, 2, 3, 4, 4, 2, 2, 1, 3, 4, 1, 2, 4, 3, 3, 1, 2, 4, 2]


def grid(obs):
    """Last layer as a 2-D array, or None when the engine hands back an empty frame."""
    if obs is None:
        return None
    f = np.array(obs.frame)
    if f.ndim < 2 or f.size == 0:
        return None
    return f[-1]


def h(g):
    return "empty" if g is None else hashlib.md5(g.tobytes()).hexdigest()[:12]


def run(env, acts):
    obs = env.reset()
    out = [h(grid(obs))]
    for a in acts:
        obs = env.step(A[a])
        out.append(h(grid(obs)))
    return out, obs


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}
print("actions:", sorted(A))

obs = env.reset()
f = np.array(obs.frame)
print("frame shape:", f.shape)
g = f[-1]
vals, cnt = np.unique(g, return_counts=True)
print("colour census:", dict(zip(vals.tolist(), cnt.tolist())))
if f.shape[0] > 1:
    for i in range(f.shape[0]):
        li = np.array(obs.frame)[i]
        print(f"  layer {i}: colours {sorted(set(li.ravel().tolist()))}")

# full board dump, one char per cell
bg = int(np.bincount(g.ravel()).argmax())
print("background colour:", bg)
print("board dump (hex chars, bg='%s'):" % CHARS[bg & 0xF])
for y in range(g.shape[0]):
    print(f"  y={y:2d} " + "".join(CHARS[v & 0xF] for v in g[y]))

# 1. determinism under replay-from-reset
r1, _ = run(env, SEQ)
r2, o2 = run(env, SEQ)
print("replay identical:", r1 == r2)
if r1 != r2:
    for i, (a, b) in enumerate(zip(r1, r2)):
        if a != b:
            print("  first divergence at step", i, a, b)
            break

# 2. step rate
t0 = time.time()
env.reset()
n = 300
for i in range(n):
    env.step(A[(i % 4) + 1])
dt = time.time() - t0
print(f"step rate: {n / dt:.0f}/s  ({dt:.2f}s for {n})")

# 3. does a fresh env in the SAME process start identically?
env2 = arc.make("sp80")
print("second env same start:", h(grid(env2.reset())) == r1[0])
sys.stdout.flush()
