"""sb26 L2: exhaust the slot ASSIGNMENTS with the insertion order fixed.

The naive frame-BFS explodes (branching ~15) and carries a principle bug: A7
is an UNDO, so the game keeps an insertion stack, and two states with one
frame can differ in history -- frame-dedup would merge them (the sp80 hidden
-state law). This search sidesteps both:

  * the insertion ORDER is pinned to the recipe (colour i is always placed
    i-th), so if the win test is positional the order cannot hurt, and
  * what is searched is only WHICH SLOT each colour takes: 7! = 5,040
    leaves, ~13,700 engine nodes via incremental deepcopy -- affordable.

First, one measurement the whole approach rests on: the same assignment
loaded in two different insertion orders, A5 pressed on both. If those
disagree, the win test reads the stack and this search is unsound -- print
and stop rather than searching anyway.
"""
import copy
import sys

import numpy as np

import arc_agi

L1 = [("c", 35, 58), ("c", 22, 29), ("c", 19, 58), ("c", 28, 29),
      ("c", 43, 58), ("c", 34, 29), ("c", 27, 58), ("c", 40, 29), ("m", 5)]
RECIPE = [12, 15, 8, 9, 14, 11, 6]
STOCK = {8: 10, 15: 17, 14: 24, 12: 31, 6: 38, 9: 45, 11: 52}
SLOTS = [(22, 22), (28, 22), (40, 22), (22, 36), (28, 36), (34, 36), (40, 36)]


def grid_of(o):
    if o is None:
        return None
    f = np.array(o.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def act(e, v, x=None, y=None):
    a = {t.value: t for t in e.action_space}
    return e.step(a[6], data={"x": x, "y": y}) if v == 6 else e.step(a[v])


arc = arc_agi.Arcade()
envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
env = arc.make(envs["sb26"].game_id)
obs = env.reset()
for s in L1:
    obs = (act(env, 6, s[1], s[2]) if s[0] == "c" else act(env, s[1]))
assert obs.levels_completed == 1
BASE = env
print("at level 1; base built")
sys.stdout.flush()

# --- soundness check: same assignment, two insertion orders -----------------
def load(e, pairs):
    o = None
    for c, (sx, sy) in pairs:
        o = act(e, 6, STOCK[c], 58)
        o = act(e, 6, sx, sy)
    return o


am = list(zip(RECIPE, SLOTS))
for label, pairs in (("recipe order", am), ("reversed order", am[::-1])):
    e = copy.deepcopy(BASE)
    o = load(e, pairs)
    g = grid_of(o)
    o = act(e, 5)
    g2 = grid_of(o)
    print(f"  soundness {label}: A5 n={int((g != g2).sum())} "
          f"lvl={o.levels_completed}")
sys.stdout.flush()

# --- the search -------------------------------------------------------------
found = None
tried = [0]


def dfs(e, i, used):
    """Place colour RECIPE[i] into each free slot in turn; A5 at depth 7."""
    global found
    if found is not None:
        return
    if i == len(RECIPE):
        tried[0] += 1
        if tried[0] % 240 == 0:
            print(f"  assignments tried: {tried[0]}")
            sys.stdout.flush()
        o = act(e, 5)
        if o is not None and o.levels_completed >= 2:
            found = "leaf"
        return
    for s, slot in enumerate(SLOTS):
        if used & (1 << s):
            continue
        child = copy.deepcopy(e)
        act(child, 6, STOCK[RECIPE[i]], 58)
        o = act(child, 6, slot[0], slot[1])
        if o is None or str(o.state) != "GameState.NOT_FINISHED":
            continue
        path.append((RECIPE[i], slot))
        dfs(child, i + 1, used | (1 << s))
        if found is not None:
            if found == "leaf":
                found = list(path)
            return
        path.pop()


path = []
dfs(copy.deepcopy(BASE), 0, 0)
print(f"assignments tried: {tried[0]}")
if found:
    print("WIN assignment (colour -> slot):")
    for c, slot in found:
        print(f"  {c:2d} -> {slot}")
else:
    print("EXHAUSTED with the recipe insertion order: no assignment wins.")
    print("Either the win test reads the stack, or the recipe/stock reading "
          "is wrong.")
