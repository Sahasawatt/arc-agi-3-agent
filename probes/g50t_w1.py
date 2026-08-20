"""g50t_w1.py -- reproduce squirrel.py's g50t L1 win with FULL instrumentation.

Records the exact ordered sequence of env interactions (resets AND steps) from
the very first env.reset() to the level-up, using the seed(0) recipe from the
task. Also captures the raw board (last frame plane) after every event, so a
later pass can byte-diff pre-death / post-reset / L1-entry.

Output: results/g50t-win-events.json  (events + per-event grid bytes as lists)
        printed summary to stdout
"""
import json
import random
import sys
import time

import numpy as np
import arc_agi
from arcengine import GameState

from squirrel import Squirrel

SEED = 0
MAX_ACTIONS = 500


def grid_of(obs):
    f = np.array(obs.frame)
    return f[-1]


def main():
    random.seed(SEED)
    arc = arc_agi.Arcade()
    env = arc.make("g50t", seed=SEED)

    events = []   # 'RESET' | int (plain action value) | ['click', y, x]
    grids = []    # grid (list of list ints) AFTER the corresponding event

    obs = env.reset()
    events.append("RESET")
    grids.append(grid_of(obs).tolist())

    def logged_reset():
        events.append("RESET")
        o = env.reset()
        grids.append(grid_of(o).tolist())
        return o

    agent = Squirrel(list(env.action_space), max_actions=MAX_ACTIONS, reset_fn=logged_reset)

    win_event_idx = None
    win_agent_action_count = None
    t0 = time.time()
    while True:
        if time.time() - t0 > 120:
            print("WALL_CAP hit, aborting", flush=True)
            break
        try:
            action = agent.act(obs)
        except StopIteration:
            print(f"StopIteration at agent.n_actions={agent.n_actions}", flush=True)
            break
        data = agent.pending_data
        if data is not None:
            ev = ["click", data["y"], data["x"]]
        else:
            ev = int(action.value)
        events.append(ev)

        obs = env.step(action, data=data)
        grids.append(grid_of(obs).tolist())

        if obs.state == GameState.GAME_OVER:
            # next act() call will handle the reset; nothing more to do here
            pass

        if obs.levels_completed >= 1:
            win_event_idx = len(events) - 1
            win_agent_action_count = agent.n_actions
            print(f"WIN: levels_completed={obs.levels_completed} at event idx "
                  f"{win_event_idx} (agent.n_actions={win_agent_action_count})", flush=True)
            break

        if agent.n_actions >= MAX_ACTIONS:
            print(f"max_actions reached ({MAX_ACTIONS}) without a win", flush=True)
            break

    n_resets = sum(1 for e in events if e == "RESET")
    print(f"total events={len(events)}  resets={n_resets}  "
          f"agent.n_actions={agent.n_actions}", flush=True)

    out = {
        "seed": SEED,
        "win_event_idx": win_event_idx,
        "win_agent_action_count": win_agent_action_count,
        "n_resets": n_resets,
        "n_events": len(events),
        "events": events,
        "grids": grids,
    }
    with open("results/g50t-win-events.json", "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("wrote results/g50t-win-events.json", flush=True)


if __name__ == "__main__":
    main()
