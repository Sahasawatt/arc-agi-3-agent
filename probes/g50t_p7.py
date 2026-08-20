"""g50t probe 7: after the snake clears x14-18, can the piece go down there?

    ./.venv/Scripts/python.exe g50t_p7.py

Probe 6 measured that the consuming press at (38, 8) turns x14-18 y38-42 from
colour 8 to floor -- which is the exact square that refused the piece before
(`g50t-p1.txt` C). The engine BFS nonetheless never reached (14, 38)
(`g50t-p5.txt`), so one of those two is wrong. Drive it by hand and read the
board at each step.
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


def piece(g):
    ys, xs = np.nonzero(g == 9)
    cells = {(int(x), int(y)) for x, y in zip(xs, ys) if y < 60 and x > 10}
    best = set()
    while cells:
        stack, blob = [next(iter(cells))], set()
        while stack:
            p = stack.pop()
            if p in blob or p not in cells:
                continue
            blob.add(p)
            x, y = p
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) in cells:
                    stack.append((x + dx, y + dy))
        cells -= blob
        if len(blob) > len(best):
            best = blob
    return None if not best else (min(p[0] for p in best), min(p[1] for p in best))


def eights(g, x0, x1, y0, y1):
    return int((g[y0:y1 + 1, x0:x1 + 1] == 8).sum())


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["g50t"].game_id)
A = {a.value: a for a in env.action_space}
NAME = {1: "up", 2: "down", 3: "left", 4: "right", 5: "act5"}

obs = env.reset()
g = grid_of(obs)
print(f"reset: piece={piece(g)} 8s in x14-18 y38-42 = {eights(g, 14, 18, 38, 42)}")

plan = [4, 4, 4, 4] + [3, 3, 3, 3] + [2, 2, 2, 2, 2, 2]
last = piece(g)
for i, a in enumerate(plan):
    obs = env.step(A[a])
    g = grid_of(obs)
    if g is None:
        print(f"  {i:2d} {NAME[a]:5s}: frame empty state={obs.state}")
        break
    p = piece(g)
    print(f"  {i:2d} {NAME[a]:5s}: piece={p} {'MOVED' if p != last else 'REFUSED'}"
          f"  8s@x14-18y38-42={eights(g, 14, 18, 38, 42)}"
          f"  total8={int((g == 8).sum())}"
          f"  state={str(obs.state).split('.')[-1]} lvl={obs.levels_completed}")
    last = p

print("\nboard around the gate now (x10-30, y30-48):")
for y in range(30, 49):
    print(f"  y={y:2d} " + "".join(CHARS[int(v) & 0xF] for v in g[y, 10:31]))
sys.stdout.flush()
