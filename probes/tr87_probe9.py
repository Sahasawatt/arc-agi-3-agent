"""tr87: the y40-46 colour-10 band sits directly ABOVE the room (y51-57) and
spans roughly the same x-range -- unexamined so far. Dump it precisely and
check whether it divides into 5 station-aligned sub-blocks that could encode
each station's TARGET symbol (compare against the S0-S6 deck built earlier).
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
g = np.array(env.reset().frame)[-1]

print("== y40-46 band, x0-64, raw ==")
band = g[40:47, :]
for y, row in enumerate(band, start=40):
    print(f"  y={y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in row))

ys, xs = np.nonzero(g[40:47, :] != 3)
print("\nband non-background(3) x-range:", xs.min(), "-", xs.max())
vals, cnt = np.unique(g[40:47, :], return_counts=True)
print("band census:", dict(zip(vals.tolist(), cnt.tolist())))

# does it break into 5 sub-blocks aligned with the room's stations (x15,22,29,36,43)?
print("\n5-wide slices at each station x, y40-46:")
for x0 in (15, 22, 29, 36, 43):
    sub = g[40:47, x0:x0 + 5]
    print(f" station x={x0}:")
    for row in sub:
        print("    " + "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in row))

sys.stdout.flush()
