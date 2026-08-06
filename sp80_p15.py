"""sp80 probe 15: is the L2 win clock-gated? Fire from candidate positions at
every affordable clock value.

    ./.venv/Scripts/python.exe sp80_p15.py

Candidates: stack-aligned columns for both bodies (the L1 rule analogues) at
the floor row and the ceiling row. Delay = up/down (or left/right) wait pairs
inserted before the fire; the 45-action budget caps the reachable clock range.
"""

import sys

import numpy as np

import arc_agi

RECIPE1 = [4, 4, 4, 5]
TAKE_B2 = [1, 1, 1, 5]


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

# (label, setup actions after L2 entry, body, position route, wait axis)
# 80-body candidates: x-left 28 (stack cols 40-43 at offset +12) and 40 (cover).
# b2 candidates: x-left 40 (cover) and 28 (offset +12).
CASES = [
    ("80 at (28,44) floor", [], [4, 4] + [2, 2], "lr"),
    ("80 at (28,16) ceiling", [], [4, 4] + [1, 1, 1, 1, 1], "lr"),
    ("80 at (40,44) floor", [], [4] * 5 + [2, 2], "lr"),
    ("b2 at (40,44) floor", TAKE_B2, [4, 4, 4] + [2] * 5, "lr"),
    ("b2 at (28,48) floor", TAKE_B2, [2] * 6, "lr"),
    ("b2 at (40,16) ceiling", TAKE_B2, [4, 4, 4] + [1, 1], "lr"),
]

wins = []
for label, setup, route, wax in CASES:
    base_len = len(setup) + len(route)
    for delay in range(0, 40 - base_len, 1):
        obs = env.reset()
        if obs.levels_completed == 0:
            for a in RECIPE1:
                obs = env.step(A[a])
        ok = True
        for a in setup + route:
            obs = env.step(A[a])
            if obs.state.name != "NOT_FINISHED":
                ok = False
                break
        if not ok:
            continue
        # burn `delay` actions in place with an alternating blocked-or-paired axis
        w = [3, 4] if wax == "lr" else [1, 2]
        dead = False
        for i in range(delay):
            obs = env.step(A[w[i % 2]])
            if obs.state.name != "NOT_FINISHED":
                dead = True
                break
        if dead:
            continue
        obs = env.step(A[5])
        if obs.levels_completed > 1 or obs.state.name == "WIN":
            wins.append((label, delay, obs.state.name, obs.levels_completed))
            print(f"  WIN: {label} delay={delay}")
        elif obs.state.name != "NOT_FINISHED":
            pass
    print(f"  done: {label}")
    sys.stdout.flush()

print(f"clock-gate wins: {wins if wins else 'NONE'}")
sys.stdout.flush()
