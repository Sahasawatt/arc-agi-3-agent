"""Replay to sb26 L7 and introspect read() piece by piece."""
import sys

import numpy as np

import arc_agi
import sorter
from sorter import Sorter, band, read, rows_of

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
g = np.array(obs.frame)[-1]
drv = Sorter([a.value for a in env.action_space])
for i in range(600):
    v = drv.act(g, obs.levels_completed)
    if v is None:
        break
    if isinstance(v, tuple):
        obs = env.step(A[6], data={"x": v[1], "y": v[2]})
    else:
        obs = env.step(A[v])
    g = np.array(obs.frame)[-1]
print(f"stopped at level {obs.levels_completed + 1}")

h = g.shape[0]
top = band(g, 0, h // 3, 3)
bot = band(g, 2 * h // 3, h, 1)
print("top:", top)
print("bot pre-walk:", bot)
while bot[0] - 1 > 2 * h // 3 and rows_of(g, bot[0] - 1):
    cand = [t for t in rows_of(g, bot[0] - 1) if t[2] != sorter.SLOT_COLOUR]
    if len(cand) >= len([t for t in bot[1] if t[2] != sorter.SLOT_COLOUR]):
        bot = (bot[0] - 1, rows_of(g, bot[0] - 1))
    else:
        break
print("bot walked:", bot)
bg = int(np.bincount(g.ravel()).argmax())
hollow = set()
for x0, x1, c in bot[1]:
    if c != sorter.SLOT_COLOUR and int(g[bot[0] + 1, (x0 + x1) // 2]) == bg:
        hollow.add((x0, x1))
print("hollow runs:", hollow)
rows = []
for y in range(top[0] + 1, bot[0]):
    marks = [t for t in rows_of(g, y) if t[2] == sorter.SLOT_COLOUR]
    if len(marks) >= 2 and (not rows or y > rows[-1][0] + 2):
        rows.append((y, [(t[0] + t[1]) // 2 for t in marks]))
    elif len(marks) >= 2 and rows and len(marks) > len(rows[-1][1]):
        rows[-1] = (y, [(t[0] + t[1]) // 2 for t in marks])
print("rows:", rows)
for y, xs in rows:
    runs = rows_of(g, y)
    groups = [[xs[0]]]
    for x in xs[1:]:
        if x - groups[-1][-1] > 8:
            groups.append([])
        groups[-1].append(x)
    for gr in groups:
        walls_l = [t for t in runs if t[1] < gr[0] and t[0] == t[1]]
        walls_r = [t for t in runs if t[0] > gr[-1] and t[0] == t[1]]
        print(f"  y{y} gr={gr} walls_l={walls_l} walls_r={walls_r}")
reps = []
for y in range(0, rows[0][0]):
    r = [t for t in rows_of(g, y) if t[1] - t[0] >= 1]
    if len(r) >= 3 and len({t[2] for t in r}) >= 2:
        if not reps or y >= reps[-1][0] + 6:
            reps.append((y, r))
print("reps:", [(y, [t[2] for t in r]) for y, r in reps])
for y in range(0, g.shape[0]):
    line = "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                   for v in g[y])
    if len(set(line)) > 1:
        print(f"  y{y:2d} {line}")
b = read(g)
print("read():", "None" if b is None else
      {k: b[k] for k in ("recipe", "plan", "order")})
sys.stdout.flush()
