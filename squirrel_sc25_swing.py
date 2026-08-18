"""squirrel_sc25_swing.py -- sc25 alone, max_actions=2000, 3 seeds.

sc25 is the last remaining zero (0/6 under v1 and wave14) and has a measured
absorption rule (CLAUDE.md, sc25 section): the FIRST action of every life is
absorbed regardless of type. squirrel v2's generic first-action-of-life
guard (squirrel.py's pending_first_edge) should stop that press from
poisoning the graph. Report levels_completed honestly, per seed.

    ./.venv/Scripts/python.exe squirrel_sc25_swing.py > results/squirrel-v2-sc25-swing.txt
"""
import time

import arc_agi

from squirrel import Squirrel

MAX_ACTIONS = 2000
SEEDS = [0, 1, 2]
WALL_CAP_S = 150


def play(seed):
    arc = arc_agi.Arcade()
    env = arc.make("sc25", seed=seed)
    obs = env.reset()
    agent = Squirrel(list(env.action_space), max_actions=MAX_ACTIONS,
                      reset_fn=env.reset, seed=seed)
    t0 = time.time()
    note = ""
    while True:
        if time.time() - t0 > WALL_CAP_S:
            note = "WALL_CAP"
            break
        try:
            action = agent.act(obs)
        except StopIteration:
            break
        obs = env.step(action, data=agent.pending_data)
        if obs is None:
            note = "obs=None"
            break
    return obs.levels_completed if obs is not None else 0, agent.n_actions, agent.lives, note


def main():
    for seed in SEEDS:
        levels, n_actions, lives, note = play(seed)
        print(f"seed={seed} levels_completed={levels} n_actions={n_actions} "
              f"lives={lives} {note}", flush=True)


if __name__ == "__main__":
    main()
