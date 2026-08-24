"""tr87 L3 -- BFS with sp80_s11-style chain mechanics: a single global path-frontier
queue (FIFO across ALL depths, not layer-batched), each path replayed from one
in-memory ROOT deepcopy exactly once, on pop (`sp80_s11.py`'s `frontier.popleft()`
+ `replay(seq)` pattern). Same root, same board key (full frame minus row 63, the
budget bar), same 4-verb alphabet, same win/death handling as `tr87_b1_bfs.py`
(`results/tr87-L3-bfs-20260817.md`). b1's flaw was checkpointing only at LAYER
boundaries, which stalls resumability until a whole layer finishes; this pops and
checkpoints as one continuous queue, granular every 2,000 expansions regardless of
depth, and never re-replays a node it has already expanded (each path is replayed
from root exactly once, when it is popped -- not once per layer it survives into).

    ./.venv/Scripts/python.exe tr87_b2_l3chain.py --fresh --budget-seconds 60
    ./.venv/Scripts/python.exe tr87_b2_l3chain.py                       # resume, default 3300s
    ./.venv/Scripts/python.exe tr87_b2_l3chain.py --seed-b1 --fresh     # import b1's frontier
"""
import argparse
import copy
import os
import pickle
import time
from collections import deque

import numpy as np

import arc_agi
from arcengine import GameState

ROOT_ROUTE = [1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 4, 1, 1, 1, 4, 1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1,
              1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 4, 1, 1, 1, 4, 1, 1, 4, 1, 1, 1, 4, 1, 1, 1, 4, 1, 1,
              1, 1]

CKPT_PATH = os.path.join("results", "tr87_b2_ckpt.pkl")
B1_CKPT_PATH = os.path.join("results", "tr87_b1_ckpt.pkl")
WIN_PATH = os.path.join("results", "tr87-b2-win.txt")
CURVE_EVERY = 2000
HEARTBEAT_S = 60


def grid(o):
    if o is None:
        return None
    f = np.array(o.frame)
    return None if f.ndim < 2 or f.size == 0 else f[-1]


def is_over(o):
    if o is None:
        return True
    if np.array(o.frame).size == 0:
        return True
    return o.state == GameState.GAME_OVER


def keyify(g):
    """Full board minus row 63, the confirmed budget bar -- identical to
    tr87_b1_bfs.py's key, not re-derived."""
    g2 = g.copy()
    g2[63] = 0
    return g2.tobytes()


def make_root():
    env = arc_agi.Arcade().make("tr87")
    A = {a.value: a for a in env.action_space}
    plain = sorted(v for v in A if not A[v].is_complex())
    obs = env.reset()
    for v in ROOT_ROUTE:
        obs = env.step(A[v])
    assert obs is not None and obs.levels_completed == 2, f"ROOT FAILED: {obs}"
    print(f"action space (live): plain={plain}", flush=True)
    print(f"ROOT: {len(ROOT_ROUTE)} actions -> levels_completed=2 (L3 entry)", flush=True)
    return env, A, obs


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


def seed_from_b1(root_env, root_frame, A):
    """b1's pickle schema (read directly from tr87_b1_bfs.py, not assumed):
    {frontier: [action-paths], seen_paths: [action-paths], depth, node_count} --
    NO stored state keys, only paths. Import b1's frontier as our own starting
    chain-frontier, and rebuild the state-key `seen` set by replaying every one
    of b1's seen_paths from root ONCE (this is the exact cost the b1 writeup
    flagged as deferred). A path that turns out dead on replay is dropped, not
    trusted -- b1 pruned deaths, so this should never fire, but never assume."""
    if not os.path.exists(B1_CKPT_PATH):
        return None
    with open(B1_CKPT_PATH, "rb") as f:
        d = pickle.load(f)
    seen = set()
    dropped = 0
    t0 = time.time()
    for p in d["seen_paths"]:
        if not p:
            seen.add(keyify(root_frame))
            continue
        e = copy.deepcopy(root_env)
        o, ok = None, True
        for v in p:
            o = e.step(A[v])
            if o is None or is_over(o) or o.levels_completed != 2:
                ok = False
                break
        if not ok:
            dropped += 1
            continue
        g = grid(o)
        if g is None:
            dropped += 1
            continue
        seen.add(keyify(g))
    frontier = deque(tuple(p) for p in d["frontier"])
    print(f"SEED-B1: b1_depth={d['depth']} b1_node_count={d['node_count']} "
          f"imported_frontier={len(frontier)} seen_paths_replayed={len(d['seen_paths'])} "
          f"seen_keys_rebuilt={len(seen)} dropped={dropped} "
          f"replay_time={time.time()-t0:.1f}s", flush=True)
    return frontier, seen


def run_bfs(budget_seconds, fresh, seed_b1):
    root_env, A, root_obs = make_root()
    root_frame = grid(root_obs)

    def replay(seq):
        e = copy.deepcopy(root_env)
        o = root_obs
        for v in seq:
            o = e.step(A[v])
        return e, o

    ckpt = None if fresh else load_checkpoint()
    if ckpt is not None:
        frontier = deque(tuple(p) for p in ckpt["frontier"])
        seen = ckpt["seen"]
        expanded = ckpt["expanded"]
        deaths = ckpt["deaths"]
        divergence = ckpt["divergence"]
        curve = ckpt["curve"]
        replay_time_total = ckpt["replay_time_total"]
        win = ckpt["win"]
        print(f"RESUMED expanded={expanded} states={len(seen)} frontier={len(frontier)} "
              f"deaths={deaths} divergence={divergence}", flush=True)
    else:
        seeded = seed_from_b1(root_env, root_frame, A) if seed_b1 else None
        if seeded is not None:
            frontier, seen = seeded
            seen.add(keyify(root_frame))
        else:
            if seed_b1:
                print("SEED-B1: no b1 checkpoint found, falling back to FRESH START", flush=True)
            seen = {keyify(root_frame)}
            frontier = deque([()])
        expanded = deaths = divergence = 0
        curve = []
        replay_time_total = 0.0
        win = None
        print(f"{'SEED-B1 ' if seeded is not None else 'FRESH '}START "
              f"expanded=0 states={len(seen)} frontier={len(frontier)}", flush=True)

    expanded_at_start = expanded
    replay_time_at_start = replay_time_total
    t0 = time.time()
    last_heartbeat = t0
    stop_reason = None

    def checkpoint_now():
        save_checkpoint(dict(
            frontier=[list(p) for p in frontier], seen=seen, expanded=expanded,
            deaths=deaths, divergence=divergence, curve=curve,
            replay_time_total=replay_time_total, win=win,
        ))

    try:
        while True:
            if win is not None:
                stop_reason = "win"
                break
            if not frontier:
                stop_reason = "exhausted"
                break
            if time.time() - t0 >= budget_seconds:
                stop_reason = "time_budget"
                break

            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_S:
                elapsed = now - t0
                rate = expanded / max(1e-9, elapsed)
                print(f"HEARTBEAT expanded={expanded} states={len(seen)} frontier={len(frontier)} "
                      f"deaths={deaths} divergence={divergence} rate={rate:.2f}/s t={elapsed:.0f}s",
                      flush=True)
                last_heartbeat = now

            seq = frontier.popleft()
            tr0 = time.time()
            node_env, node_obs = replay(seq)
            replay_time_total += time.time() - tr0
            if node_obs is None or is_over(node_obs) or node_obs.levels_completed != 2:
                continue  # defensive -- queued paths should always be live (see docstring)

            for v in (1, 2, 3, 4):
                child = copy.deepcopy(node_env)
                oc = child.step(A[v])
                if is_over(oc):
                    deaths += 1
                    continue
                if oc.levels_completed > 2:
                    win = list(seq) + [v]
                    print(f"WIN: sequence of {len(win)} actions after root: {win}", flush=True)
                    break
                gframe = grid(oc)
                if gframe is None:
                    deaths += 1
                    continue
                k = keyify(gframe)
                if k in seen:
                    divergence += 1
                    continue
                seen.add(k)
                frontier.append(seq + (v,))

            expanded += 1
            if expanded % CURVE_EVERY == 0:
                elapsed = time.time() - t0
                curve.append((expanded, len(seen), len(frontier), elapsed))
                checkpoint_now()
                avg_replay_ms = 1000 * replay_time_total / expanded
                print(f"  CHECKPOINT expanded={expanded} states={len(seen)} "
                      f"frontier={len(frontier)} deaths={deaths} divergence={divergence} "
                      f"avg_replay_ms/node={avg_replay_ms:.2f} t={elapsed:.0f}s", flush=True)
    finally:
        checkpoint_now()

    exhausted = stop_reason == "exhausted"
    win_bool = win is not None
    elapsed = time.time() - t0

    expanded_this_run = expanded - expanded_at_start
    replay_time_this_run = replay_time_total - replay_time_at_start
    print(f"\n== throughput (this invocation) ==", flush=True)
    print(f"stop_reason={stop_reason} expanded_this_run={expanded_this_run} "
          f"expanded_cumulative={expanded} elapsed={elapsed:.0f}s "
          f"replay_time_this_run={replay_time_this_run:.0f}s "
          f"replay_share={100 * replay_time_this_run / max(1e-9, elapsed):.1f}%", flush=True)

    if win is not None:
        full_line = ROOT_ROUTE + list(win)
        print(f"FULL LINE (root + win): {full_line}", flush=True)
        venv = arc_agi.Arcade().make("tr87")
        vA = {a.value: a for a in venv.action_space}
        vo = venv.reset()
        for v in full_line:
            vo = venv.step(vA[v])
        verified = vo is not None and vo.levels_completed >= 3
        lvl = vo.levels_completed if vo is not None else None
        print(f"VERIFY (fresh reset, full replay): levels_completed={lvl} "
              f"(want >=3) verified={verified}", flush=True)
        with open(WIN_PATH, "w") as f:
            f.write(f"win_suffix={win}\n")
            f.write(f"full_line={full_line}\n")
            f.write(f"verified_levels_completed={lvl}\n")
        print(f"WIN file written: {WIN_PATH}", flush=True)
    elif exhausted:
        print(f"EXHAUSTED: {len(seen)} distinct states, expanded={expanded}, no win found.",
              flush=True)
        print(f"NOTE: divergence={divergence} dedup hits observed; collision-divergence "
              "(whether the key ever merges two genuinely different real states) is NOT "
              "independently verified this run -- treat EXHAUSTED as provisional per the "
              "dc22/ka59/sp80 lesson in CLAUDE.md.", flush=True)
    else:
        print(f"GROWING: stopped on {stop_reason}, budget_seconds={budget_seconds}.", flush=True)

    print(f"\nFINAL expanded={expanded} states={len(seen)} frontier={len(frontier)} "
          f"deaths={deaths} divergence={divergence} exhausted={exhausted} win={win_bool}",
          flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-seconds", type=int, default=3300)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--seed-b1", action="store_true")
    args = ap.parse_args()
    run_bfs(args.budget_seconds, args.fresh, args.seed_b1)
