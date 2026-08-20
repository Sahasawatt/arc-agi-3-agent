"""bp35 probes (a) + (b) from breadth-recon §bp35:

(a) A7's contexts -- press it once from every piece x-position (fresh episode
    each: k x A4 then A7) and classify the answer: no-op / piece move /
    conveyor event.
(b) does the conveyor event REPEAT -- park under the chute, then keep
    pressing A7; log each event's cell count and dump the left/right column
    contents compactly so consecutive steps can be diffed.

Column fingerprint: for each 6-row band, what sits in the left column
(x13-29) and right column (x31-53) -- 'BOX' (mostly colour 10), '3G'/'4G'
(the e-block groups, counted by their 5-wide block slots), '.' (background).
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def fingerprint(g):
    """Per 6-row band from y0: left/right column content codes."""
    out = []
    for y0 in range(0, 60, 6):
        band = g[y0:y0 + 6]
        codes = []
        for x0, x1 in ((13, 29), (31, 53)):
            sub = band[:, x0:x1 + 1]
            n10 = int((sub == 10).sum())
            n14 = int((sub == 14).sum())
            if n14 > 30:
                codes.append(f"{(n14 // 21)}G")   # ~21 cells per block
            elif n10 > 60:
                codes.append("BOX")
            elif n10 > 10:
                codes.append("box")
            else:
                codes.append(".")
        out.append(f"y{y0:02d} {codes[0]:>4s}|{codes[1]}")
    return out


def piece_x(g):
    ys, xs = np.nonzero((g == 9) | (g == 11))
    return int(xs.min()) if len(xs) else None


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

print("== (a) A7 from every reachable piece x ==")
for k in range(6):
    env = arc.make(envs["bp35"].game_id)
    obs = env.reset()
    for _ in range(k):
        obs = env.step({a.value: a for a in env.action_space}[4])
    A = {a.value: a for a in env.action_space}
    g0 = grid_of(obs)
    px = piece_x(g0)
    obs = env.step(A[7])
    g1 = grid_of(obs)
    n = int((g0 != g1).sum())
    kind = "no-op" if n <= 1 else ("piece-move" if n < 100 else "EVENT")
    print(f"  after {k}x A4 (piece x={px}): A7 -> {n} cells = {kind}  "
          f"lvl={obs.levels_completed}")
    sys.stdout.flush()

print("\n== (b) park under the chute, A7 repeatedly ==")
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
for _ in range(4):
    obs = env.step(A[4])       # the 4th arrival fires event #1
g = grid_of(obs)
print("after arrival event, piece x =", piece_x(g))
for line in fingerprint(g):
    print("   ", line)
for i in range(6):
    obs = env.step(A[7])
    g2 = grid_of(obs)
    n = int((g != g2).sum())
    print(f"A7 #{i}: {n} cells  lvl={obs.levels_completed} "
          f"state={str(obs.state).split('.')[-1]} piece_x={piece_x(g2)}")
    if n > 100:
        for line in fingerprint(g2):
            print("   ", line)
    g = g2
    if str(obs.state) != "GameState.NOT_FINISHED":
        break
    sys.stdout.flush()
