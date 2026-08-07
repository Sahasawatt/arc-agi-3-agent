"""sp80 probe 17: what does a GAME_OVER cost, with NO reset() to rescue it?

    ./.venv/Scripts/python.exe sp80_p17.py

The rung will deliberately spend lives (5-shot magazine, 30-action bar). Whether
that is affordable depends entirely on what the ENGINE does after GAME_OVER when
the caller just keeps stepping -- which every probe so far hid behind a reset().
"""

import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def blk(g):
    if g is None:
        return None
    ys, xs = np.nonzero(g == 9)
    return (int(xs.min()), int(ys.min()), len(xs)) if len(xs) else None


def bar(g):
    return None if g is None else int((g == 14).sum())


arc = arc_agi.Arcade()
env = arc.make("sp80")
A = {a.value: a for a in env.action_space}

print("== A: die by MAGAZINE (5 fires), then keep stepping, never reset ==")
obs = env.reset()
for i in range(5):
    obs = env.step(A[5])
print(f"  after 5 fires: state={obs.state.name} lvl={obs.levels_completed} "
      f"grid={'None' if grid_of(obs) is None else 'ok'}")
for i in range(8):
    obs = env.step(A[4])
    g = grid_of(obs)
    print(f"  step {i} (right): state={obs.state.name} lvl={obs.levels_completed} "
          f"blk={blk(g)} bar={bar(g)}")
    if obs.state.name == "NOT_FINISHED" and g is not None:
        print("  -> engine came back on its own")
        break

print("\n== B: die by BAR (30 actions), then keep stepping ==")
env2 = arc.make("sp80")
obs = env2.reset()
n = 0
while n < 40 and obs.state.name == "NOT_FINISHED":
    obs = env2.step(A[3 if n % 2 == 0 else 4])
    n += 1
print(f"  died at action {n}: state={obs.state.name}")
for i in range(6):
    obs = env2.step(A[4])
    g = grid_of(obs)
    print(f"  step {i}: state={obs.state.name} lvl={obs.levels_completed} "
          f"blk={blk(g)} bar={bar(g)}")

print("\n== C: does reset() AFTER a GAME_OVER restore level 1 and the start block? ==")
env3 = arc.make("sp80")
obs = env3.reset()
for i in range(5):
    obs = env3.step(A[5])
print(f"  post-magazine: {obs.state.name}")
obs = env3.reset()
g = grid_of(obs)
print(f"  after reset: state={obs.state.name} lvl={obs.levels_completed} "
      f"blk={blk(g)} bar={bar(g)}")

print("\n== D: how many fires can a life afford WITHOUT dying? ==")
env4 = arc.make("sp80")
obs = env4.reset()
for i in range(4):
    obs = env4.step(A[5])
    print(f"  fire {i + 1}: state={obs.state.name} bar={bar(grid_of(obs))}")
print("  4 fires survived:", obs.state.name == "NOT_FINISHED")
# ...and does a level-up refill the magazine?
env5 = arc.make("sp80")
obs = env5.reset()
for a in [4, 4, 4, 5]:
    obs = env5.step(A[a])
print(f"  after winning L1: lvl={obs.levels_completed} state={obs.state.name}")
for i in range(5):
    obs = env5.step(A[5])
    print(f"  L2 fire {i + 1}: state={obs.state.name} lvl={obs.levels_completed}")
    if obs.state.name != "NOT_FINISHED":
        break
sys.stdout.flush()
