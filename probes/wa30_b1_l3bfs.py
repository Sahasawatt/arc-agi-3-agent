"""wa30 L3 -- hypothesis-free real-engine BFS from a constructed L3 root (2026-08-17).

Standing closure for L3 is HYPOTHESIS-SCOPED: "the win is not 'empty the
interior' as modelled, or L3 is unwinnable as modelled" -- an arithmetic
argument (5 crates x 16 cells <= 57 < 84 interior cells) plus four reactive
guards, none of which beat control (breadth-recon.md, wa30 L3 sections). No
hypothesis-free search has ever run. Today the same gap closed two levels
(sp80 L3, m0r0 L2) via a plain board-keyed BFS that reads levels_completed
and assumes nothing about what "winning" looks like.

Plan:
  1. Construct the L3 root (levels_completed==2) by driving `haul.py`'s
     `Haul` class from a fresh reset -- it clears L1 and L2 live (haul.py's
     own docstring + wa30-q22.txt say it clears both). Record the action
     sequence taken; that IS the recipe, no replay-from-file needed.
  2. Deepcopy fidelity control (g50t_r1.py / m0r0_b1_l2bfs.py pattern).
  3. Death-reverts-to-root control: run one life out to GAME_OVER and confirm
     the board matches the root board again (breadth-recon.md already
     measured this a=114,214,314... over 28 lives; this is an independent
     one-arm re-check in THIS session before trusting the BFS's GAME_OVER
     pruning).
  4. Real-engine BFS over deepcopy(env) nodes, actions {1,2,3,4,5} (wa30's
     full plain set, no clicks -- results/breadth-recon.md line 3447), keyed
     on raw last-plane frame bytes (wa30 is single-plane per the framestack
     sweep -- not in the 8-game multi-plane list). Depth capped at 100 (the
     life clock) since a life is <=100 actions and lives are equivalent.

    ./.venv/Scripts/python.exe wa30_b1_l3bfs.py > results/wa30-b1-l3bfs.txt
"""
import copy
import pickle
import sys
import time
from collections import deque

import numpy as np
import arc_agi
from arcengine.enums import GameState

from haul import Haul, grid_of as grid

BUDGET_S = 280          # BFS wall-clock cap
MAX_NODES = 6_000       # frontier holds deepcopy(env) nodes (g50t_r1.py/m0r0 pattern) --
                        # CLAUDE.md's own sp80-L3 incident hit 6.3GB at 12k such nodes,
                        # so this cap is deliberately well under that regime
ENGINE_CAP_S = 8 * 60   # stop touching the live engine after this much wall time (foreground run)
DEPTH_CAP = 100          # one life's clock

t_engine0 = time.time()

arc = arc_agi.Arcade()
env = arc.make("wa30")
A = {a.value: a for a in env.action_space}
PLAIN = sorted(a.value for a in env.action_space if not a.is_complex())
CX = sorted(a.value for a in env.action_space if a.is_complex())
print(f"wa30 verbs: plain={PLAIN} complex={CX}", flush=True)
assert not CX, "wa30 is supposed to have no complex actions -- STOP if this fires"

# --- phase 1: construct the L3 root by driving Haul from a fresh reset -----
obs = env.reset()
print(f"root reset: level={obs.levels_completed}, board {grid(obs).shape}")
h = Haul(PLAIN)
recipe = []
i = 0
MAX_DRIVE = 400
while obs.levels_completed < 2 and i < MAX_DRIVE:
    v = h.act(grid(obs), obs.levels_completed)
    if v is None:
        print(f"i={i}: Haul out of ideas at level {obs.levels_completed} "
              f"(levels_completed={obs.levels_completed})")
        break
    obs = env.step(A[v])
    recipe.append(v)
    i += 1
    if obs is None or grid(obs) is None or not str(obs.state).endswith("NOT_FINISHED"):
        if obs is None:
            print("!! engine returned None mid-drive -- STOP")
            sys.exit(1)
        # a life boundary (death) during construction -- Haul's own guard
        # handles the revert bookkeeping; reset() only if truly GAME_OVER
        if str(obs.state) == str(GameState.GAME_OVER):
            print(f"i={i}: GAME_OVER during construction, resetting")
            obs = env.reset()
            recipe = []  # a game reset restarts the whole recipe
            h = Haul(PLAIN)
        continue

print(f"drive finished: i={i} actions, levels_completed={obs.levels_completed}, "
      f"recipe len={len(recipe)}")
if obs.levels_completed < 2:
    print("!! FAILED to construct L3 root within the drive cap -- BLOCKED, "
          "cannot run the BFS")
    print(f"recipe so far: {recipe}")
    sys.exit(1)

print(f"L3 ROOT RECIPE ({len(recipe)} actions): {recipe}")
G0 = grid(obs)
print(f"L3 root board shape={G0.shape}")

# --- phase 2: deepcopy fidelity control -------------------------------------
probe = copy.deepcopy(env)
o1 = probe.step(A[PLAIN[0]])
o2 = env.step(A[PLAIN[0]])
same = np.array_equal(grid(o1), grid(o2))
print(f"CONTROL deepcopy fidelity (same action, copy vs original agree): "
      f"{'PASS' if same else 'FAIL'}")
if not same:
    print("!! deepcopy is not faithful on this game -- BFS below is not evidence")
    sys.exit(1)

# --- re-establish a clean L3 root (env advanced one extra action above) ----
env = arc.make("wa30")
A = {a.value: a for a in env.action_space}
obs = env.reset()
for act in recipe:
    obs = env.step(A[act])
    if obs is None:
        print("!! engine None while replaying recipe -- BLOCKED")
        sys.exit(1)
assert obs.levels_completed == 2, (
    f"recipe replay did not reproduce the L3 root: levels_completed="
    f"{obs.levels_completed}")
print("L3 root recipe replay VERIFIED fresh.")
ROOT = copy.deepcopy(env)
root_key = grid(obs).tobytes()
print(f"L3 root re-established, key len={len(root_key)}")

# --- phase 3: death-reverts-to-root control (one arm) -----------------------
death_env = copy.deepcopy(ROOT)
d_obs = obs
death_action = PLAIN[0]
tries = 0
reverted = None
while tries < DEPTH_CAP + 20:
    d_obs = death_env.step(A[death_action])
    tries += 1
    if d_obs is None:
        print("!! None during death control -- inconclusive")
        break
    if str(d_obs.state) == str(GameState.GAME_OVER):
        # compete.py's own convention: GAME_OVER is answered with reset(),
        # never with another step() -- the engine holds GAME_OVER and hands
        # back empty frames without it (breadth-recon.md, sp80 section).
        # reset() with actions already taken this life scopes to the CURRENT
        # level (CLAUDE.md), so this should land back at the L3 root board.
        after = death_env.reset()
        match = np.array_equal(grid(after), G0)
        print(f"CONTROL death-reverts (GAME_OVER at try={tries}, reset() board "
              f"matches L3 root): {'PASS' if match else 'FAIL'}")
        reverted = match
        break
print(f"death control resolved: reverted={reverted} after {tries} presses of "
      f"action {death_action}")
if reverted is None:
    print("!! death control did not observe a GAME_OVER within DEPTH_CAP+20 "
          "presses -- proceeding, but GAME_OVER pruning below is UNVERIFIED "
          "by this control (cite breadth-recon.md's 28-life measurement instead)")

# --- phase 4: real-engine BFS ------------------------------------------------
MOVES = PLAIN  # {1,2,3,4,5} -- wa30's whole plain action set, no clicks to add
print(f"BFS action set: {MOVES}", flush=True)

CKPT = "results/wa30_b1_ckpt.pkl"
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
    if time.time() - t_engine0 > ENGINE_CAP_S:
        print("!! engine time cap hit, stopping early", flush=True)
        break
    node, path, depth, here_key = q.popleft()
    nodes += 1
    if depth >= DEPTH_CAP:
        continue  # life clock -- no successors beyond the life boundary
    for a in MOVES:
        c = copy.deepcopy(node)
        o = c.step(A[a])
        if o is None:
            continue
        if o.levels_completed >= 3:
            win = path + (a,)
            print(f"*** LEVEL 3 CLEARED, depth {depth + 1}: {win} ***", flush=True)
            q.clear()
            break
        if str(o.state) == str(GameState.GAME_OVER):
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
    if nodes % 250 == 0:
        el = time.time() - t0
        print(f"...expanded={nodes} distinct={len(seen)} frontier={len(q)} "
              f"deaths={deaths} elapsed={el:.1f}s", flush=True)
        if el > BUDGET_S * 0.85:
            with open(CKPT, "wb") as fh:
                pickle.dump({"seen_paths": list(seen.values()),
                             "frontier": [(p, d) for _, p, d, _ in q],
                             "recipe": recipe}, fh)
            print(f"checkpoint written to {CKPT}", flush=True)

el = time.time() - t0
exhausted = (not q) and win is None and el <= BUDGET_S and nodes < MAX_NODES and \
            (time.time() - t_engine0) <= ENGINE_CAP_S
growing = (not exhausted) and win is None

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
    print(f"WIN PATH (recipe + these L3 actions): {win}")
    print(f"FULL SEQUENCE: {recipe + list(win)}")
elif exhausted:
    print("VERDICT: L3's reachable state graph (a single life, actions 1-5, "
          "depth<=100) is EXHAUSTED with no win. Independent, hypothesis-free "
          "cross-check of the arithmetic/reactive-guard closure.")
elif growing and (time.time() - t0) > BUDGET_S * 0.5:
    with open(CKPT, "wb") as fh:
        pickle.dump({"seen_paths": list(seen.values()),
                     "frontier": [(p, d) for _, p, d, _ in q],
                     "recipe": recipe}, fh)
    print(f"VERDICT: GROWING -- checkpoint written to {CKPT}. Resume by "
          f"reloading the pickle's frontier paths and replaying `recipe` then "
          f"each path from a fresh env.")
else:
    print("VERDICT: NOT exhausted -- hit a cap, rules nothing out on its own.")
