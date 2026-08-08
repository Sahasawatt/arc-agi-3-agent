"""tr87: single-station targets (probe17) were both refuted. The top region
decodes into exactly 5 (icon,block) pairs with a hint match -- one per
station -- plus a 6th pair with none. Test the hypothesis that ALL FIVE
stations must be set simultaneously to their own pair's target, derived
from probe16's block-vs-own-deck match:

  station15 (pair1,1, icon~hint@15, block EXACT==deck@15 state5)  -> phase5
  station22 (pair2,0, icon EXACT==hint@22, block shape~deck@22 state5) -> phase5
  station29 (pair0,0, icon shape~hint@29, block EXACT==deck@29 state3) -> phase3
  station36 (pair0,1, icon shape~hint@36, block shape~deck@36 state6) -> phase6
  station43 (pair1,0, icon shape~hint@43, block shape~deck@43 state5) -> phase5

Checks levels_completed after EACH station is set, not just at the end.
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}

TARGETS = [(15, 5), (22, 5), (29, 3), (36, 6), (43, 5)]  # (station x, target phase)


def report(obs, label):
    print(f"  {label}: lvl={obs.levels_completed} state={str(obs.state).split('.')[-1]}")
    return obs


obs = env.reset()
report(obs, "reset")
prev_x = 15
for x0, phase in TARGETS:
    moves = ((x0 - prev_x) // 7) % 5
    for _ in range(moves):
        obs = env.step(A[4])
    for _ in range(phase):
        obs = env.step(A[1])
    report(obs, f"station{x0}@phase{phase} set")
    prev_x = x0
    if obs.levels_completed:
        print("  LEVEL UP -- stopping")
        break

sys.stdout.flush()
