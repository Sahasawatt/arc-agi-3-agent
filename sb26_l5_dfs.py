"""sb26 L5: exhaust the colour->slot assignments, insertion pinned to path
order.

The four instrument-(a) arms all load cleanly and A5 answers a timer tick
(results/sb26-l5-arms.txt, sb26-l5-cell.txt: the n=1 cell is the y53 bar,
identical for a plausible arm and an absurd control -- no feedback channel).
So the mapping is searched, the L2/L4 way:

  * blocks reduce to SIX colour classes -- 6, e, b, f, 8 (x2 solid), 9h (x2
    hollow) -- so distinct assignments are multiset permutations,
    8!/(2!*2!) = 10,080 leaves, not 40,320;
  * insertion order is pinned to the machine path (slots filled P1..P8 in
    order), sound if the win test is positional -- checked first by loading
    ONE assignment in two insertion orders and comparing A5's answers;
  * the win check is A5 at depth 8, levels_completed >= 5.
"""
import copy
import sys

import numpy as np

import arc_agi
from sorter import Sorter

STOCK_XS = {"f": [6], "6": [13], "8": [20, 27], "b": [34], "e": [41],
            "9h": [48, 55]}
STOCK_Y = 58
U = [(19, 22), (25, 22), (31, 22), (37, 22), (43, 22)]
L = [(25, 36), (31, 36), (37, 36)]
PATH = [U[0], U[1], U[2], L[0], L[1], L[2], U[3], U[4]]


def grid_of(obs):
    if obs is None:
        return None
    f = np.array(obs.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


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
BASE = env
print(f"at level 5 after {i} driver actions")
sys.stdout.flush()

# --- soundness: one assignment, two insertion orders ------------------------
SEQ = ["6", "e", "8", "8", "9h", "9h", "b", "f"]


def load(e, pairs):
    """pairs = [(colour_class, (sx_index_consumed_in_order), slot)] -- the
    stock x for a class is consumed left-to-right per class."""
    used = {k: 0 for k in STOCK_XS}
    o = None
    for c, slot in pairs:
        x = STOCK_XS[c][used[c]]
        used[c] += 1
        e.step(A[6], data={"x": x, "y": STOCK_Y})
        o = e.step(A[6], data={"x": slot[0], "y": slot[1]})
    return o


am = list(zip(SEQ, PATH))
for label, pairs in (("path order", am), ("reversed", am[::-1])):
    e = copy.deepcopy(BASE)
    o = load(e, pairs)
    g1 = grid_of(o)
    o = e.step(A[5])
    g2 = grid_of(o)
    print(f"  soundness {label}: A5 n={int((g1 != g2).sum())} "
          f"lvl={o.levels_completed}")
sys.stdout.flush()

# --- the search -------------------------------------------------------------
found = None
tried = [0]
path_taken = []


def dfs(e, depth, remaining):
    global found
    if found is not None:
        return
    if depth == len(PATH):
        tried[0] += 1
        if tried[0] % 240 == 0:
            print(f"  assignments tried: {tried[0]}")
            sys.stdout.flush()
        o = e.step(A[5])
        if o is not None and o.levels_completed >= 5:
            found = list(path_taken)
        return
    slot = PATH[depth]
    seen = set()
    for c in list(remaining):
        if c in seen or remaining[c] == 0:
            continue
        seen.add(c)
        child = copy.deepcopy(e)
        x = STOCK_XS[c][len(STOCK_XS[c]) - remaining[c]]
        child.step(A[6], data={"x": x, "y": STOCK_Y})
        o = child.step(A[6], data={"x": slot[0], "y": slot[1]})
        if o is None or str(o.state) != "GameState.NOT_FINISHED":
            continue
        remaining[c] -= 1
        path_taken.append((c, slot))
        dfs(child, depth + 1, remaining)
        path_taken.pop()
        remaining[c] += 1
        if found is not None:
            return


dfs(copy.deepcopy(BASE), 0,
    {"6": 1, "e": 1, "b": 1, "f": 1, "8": 2, "9h": 2})
print(f"assignments tried: {tried[0]}")
if found:
    print("WIN assignment (class -> slot):")
    for c, slot in found:
        print(f"  {c:>3} -> {slot}")
else:
    print("EXHAUSTED with path-order insertion: no assignment wins.")
sys.stdout.flush()
