"""What do sb26/dc22/bp35 level 2 look like -- and where does each driver stop?

Each game's level 1 is now driven; the drivers were built from level 1 alone.
One episode per game: drive level 1 with the driver, then dump level 2's
first frame and let the driver keep answering until it returns None, logging
what it tried. That names the gap between the driver and level 2 without any
hand play.
"""
import sys

import numpy as np

import arc_agi
from bridge import Bridge
from bridge import signature as bridge_sig
from sorter import Sorter
from sorter import signature as sorter_sig
from tape import Tape
from tape import signature as tape_sig

DRIVERS = {
    "sb26": (Sorter, sorter_sig),
    "dc22": (Bridge, bridge_sig),
    "bp35": (Tape, tape_sig),
}


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def dump(g, label):
    print(f"  --- {label} ---")
    for y in range(g.shape[0]):
        line = "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                       for v in g[y])
        if len(set(line)) > 1:
            print(f"    y{y:2d} {line}")


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}

for name, (cls, sig) in DRIVERS.items():
    print(f"== {name} ==")
    env = arc.make(envs[name].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    g = grid_of(obs)
    drv = cls([a.value for a in env.action_space])
    l2_shown = False
    nones = 0
    for i in range(400):
        v = drv.act(g, obs.levels_completed)
        if v is None:
            nones += 1
            if obs.levels_completed >= 1:
                print(f"  driver None at action {i} on level "
                      f"{obs.levels_completed + 1}")
                break
            if nones > 3:
                print(f"  driver gave up on level 1 at action {i}")
                break
            continue
        nones = 0
        if isinstance(v, tuple):
            obs = env.step(A[6], data={"x": v[1], "y": v[2]})
            what = f"click({v[1]},{v[2]})"
        else:
            obs = env.step(A[v])
            what = f"A{v}"
        g2 = grid_of(obs)
        if g2 is None:
            print(f"  i={i}: DEAD FRAME after {what}")
            break
        if obs.levels_completed >= 1 and not l2_shown:
            print(f"  level 1 cleared at action {i + 1}")
            dump(g2, f"{name} level 2, first frame")
            l2_shown = True
            print(f"  signature on the L2 board: {sig(g2)}")
        elif obs.levels_completed >= 1:
            print(f"  L2 i={i} {what}: n={int((g != g2).sum())} "
                  f"lvl={obs.levels_completed}")
        g = g2
        if obs.levels_completed >= 2:
            print("  ** LEVEL 2 CLEARED **")
            break
        if str(obs.state) != "GameState.NOT_FINISHED":
            print(f"  state={str(obs.state).split('.')[-1]}")
            break
    sys.stdout.flush()
    print()
