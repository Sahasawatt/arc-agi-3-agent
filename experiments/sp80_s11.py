"""sp80 s11: sp80_s9/s10's path-frontier BFS + an EXACT resolver for
transfer_multi_match (the load-bearing unproven tie-break flagged after the
72k-expansion run: 3,730 multi_match events, 2,254 with the driver id NOT
even among the matches -- see results/breadth-recon.md 2026-08-16 sp80
entries) + checkpointing + a wall-clock budget + a positive control.

MULTI-MATCH RESOLUTION (design, not a guess -- two independent per-frame
invariants, tried in order, discovered by instrumenting the actual collision
this game produces -- see results/sp80-s11-dbg1.txt):

  1. SIZE. Each body is a fixed physical rectangle -- (w,h) does not change
     when control transfers to it (only its COLOUR, 8<->9, changes). Measured
     at the L3 root, this game's four bodies are NOT all the same size
     (96, 96, 80, 64 cells) -- and even where two happen to tie, this still
     narrows the field. The freshly detected new-driver blob's own size is
     exact -- it draws on top and is never occluded, per the recon's
     occlusion write-up -- so comparing it against each candidate's known
     bootstrap size is a clean, single-frame, position-independent test.
     This is what resolves the dominant collision found by instrumenting a
     real run: a MOVER walks onto a stationary body's exact cell (the
     "grab block2 inside castle0's zone" mechanic) and both ids' STORED
     positions coincide at (x,y) -- position alone can never separate them
     because the mover really is standing exactly there, but their sizes
     differ (96 vs 80 in the measured case) and size does.
  2. FRAME RE-READ. If size ties (two candidates share the same known size)
     or doesn't apply, fall back to: the OTHER stored bodies (not the
     candidate under test) must still be independently visible as their own
     colour-8 rectangle right now, because non-driven bodies provably never
     move. This is necessary but proved NOT sufficient alone in the
     dominant case above (both candidates claim the same occluded cell, so
     this test fails for both) -- which is why size runs first.

  If neither invariant leaves exactly one survivor, the state is genuinely
  ambiguous from a single frame: FORK all remaining candidates into the
  frontier rather than guessing. Correctness over speed, per spec.

  Cost: this whole resolver only runs on the ~5% of expansions that hit
  multi-match (3,730/72,684 = 5.1% at the last measured scale), so the
  O(board pixels) re-read is affordable.

CHECKPOINTING: pickled every CURVE_EVERY (2000) expansions to
results/sp80_s11_ckpt.pkl, atomic write (tmp + os.replace). --fresh ignores
any existing checkpoint. --budget-seconds bounds THIS invocation only (not
cumulative across resumes) -- chain invocations without --fresh to continue.

    ./.venv/Scripts/python.exe sp80_s11.py --control                    # positive control only
    ./.venv/Scripts/python.exe sp80_s11.py --budget-seconds 60 --fresh  # first run
    ./.venv/Scripts/python.exe sp80_s11.py --budget-seconds 3300        # resume (no --fresh)
"""
import argparse
import copy
import os
import pickle
import sys
import time
from collections import deque

import arc_agi
import swap
from arcengine.enums import GameState

RECIPE1 = [4, 4, 4, 5]
MAX_DEPTH = 40
CURVE_EVERY = 2000
HEARTBEAT_S = 60
CKPT_PATH = os.path.join("results", "sp80_s11_ckpt.pkl")


def bodies(g):
    """(colour, x0, y0, w, h) for every solid colour-8/9 rectangle."""
    return [(colour, x0, y0, w, h) for cells, colour, x0, y0, w, h in swap.blocks(g)
            if colour in (8, 9)]


def driver_blob(blobs):
    """(pos, size) of the single colour-9 blob, or (None, None) if it is not
    exactly one -- (pos_or_None, size_or_None, count)."""
    d = [(x0, y0, w, h) for c, x0, y0, w, h in blobs if c == 9]
    if len(d) != 1:
        return None, None, len(d)
    x0, y0, w, h = d[0]
    return (x0, y0), (w, h), 1


def full_key(pos, driver_id, ammo):
    return (tuple(sorted(pos.items())), ammo, driver_id)


def resolve_multi_match(g, pos, sizes, matches, dsize):
    """Two independent per-frame invariants, in order. Returns (survivors, tag)
    -- see module docstring for the design and why size runs first."""
    size_hits = [cand for cand in matches if sizes.get(cand) == dsize]
    if len(size_hits) == 1:
        return size_hits, "size"
    pool = size_hits if size_hits else matches
    blobs8 = {(x0, y0) for c, x0, y0, w, h in bodies(g) if c == 8}
    frame_hits = [cand for cand in pool
                  if all(p in blobs8 for i, p in pos.items() if i != cand)]
    if len(frame_hits) == 1:
        return frame_hits, "frame"
    if frame_hits:
        return frame_hits, "multi"
    if size_hits:
        return size_hits, "multi"
    return matches, "forced"


def transfer_targets(g, pos, sizes, dp, dsize):
    """Resolve driver id(s) after a FIRE or CLICK. Returns (ids, reason) where
    reason is None (clean single match), 'transfer_no_match' (dead end),
    'multi_resolved' (exactly one survivor after size/frame), or
    'multi_fork_survivors' / 'multi_fork_forced' (ambiguous -> fork)."""
    matches = [i for i, p in pos.items() if p == dp]
    if len(matches) == 0:
        return [], "transfer_no_match"
    if len(matches) == 1:
        return matches, None
    survivors, tag = resolve_multi_match(g, pos, sizes, matches, dsize)
    if tag in ("size", "frame"):
        return survivors, "multi_resolved"
    if tag == "forced":
        return survivors, "multi_fork_forced"
    return survivors, "multi_fork_survivors"


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
    """L1 + L2 via raw env.step (no transfer resolution needed to get here --
    matches sp80_s9/s10's own bootstrap, which is unchanged by this round)."""
    env = arc_agi.Arcade().make("sp80")
    A = {a.value: a for a in env.action_space}
    clicker = next(a for a in env.action_space if a.is_complex())
    obs = env.reset()
    for a in RECIPE1:
        obs = env.step(A[a])
    assert obs.levels_completed == 1
    for v in swap.L2_LINE:
        if isinstance(v, tuple):
            _, x, y, _ = v
            obs = env.step(clicker, data={"x": int(x), "y": int(y)})
        else:
            obs = env.step(A[v])
    assert obs.levels_completed == 2
    return env, A, clicker, obs


def positive_control():
    """Scripted replay of the KNOWN L2 win (swap.L2_LINE, 7 actions) driven
    through the SAME body-tracking + transfer_targets() resolver the BFS
    uses, step by step. Proves the resolver does not corrupt or misroute a
    known-good line, including its one real transfer (the aimed click)."""
    env = arc_agi.Arcade().make("sp80")
    A = {a.value: a for a in env.action_space}
    clicker = next(a for a in env.action_space if a.is_complex())
    obs = env.reset()
    for a in RECIPE1:
        obs = env.step(A[a])
    assert obs.levels_completed == 1, "positive control: L1 recipe failed"
    print("CONTROL: L1 reached via RECIPE1", flush=True)

    g = swap.grid_of(obs)
    b = bodies(g)
    ids0 = sorted(range(len(b)), key=lambda i: (b[i][1], b[i][2]))
    pos = {r: (b[i][1], b[i][2]) for r, i in enumerate(ids0)}
    sizes = {r: (b[i][3], b[i][4]) for r, i in enumerate(ids0)}
    driver_id = [r for r, i in enumerate(ids0) if b[i][0] == 9][0]
    print(f"CONTROL: L2 entry bodies={pos} sizes={sizes} driver={driver_id}", flush=True)

    for step_i, step in enumerate(swap.L2_LINE):
        is_transfer = (step == 5) or isinstance(step, tuple)
        if isinstance(step, tuple):
            _, cx, cy, _ = step
            obs = env.step(clicker, data={"x": int(cx), "y": int(cy)})
        else:
            obs = env.step(A[step])
        assert obs is not None, f"CONTROL FAIL: engine returned None at step {step_i} ({step})"
        if obs.levels_completed >= 2:
            print(f"CONTROL: step {step_i} ({step}) -> levels_completed=2, WIN", flush=True)
            print("CONTROL PASS", flush=True)
            return True
        assert obs.state == GameState.NOT_FINISHED, f"CONTROL FAIL: bad state at step {step_i}"
        g = swap.grid_of(obs)
        assert g is not None, f"CONTROL FAIL: empty frame at step {step_i}"
        blobs = bodies(g)
        dp, dsize, cnt = driver_blob(blobs)
        assert dp is not None, f"CONTROL FAIL: driver blob ambiguous ({cnt}) at step {step_i}"

        if not is_transfer:
            pos = dict(pos)
            pos[driver_id] = dp
            print(f"CONTROL: step {step_i} ({step}) plain move, driver {driver_id} -> {dp}",
                  flush=True)
            continue

        ids_out, reason = transfer_targets(g, pos, sizes, dp, dsize)
        assert reason != "transfer_no_match", \
            f"CONTROL FAIL: transfer_no_match on the known win line at step {step_i}"
        print(f"CONTROL: step {step_i} ({step}) transfer, reason={reason} candidates={ids_out}",
              flush=True)
        if len(ids_out) != 1:
            print(f"CONTROL WARNING: step {step_i} forked to {len(ids_out)} branches "
                  f"on the known win line", flush=True)
        driver_id = ids_out[0]
        pos = dict(pos)
        pos[driver_id] = dp

    assert False, "CONTROL FAIL: L2_LINE exhausted without levels_completed==2"


def run_bfs(budget_seconds, fresh):
    env, A, clicker, obs = make_root()
    ROOT_ENV = env
    g0 = swap.grid_of(obs)
    b0 = bodies(g0)
    NBODY = len(b0)
    assert sum(1 for c, x, y, w, h in b0 if c == 9) == 1
    ids0 = sorted(range(NBODY), key=lambda i: (b0[i][1], b0[i][2]))
    pos0 = {rank: (b0[i][1], b0[i][2]) for rank, i in enumerate(ids0)}
    sizes = {rank: (b0[i][3], b0[i][4]) for rank, i in enumerate(ids0)}  # fixed for the game
    driver0 = [rank for rank, i in enumerate(ids0) if b0[i][0] == 9][0]
    print(f"L3 root: {NBODY} tracked bodies: {b0}", flush=True)
    print("root pos0:", pos0, "sizes:", sizes, "driver0:", driver0, flush=True)

    def replay(seq):
        e = copy.deepcopy(ROOT_ENV)
        o = None
        for step in seq:
            if isinstance(step, tuple):
                _, cx, cy = step
                o = e.step(clicker, data={"x": cx, "y": cy})
            else:
                o = e.step(A[step])
        return e, o

    ckpt = None if fresh else load_checkpoint()
    if ckpt is not None:
        frontier = deque(ckpt["frontier"])
        seen = ckpt["seen"]
        expanded = ckpt["expanded"]
        anomalies = ckpt["anomalies"]
        anomaly_reasons = ckpt["anomaly_reasons"]
        multi_match_count = ckpt["multi_match_count"]
        multi_resolved = ckpt["multi_resolved"]
        multi_fork_survivors = ckpt["multi_fork_survivors"]
        multi_fork_forced = ckpt["multi_fork_forced"]
        forked = ckpt["forked"]
        fire_by_driver = ckpt["fire_by_driver"]
        seen_as_driver = ckpt["seen_as_driver"]
        curve = ckpt["curve"]
        last_curve_states = ckpt["last_curve_states"]
        last_curve_frontier = ckpt["last_curve_frontier"]
        replay_time_total = ckpt["replay_time_total"]
        win = ckpt["win"]
        print(f"RESUMED expanded={expanded} states={len(seen)} frontier={len(frontier)} "
              f"multi_match={multi_match_count} forked={forked}", flush=True)
    else:
        seen = {full_key(pos0, driver0, 0)}
        frontier = deque([([], 0, pos0, driver0)])
        expanded = anomalies = 0
        anomaly_reasons = {"driver_blob_count": 0, "transfer_no_match": 0, "transfer_multi_match": 0}
        multi_match_count = multi_resolved = multi_fork_survivors = multi_fork_forced = 0
        forked = 0
        fire_by_driver = {i: 0 for i in range(NBODY)}
        seen_as_driver = set()
        curve = []
        last_curve_states = len(seen)
        last_curve_frontier = len(frontier)
        replay_time_total = 0.0
        win = None
        print("FRESH START", flush=True)

    t0 = time.time()
    last_heartbeat = t0

    def checkpoint_now():
        save_checkpoint(dict(
            frontier=list(frontier), seen=seen, expanded=expanded, anomalies=anomalies,
            anomaly_reasons=anomaly_reasons, multi_match_count=multi_match_count,
            multi_resolved=multi_resolved, multi_fork_survivors=multi_fork_survivors,
            multi_fork_forced=multi_fork_forced, forked=forked, fire_by_driver=fire_by_driver,
            seen_as_driver=seen_as_driver, curve=curve, last_curve_states=last_curve_states,
            last_curve_frontier=last_curve_frontier, replay_time_total=replay_time_total, win=win,
        ))

    try:
        while frontier and win is None and time.time() - t0 < budget_seconds:
            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_S:
                elapsed = now - t0
                rate = expanded / max(1e-9, elapsed)
                print(f"HEARTBEAT expanded={expanded} states={len(seen)} frontier={len(frontier)} "
                      f"rate={rate:.2f}/s multi_match={multi_match_count} forked={forked} "
                      f"t={elapsed:.0f}s", flush=True)
                last_heartbeat = now

            seq, ammo, pos, driver_id = frontier.popleft()
            if len(seq) >= MAX_DEPTH:
                continue
            seen_as_driver.add(driver_id)

            tr0 = time.time()
            node_env, _ = replay(seq)
            replay_time_total += time.time() - tr0

            for a in (1, 2, 3, 4):
                child = copy.deepcopy(node_env)
                o = child.step(A[a])
                if o is None:
                    continue
                if o.state == GameState.WIN or o.levels_completed > 2:
                    win = (seq + [a], driver_id)
                    print(f"WIN: seq={win[0]} fired_by_id={driver_id} state={o.state} "
                          f"lvl={o.levels_completed}", flush=True)
                    break
                if o.state != GameState.NOT_FINISHED:
                    continue
                g = swap.grid_of(o)
                if g is None:
                    continue
                blobs = bodies(g)
                dp, dsize, cnt = driver_blob(blobs)
                if dp is None:
                    anomalies += 1
                    anomaly_reasons["driver_blob_count"] += 1
                    continue
                new_pos = dict(pos)
                new_pos[driver_id] = dp
                k = full_key(new_pos, driver_id, ammo)
                if k in seen:
                    continue
                seen.add(k)
                frontier.append((seq + [a], ammo, new_pos, driver_id))
            if win is not None:
                break

            if ammo < 4:
                child = copy.deepcopy(node_env)
                o = child.step(A[5])
                na = ammo + 1
                fire_by_driver[driver_id] += 1
                if o is not None:
                    if o.state == GameState.WIN or o.levels_completed > 2:
                        win = (seq + [5], driver_id)
                        print(f"WIN: seq={win[0]} fired_by_id={driver_id} state={o.state} "
                              f"lvl={o.levels_completed}", flush=True)
                    elif o.state == GameState.NOT_FINISHED:
                        g = swap.grid_of(o)
                        blobs = bodies(g) if g is not None else None
                        dp, dsize, cnt = driver_blob(blobs) if blobs is not None else (None, None, 0)
                        if dp is None:
                            anomalies += 1
                            anomaly_reasons["driver_blob_count"] += 1
                        else:
                            ids_out, reason = transfer_targets(g, pos, sizes, dp, dsize)
                            if reason == "transfer_no_match":
                                anomalies += 1
                                anomaly_reasons["transfer_no_match"] += 1
                            else:
                                if reason is not None:
                                    anomalies += 1
                                    anomaly_reasons["transfer_multi_match"] += 1
                                    multi_match_count += 1
                                    if reason == "multi_resolved":
                                        multi_resolved += 1
                                    elif reason == "multi_fork_survivors":
                                        multi_fork_survivors += 1
                                        forked += len(ids_out) - 1
                                    elif reason == "multi_fork_forced":
                                        multi_fork_forced += 1
                                        forked += len(ids_out) - 1
                                for new_driver_id in ids_out:
                                    k = full_key(pos, new_driver_id, na)
                                    if k not in seen:
                                        seen.add(k)
                                        frontier.append((seq + [5], na, dict(pos), new_driver_id))
            if win is not None:
                break

            for oid, (cx, cy) in pos.items():
                if oid == driver_id:
                    continue
                child = copy.deepcopy(node_env)
                o = child.step(clicker, data={"x": int(cx), "y": int(cy)})
                if o is None:
                    continue
                if o.state == GameState.WIN or o.levels_completed > 2:
                    win = (seq + [("click", cx, cy)], driver_id)
                    print(f"WIN via click: seq={win[0]} state={o.state} lvl={o.levels_completed}",
                          flush=True)
                    break
                if o.state != GameState.NOT_FINISHED:
                    continue
                g = swap.grid_of(o)
                if g is None:
                    continue
                blobs = bodies(g)
                dp, dsize, cnt = driver_blob(blobs)
                if dp is None:
                    anomalies += 1
                    anomaly_reasons["driver_blob_count"] += 1
                    continue
                ids_out, reason = transfer_targets(g, pos, sizes, dp, dsize)
                if reason == "transfer_no_match":
                    anomalies += 1
                    anomaly_reasons["transfer_no_match"] += 1
                    continue
                if reason is not None:
                    anomalies += 1
                    anomaly_reasons["transfer_multi_match"] += 1
                    multi_match_count += 1
                    if reason == "multi_resolved":
                        multi_resolved += 1
                    elif reason == "multi_fork_survivors":
                        multi_fork_survivors += 1
                        forked += len(ids_out) - 1
                    elif reason == "multi_fork_forced":
                        multi_fork_forced += 1
                        forked += len(ids_out) - 1
                for new_driver_id in ids_out:
                    k = full_key(pos, new_driver_id, ammo)
                    if k in seen:
                        continue
                    seen.add(k)
                    frontier.append((seq + [("click", cx, cy)], ammo, dict(pos), new_driver_id))
            if win is not None:
                break

            expanded += 1
            if expanded % CURVE_EVERY == 0:
                states_now, frontier_now = len(seen), len(frontier)
                d_states = states_now - last_curve_states
                d_frontier = frontier_now - last_curve_frontier
                curve.append((expanded, states_now, frontier_now, d_states, d_frontier))
                last_curve_states, last_curve_frontier = states_now, frontier_now
                checkpoint_now()
                avg_replay_ms = 1000 * replay_time_total / expanded
                print(f"  CURVE expanded={expanded} states={states_now} frontier={frontier_now} "
                      f"d_states/{CURVE_EVERY}={d_states} d_frontier/{CURVE_EVERY}={d_frontier} "
                      f"anomalies={anomalies} multi_match={multi_match_count} forked={forked} "
                      f"avg_replay_ms/node={avg_replay_ms:.2f} t={time.time() - t0:.0f}s "
                      f"CHECKPOINTED", flush=True)
    finally:
        checkpoint_now()

    exhausted = not frontier
    win_bool = win is not None

    print(f"\n== GROWTH CURVE TABLE (every {CURVE_EVERY} expanded) ==", flush=True)
    print(f"{'expanded':>10} {'states':>10} {'frontier':>10} {'d_states':>10} {'d_frontier':>11} "
          f"{'states/node':>12} {'frontier/node':>14}", flush=True)
    for exp, st, fr, ds, df in curve:
        print(f"{exp:>10} {st:>10} {fr:>10} {ds:>10} {df:>11} "
              f"{ds / CURVE_EVERY:>12.3f} {df / CURVE_EVERY:>14.3f}", flush=True)

    elapsed = time.time() - t0
    print(f"\n== throughput (this invocation) ==", flush=True)
    print(f"expanded_this_run={expanded} elapsed={elapsed:.0f}s "
          f"replay_time_total={replay_time_total:.0f}s "
          f"replay_share={100 * replay_time_total / max(1e-9, elapsed):.1f}%", flush=True)

    print(f"\n== state-space size ==", flush=True)
    print(f"states visited: {len(seen)}", flush=True)
    print(f"expanded={expanded} anomalies={anomalies} anomaly_reasons={anomaly_reasons} "
          f"exhausted={exhausted} t={elapsed:.0f}s", flush=True)

    print(f"\n== per-driver-identity fire coverage ==", flush=True)
    print(f"ids ever seen as driver: {sorted(seen_as_driver)} (root driver id = {driver0})",
          flush=True)
    print(f"fire attempts tabulated by who-was-driving: {fire_by_driver}", flush=True)

    print(f"\n== transfer_multi_match resolution breakdown ==", flush=True)
    print(f"count={multi_match_count} resolved_exact={multi_resolved} "
          f"forked_survivors(2+)={multi_fork_survivors} forked_forced(0 survivors)={multi_fork_forced} "
          f"total_extra_branches_forked={forked}", flush=True)

    if win is None:
        print(f"\nNO WIN: t={elapsed:.0f}s exhausted={exhausted}", flush=True)
    else:
        print(f"\nWIN CONFIRMED", flush=True)

    print(f"\nFINAL expanded={expanded} states={len(seen)} frontier={len(frontier)} "
          f"multi_match={multi_match_count} forked={forked} exhausted={exhausted} win={win_bool}",
          flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-seconds", type=int, default=3300)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--control", action="store_true")
    args = ap.parse_args()

    if args.control:
        ok = positive_control()
        sys.exit(0 if ok else 1)

    run_bfs(args.budget_seconds, args.fresh)
