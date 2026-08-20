"""Is `copy.deepcopy(env)` really a fork? The control that was never run.

    ./.venv/Scripts/python.exe deepcopy_check.py [game ...]

Both BFS harnesses in this repo (`sp80_p11.py`, `g50t_p3.py`, `g50t_p5.py`) treat
a deepcopy as an independent branch. The control that was run for sp80
(`results/sp80-p10.txt`) asked two questions -- "does the copy see the same next
frame" and "does it advance independently" -- and BOTH are true even when the
copy shares the parent's game state, because the copy's later frame differs from
the parent's earlier one either way.

The question that discriminates is the third one: after the COPY steps, has the
PARENT moved? If it has, every BFS built on this is a random walk wearing a
tree's clothes, and every "no win exists" it produced is worthless.

Positive control in the same run: a case that MUST answer "the parent moved" --
stepping the parent itself -- so a check that cannot detect movement at all is
visible as such.
"""

import copy
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def read(env):
    """Read the parent's CURRENT frame without stepping it. `reset()` would step
    the world, so the only honest read is whatever the env exposes."""
    for attr in ("frame", "_frame", "last_obs", "_obs", "observation"):
        v = getattr(env, attr, None)
        if v is not None:
            try:
                f = np.array(v.frame if hasattr(v, "frame") else v)
                if f.ndim >= 2 and f.size:
                    return f[-1]
            except Exception:
                continue
    return None


games = sys.argv[1:] or ["g50t", "sp80"]
arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

for name in games:
    print(f"\n===== {name} =====")
    env = arc.make(envs[name].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    obs = env.step(A[4])
    base = grid_of(obs)
    print("  parent frame after one step: piece-bearing:", base is not None)

    twin = copy.deepcopy(env)
    # step the TWIN several times, never the parent
    tw = None
    for _ in range(3):
        tw = twin.step(A[2])
    twin_grid = grid_of(tw)

    # THE question: read the parent's own view without advancing it
    par_view = read(env)
    if par_view is None:
        print("  (no readable frame attribute on the env -- falling back to a step probe)")
    else:
        print("  parent's own frame unchanged after the twin's 3 steps:",
              np.array_equal(par_view, base))
        print("  parent view == twin view (would mean SHARED state):",
              np.array_equal(par_view, twin_grid))

    # Step probe: the parent takes ONE action. If state is shared, the parent is
    # now wherever the twin left it and its next frame follows from THERE.
    p1 = grid_of(env.step(A[4]))
    # what the parent's next frame SHOULD be, computed on a fresh line
    fresh = arc.make(envs[name].game_id)
    fresh.reset()
    fresh.step(A[4])
    expected = grid_of(fresh.step(A[4]))
    same = p1 is not None and expected is not None and np.array_equal(p1[:60], expected[:60])
    print(f"  parent's next frame matches an untouched replica: {same}"
          f"   <- False means the twin's steps LEAKED into the parent")

    # positive control: this comparison must be able to say False
    other = grid_of(fresh.step(A[2]))
    print("  control (a genuinely different frame compares False):",
          not np.array_equal(expected[:60], other[:60]))
sys.stdout.flush()
