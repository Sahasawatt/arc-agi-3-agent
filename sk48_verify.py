"""sk48 level 1: forward-only replay of the BFS line in a fresh process.
No rewinding -- reset once, step the list, assert the level."""
import sys

import numpy as np

import arc_agi

LINE = [1, 1, 1, 4, 4, 4, 4, 3, 2, 2, 4, 3, 1, 4]

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sk48"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
print(f"reset: lvl={obs.levels_completed}")
for i, v in enumerate(LINE):
    obs = env.step(A[v])
    if obs is None:
        print(f"press {i+1} (A{v}): obs=None")
        sys.exit(1)
    if obs.levels_completed:
        print(f"press {i+1}/{len(LINE)} (A{v}): levels_completed={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]}  <-- WIN")
        break
else:
    print(f"final: lvl={obs.levels_completed} state={str(obs.state).split('.')[-1]} NO WIN")

assert obs.levels_completed >= 1, "line did not clear level 1"
print("PASS: level 1 cleared in", len(LINE), "actions (baseline 61)")

g = np.array(obs.frame)[-1]
print("\nlevel 2 board, non-bg rows:")
bg = int(np.bincount(g.ravel()).argmax())
for y in range(64):
    row = "".join(str(int(v)) if v < 10 else chr(87 + int(v)) for v in g[y])
    if any(int(v) != bg for v in g[y]):
        print(f"  y{y:2d} {row}")
sys.stdout.flush()
