"""Play a fixed action list. Dumps a PNG per frame AND prints what moved each step,
so a rule can be read off stdout without opening a single image."""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

import arc_agi
from arc_agi.rendering import frame_to_rgb_array
from perception import describe, movement, objects

GAME = sys.argv[1] if len(sys.argv) > 1 else "ls20"
ACTIONS = [int(a) for a in sys.argv[2].split(",")] if len(sys.argv) > 2 else []

out = Path("frames") / GAME
out.mkdir(parents=True, exist_ok=True)

arc = arc_agi.Arcade()
env = arc.make(GAME)
obs = env.reset()


def save(step, obs):
    rgb = frame_to_rgb_array(step, np.array(obs.frame)[-1], scale=8)
    Image.fromarray(rgb.astype("uint8")).save(out / f"{step:03d}.png")


save(0, obs)
space = {a.value: a for a in env.action_space}
prev_objs, terrain = objects(obs.frame)
level = obs.levels_completed
print(f"{GAME} actions={sorted(space)}")
print("scene at step 0:")
print(describe(prev_objs, terrain))

for i, a in enumerate(ACTIONS, start=1):
    obs = env.step(space[a])
    save(i, obs)
    cur_objs, terrain = objects(obs.frame)
    events = "; ".join(movement(prev_objs, cur_objs))
    flag = "  <<< LEVEL UP" if obs.levels_completed > level else ""
    print(f"step {i:3d} action {a}  lvl={obs.levels_completed}  {events}{flag}")
    if obs.levels_completed > level:  # new level, new board — dump the whole scene
        print(describe(cur_objs, terrain))
    prev_objs, level = cur_objs, obs.levels_completed

print("\nfinal scene:")
print(describe(prev_objs, terrain))
print("frames ->", out.resolve())
