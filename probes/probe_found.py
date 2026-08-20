"""Foundation probe for ANY game: replay determinism, step rate, census, board dump.

    ./.venv/Scripts/python.exe probe_found.py <game> [n]

The three questions every new game has to answer before anything is built on it,
generalised out of `probe_re86.py` / `probe_sp80.py` (both of which hardcode their
game). Copying that file per game is how a fix to it stops propagating.

  1. does reset() + a fixed action sequence reproduce the SAME frames in-process?
     (re86 4,307 steps/s, sp80 80,469 -- an offline search is only affordable here)
  2. what is on the board at reset, and where?
  3. does a fresh env in the same process start identically? (cn04 does not)
"""

import hashlib
import sys
import time

import numpy as np

import arc_agi

CHARS = "0123456789abcdef"
SEQ = [1, 4, 2, 3, 4, 4, 2, 2, 1, 3, 4, 1, 2, 4, 3, 3, 1, 2, 4, 2]


def grid_of(obs):
    """Last layer as a 2-D array, or None -- the engine hands back empty frames."""
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def h(g):
    return "empty" if g is None else hashlib.md5(g.tobytes()).hexdigest()[:12]


def replay(env, A, acts):
    obs = env.reset()
    out = [h(grid_of(obs))]
    for a in acts:
        if a not in A:
            continue
        obs = env.step(A[a])
        out.append(h(grid_of(obs)))
        if obs is None or str(obs.state) != "GameState.NOT_FINISHED":
            break
    return out


game = sys.argv[1] if len(sys.argv) > 1 else "ls20"
arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
info = envs[game]
env = arc.make(info.game_id)
A = {a.value: a for a in env.action_space}
print(f"game: {game}")
print("actions:", sorted(A), "complex:",
      sorted(a.value for a in env.action_space if a.is_complex()))
print("baseline_actions:", getattr(info, "baseline_actions", "ABSENT"))

obs = env.reset()
f = np.array(obs.frame)
print("frame shape:", f.shape)
g = f[-1]
vals, cnt = np.unique(g, return_counts=True)
print("colour census:", dict(zip(vals.tolist(), cnt.tolist())))
if f.shape[0] > 1:
    for i in range(f.shape[0]):
        print(f"  layer {i}: colours {sorted(set(f[i].ravel().tolist()))}")

bg = int(np.bincount(g.ravel()).argmax())
print("background colour:", bg)
print(f"board dump (hex chars, bg='{CHARS[bg & 0xF]}'):")
for y in range(g.shape[0]):
    print(f"  y={y:2d} " + "".join(CHARS[v & 0xF] for v in g[y]))

r1 = replay(env, A, SEQ)
r2 = replay(env, A, SEQ)
print("replay identical:", r1 == r2, f"({len(r1)} frames)")
if r1 != r2:
    for i, (a, b) in enumerate(zip(r1, r2)):
        if a != b:
            print("  first divergence at step", i, a, b)
            break

t0 = time.time()
env.reset()
n, dirs = 300, [a for a in sorted(A) if a in (1, 2, 3, 4)] or sorted(A)
for i in range(n):
    env.step(A[dirs[i % len(dirs)]])
dt = time.time() - t0
print(f"step rate: {n / dt:.0f}/s  ({dt:.2f}s for {n})")

env2 = arc.make(info.game_id)
print("second env same start:", h(grid_of(env2.reset())) == r1[0])
sys.stdout.flush()
