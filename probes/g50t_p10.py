"""g50t probe 10: is there state the FRAME does not show?

    ./.venv/Scripts/python.exe g50t_p10.py

The BFS keys on (visible board, actions taken) and reports the level unwinnable
(`g50t-p5.txt`) against a human baseline of 78 on a 128-action clock. Its harness
is verified (`bfs-control.txt`) and its deepcopy is a true fork
(`deepcopy-check.txt`), so if the report is wrong the key is incomplete -- exactly
the sp80 null, where the missing term was the magazine.

The test for an incomplete key needs no theory about WHAT the hidden term is:
walk two different routes to the same board at the same depth, apply the same
continuation to both, and compare. Identical frames all the way = the key is
complete over these routes. Divergence = hidden state, and the search is void.

Positive control in the same run: two routes that end at DIFFERENT boards, whose
continuations must therefore differ, so a comparison that cannot see a difference
is visible as such.
"""

import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def run(env, A, seq):
    obs = env.reset()
    for a in seq:
        obs = env.step(A[a])
        if obs is None or not str(obs.state).endswith("NOT_FINISHED"):
            return obs, grid_of(obs), False
    return obs, grid_of(obs), True


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
A = None


def fresh():
    global A
    env = arc.make(envs["g50t"].game_id)
    A = {a.value: a for a in env.action_space}
    return env


# Two 20-action routes that both end with the piece back at (14, 8):
#   R1 paces right/left along the top row
#   R2 paces down/up along the left column
R1 = [4, 3] * 10
R2 = [2, 1] * 10
# a route that ends somewhere else, for the control
R3 = [4, 3] * 9 + [4, 4]

CONT = [4, 4, 4, 4] + [3, 3, 3, 3] + [2, 2, 2, 2, 2]

print("== do two routes to the same board share a future? ==")
results = {}
for name, seq in (("R1 right/left", R1), ("R2 down/up", R2), ("R3 control", R3)):
    env = fresh()
    obs, g, alive = run(env, A, seq)
    if not alive:
        print(f"  {name}: died during the route")
        continue
    frames = [g.copy()]
    for a in CONT:
        obs = env.step(A[a])
        cg = grid_of(obs)
        frames.append(None if cg is None else cg.copy())
        if obs is None or not str(obs.state).endswith("NOT_FINISHED"):
            break
    results[name] = frames
    print(f"  {name}: route ok, {len(frames)} frames recorded, "
          f"final lvl={obs.levels_completed}")


def cmp(a, b, label):
    n = min(len(a), len(b))
    diffs = []
    for i in range(n):
        fa, fb = a[i], b[i]
        if fa is None or fb is None:
            diffs.append((i, "empty"))
            continue
        # ignore the clock row: both routes are the same length, so it matches
        # anyway, but this keeps the comparison about the play area
        if not np.array_equal(fa[:63], fb[:63]):
            diffs.append((i, int((fa[:63] != fb[:63]).sum())))
    print(f"  {label}: {len(diffs)} of {n} frames differ" +
          (f"  first at step {diffs[0][0]} ({diffs[0][1]} cells)" if diffs else ""))
    return diffs


print()
if "R1 right/left" in results and "R2 down/up" in results:
    same = cmp(results["R1 right/left"], results["R2 down/up"], "R1 vs R2 (same board)")
if "R1 right/left" in results and "R3 control" in results:
    ctrl = cmp(results["R1 right/left"], results["R3 control"], "R1 vs R3 (CONTROL)")
    print("  control ok: the comparison CAN see a difference"
          if ctrl else "  CONTROL FAILED: the comparison is blind")
print("\nVERDICT:", "no hidden state along these routes -- the key is complete"
      if "same" in dir() and not same else
      "HIDDEN STATE: identical boards have different futures")
sys.stdout.flush()
