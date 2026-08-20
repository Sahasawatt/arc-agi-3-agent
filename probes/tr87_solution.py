"""tr87 level 1 SOLUTION, clean re-verification in a fresh process.

Win condition (decoded from the top y4-28 region, probe16/probe18): the six
(icon,block) pairs there are (icon ~ hint-band icon -> names a STATION;
block ~ a state in THAT station's own 7-state deck -> names a TARGET
PHASE). Five of the six pairs carry a hint match, one per station -- their
targets, set simultaneously, are the level-1 win:
  station15 -> phase5, station22 -> phase5, station29 -> phase3,
  station36 -> phase6, station43 -> phase5.

Action list (28 actions, ACTION1=dial forward, ACTION4=clamp +1 station):
  1,1,1,1,1, 4, 1,1,1,1,1, 4, 1,1,1, 4, 1,1,1,1,1,1, 4, 1,1,1,1,1
"""
import sys
import arc_agi

ACTIONS = [1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 4, 1, 1, 1, 4, 1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1]
assert len(ACTIONS) == 28

arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["tr87"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
print(f"reset: lvl={obs.levels_completed}")
for i, a in enumerate(ACTIONS):
    obs = env.step(A[a])
    if obs.levels_completed:
        print(f"action {i+1}/{len(ACTIONS)} (A{a}): levels_completed={obs.levels_completed} "
              f"state={str(obs.state).split('.')[-1]}  <-- WIN")
        break
else:
    print(f"final: levels_completed={obs.levels_completed} state={str(obs.state).split('.')[-1]}  NO WIN")

print(f"\nFINAL CHECK: levels_completed={obs.levels_completed} (expect >=1)")
assert obs.levels_completed >= 1, "solution did not clear level 1"
print("PASS: level 1 cleared.")
sys.stdout.flush()
