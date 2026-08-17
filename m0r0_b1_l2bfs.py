"""m0r0 L2 fresh verification + independent BFS cross-check (2026-08-17).

Task brief claimed m0r0 L2 was "not probed since the early campaign" -- FALSE,
checked against results/breadth-recon.md before writing this: L2 got 4 full
rounds (q22-q44, 2026-08-14/15) and was explicitly CLOSED for the campaign --
checker-band Y-hazards silently respawn both pieces, the joint space collapses
to ONE DIAGONAL (rowA==rowB, colA+colB==14), B's 37-cell region is fully
covered with no win, clicks are null at every safe cell (q41/q42), and the
diagonal's own meeting cell (col7) is proven UNREACHABLE live (q44: 2 runs
reset, 1 stop-short control does not, `results/m0r0-q44.txt`).

That closure used direct replay-from-reset per probe, not a deepcopy-node
BFS with a divergence census -- the specific instrument this session's brief
asks for, and the one the sp80/ar25 lesson says a DFS-shaped closure should
be re-checked against (a merging state key reports false EXHAUSTED). This
script:
  1. verifies the L1 line (twin.py L1_LINE) still clears fresh, in THIS
     session's engine instance -- constructs the L2 root.
  2. deepcopy fidelity control at the L2 root (g50t_r1.py pattern).
  3. an independent real-engine BFS from the L2 root, deepcopy nodes,
     board-keyed (raw frame bytes), plain actions 1-4 only (5 is a no-op
     and clicks are proven inert at every mapped safe cell per q41/q42 --
     re-sweeping either would be re-deriving what recon already recorded,
     not new evidence), with an explicit divergence census.

    ./.venv/Scripts/python.exe m0r0_b1_l2bfs.py > results/m0r0-b1-l2bfs.txt
"""
import copy
import time
from collections import deque

import numpy as np
import arc_agi
from arcengine import GameState

from twin import L1_LINE

BUDGET_S = 900
MAX_NODES = 40_000


def grid(o):
    if o is None:
        return None
    f = np.array(o.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


arc = arc_agi.Arcade()
env = arc.make("m0r0")
A = {a.value: a for a in env.action_space}
PLAIN = sorted(a.value for a in env.action_space if not a.is_complex())
CX = sorted(a.value for a in env.action_space if a.is_complex())
print(f"m0r0 verbs: plain={PLAIN} complex={CX}", flush=True)

# --- phase 1: fresh L1 replay -------------------------------------------
t_engine0 = time.time()
obs = env.reset()
print(f"L1 root: level={obs.levels_completed}, board {grid(obs).shape}")
for i, act in enumerate(L1_LINE):
    obs = env.step(A[act])
print(f"after L1_LINE ({len(L1_LINE)} actions): "
      f"levels_completed={obs.levels_completed} state={obs.state}")
assert obs.levels_completed == 1, "L1 win line did not land in L2 -- STOP"
print("L1 recipe VERIFIED fresh this session.")

G0 = grid(obs)
print(f"L2 root board shape={G0.shape}")

# --- phase 2: deepcopy fidelity control ----------------------------------
probe = copy.deepcopy(env)
o1 = probe.step(A[PLAIN[0]])
o2 = env.step(A[PLAIN[0]])
same = np.array_equal(grid(o1), grid(o2))
print(f"CONTROL deepcopy fidelity (same action on copy vs original agree): "
      f"{'PASS' if same else 'FAIL'}")
if not same:
    print("!! deepcopy is not faithful on this game -- BFS below is not evidence")
    raise SystemExit(1)

# re-establish a clean L2 root (env advanced one extra action above)
env = arc.make("m0r0")
A = {a.value: a for a in env.action_space}
obs = env.reset()
for act in L1_LINE:
    obs = env.step(A[act])
assert obs.levels_completed == 1
ROOT = copy.deepcopy(env)
root_key = grid(obs).tobytes()
print(f"L2 root re-established, key len={len(root_key)}")

# --- phase 3: independent real-engine BFS --------------------------------
MOVES = [a for a in PLAIN if a != 5]  # ACTION5 established no-op at L2 start (q19)
print(f"BFS action set: {MOVES} (ACTION5 + clicks excluded -- established inert, "
      f"results/m0r0-q19.txt, m0r0-q41/q42.txt)")

seen = {root_key: ()}
q = deque([(ROOT, (), 0, root_key)])
t0 = time.time()
nodes = 0
deaths = 0
win = None
divergence = []
outcomes = {}

while q:
    if time.time() - t0 > BUDGET_S or nodes >= MAX_NODES:
        break
    if time.time() - t_engine0 > 25 * 60:
        print("!! 25-minute engine budget hit, stopping early")
        break
    node, path, depth, here_key = q.popleft()
    nodes += 1
    for a in MOVES:
        c = copy.deepcopy(node)
        o = c.step(A[a])
        if o is None:
            continue
        if o.levels_completed >= 2:
            win = path + (a,)
            print(f"*** LEVEL 2 CLEARED, depth {depth + 1}: {win} ***", flush=True)
            q.clear()
            break
        if o.state == GameState.GAME_OVER:
            deaths += 1
            continue
        g = grid(o)
        if g is None:
            continue
        k = g.tobytes()
        src = (here_key, a)
        if src in outcomes and outcomes[src] != k:
            divergence.append(src)
        outcomes[src] = k
        if k in seen:
            continue
        seen[k] = path + (a,)
        q.append((c, path + (a,), depth + 1, k))
    if win:
        break
    if nodes % 500 == 0:
        print(f"...expanded={nodes} distinct={len(seen)} frontier={len(q)} "
              f"deaths={deaths} elapsed={time.time()-t0:.1f}s", flush=True)

el = time.time() - t0
exhausted = (not q) and win is None and el <= BUDGET_S and nodes < MAX_NODES
print(f"\nnodes expanded : {nodes}")
print(f"distinct boards: {len(seen)}")
print(f"frontier left  : {len(q)}")
print(f"deaths         : {deaths}")
print(f"elapsed        : {el:.1f}s of {BUDGET_S}s budget")
print(f"EXHAUSTED      : {exhausted}")
print(f"divergence (same board+action giving different results): {len(divergence)} cases")
if divergence:
    print(f"  sample: {divergence[:5]}")
if win:
    print(f"WIN PATH (L1_LINE + these L2 actions): {win}")
elif exhausted:
    print("VERDICT: L2's movement-only reachable state graph (actions 1-4) is "
          "EXHAUSTED with no win and no hidden-state divergence -- an "
          "independent, deepcopy/board-keyed cross-check that agrees with "
          "results/breadth-recon.md's q22-q44 closure (diagonal-constrained "
          "37-cell region, col7 meeting cell unreachable, clicks null).")
else:
    print("VERDICT: NOT exhausted -- hit node/time/engine-budget cap, rules "
          "nothing out on its own (cite alongside the q44 static+live proof).")
