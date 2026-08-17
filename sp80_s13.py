"""sp80 s13: s12's checkpointed BFS + resolver, with a RECOVERING driver reader.

s12 was STOPPED at ~43k expansions: `driver_blob()` returning count != 1 (not
exactly one colour-9 blob) fired 56,477 times and all three call sites
(`continue`) silently DROPPED the child -- the search was exploring a
subgraph (see results/breadth-recon.md, "the s12 chain was STOPPED"). s13 is
byte-identical to s12 (root, resolve_multi_match/transfer_targets, checkpoint
shape, budget handling, heartbeat, FINAL) except for one addition:
`driver_blob_recover()`, called ONLY when `driver_blob()` returns count != 1,
attempting a measured recovery instead of dropping. Nothing is ever silently
dropped: every recovery attempt increments its own counter
(driver_recovered_size / driver_recovered_split / driver_forked /
driver_dropped_hard), reported in the FINAL line.

--diagnose reproduces anomaly cases from the L4 root by driving short random
action sequences and classifying each per driver_blob_recover's tiers; see
results/sp80-s13-engineering-20260817.md for the measured taxonomy this
design follows (measured, not guessed -- run --diagnose before trusting the
recovery tiers below).

    ./.venv/Scripts/python.exe sp80_s13.py --diagnose                       # anomaly taxonomy
    ./.venv/Scripts/python.exe sp80_s13.py --control                        # positive control
    ./.venv/Scripts/python.exe sp80_s13.py --budget-seconds 60 --fresh      # first run
    ./.venv/Scripts/python.exe sp80_s13.py --budget-seconds 3300            # resume
"""
import argparse
import copy
import os
import pickle
import random
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
CKPT_PATH = os.path.join("results", "sp80_s13_ckpt.pkl")


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


def driver_blob_recover(blobs, known_size):
    """Called ONLY when driver_blob() found colour-9 blob count != 1. Recovery
    tiers, in order (measured taxonomy -- see sp80-s13-engineering report):

      (a) exact-size match among candidate colour-9 blobs -> single recovery,
          tag 'size'.
      (b) SPLIT: 2+ blobs whose UNION bbox equals the driver's known (w,h) ->
          single recovery at the union position, tag 'split'.
      (c) MISSING (0 blobs): no signal survives in this frame to recover a
          position from -> tag 'dropped_hard' (measured: see report; no
          occlusion-shrink case was found that yields a recoverable partial
          blob here, because swap.blocks() already requires a SOLID
          rectangle -- a non-rectangular remainder is dropped before this
          function ever sees it, same false-zero as a full cover).
      (d) genuinely ambiguous, <=3 plausible candidates -> FORK, one branch
          per candidate, tag 'fork'.
      (e) >3 plausible candidates -> tag 'dropped_hard' (bounded, never
          explodes the frontier).

    Returns (candidates, tag) where candidates is a list of (pos, size)
    tuples (len 0 = nothing recovered, len 1 = single recovery, len 2-3 =
    fork).
    """
    d = [(x0, y0, w, h) for c, x0, y0, w, h in blobs if c == 9]
    cnt = len(d)
    if cnt == 0:
        return [], "dropped_hard"
    if known_size is not None:
        exact = [(x0, y0, w, h) for x0, y0, w, h in d if (w, h) == known_size]
        if len(exact) == 1:
            x0, y0, w, h = exact[0]
            return [((x0, y0), (w, h))], "size"
        x0s = min(b[0] for b in d)
        y0s = min(b[1] for b in d)
        x1s = max(b[0] + b[2] for b in d)
        y1s = max(b[1] + b[3] for b in d)
        uw, uh = x1s - x0s, y1s - y0s
        if (uw, uh) == known_size:
            return [((x0s, y0s), (uw, uh))], "split"
    if cnt <= 3:
        return [((x0, y0), (w, h)) for x0, y0, w, h in d], "fork"
    return [], "dropped_hard"


def full_key(pos, driver_id, ammo):
    return (tuple(sorted(pos.items())), ammo, driver_id)


def resolve_multi_match(g, pos, sizes, matches, dsize):
    """Two independent per-frame invariants, in order -- unchanged from
    s11/s12. Driver READER recovery (above) is the only thing s13 adds."""
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


def _play_click_line(env, A, clicker, obs, line):
    for v in line:
        if isinstance(v, tuple):
            _, x, y, _ = v
            obs = env.step(clicker, data={"x": int(x), "y": int(y)})
        else:
            obs = env.step(A[v])
    return obs


def make_root():
    """L1 + L2 + L3 via raw env.step (no transfer resolution needed to get
    here): RECIPE1, then swap.L2_LINE, then swap.L3_LINE. Asserts
    levels_completed == 3 (the L4 entry)."""
    env = arc_agi.Arcade().make("sp80")
    A = {a.value: a for a in env.action_space}
    clicker = next(a for a in env.action_space if a.is_complex())
    obs = env.reset()
    for a in RECIPE1:
        obs = env.step(A[a])
    assert obs.levels_completed == 1
    obs = _play_click_line(env, A, clicker, obs, swap.L2_LINE)
    assert obs.levels_completed == 2
    obs = _play_click_line(env, A, clicker, obs, swap.L3_LINE)
    assert obs.levels_completed == 3
    return env, A, clicker, obs


def root_state():
    """(env, A, clicker, obs, pos0, sizes, driver0) -- shared by run_bfs and
    diagnose so both read the identical L4 root body model."""
    env, A, clicker, obs = make_root()
    g0 = swap.grid_of(obs)
    b0 = bodies(g0)
    assert sum(1 for c, x, y, w, h in b0 if c == 9) == 1
    ids0 = sorted(range(len(b0)), key=lambda i: (b0[i][1], b0[i][2]))
    pos0 = {rank: (b0[i][1], b0[i][2]) for rank, i in enumerate(ids0)}
    sizes = {rank: (b0[i][3], b0[i][4]) for rank, i in enumerate(ids0)}
    driver0 = [rank for rank, i in enumerate(ids0) if b0[i][0] == 9][0]
    return env, A, clicker, obs, b0, pos0, sizes, driver0


def positive_control():
    """Scripted replay of the KNOWN L3 win (swap.L3_LINE, from the L3 entry
    reached by RECIPE1 + L2_LINE) driven through the SAME body-tracking +
    transfer_targets() resolver the BFS uses, step by step. Proves the
    resolver does not corrupt or misroute a known-good line on L4's 6-body
    model, including its three real transfers (the aimed clicks). Unchanged
    from s12: the counter this file exists to fix stayed at ZERO across
    L3's entire run, so the control line never needs the recovering reader."""
    env = arc_agi.Arcade().make("sp80")
    A = {a.value: a for a in env.action_space}
    clicker = next(a for a in env.action_space if a.is_complex())
    obs = env.reset()
    for a in RECIPE1:
        obs = env.step(A[a])
    assert obs.levels_completed == 1, "positive control: L1 recipe failed"
    print("CONTROL: L1 reached via RECIPE1", flush=True)

    obs = _play_click_line(env, A, clicker, obs, swap.L2_LINE)
    assert obs.levels_completed == 2, "positive control: L2_LINE failed"
    print("CONTROL: L2 reached via L2_LINE", flush=True)

    g = swap.grid_of(obs)
    b = bodies(g)
    ids0 = sorted(range(len(b)), key=lambda i: (b[i][1], b[i][2]))
    pos = {r: (b[i][1], b[i][2]) for r, i in enumerate(ids0)}
    sizes = {r: (b[i][3], b[i][4]) for r, i in enumerate(ids0)}
    driver_id = [r for r, i in enumerate(ids0) if b[i][0] == 9][0]
    print(f"CONTROL: L3 entry bodies={pos} sizes={sizes} driver={driver_id}", flush=True)

    for step_i, step in enumerate(swap.L3_LINE):
        is_transfer = (step == 5) or isinstance(step, tuple)
        if isinstance(step, tuple):
            _, cx, cy, _ = step
            obs = env.step(clicker, data={"x": int(cx), "y": int(cy)})
        else:
            obs = env.step(A[step])
        assert obs is not None, f"CONTROL FAIL: engine returned None at step {step_i} ({step})"
        if obs.levels_completed >= 3:
            print(f"CONTROL: step {step_i} ({step}) -> levels_completed=3, WIN", flush=True)
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

    assert False, "CONTROL FAIL: L3_LINE exhausted without levels_completed==3"


def diagnose(n_target=20, max_trials=4000, max_len=12, seed=0):
    """Reproduce ~n_target anomaly cases (driver_blob count != 1) from the L4
    root by driving short random action sequences, independent trials (fresh
    deepcopy of the root env each trial, so each sample is an unbiased draw
    over reachable L4 states rather than one biased walk). For each anomaly:
    print the colour-9 blob count, every blob's bbox+size, the known driver
    size, and what driver_blob_recover() classifies it as. This is the
    measurement the recovery design in driver_blob_recover() is built from --
    read the printed tag_hist before trusting the tiers."""
    env, A, clicker, obs, b0, pos0, sizes, driver0 = root_state()
    print(f"DIAGNOSE root: bodies={b0}", flush=True)
    print(f"DIAGNOSE root pos0={pos0} sizes={sizes} driver0={driver0}", flush=True)

    rng = random.Random(seed)
    found = 0
    trial = 0
    count_hist = {}
    tag_hist = {}

    while found < n_target and trial < max_trials:
        trial += 1
        length = rng.randint(1, max_len)
        e = copy.deepcopy(env)
        pos = dict(pos0)
        driver_id = driver0
        ammo = 0
        seq = []
        for _ in range(length):
            choices = ["move"] * 4
            if ammo < 4:
                choices.append("fire")
            other_ids = [i for i in pos if i != driver_id]
            if other_ids:
                choices.append("click")
            act = rng.choice(choices)
            if act == "move":
                a = rng.choice([1, 2, 3, 4])
                o = e.step(A[a])
                seq.append(a)
            elif act == "fire":
                o = e.step(A[5])
                ammo += 1
                seq.append(5)
            else:
                oid = rng.choice(other_ids)
                cx, cy = pos[oid]
                o = e.step(clicker, data={"x": int(cx), "y": int(cy)})
                seq.append(("click", cx, cy))

            if o is None or o.state != GameState.NOT_FINISHED:
                break
            g = swap.grid_of(o)
            if g is None:
                break
            blobs = bodies(g)
            dp, dsize, cnt = driver_blob(blobs)

            if dp is None:
                found += 1
                count_hist[cnt] = count_hist.get(cnt, 0) + 1
                d9 = [(x0, y0, w, h) for c, x0, y0, w, h in blobs if c == 9]
                known = sizes.get(driver_id)
                cands, tag = driver_blob_recover(blobs, known)
                tag_hist[tag] = tag_hist.get(tag, 0) + 1
                print(f"ANOMALY #{found} trial={trial} seq={seq} driver_id={driver_id} "
                      f"known_driver_size={known} colour9_blobs={d9} count={cnt} "
                      f"recover_tag={tag} recover_candidates={cands}", flush=True)
                break

            pos = dict(pos)
            if act == "move":
                pos[driver_id] = dp
            else:
                ids_out, reason = transfer_targets(g, pos, sizes, dp, dsize)
                if reason == "transfer_no_match":
                    pos[driver_id] = dp
                else:
                    driver_id = ids_out[0]
                    pos[driver_id] = dp

    print(f"\nDIAGNOSE SUMMARY: found={found} trials={trial} "
          f"count_hist={count_hist} tag_hist={tag_hist}", flush=True)
    return found, trial, count_hist, tag_hist


def run_bfs(budget_seconds, fresh):
    env, A, clicker, obs, b0, pos0, sizes, driver0 = root_state()
    ROOT_ENV = env
    NBODY = len(b0)
    print(f"L4 root: {NBODY} tracked bodies: {b0}", flush=True)
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
        driver_recovered_size = ckpt["driver_recovered_size"]
        driver_recovered_split = ckpt["driver_recovered_split"]
        driver_forked = ckpt["driver_forked"]
        driver_dropped_hard = ckpt["driver_dropped_hard"]
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
        driver_recovered_size = driver_recovered_split = 0
        driver_forked = driver_dropped_hard = 0
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
            driver_recovered_size=driver_recovered_size, driver_recovered_split=driver_recovered_split,
            driver_forked=driver_forked, driver_dropped_hard=driver_dropped_hard,
        ))

    def recover_and_tally(blobs, known_size):
        """Wraps driver_blob_recover() with the counter bookkeeping shared by
        all three call sites below. Returns candidates (list of (pos,size))."""
        nonlocal driver_recovered_size, driver_recovered_split, driver_forked, driver_dropped_hard
        cands, tag = driver_blob_recover(blobs, known_size)
        if tag == "size":
            driver_recovered_size += 1
        elif tag == "split":
            driver_recovered_split += 1
        elif tag == "fork":
            driver_forked += 1
        else:
            driver_dropped_hard += 1
        return cands

    try:
        while frontier and win is None and time.time() - t0 < budget_seconds:
            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_S:
                elapsed = now - t0
                rate = expanded / max(1e-9, elapsed)
                print(f"HEARTBEAT expanded={expanded} states={len(seen)} frontier={len(frontier)} "
                      f"rate={rate:.2f}/s multi_match={multi_match_count} forked={forked} "
                      f"recovered_size={driver_recovered_size} recovered_split={driver_recovered_split} "
                      f"driver_forked={driver_forked} driver_dropped_hard={driver_dropped_hard} "
                      f"t={elapsed:.0f}s", flush=True)
                last_heartbeat = now

            seq, ammo, pos, driver_id = frontier.popleft()
            if len(seq) >= MAX_DEPTH:
                continue
            seen_as_driver.add(driver_id)

            tr0 = time.time()
            node_env, _ = replay(seq)
            replay_time_total += time.time() - tr0

            # -- plain moves (1..4): read the driver's new position directly --
            for a in (1, 2, 3, 4):
                child = copy.deepcopy(node_env)
                o = child.step(A[a])
                if o is None:
                    continue
                if o.state == GameState.WIN or o.levels_completed > 3:
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
                    cands = recover_and_tally(blobs, sizes.get(driver_id))
                    for cdp, _csize in cands:
                        new_pos = dict(pos)
                        new_pos[driver_id] = cdp
                        k = full_key(new_pos, driver_id, ammo)
                        if k in seen:
                            continue
                        seen.add(k)
                        frontier.append((seq + [a], ammo, new_pos, driver_id))
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

            # -- fire: transfer_targets() decides the new driver id --
            if ammo < 4:
                child = copy.deepcopy(node_env)
                o = child.step(A[5])
                na = ammo + 1
                fire_by_driver[driver_id] += 1
                if o is not None:
                    if o.state == GameState.WIN or o.levels_completed > 3:
                        win = (seq + [5], driver_id)
                        print(f"WIN: seq={win[0]} fired_by_id={driver_id} state={o.state} "
                              f"lvl={o.levels_completed}", flush=True)
                    elif o.state == GameState.NOT_FINISHED:
                        g = swap.grid_of(o)
                        blobs = bodies(g) if g is not None else None
                        candidates = []
                        if blobs is not None:
                            dp, dsize, cnt = driver_blob(blobs)
                            if dp is not None:
                                candidates = [(dp, dsize)]
                            else:
                                anomalies += 1
                                anomaly_reasons["driver_blob_count"] += 1
                                candidates = recover_and_tally(blobs, sizes.get(driver_id))
                        else:
                            anomalies += 1
                            anomaly_reasons["driver_blob_count"] += 1
                            driver_dropped_hard += 1
                        for cdp, csize in candidates:
                            ids_out, reason = transfer_targets(g, pos, sizes, cdp, csize)
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
                                k = full_key(pos, new_driver_id, na)
                                if k not in seen:
                                    seen.add(k)
                                    frontier.append((seq + [5], na, dict(pos), new_driver_id))
            if win is not None:
                break

            # -- click each non-driver body: transfer_targets() decides the new driver id --
            for oid, (cx, cy) in pos.items():
                if oid == driver_id:
                    continue
                child = copy.deepcopy(node_env)
                o = child.step(clicker, data={"x": int(cx), "y": int(cy)})
                if o is None:
                    continue
                if o.state == GameState.WIN or o.levels_completed > 3:
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
                candidates = []
                if dp is not None:
                    candidates = [(dp, dsize)]
                else:
                    anomalies += 1
                    anomaly_reasons["driver_blob_count"] += 1
                    candidates = recover_and_tally(blobs, sizes.get(driver_id))
                for cdp, csize in candidates:
                    ids_out, reason = transfer_targets(g, pos, sizes, cdp, csize)
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
                      f"recovered_size={driver_recovered_size} recovered_split={driver_recovered_split} "
                      f"driver_forked={driver_forked} driver_dropped_hard={driver_dropped_hard} "
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

    print(f"\n== driver-reader recovery breakdown ==", flush=True)
    print(f"driver_recovered_size={driver_recovered_size} driver_recovered_split={driver_recovered_split} "
          f"driver_forked={driver_forked} driver_dropped_hard={driver_dropped_hard}", flush=True)

    if win is None:
        print(f"\nNO WIN: t={elapsed:.0f}s exhausted={exhausted}", flush=True)
    else:
        print(f"\nWIN CONFIRMED", flush=True)

    print(f"\nFINAL expanded={expanded} states={len(seen)} frontier={len(frontier)} "
          f"multi_match={multi_match_count} forked={forked} exhausted={exhausted} win={win_bool} "
          f"driver_recovered_size={driver_recovered_size} driver_recovered_split={driver_recovered_split} "
          f"driver_forked={driver_forked} driver_dropped_hard={driver_dropped_hard}",
          flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-seconds", type=int, default=3300)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--diagnose", action="store_true")
    args = ap.parse_args()

    if args.control:
        ok = positive_control()
        sys.exit(0 if ok else 1)

    if args.diagnose:
        diagnose()
        sys.exit(0)

    run_bfs(args.budget_seconds, args.fresh)
