"""tr87: two untested hypotheses in one life each.

(A) Does the dial state at a station PERSIST once the clamp leaves it? The
room is one continuous strip (not occluded by the clamp, which sits at
y48-49/y59-60, never y51-57) so this is readable directly without even
walking back -- read station0's window right after moving away.

(B) Does merely VISITING all five stations (no dial presses at all) trip
levels_completed?
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}
STATIONS = [15, 22, 29, 36, 43]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def window(g, x0):
    return g[51:58, x0:x0 + 5].copy()


print("== (A) persistence: station0 to phase3, move away twice, re-read WITHOUT returning ==")
obs = env.reset()
g = grid_of(obs)
for _ in range(3):
    obs = env.step(A[1])
    g = grid_of(obs)
target = window(g, 15).copy()
print("station0 window right after 3x ACTION1 (target phase3):")
print(target.tolist())

obs = env.step(A[4])  # -> station1
g = grid_of(obs)
away1 = window(g, 15).copy()
print("station0 window read from station1 (no return):", "MATCH" if np.array_equal(away1, target) else "DIFFERENT")

obs = env.step(A[4])  # -> station2
g = grid_of(obs)
away2 = window(g, 15).copy()
print("station0 window read from station2 (no return):", "MATCH" if np.array_equal(away2, target) else "DIFFERENT")

obs = env.step(A[3])
obs = env.step(A[3])  # back to station0
g = grid_of(obs)
back = window(g, 15).copy()
print("station0 window after walking back to it:", "MATCH" if np.array_equal(back, target) else "DIFFERENT")
print("levels_completed so far:", obs.levels_completed)

print("\n== (B) visit all 5 stations, zero dial presses -- win at any point? ==")
obs = env.reset()
print(f"  reset: piece x={np.nonzero(grid_of(obs) == 0)[1].min()} lvl={obs.levels_completed}")
for i in range(5):
    obs = env.step(A[4])
    x = np.nonzero(grid_of(obs) == 0)[1].min()
    print(f"  after ACTION4 #{i+1}: piece x={x} lvl={obs.levels_completed} "
          f"state={str(obs.state).split('.')[-1]}")
    if obs.levels_completed:
        print("  LEVEL UP")
        break

sys.stdout.flush()
