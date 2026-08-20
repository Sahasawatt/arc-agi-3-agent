"""Replay a prefix, then probe — printing block position, HUD counts and events per step.

    uv run python walk.py ls20 <prefix-actions> -- <probe-actions>

Everything after `--` is the experiment; everything before it just gets you there.
"""

import sys

import arc_agi
from perception import hud, icon, movement, objects


def plates(frame, objs):
    """The two glyphs that must match: the indicator panel and the goal marker.
    Both are a big colour-5 plate; the goal one is the plate the block must enter."""
    out = {}
    for o in sorted((o for o in objs if o["colour"] == 5 and o["cells"] > 30),
                    key=lambda o: o["x"][0]):
        out[f"plate@x{o['x'][0]}y{o['y'][0]}"] = icon(
            frame, o["x"][0], o["x"][1], o["y"][0], o["y"][1])
    return out

GAME = sys.argv[1]
argv = sys.argv[2:]
cut = argv.index("--") if "--" in argv else len(argv)
PREFIX = [int(a) for a in argv[:cut][0].split(",")] if cut else []
PROBE = [int(a) for a in argv[cut + 1:][0].split(",")] if cut + 1 < len(argv) else []


def block(objs):
    """The moving piece: the orange (12) component."""
    for o in objs:
        if o["colour"] == 12:
            return f"x{o['x'][0]}-{o['x'][1]} y{o['y'][0]}-{o['y'][1]}"
    return "gone"


def yellows(objs):
    return [f"x{o['x'][0]}-{o['x'][1]} y{o['y'][0]}-{o['y'][1]}"
            for o in objs if o["colour"] == 11]


arc = arc_agi.Arcade()
env = arc.make(GAME)
obs = env.reset()

for a in PREFIX:  # get to the state under test, quietly
    obs = env.step({x.value: x for x in env.action_space}[a])
    # A run that starves mid-prefix ends in GAME_OVER; the engine's reset is a LEVEL
    # reset, exactly as compete.play handles it — replaying its action list needs the
    # same response or every step after the first death reads an empty frame.
    import numpy as _np
    from arcengine import GameState as _GS
    if _np.array(obs.frame).size == 0 or obs.state == _GS.GAME_OVER:
        obs = env.reset()

prev, _ = objects(obs.frame)
space = {a.value: a for a in env.action_space}
print(f"start  lvl={obs.levels_completed}  block={block(prev)}  hud={hud(obs.frame)}")
print(f"       yellow={yellows(prev)}")

for i, a in enumerate(PROBE, start=1):
    obs = env.step(space[a])
    cur, _ = objects(obs.frame)
    p = plates(obs.frame, cur)
    match = "MATCH" if len(set(p.values())) == 1 and len(p) > 1 else "differ"
    print(f"{i:3d} act{a}  lvl={obs.levels_completed}  block={block(cur)}  "
          f"budget={hud(obs.frame).get(11, 0)}  yellow={len(yellows(cur))}  {match}")
    for k, v in p.items():
        print(f"      {k} = {v}")
    prev = cur
