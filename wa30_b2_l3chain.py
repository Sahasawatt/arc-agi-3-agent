"""wa30 L3 -- b1's real-engine BFS converted to the sp80_s11 engineering shape
(2026-08-17): path frontier (no deepcopy(env) nodes held in memory -- b1 hit
a RAM wall around 12k such nodes, capped at 6,000), atomic checkpoint/resume,
--budget-seconds, heartbeat, machine-readable FINAL line.

Root recipe, board key, action set {1,2,3,4,5} and death handling are UNCHANGED
from wa30_b1_l3bfs.py -- only the frontier representation and the run/resume
machinery differ. See results/wa30-b2-engineering-20260817.md for the diff
writeup.

    ./.venv/Scripts/python.exe wa30_b2_l3chain.py --budget-seconds 60 --fresh
    ./.venv/Scripts/python.exe wa30_b2_l3chain.py --budget-seconds 3300
"""
import argparse
import copy
import os
import pickle
import sys
import time
from collections import deque

import numpy as np
import arc_agi
from arcengine.enums import GameState

from haul import Haul, grid_of as grid

MAX_DRIVE = 400          # cap on Haul-driven root construction (b1: same)
DEPTH_CAP = 100          # one life's clock (b1: same)
CURVE_EVERY = 2000       # checkpoint cadence, in expansions (s11 pattern)
HEARTBEAT_S = 60
CKPT_PATH = os.path.join("results", "wa30_b2_ckpt.pkl")
WIN_PATH = os.path.join("results", "wa30-b2-win.txt")


def save_checkpoint(state):
    os.makedirs(os.path.dirname(CKPT_PATH), exist_ok=True)
    tmp = CKPT_PATH + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump(state, f)
    os.replace(tmp, CKPT_PATH)


def load_checkpoint():
    if not os.path.exists(CKPT_PATH):
        return None
    with open(CKPT_PATH, "rb") as f:
        return pickle.load(f)


def make_root():
    """Construct the L3 root by driving Haul from a fresh reset, then run the
    two b1 controls (deepcopy fidelity, death-reverts-to-root). Identical to
    wa30_b1_l3bfs.py phases 1-3 -- reused verbatim, just wrapped as a function
    so run_bfs() can call it once per invocation (fresh or resumed)."""
    arc = arc_agi.Arcade()
    env = arc.make("wa30")
    A = {a.value: a for a in env.action_space}
    PLAIN = sorted(a.value for a in env.action_space if not a.is_complex())
    CX = sorted(a.value for a in env.action_space if a.is_complex())
    print(f"wa30 verbs: plain={PLAIN} complex={CX}", flush=True)
    assert not CX, "wa30 is supposed to have no complex actions -- STOP if this fires"

    # --- phase 1: construct the L3 root by driving Haul from a fresh reset --
    obs = env.reset()
    print(f"root reset: level={obs.levels_completed}, board {grid(obs).shape}", flush=True)
    h = Haul(PLAIN)
    recipe = []
    i = 0
    while obs.levels_completed < 2 and i < MAX_DRIVE:
        v = h.act(grid(obs), obs.levels_completed)
        if v is None:
            print(f"i={i}: Haul out of ideas at level {obs.levels_completed}", flush=True)
            break
        obs = env.step(A[v])
        recipe.append(v)
        i += 1
        if obs is None or grid(obs) is None or not str(obs.state).endswith("NOT_FINISHED"):
            if obs is None:
                print("!! engine returned None mid-drive -- STOP", flush=True)
                sys.exit(1)
            if str(obs.state) == str(GameState.GAME_OVER):
                print(f"i={i}: GAME_OVER during construction, resetting", flush=True)
                obs = env.reset()
                recipe = []
                h = Haul(PLAIN)
            continue

    print(f"drive finished: i={i} actions, levels_completed={obs.levels_completed}, "
          f"recipe len={len(recipe)}", flush=True)
    if obs.levels_completed < 2:
        print("!! FAILED to construct L3 root within the drive cap -- BLOCKED", flush=True)
        sys.exit(1)
    print(f"L3 ROOT RECIPE ({len(recipe)} actions): {recipe}", flush=True)
    G0 = grid(obs)

    # --- phase 2: deepcopy fidelity control ---------------------------------
    probe = copy.deepcopy(env)
    o1 = probe.step(A[PLAIN[0]])
    o2 = env.step(A[PLAIN[0]])
    same = np.array_equal(grid(o1), grid(o2))
    print(f"CONTROL deepcopy fidelity: {'PASS' if same else 'FAIL'}", flush=True)
    if not same:
        print("!! deepcopy is not faithful on this game -- BFS below is not evidence", flush=True)
        sys.exit(1)

    # --- re-establish a clean L3 root ---------------------------------------
    env = arc.make("wa30")
    A = {a.value: a for a in env.action_space}
    obs = env.reset()
    for act in recipe:
        obs = env.step(A[act])
        if obs is None:
            print("!! engine None while replaying recipe -- BLOCKED", flush=True)
            sys.exit(1)
    assert obs.levels_completed == 2, (
        f"recipe replay did not reproduce the L3 root: levels_completed={obs.levels_completed}")
    print("L3 root recipe replay VERIFIED fresh.", flush=True)
    ROOT = copy.deepcopy(env)
    root_key = grid(obs).tobytes()

    # --- phase 3: death-reverts-to-root control (one arm) -------------------
    death_env = copy.deepcopy(ROOT)
    death_action = PLAIN[0]
    tries = 0
    reverted = None
    while tries < DEPTH_CAP + 20:
        d_obs = death_env.step(A[death_action])
        tries += 1
        if d_obs is None:
            print("!! None during death control -- inconclusive", flush=True)
            break
        if str(d_obs.state) == str(GameState.GAME_OVER):
            after = death_env.reset()
            match = np.array_equal(grid(after), G0)
            print(f"CONTROL death-reverts (try={tries}): {'PASS' if match else 'FAIL'}", flush=True)
            reverted = match
            break
    if reverted is None:
        print("!! death control did not observe GAME_OVER within cap -- proceeding "
              "UNVERIFIED (cite breadth-recon.md's 28-life measurement instead)", flush=True)

    return A, PLAIN, recipe, ROOT, root_key


def run_bfs(budget_seconds, fresh):
    A, MOVES, recipe, ROOT, root_key = make_root()
    print(f"BFS action set: {MOVES}", flush=True)

    def replay(path):
        e = copy.deepcopy(ROOT)
        for a in path:
            e.step(A[a])
        return e

    ckpt = None if fresh else load_checkpoint()
    if ckpt is not None:
        frontier = deque(ckpt["frontier"])
        seen = ckpt["seen"]
        expanded = ckpt["expanded"]
        deaths = ckpt["deaths"]
        divergence = ckpt["divergence"]
        outcomes = ckpt["outcomes"]
        win = ckpt["win"]
        print(f"RESUMED expanded={expanded} states={len(seen)} frontier={len(frontier)} "
              f"deaths={deaths} divergence={len(divergence)}", flush=True)
    else:
        frontier = deque([((), root_key)])
        seen = {root_key}
        expanded = deaths = 0
        divergence = []
        outcomes = {}
        win = None
        print("FRESH START", flush=True)

    def checkpoint_now():
        save_checkpoint(dict(
            frontier=list(frontier), seen=seen, expanded=expanded, deaths=deaths,
            divergence=divergence, outcomes=outcomes, win=win, recipe=recipe,
        ))

    t0 = time.time()
    last_heartbeat = t0

    try:
        while frontier and win is None and time.time() - t0 < budget_seconds:
            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_S:
                elapsed = now - t0
                rate = expanded / max(1e-9, elapsed)
                print(f"HEARTBEAT expanded={expanded} states={len(seen)} frontier={len(frontier)} "
                      f"deaths={deaths} divergence={len(divergence)} rate={rate:.2f}/s "
                      f"t={elapsed:.0f}s", flush=True)
                last_heartbeat = now

            path, here_key = frontier.popleft()
            expanded += 1
            if len(path) >= DEPTH_CAP:
                continue  # life clock -- no successors beyond the life boundary

            node_env = replay(path)
            for a in MOVES:
                c = copy.deepcopy(node_env)
                o = c.step(A[a])
                if o is None:
                    continue
                if o.levels_completed >= 3:
                    win = list(path) + [a]
                    print(f"*** LEVEL 3 CLEARED, depth {len(path) + 1}: {win} ***", flush=True)
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
                seen.add(k)
                frontier.append((tuple(path) + (a,), k))
            if win is not None:
                break

            if expanded % CURVE_EVERY == 0:
                checkpoint_now()
                print(f"  CURVE expanded={expanded} states={len(seen)} frontier={len(frontier)} "
                      f"deaths={deaths} divergence={len(divergence)} t={time.time() - t0:.0f}s "
                      f"CHECKPOINTED", flush=True)
    finally:
        checkpoint_now()

    exhausted = (not frontier) and win is None
    elapsed = time.time() - t0

    print(f"\nnodes expanded : {expanded}")
    print(f"distinct boards: {len(seen)}")
    print(f"frontier left  : {len(frontier)}")
    print(f"deaths         : {deaths}")
    print(f"elapsed        : {elapsed:.1f}s of {budget_seconds}s budget")
    print(f"divergence (same board+action giving different results): {len(divergence)} cases")
    if divergence:
        print(f"  sample: {divergence[:5]}")

    if win is not None:
        full_seq = recipe + list(win)
        print(f"WIN: seq={win}", flush=True)
        print(f"FULL SEQUENCE (recipe + L3 win): {full_seq}", flush=True)
        os.makedirs(os.path.dirname(WIN_PATH), exist_ok=True)
        with open(WIN_PATH, "w") as f:
            f.write(f"L3 win path (from L3 root): {win}\n")
            f.write(f"L3 root recipe: {recipe}\n")
            f.write(f"FULL SEQUENCE (recipe + L3 win): {full_seq}\n")
        print(f"win written to {WIN_PATH}", flush=True)

    print(f"\nFINAL expanded={expanded} states={len(seen)} frontier={len(frontier)} "
          f"deaths={deaths} divergence={len(divergence)} exhausted={exhausted} "
          f"win={win is not None}", flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-seconds", type=int, default=3300)
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()
    run_bfs(args.budget_seconds, args.fresh)
