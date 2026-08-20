"""tr87: re-run haul.crates() against THIS process's live reset frame (read-only
import -- haul.py itself is not modified) to get trustworthy current coords,
since results/haul-sig.txt ran in a separate process and tr87's crate list
there only showed 4 of the claimed 5 tuples (print truncation or a genuine
process-to-process difference -- settle it here rather than assume).
"""
import sys
import numpy as np
import arc_agi
import haul

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
g = np.array(env.reset().frame)[-1]

cr = haul.crates(g)
print(f"crates() found {len(cr)}:")
for w, h, ring, inner, x0, y0 in cr:
    print(f"  w={w} h={h} ring={ring} inner={inner} x0={x0} y0={y0}")

print("\nsignature() ->", haul.signature(g))

# the two colour-10 bordered "glyph" boxes + colour-7 solid blocks up top --
# what are THOSE, structurally? Are they also caught by crates()?
print("\nfull colour-10 bounding regions (candidate glyph displays):")
ys, xs = np.nonzero(g == 10)
print(f"  colour 10: x[{xs.min()}-{xs.max()}] y[{ys.min()}-{ys.max()}] n={len(xs)}")

sys.stdout.flush()
