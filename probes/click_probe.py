"""Is the repo's click AIMED? Two ways of attaching coordinates, side by side.

`compete.py:1965` does `clicker.set_data({...})` then `env.step(clicker)`.
The local wrapper builds its ActionInput from its own `data` kwarg
(`local_wrapper.py:234`: `ActionInput(id=action, data=data or {})`) and never
consults the action object, so that path arrives with `data={}` -- which is
what a game reading `data['x']` answers `KeyError: 'x'` to.

That KeyError is recorded in CLAUDE.md as cn04's OWN bug ("one click kills
the run at the engine"). This decides between the two readings on the games
that carry a complex action, with both call styles in one invocation.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

for gid in ("cn04", "bp35", "dc22"):
    if gid not in envs:
        print(f"{gid}: not in the playable set")
        continue
    print(f"== {gid} ==")
    print(f"  GameAction.set_data exists: "
          f"{hasattr(arc.make(envs[gid].game_id).action_space[0], 'set_data')}")
    for style in ("set_data", "data-kwarg"):
        env = arc.make(envs[gid].game_id)
        clicker = next((a for a in env.action_space if a.is_complex()), None)
        if clicker is None:
            print(f"  {style}: no complex action")
            continue
        obs = env.reset()
        g = grid_of(obs)
        h, w = g.shape
        x, y = w // 2, h // 2
        if style == "set_data":
            clicker.set_data({"x": x, "y": y})
            obs = env.step(clicker)
        else:
            obs = env.step(clicker, data={"x": x, "y": y})
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  {style} click at ({x},{y}): DEAD (obs=None, the "
                  f"KeyError path)")
        else:
            print(f"  {style} click at ({x},{y}): alive, n="
                  f"{int((g != g2).sum())} cells changed, "
                  f"state={str(obs.state).split('.')[-1]}")
        sys.stdout.flush()
    print()
