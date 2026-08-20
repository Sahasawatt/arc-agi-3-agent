"""sb26 L5: forward-only verification of the DFS winner, twice, plus a
control with the two child 8s' slots swapped against e's -- the winner must
repeat and the perturbed load must stay silent.

Winner (sb26-l5-dfs.txt, leaf 1211): U19=6, U25=9h, U31=9h, child box
L25=e, L31=8, L37=8, U37=b, U43=f -- the recipe [6,e,8,8,e,8,8,b,f] is the
UPPER ROW FLATTENED, each hollow-9 expanding to the child box's own content
(e,8,8): the hollow block is a reference to the box wearing its frame
colour, loaded once and called twice.
"""
import sys

import numpy as np

import arc_agi
from sorter import Sorter

STOCK_Y = 58
WIN = [(13, (19, 22)), (48, (25, 22)), (55, (31, 22)),
       (41, (25, 36)), (20, (31, 36)), (27, (37, 36)),
       (34, (37, 22)), (6, (43, 22))]
# control: e and the first 8 trade slots inside the child box
CTRL = [(13, (19, 22)), (48, (25, 22)), (55, (31, 22)),
        (20, (25, 36)), (41, (31, 36)), (27, (37, 36)),
        (34, (37, 22)), (6, (43, 22))]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def run(label, pairs):
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    env = arc.make(envs["sb26"].game_id)
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    g = grid_of(obs)
    drv = Sorter([a.value for a in env.action_space])
    for i in range(200):
        v = drv.act(g, obs.levels_completed)
        if v is None:
            break
        if isinstance(v, tuple):
            obs = env.step(A[6], data={"x": v[1], "y": v[2]})
        else:
            obs = env.step(A[v])
        g = grid_of(obs)
    assert obs.levels_completed == 4
    for x, slot in pairs:
        env.step(A[6], data={"x": x, "y": STOCK_Y})
        obs = env.step(A[6], data={"x": slot[0], "y": slot[1]})
    obs = env.step(A[5])
    print(f"{label}: lvl={obs.levels_completed} "
          f"state={str(obs.state).split('.')[-1]}")
    sys.stdout.flush()


run("winner #1", WIN)
run("winner #2", WIN)
run("control (e<->8 swapped)", CTRL)
