"""sb26 L2: search the real engine instead of guessing the mapping.

Seven blocks into seven slots is 5,040 assignments; five hand-guessed
mappings are dead and A5 is an all-or-nothing oracle, so this is a search
problem. sb26's env deepcopies cleanly (only bp35's does not), and the
action set at each node is tiny: select one of the remaining stock blocks,
place into one of the empty slots, or press A5. Depth 15 covers any full
load plus the run press.

Pruning that keeps it honest rather than clever: a click that changes
nothing is not expanded (selection no-ops), and a state is keyed on the
frame bytes so transpositions collapse. BFS by depth; stops at the first
levels_completed >= 2.
"""
import copy
import sys
from collections import deque

import numpy as np

import arc_agi

L1 = [("c", 35, 58), ("c", 22, 29), ("c", 19, 58), ("c", 28, 29),
      ("c", 43, 58), ("c", 34, 29), ("c", 27, 58), ("c", 40, 29), ("m", 5)]
STOCK_XS = [10, 17, 24, 31, 38, 45, 52]
SLOTS = [(22, 22), (28, 22), (40, 22), (22, 36), (28, 36), (34, 36), (40, 36)]


def grid_of(o):
    if o is None:
        return None
    f = np.array(o.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
A = {a.value: a for a in env.action_space}
obs = env.reset()
for s in L1:
    obs = (env.step(A[6], data={"x": s[1], "y": s[2]}) if s[0] == "c"
           else env.step(A[s[1]]))
g0 = grid_of(obs)
print(f"at level {obs.levels_completed}; searching")
sys.stdout.flush()

MOVES = ([("stock", x, 58) for x in STOCK_XS]
         + [("slot", x, y) for x, y in SLOTS]
         + [("run", 5, 0)])

seen = {g0.tobytes()}
q = deque([(env, obs, [])])
expanded = 0
found = None
while q and found is None:
    cur, cobs, path = q.popleft()
    expanded += 1
    if expanded % 200 == 0:
        print(f"  expanded={expanded} frontier={len(q)} depth={len(path)}")
        sys.stdout.flush()
    if len(path) >= 15:
        continue
    for kind, x, y in MOVES:
        child = copy.deepcopy(cur)
        if kind == "run":
            cobs2 = child.step({a.value: a for a in child.action_space}[5])
        else:
            cobs2 = child.step(
                {a.value: a for a in child.action_space}[6],
                data={"x": x, "y": y})
        if cobs2 is None:
            continue
        g = grid_of(cobs2)
        if g is None:
            continue
        if cobs2.levels_completed >= 2:
            found = path + [(kind, x, y)]
            print(f"  WIN in {len(found)} actions: {found}")
            break
        if str(cobs2.state) != "GameState.NOT_FINISHED":
            continue
        key = g.tobytes()
        if key in seen:
            continue
        seen.add(key)
        q.append((child, cobs2, path + [(kind, x, y)]))
print(f"done: expanded={expanded} states={len(seen)} "
      f"found={'YES' if found else 'NO'}")
if found:
    print("LINE:", found)
