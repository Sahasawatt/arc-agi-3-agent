"""bp35: WHAT is the 1141-cell event? Full-frame dumps around it.

Drive the piece under the chute (A4 x3 puts it at the press that fired the
event in `bp35-p1.txt`), dumping the whole frame before and after the event
press, then keep going and dump each further event. ASCII, both layers when
they differ.
"""
import sys

import numpy as np

import arc_agi


def layers(obs):
    f = np.array(obs.frame)
    return f if f.ndim == 3 else f[None]


def dump(g, label):
    print(label)
    for y in range(64):
        row = "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in g[y])
        print(f"  y{y:2d} {row}")


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["bp35"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
g = layers(obs)[-1]
dump(g, "== RESET ==")
SEQ = [4, 4, 4, 4, 4, 7, 7, 7]
for i, v in enumerate(SEQ):
    obs = env.step(A[v])
    g2 = layers(obs)[-1]
    n = int((g != g2).sum())
    print(f"\npress {i} A{v}: {n} cells changed  lvl={obs.levels_completed} "
          f"state={str(obs.state).split('.')[-1]}")
    if n > 100:
        dump(g2, f"== after press {i} (A{v}) ==")
    g = g2
    sys.stdout.flush()
