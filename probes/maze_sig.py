"""Which of the seventeen playable games show tu93's notched-piece maze shape?

    ./.venv/Scripts/python.exe maze_sig.py

Same discipline as sp80_sig.py/haul_sig.py: print the candidate feature for
every game's reset frame and CHOOSE the predicate from the table, rather than
proposing one and defending it afterwards.

The shape: a small "notched" solid block -- one body colour filling 8 of 9
cells of a 3x3 window, the ninth cell a second colour -- which is how tu93's
heading-marked piece renders (`results/tu93-p1.txt`).
"""

import sys

import numpy as np

import arc_agi
from compete import PLAYABLE


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def notched(g, exclude):
    """Every solid 3x3 window with exactly two colours, 8 cells of one and 1
    of the other, neither in `exclude` -> [(x0, y0, body, notch)]."""
    out = []
    H, W = g.shape
    for y0 in range(H - 2):
        for x0 in range(W - 2):
            win = g[y0:y0 + 3, x0:x0 + 3]
            vals, counts = np.unique(win, return_counts=True)
            if len(vals) != 2 or 8 not in counts.tolist():
                continue
            counts_l = counts.tolist()
            body = int(vals[counts_l.index(8)])
            notch = int(vals[counts_l.index(1)])
            if body in exclude or notch in exclude:
                continue
            out.append((x0, y0, body, notch))
    return out


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
print("game  acts        bg  n_notched  first3")
rows = {}
for name in PLAYABLE:
    try:
        env = arc.make(envs[name].game_id)
    except Exception as e:
        print(f"{name}  MAKE FAILED {type(e).__name__}")
        continue
    obs = env.reset()
    g = grid_of(obs)
    if g is None:
        print(f"{name}  EMPTY FRAME AT RESET")
        continue
    acts = sorted(a.value for a in env.action_space)
    bg = int(np.bincount(g.ravel()).argmax())
    nb = notched(g, {bg})
    rows[name] = (acts, bg, nb)
    print(f"{name}  {str(acts):12s} {bg:3d} n={len(nb):3d}  {nb[:3]}")
    sys.stdout.flush()

print("\n== candidate signature: >=1 notched 3x3 window at reset ==")
for name, (acts, bg, nb) in rows.items():
    print(f"  {name}: n_notched={len(nb)} -> {len(nb) >= 1}")

print("\n== candidate signature 2: >=1 notched window AND no complex actions ==")
for name, (acts, bg, nb) in rows.items():
    no_complex = True
    try:
        env = arc.make(envs[name].game_id)
        no_complex = not any(a.is_complex() for a in env.action_space)
    except Exception:
        pass
    print(f"  {name}: n_notched={len(nb)} no_complex={no_complex} "
          f"-> {len(nb) >= 1 and no_complex}")
sys.stdout.flush()
