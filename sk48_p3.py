"""sk48 hypothesis 3: the HUD picture is a SKEWER -- the arm fully extended
with the three blocks threaded ON it in order 8, 14, 9 outward from the
mouth. The 8 rides the arm tip once grabbed; threading the next block should
be the held block PUSHING INTO it. p2 stopped one extend short at 14's rows.
This drive extends UNTIL the presses stop answering, at every station, and
dumps the room after each phase instead of leaning on diffs.
"""
import sys

import numpy as np

import arc_agi


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def room(g, label):
    print(label)
    for y in range(12, 42):
        print(f"  y{y:2d} " + "".join(str(int(v)) if v < 10 else chr(87 + int(v))
                                       for v in g[y, 10:50]))


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sk48"].game_id)
A = {a.value: a for a in env.action_space}

obs = env.reset()
lvl = 0


def run(seq, label):
    global obs, lvl
    for v in seq:
        prev = grid_of(obs)
        obs = env.step(A[v])
        if obs is None:
            print(f"  A{v}: obs=None")
            return False
        g = grid_of(obs)
        moved = int((prev != g).sum()) if g is not None else -1
        if obs.levels_completed > lvl:
            print(f"  A{v}: LEVEL UP -> {obs.levels_completed}")
            lvl = obs.levels_completed
            return False
        if str(obs.state) != "GameState.NOT_FINISHED":
            print(f"  A{v}: {str(obs.state).split('.')[-1]}")
            return False
        if moved <= 1:   # nothing but the clock -- the press was refused
            print(f"  A{v}: dead press ({moved})")
    room(grid_of(obs), label)
    return True


print("== phase 1: grab 8 (up 3, extend to grab, retract home) ==")
run([1, 1, 1] + [4] * 4 + [3] * 4, "after 8-grab:")
print("== phase 2: down to 14's rows, extend to the wall ==")
run([2, 2] + [4] * 6, "after pushing 8 out at 14's rows:")
print("== phase 3: retract ==")
run([3] * 6, "after retract:")
sys.stdout.flush()
