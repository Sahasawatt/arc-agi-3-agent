"""tr87: (a) own-cycle period for stations 1 (x22) and 2 (x29) -- do they
close a loop like station 0 does, and at what period? (b) does aligning the
three family-0 stations (0,3,4 -- which we showed share one 7-symbol deck)
to a COMMON symbol trigger level completion or ANY change outside the room
(full-frame diff, not just the room slice)?
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


def window(g, x0):
    return g[51:58, x0:x0 + 5].copy()


def whash(w):
    return hashlib.md5(w.tobytes()).hexdigest()[:10]


for st_idx, x0 in [(1, 22), (2, 29)]:
    print(f"== station{st_idx} (x{x0}) own-cycle period, up to 12 presses ==")
    obs = env.reset()
    for _ in range(st_idx):
        obs = env.step(A[4])
    g = grid_of(obs)
    seen = {whash(window(g, x0)): 0}
    period = None
    for i in range(1, 13):
        obs = env.step(A[1])
        g = grid_of(obs)
        hh = whash(window(g, x0))
        if hh in seen and period is None:
            period = i - seen[hh]
            print(f"  press{i}: repeats press{seen[hh]}  period={period}")
            break
        seen.setdefault(hh, i)
    else:
        print("  no repeat within 12 presses")

print("\n== align stations 0,3,4 (shared 7-deck) to symbol S0, watch full frame ==")
obs = env.reset()
g0 = grid_of(obs)
# station0 already at S0 (reset). station3 at S4 -> needs 3x ACTION1 to reach S0 (4+3=7).
for _ in range(3):
    obs = env.step(A[4])  # -> station3 (x36)
for _ in range(3):
    obs = env.step(A[1])  # 4 -> 0 (mod 7, forward 3)
# station4 at S2 -> needs 5x ACTION1 to reach S0 (2+5=7), or move there first
obs = env.step(A[4])  # station3 -> station4 (x43)
for _ in range(5):
    obs = env.step(A[1])
g_after = grid_of(obs)
print("levels_completed:", obs.levels_completed, "state:", str(obs.state).split(".")[-1])
d = np.nonzero(g0 != g_after)
ys, xs = d
outside_room = [(int(x), int(y)) for x, y in zip(xs, ys) if not (51 <= y <= 57) and y != 63]
print("cells changed outside room+bar:", len(outside_room), outside_room[:20])
print("total cells changed:", len(xs))

sys.stdout.flush()
