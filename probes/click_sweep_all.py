"""Which of the remaining games have a click at all -- and does anything answer it?

The two games that fell today both fell because the click had never been
aimed (results/click-probe.txt). Every wall recorded for ka59, sc25, sb26 and
g50t was measured in that same era, so before any of them is re-probed by
hand the cheap question is: do they even have a complex action, and does the
board answer an aimed one?

One click per FRESH episode, at the centre of every component of the reset
frame, smallest first. A component that answers more than the HUD tick is
printed. Controls: the run prints the component count, so "no responders" is
distinguishable from "nothing was clicked", and a click on the emptiest
corner is included in every game's sweep.
"""
import sys

import numpy as np

import arc_agi

GAMES = ["ka59", "sc25", "sb26", "g50t", "cn04", "bp35"]
MAX_TARGETS = 45


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def components(g):
    bg = int(np.bincount(g.ravel()).argmax())
    seen = np.zeros(g.shape, dtype=bool)
    out = []
    for y in range(g.shape[0]):
        for x in range(g.shape[1]):
            if seen[y, x] or g[y, x] == bg:
                continue
            col = int(g[y, x])
            stack, cells = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < g.shape[0] and 0 <= nx < g.shape[1]
                            and not seen[ny, nx] and g[ny, nx] == col):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            ys = [c[0] for c in cells]
            xs = [c[1] for c in cells]
            out.append(((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2,
                        col, len(cells)))
    return out


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

for name in GAMES:
    if name not in envs:
        print(f"{name}: not on the roster")
        continue
    env = arc.make(envs[name].game_id)
    acts = [a.value for a in env.action_space]
    clicker = next((a for a in env.action_space if a.is_complex()), None)
    obs = env.reset()
    g = grid_of(obs)
    if g is None:
        print(f"{name}: EMPTY FRAME AT RESET")
        continue
    cands = sorted(components(g), key=lambda c: c[3])[:MAX_TARGETS]
    print(f"== {name}: actions={acts} complex={'yes' if clicker else 'NO'} "
          f"components={len(cands)} ==")
    if clicker is None:
        print("  no complex action -- its walls cannot be a click artefact")
        sys.stdout.flush()
        continue
    live = []
    for cx, cy, col, size in cands + [(1, 1, -1, 0)]:
        env2 = arc.make(envs[name].game_id)
        A2 = {a.value: a for a in env2.action_space}
        obs2 = env2.reset()
        gg = grid_of(obs2)
        obs2 = env2.step(A2[clicker.value], data={"x": cx, "y": cy})
        g2 = grid_of(obs2)
        if g2 is None:
            print(f"  ({cx:2d},{cy:2d}) colour{col:3d} size{size:5d}: DEAD FRAME")
            continue
        n = int((gg != g2).sum())
        if n > 1:
            live.append((cx, cy, col, size, n))
            print(f"  ({cx:2d},{cy:2d}) colour{col:3d} size{size:5d}: n={n:5d} "
                  f"lvl={obs2.levels_completed}   RESPONDS")
        sys.stdout.flush()
    print(f"  responders beyond the 1-cell tick: {len(live)} of "
          f"{len(cands)} components\n")
