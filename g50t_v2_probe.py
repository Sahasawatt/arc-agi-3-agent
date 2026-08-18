"""g50t_v2_probe.py -- quick diagnostic: why did v2 lose v1's only win?
Runs g50t across a few seeds, prints end-state diagnostics (remasked, lives,
stagnant_actions, len(graph)) so the regression can be isolated fast.
"""
import time
import arc_agi
from squirrel import Squirrel

MAX_ACTIONS = 500

for seed in [0, 1, 2, 3, 4]:
    arc = arc_agi.Arcade()
    env = arc.make("g50t", seed=seed)
    obs = env.reset()
    agent = Squirrel(list(env.action_space), max_actions=MAX_ACTIONS, reset_fn=env.reset, seed=seed)
    t0 = time.time()
    note = ""
    while True:
        if time.time() - t0 > 60:
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
        if obs.levels_completed >= 1:
            note = f"WIN at n_actions={agent.n_actions}"
            break
    print(f"seed={seed} levels={obs.levels_completed if obs else '?'} n_actions={agent.n_actions} "
          f"remasked={agent.remasked} lives={agent.lives} stagnant={agent.stagnant_actions} "
          f"graph_states={len(agent.graph)} note={note}", flush=True)
