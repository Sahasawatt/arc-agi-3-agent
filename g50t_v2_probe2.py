"""g50t_v2_probe2.py -- does ANY squirrel-RNG seed (env fixed at default) recover the win?"""
import time
import arc_agi
from squirrel import Squirrel

MAX_ACTIONS = 500
arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
info = envs["g50t"]

for rng_seed in range(8):
    env = arc.make(info.game_id)
    obs = env.reset()
    agent = Squirrel(list(env.action_space), max_actions=MAX_ACTIONS, reset_fn=env.reset, seed=rng_seed)
    t0 = time.time()
    win_at = None
    while True:
        if time.time() - t0 > 40:
            break
        try:
            action = agent.act(obs)
        except StopIteration:
            break
        obs = env.step(action, data=agent.pending_data)
        if obs is None:
            break
        if obs.levels_completed >= 1:
            win_at = agent.n_actions
            break
    print(f"rng_seed={rng_seed} win_at={win_at} n_actions={agent.n_actions}", flush=True)
