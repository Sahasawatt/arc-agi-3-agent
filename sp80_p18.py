"""sp80 probe 18: does the MAGAZINE death mask a win? And what is the baseline?

    ./.venv/Scripts/python.exe sp80_p18.py

A sweep rung fires at every position it has not tried. If a fire that happens to
land on the winning column while the magazine is empty DIES instead of winning,
that position reads as tested-and-negative and the sweep can miss the answer
forever. That is the difference between needing magazine bookkeeping and not.
"""

import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
info = envs["sp80"]
print("sp80 baseline_actions:", getattr(info, "baseline_actions", "ABSENT"))
for other in ("ls20", "re86", "cn04"):
    print(f"  ({other} baseline for scale:",
          getattr(envs[other], "baseline_actions", "ABSENT"), ")")

env = arc.make(info.game_id)
A = {a.value: a for a in env.action_space}

print("\n== A: 4 dud fires, then the 5th ON the winning column (x-left 24) ==")
obs = env.reset()
# 4 duds at x-left 12 (measured inert), then walk to 24 and fire as shot 5
for i in range(4):
    obs = env.step(A[5])
print(f"  after 4 duds: state={obs.state.name}")
for a in [4, 4, 4]:
    obs = env.step(A[a])
ys, xs = np.nonzero(grid_of(obs) == 9)
print(f"  block at x-left={int(xs.min())} state={obs.state.name}")
obs = env.step(A[5])
print(f"  SHOT 5 on the win column -> state={obs.state.name} lvl={obs.levels_completed}")
print("  VERDICT: magazine death MASKS the win" if obs.levels_completed == 0
      else "  VERDICT: the win BEATS the magazine death")

print("\n== B: control -- the same walk with a fresh magazine wins ==")
env2 = arc.make(info.game_id)
obs = env2.reset()
for a in [4, 4, 4, 5]:
    obs = env2.step(A[a])
print(f"  fresh magazine, same position: state={obs.state.name} lvl={obs.levels_completed}")

print("\n== C: how many fires does one life really allow? (fire only, no moves) ==")
env3 = arc.make(info.game_id)
obs = env3.reset()
n = 0
while obs.state.name == "NOT_FINISHED" and n < 12:
    obs = env3.step(A[5])
    n += 1
print(f"  died on fire #{n} (state={obs.state.name})")

print("\n== D: does a MOVE-only life also cap fires? interleave move+fire ==")
env4 = arc.make(info.game_id)
obs = env4.reset()
fires = 0
acts = 0
while obs.state.name == "NOT_FINISHED" and acts < 40:
    obs = env4.step(A[3])   # left, walls off after 3
    acts += 1
    if obs.state.name != "NOT_FINISHED":
        break
    obs = env4.step(A[5])
    fires += 1
    acts += 1
print(f"  died after {acts} actions with {fires} fires (state={obs.state.name} "
      f"lvl={obs.levels_completed})")
sys.stdout.flush()
