"""bp35 probe (c): pump the conveyor. Shuttle the piece back and forth
across the chute (every crossing of x44 fires the board-step event) and
watch for a level, a game over, or a cycle in the conveyor fingerprints.
Also try PARKING under the chute pressing A4 against the wall (does an
in-place press fire it?)."""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def fingerprint(g):
    out = []
    for y0 in range(0, 60, 6):
        band = g[y0:y0 + 6]
        codes = []
        for x0, x1 in ((13, 29), (31, 53)):
            sub = band[:, x0:x1 + 1]
            n10 = int((sub == 10).sum())
            n14 = int((sub == 14).sum())
            if n14 > 30:
                codes.append(f"{n14 // 21}G")
            elif n10 > 60:
                codes.append("B")
            elif n10 > 10:
                codes.append("b")
            else:
                codes.append(".")
        out.append(codes[0] + "/" + codes[1])
    return " ".join(out)


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = grid_of(obs)
events = 0
seen = {}
# Shuttle: right to x50, left to x38, right to x50 ... every leg crosses x44.
plan = ([4] * 5 + ([3, 4] * 30))
for i, v in enumerate(plan):
    obs = env.step(A[v])
    g2 = grid_of(obs)
    if g2 is None:
        print(f"i={i}: empty frame")
        break
    n = int((g != g2).sum())
    if n > 100:
        events += 1
        fp = fingerprint(g2)
        mark = ""
        if fp in seen:
            mark = f"  <-- CYCLE with event {seen[fp]}"
        seen[fp] = events
        print(f"i={i} A{v} EVENT #{events}: {fp}{mark}")
    g = g2
    if obs.levels_completed:
        print(f"i={i}: LEVEL {obs.levels_completed}")
        break
    if str(obs.state) != "GameState.NOT_FINISHED":
        print(f"i={i}: {str(obs.state).split('.')[-1]} after {events} events")
        break
    sys.stdout.flush()
print(f"done: {events} events, lvl={obs.levels_completed}, "
      f"state={str(obs.state).split('.')[-1]}")
