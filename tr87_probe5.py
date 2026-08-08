"""tr87: period of the ACTION1 cycle at one station, and whether ACTION2 is its
exact inverse (not just 4-vs-4 net-zero, verified step by step). Also whether
any single-column state ever matches one of the six top reference patterns.
"""
import sys
import hashlib
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


def room_hash(g):
    return hashlib.md5(g[51:58, 14:52].tobytes()).hexdigest()[:10]


print("== ACTION1 x30 at station 1 (x15), room hash each press, find period ==")
obs = env.reset()
g = grid_of(obs)
h0 = room_hash(g)
print(f"  reset: {h0}")
seen = {h0: 0}
period = None
for i in range(1, 31):
    obs = env.step(A[1])
    g = grid_of(obs)
    hh = room_hash(g)
    if hh in seen and period is None:
        period = i - seen[hh]
        print(f"  press{i}: {hh}  <-- repeats press{seen[hh]}, period={period}")
    else:
        print(f"  press{i}: {hh}")
    seen.setdefault(hh, i)
    if obs.levels_completed > 0:
        print("  LEVEL UP at press", i)
        break

print("\n== verify ACTION2 undoes ACTION1 step by step (not just net over 4) ==")
obs = env.reset()
g = grid_of(obs)
hashes = [room_hash(g)]
for i in range(5):
    obs = env.step(A[1])
    hashes.append(room_hash(grid_of(obs)))
print("forward hashes:", hashes)
back = [hashes[-1]]
for i in range(5):
    obs = env.step(A[2])
    back.append(room_hash(grid_of(obs)))
print("backward hashes:", back)
print("backward == reversed(forward)?", back == list(reversed(hashes)))

sys.stdout.flush()
