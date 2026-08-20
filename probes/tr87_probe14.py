"""tr87: dump the top region (y0-30) in full, and try to auto-segment the
"six 7x7 glyph-tile pairs at y4-28 (colour 10 ink on colour 5, paired with a
colour-7 block each)" noted in Foundation but never examined. Column-gap
segmentation (background-colour runs), same technique as the station spacing
discovery, no eyeballing.
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
g = np.array(env.reset().frame)[-1]

print("== y0-30, x0-64, raw ==")
top = g[0:31, :]
for y, row in enumerate(top):
    print(f"  y={y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in row))

vals, cnt = np.unique(top, return_counts=True)
print("\ntop census:", dict(zip(vals.tolist(), cnt.tolist())))

print("\n== per-column non-background(2) census, y0-30 ==")
bg = 2  # top region background per Foundation ("background colour 2 (top)")
colmask = (top != bg)
colsum = colmask.sum(axis=0)
# find contiguous x-runs where colsum > 0
runs = []
in_run = False
for x, c in enumerate(colsum.tolist()):
    if c > 0 and not in_run:
        start = x
        in_run = True
    if c == 0 and in_run:
        runs.append((start, x - 1))
        in_run = False
if in_run:
    runs.append((start, len(colsum) - 1))
print("non-background x-runs:", runs)

for (x0, x1) in runs:
    sub = g[0:31, x0:x1 + 1]
    vals2, cnt2 = np.unique(sub, return_counts=True)
    ys, xs = np.nonzero(sub != bg)
    print(f"\nrun x[{x0}-{x1}] width={x1-x0+1}: census={dict(zip(vals2.tolist(), cnt2.tolist()))} "
          f"y-extent=[{ys.min()}-{ys.max()}]")

sys.stdout.flush()
