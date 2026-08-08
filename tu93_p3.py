"""tu93 probe 3: replay the verified 18-action solution, dumping piece(9)/
notch(4)/goal(14) positions each step to see how the win triggers relative
to the goal marker, and the final budget-row state."""
import sys
import numpy as np
import arc_agi

SOLUTION = [4, 2, 2, 4, 1, 4, 2, 2, 3, 3, 2, 4, 4, 2, 4, 1, 4, 2]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def cells(g, color):
    ys, xs = np.nonzero(g == color)
    return sorted(zip(ys.tolist(), xs.tolist()))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tu93"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = grid_of(obs)
print(f"reset: piece9={cells(g,9)} notch4={cells(g,4)} goal14_n={len(cells(g,14))}")
budget_before = int(np.count_nonzero(g[63] == 6))
print(f"budget row6 cells at reset: {budget_before}/64")

for i, a in enumerate(SOLUTION):
    obs = env.step(A[a])
    g = grid_of(obs)
    if g is None:
        print(f"  {i}: empty frame, lvl={obs.levels_completed if obs else None}")
        break
    c9, c4, c14 = cells(g, 9), cells(g, 4), cells(g, 14)
    budget_now = int(np.count_nonzero(g[63] == 6))
    print(f"  {i}: act{a} piece9={c9} notch4={c4} goal14_n={len(c14)} "
          f"budget={budget_now}/64 lvl={obs.levels_completed}")
sys.stdout.flush()
