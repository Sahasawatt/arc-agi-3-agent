"""tr87: probe16 found the top region's SIX (icon,block) pairs decode as
(icon ~ one of the 5 hint-band icons -> WHICH STATION; block ~ one state in
THAT station's own 7-state deck -> WHAT PHASE). Two strongest candidates,
tested directly against the live win signal, one action sequence per life
(fresh reset each):

  pair(0,0): icon shape~hint@29 (station29) / block EXACT==deck@29 state3
      -> station29 to phase3 (2x ACTION4, 3x ACTION1)
  pair(2,0): icon EXACT==hint@22 (station22, strongest icon id) / block
      shape~deck@22 state5 -> station22 to phase5 (1x ACTION4, 5x ACTION1)

Also try each with the clamp returned to x=15 afterward, in case final
clamp position matters (untested lever from the brief).
"""
import sys
import numpy as np
import arc_agi

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def report(obs, label):
    print(f"  {label}: lvl={obs.levels_completed} state={str(obs.state).split('.')[-1]}")


print("== candidate A: station29 (x29) -> phase3, stay there ==")
obs = env.reset()
obs = env.step(A[4]); obs = env.step(A[4])  # x15 -> x22 -> x29
for _ in range(3):
    obs = env.step(A[1])
report(obs, "station29@phase3")

print("\n== candidate A + return clamp to x15 ==")
obs = env.step(A[4]); obs = env.step(A[4]); obs = env.step(A[4])  # x29->36->43->15 (wrap)
report(obs, "station29@phase3, clamp back at x15")

print("\n== candidate B: station22 (x22) -> phase5, fresh reset, stay there ==")
obs = env.reset()
obs = env.step(A[4])  # x15 -> x22
for _ in range(5):
    obs = env.step(A[1])
report(obs, "station22@phase5")

print("\n== candidate B + return clamp to x15 ==")
obs = env.step(A[3])  # x22 -> x15
report(obs, "station22@phase5, clamp back at x15")

sys.stdout.flush()
