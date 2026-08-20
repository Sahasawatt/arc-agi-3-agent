"""tr87: extract the SIX icon+block pairs cleanly (3 row-bands y[4-10,13-19,
22-28] x 2 column-pairs x[12-18]/[22-28] and x[35-41]/[45-51]) and compare
each icon's shape/count against the 5 hint-band icons and all 35 dial
states -- and check whether the "colour-7 block" half of each pair is
really always a featureless solid, or carries texture that would mark one
row as the active/current-level one.
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}
STATIONS = [15, 22, 29, 36, 43]

g = np.array(env.reset().frame)[-1]

ROWS = [4, 13, 22]          # y0 of each row-band (7 tall)
ICON_X = [12, 35]           # x0 of each icon (colour-10 bg, ink=5)
BLOCK_X = [22, 45]          # x0 of each paired colour-7 block

print("== six icons, ink=5 mask, cell counts ==")
icons = {}
for r_i, y0 in enumerate(ROWS):
    for c_i, x0 in enumerate(ICON_X):
        sub = g[y0:y0 + 7, x0:x0 + 7]
        mask = (sub == 5)
        icons[(r_i, c_i)] = mask
        print(f"  pair row={r_i} col={c_i} icon@({x0},{y0}): {mask.sum()} ink cells")
        for row in sub:
            print("    " + "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in row))

print("\n== six paired colour-7 blocks: solid, or textured? ==")
for r_i, y0 in enumerate(ROWS):
    for c_i, x0 in enumerate(BLOCK_X):
        sub = g[y0:y0 + 7, x0:x0 + 7]
        vals, cnt = np.unique(sub, return_counts=True)
        print(f"  pair row={r_i} col={c_i} block@({x0},{y0}): census={dict(zip(vals.tolist(), cnt.tolist()))}")

sys.stdout.flush()
