"""Probe cn04 past level 1: shim `compete.play` to hand over a LIVE env at level 2.

The engine is deterministic within a process and RANDOM across processes (twin envs
diverge 0 frames in-process; a 131-action winning prefix replayed in a fresh process
does not clear level 1), so replay-based probing is impossible — the only road to a
live level-2 state is to let the competition loop itself win level 1, then hijack.

    uv run python probe_cn04.py

Level-2 state so far, two layouts measured: the dock walk reaches body CONTACT with
the target shape and stalls — the level completes on jigsaw INTERLOCK, and the open
question is which side x orientation mates. The next experiment is the 4x4 trial
matrix (rotate x4, approach from N/S/E/W, bump in), scripted below as `trial()`.
"""

import numpy as np
import arc_agi
import compete as C


class Hop(Exception):
    def __init__(self, obs):
        self.obs = obs


class Shim:
    """Pass-through env that raises `Hop` the moment a level falls."""

    def __init__(self, env, at_level=1):
        self.env, self.at = env, at_level

    @property
    def action_space(self):
        return self.env.action_space

    def reset(self):
        return self.env.reset()

    def step(self, a, **k):
        o = self.env.step(a, **k)
        if o is not None and o.levels_completed >= self.at:
            raise Hop(o)
        return o


def live_at_level(game="cn04", level=1):
    arc = arc_agi.Arcade()
    env = arc.make(game)
    try:
        C.play(Shim(env, level))
    except Hop as h:
        return env, h.obs
    raise RuntimeError("play() ended without reaching the level")


if __name__ == "__main__":
    env, obs = live_at_level()
    print("live at level", obs.levels_completed + 1)
    f = np.array(obs.frame)[-1]
    np.save("results/probe-cn04-l2.npy", f)
