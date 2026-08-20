"""g50t probe 6: WHERE do the walls open, and what is the 8-snake?

    ./.venv/Scripts/python.exe g50t_p6.py

Covering the 8s at (38, 8) turns 24 wall cells into floor (`g50t-p1.txt` A), and
every argument made since has been about what that opens WITHOUT anyone looking
at it. This looks: the exact cells that changed, and the board either side.
"""

import sys

import numpy as np

import arc_agi

CHARS = "0123456789abcdef"


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def dump(g, label, x0=0, x1=63, y0=0, y1=63):
    print(f"  -- {label} --")
    hdr = "        " + "".join(str((x // 10) % 10) if x % 5 == 0 else " "
                               for x in range(x0, x1 + 1))
    print(hdr)
    for y in range(y0, y1 + 1):
        print(f"    y={y:2d} " + "".join(CHARS[int(v) & 0xF] for v in g[y, x0:x1 + 1]))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["g50t"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
before = grid_of(obs)
for a in [4, 4, 4]:
    obs = env.step(A[a])
pre = grid_of(obs)
obs = env.step(A[4])
post = grid_of(obs)

d = pre != post
d[63, :] = False
ys, xs = np.nonzero(d)
pairs = {}
for y, x in zip(ys.tolist(), xs.tolist()):
    pairs.setdefault((int(pre[y, x]), int(post[y, x])), []).append((x, y))
print("cell changes on the consuming press, by colour pair:")
for k, cells in sorted(pairs.items(), key=lambda t: -len(t[1])):
    xs_ = [c[0] for c in cells]
    ys_ = [c[1] for c in cells]
    print(f"  {k[0]} -> {k[1]}: {len(cells)} cells, "
          f"x[{min(xs_)}-{max(xs_)}] y[{min(ys_)}-{max(ys_)}]")
    if k in ((0, 5), (0, 8), (8, 5)):
        rows_ = {}
        for x, y in cells:
            rows_.setdefault(y, []).append(x)
        for y in sorted(rows_):
            print(f"     y={y:2d}: x={sorted(rows_[y])}")

print()
dump(pre, "BEFORE the consuming press", 30, 63, 4, 30)
print()
dump(post, "AFTER the consuming press", 30, 63, 4, 30)

print("\nthe colour-8 snake at reset, whole board:")
ys, xs = np.nonzero(before == 8)
rows = {}
for x, y in zip(xs.tolist(), ys.tolist()):
    rows.setdefault(int(y), []).append(int(x))
for y in sorted(rows):
    r = sorted(rows[y])
    print(f"  y={y:2d}: x={r[0]}-{r[-1]} ({len(r)} cells)")
sys.stdout.flush()
