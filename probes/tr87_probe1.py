"""tr87: precise object inventory at reset, from THIS process's own frame.

Does not trust results/haul-sig.txt's coordinates (that ran in a different
process at a different time; verify board layout is stable in-process first,
then re-derive the crate rectangles ourselves with connected-component logic
rather than eyeballing the ASCII dump).
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
obs = env.reset()
g = np.array(obs.frame)[-1]
print("shape:", g.shape)

vals, cnt = np.unique(g, return_counts=True)
print("census:", dict(zip(vals.tolist(), cnt.tolist())))

# second reset in-process -- same board?
obs2 = env.reset()
g2 = np.array(obs2.frame)[-1]
print("reset-vs-reset identical:", np.array_equal(g, g2))

# second env in-process -- same board?
env2 = arc.make(envs["tr87"].game_id)
g3 = np.array(env2.reset().frame)[-1]
print("second env identical:", np.array_equal(g, g3))

for color in sorted(vals.tolist()):
    ys, xs = np.nonzero(g == color)
    print(f"colour {color}: {len(xs)} cells, x[{xs.min()}-{xs.max()}] y[{ys.min()}-{ys.max()}]")

# bounding boxes of colour-0 (candidate piece)
ys, xs = np.nonzero(g == 0)
print("\ncolour-0 cells (candidate piece), sorted by y then x:")
pts = sorted(zip(ys.tolist(), xs.tolist()))
for y, x in pts:
    print(f"  ({x},{y})")

sys.stdout.flush()
