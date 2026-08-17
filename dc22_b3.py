"""Does the SAME `bridge` driver (no code changes, no L2-specific hints) keep
solving dc22 past level 1? bridge.py's algorithm is level-agnostic by design
(split()/twins()/components() re-derive geometry from the live frame every
level, Bridge._new_level() resets its per-level state on obs.levels_completed
change) -- worth testing directly before hand-building any L2-specific driver
or BFS. Runs the real engine, reading levels_completed/state after every
press, budget capped well under the 25-minute engine-time ceiling.
"""
import json
import time

import numpy as np
import arc_agi

from bridge import Bridge

T0 = time.time()


def log(msg):
    print("[%6.1fs] %s" % (time.time() - T0, msg), flush=True)


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
info = envs["dc22"]
env = arc.make(info.game_id)
obs = env.reset()
actions = [a for a in env.action_space if not a.is_complex()]
by_value = {a.value: a for a in actions}
values = sorted(by_value)
clicker = next((a for a in env.action_space if a.is_complex()), None)

bridge = Bridge(values)
trace = []
i = 0
MAXI = 600
prev_lvl = 0
stuck_reason = None
while i < MAXI:
    frame = np.array(obs.frame)[-1]
    cv = bridge.act(frame, obs.levels_completed)
    if cv is None:
        stuck_reason = "bridge returned None at i=%d lvl=%d" % (i, obs.levels_completed)
        log(stuck_reason)
        break
    i += 1
    if isinstance(cv, tuple):
        clicker.set_data({"x": cv[1], "y": cv[2]})
        obs = env.step(clicker, data={"x": cv[1], "y": cv[2]})
        trace.append({"i": i, "type": "click", "x": cv[1], "y": cv[2]})
    else:
        obs = env.step(by_value[cv])
        trace.append({"i": i, "type": "move", "v": cv})
    if obs is None:
        stuck_reason = "obs None at i=%d" % i
        log(stuck_reason)
        break
    if obs.levels_completed != prev_lvl:
        log("LEVEL UP: %d -> %d at i=%d" % (prev_lvl, obs.levels_completed, i))
        prev_lvl = obs.levels_completed
    if str(obs.state) not in ("GameState.NOT_FINISHED",):
        log("STATE=%s at i=%d lvl=%d" % (obs.state, i, obs.levels_completed))
        break
    if i % 50 == 0:
        log("i=%d lvl=%d (heartbeat)" % (i, obs.levels_completed))

result = {
    "actions_run": i,
    "final_levels_completed": obs.levels_completed if obs is not None else None,
    "final_state": str(obs.state) if obs is not None else None,
    "stuck_reason": stuck_reason,
    "trace": trace,
}
json.dump(result, open("results/dc22-b3-continue-log.json", "w"), indent=2, default=str)
log("DONE actions=%d final_lvl=%s final_state=%s stuck=%s"
    % (i, result["final_levels_completed"], result["final_state"], stuck_reason))
if str(result["final_state"]) in ("GameState.WIN",):
    print("WIN " + json.dumps([t.get("v", t) for t in trace]), flush=True)
print("DONE", flush=True)
