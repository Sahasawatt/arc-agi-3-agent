"""sb26 L5, instrument (a): greedy exact-colour load along the machine path,
the two hollow-9s tried in their two plausible roles, A5 per arm.

Facts from the one dump (results/sb26-l5a.txt): recipe row reads NINE boxes
[6,e,8,8,e,8,8,b,f] over EIGHT slots (five upper y22 at x19/25/31/37/43,
three lower y36 at x25/31/37 inside a colour-9-framed child box), stock is
eight blocks [f,6,8,8,b,e,9h,9h] where 9h is the L4-style hollow block.

Greedy matching collapses two readings into one arm: walking the recipe and
skipping any entry with no stock left (role 9h=8 skips the second e) yields
the SAME placement sequence as reading the middle e as a separator/non-entry
-- the skipped entry consumes no slot. So the four arms are role x splice
order: the child box's centroid (31.5) ties exactly with upper slot x31, so
the machine-path order is ambiguous between child-before-U31 and
child-after-U31 -- a tie L2-L4 never had.

A7 is pressed twice on the fresh board first: the dump showed no filled
slots, but a game pre-load would invalidate every arm (L4 lesson), and two
presses cost nothing.
"""
import copy
import sys

import numpy as np

import arc_agi
from sorter import Sorter

STOCK = {"f": 6, "6": 13, "8a": 20, "8b": 27, "b": 34, "e": 41,
         "9h1": 48, "9h2": 55}
STOCK_Y = 58
U = [(19, 22), (25, 22), (31, 22), (37, 22), (43, 22)]
L = [(25, 36), (31, 36), (37, 36)]

# slot orders: child spliced after U31 vs before U31
ORDER_AFTER = [U[0], U[1], U[2], L[0], L[1], L[2], U[3], U[4]]
ORDER_BEFORE = [U[0], U[1], L[0], L[1], L[2], U[2], U[3], U[4]]

# placement sequences (stock keys, in recipe-greedy order)
SEQ_8 = ["6", "e", "8a", "8b", "9h1", "9h2", "b", "f"]   # 9h = the extra 8s
SEQ_E = ["6", "e", "8a", "8b", "9h1", "b", "f", "9h2"]   # 9h = the extra e;
# only 7 entries match, the leftover 9h2 tops off the last slot.

ARMS = [
    ("9h=8, child after U31", SEQ_8, ORDER_AFTER),
    ("9h=8, child before U31", SEQ_8, ORDER_BEFORE),
    ("9h=e, child after U31", SEQ_E, ORDER_AFTER),
    ("9h=e, child before U31", SEQ_E, ORDER_BEFORE),
]


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
assert obs.levels_completed == 4, f"replay stopped at {obs.levels_completed}"
BASE = env
G_BASE = grid_of(obs)
print(f"at level 5 after {i} driver actions")
sys.stdout.flush()

# --- pre-load check: A7 twice on the fresh board ---------------------------
e = copy.deepcopy(BASE)
for k in range(2):
    o = e.step(A[7])
    g2 = grid_of(o)
    print(f"  fresh A7 #{k + 1}: n={int((g != g2).sum())}")
    g = g2
sys.stdout.flush()

# --- the four arms ---------------------------------------------------------
for label, seq, order in ARMS:
    e = copy.deepcopy(BASE)
    print(f"arm [{label}]")
    prev = G_BASE
    for key, slot in zip(seq, order):
        o = e.step(A[6], data={"x": STOCK[key], "y": STOCK_Y})
        gp = grid_of(o)
        n_pick = int((prev != gp).sum())
        o = e.step(A[6], data={"x": slot[0], "y": slot[1]})
        gd = grid_of(o)
        n_drop = int((gp != gd).sum())
        print(f"  {key:>3} -> {slot}: pick n={n_pick} drop n={n_drop} "
              f"lvl={o.levels_completed}")
        prev = gd
        if str(o.state) != "GameState.NOT_FINISHED":
            print(f"  state={str(o.state).split('.')[-1]}")
            break
    o = e.step(A[5])
    gd = grid_of(o)
    print(f"  A5: n={int((prev != gd).sum())} lvl={o.levels_completed} "
          f"state={str(o.state).split('.')[-1]}")
    if o.levels_completed >= 5:
        print("  ** LEVEL 5 CLEARED **")
        break
    sys.stdout.flush()
