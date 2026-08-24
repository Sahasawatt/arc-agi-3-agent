"""sp80 s15: s13 + a deterministic twin-merge handler (retires s13's fork tier).

s14 measured the (9,3) twin-pair colour-9 merge (s13's driver_blob_recover()
fork tier, 120/120 anomalies in the s13 diagnostic sample) is a REAL game
state with a DETERMINISTIC transition, not a hidden-selector ambiguity
(results/sp80-s14-twinmerge-20260817.md):

  - arrows (1-4): BOTH twin members move together, in lockstep, by the
    arrow's normal single-body displacement -- no fork needed, re-read both
    blobs from the post-move frame (they are visible) and apply.
  - fire (5): resolves the merge -- BOTH members revert to colour 8, and
    the true post-fire driver is a body OUTSIDE the twin pair entirely
    (re-run driver_blob() over the FULL body list; it resolves cleanly).
  - click on the twin's own position: inert.

s15 imports s13 unedited (root_state/bodies/driver_blob/driver_blob_recover/
transfer_targets/MAX_DEPTH/CURVE_EVERY/HEARTBEAT_S) and reimplements the BFS
orchestration loop, because the frontier tuple shape itself changes (a
`merged` flag has to ride alongside pos/driver_id/ammo, which s13's run_bfs
has no hook to add without editing it). s13's own checkpoint is POLLUTED
(built while the fork tier forked instead of merging) and is never read
here -- s15 seeds only from ITS OWN checkpoint or --fresh.

Genuinely unexpected post-action readings (neither a clean single driver nor
the twin pair) are counted as driver_dropped_hard and DROPPED, never forked
and never guessed -- see the WARNING print near FINAL if that ratio exceeds
0.1% of expansions (the tripwire: it means the s14 model is wrong again).

    ./.venv/Scripts/python.exe sp80_s15.py --control                    # positive control (delegates to s13)
    ./.venv/Scripts/python.exe sp80_s15.py --budget-seconds 120 --fresh # first run
    ./.venv/Scripts/python.exe sp80_s15.py --budget-seconds 3300        # resume
"""
import argparse
import copy
import os
import pickle
import sys
import time
from collections import deque

import swap
import sp80_s13
from arcengine.enums import GameState

MAX_DEPTH = sp80_s13.MAX_DEPTH
CURVE_EVERY = sp80_s13.CURVE_EVERY
HEARTBEAT_S = sp80_s13.HEARTBEAT_S
CKPT_PATH = os.path.join("results", "sp80_s15_ckpt.pkl")
DROPPED_HARD_WARN_RATIO = 0.001  # tripwire: >0.1% of expansions -> the twin model is wrong again


TWIN_SIZE_MEASURED = (9, 3)
TWIN_XY_MEASURED = {(8, 29), (20, 29)}


def compute_twin(sizes, pos0):
    """The two tracked body ranks matching the (9,3) twin pair measured in
    results/sp80-s14-twinmerge-20260817.md (root positions (8,29)/(20,29)).
    NOT "any size shared by exactly 2 ranks" -- the L4 root has 3 such
    same-size pairs among its 6 bodies (measured: (9,3),(15,3),(12,3)), so a
    generic uniqueness check is ambiguous. Both the size AND the root
    positions are asserted against the s14 measurement so a wrong root
    model fails loudly instead of silently mis-tracking."""
    ranks = [r for r, sz in sizes.items() if sz == TWIN_SIZE_MEASURED]
    assert len(ranks) == 2, (
        f"expected exactly 2 bodies of size {TWIN_SIZE_MEASURED}, got ranks={ranks} sizes={sizes}")
    twin_ranks = tuple(sorted(ranks))
    actual_xy = {pos0[r] for r in twin_ranks}
    assert actual_xy == TWIN_XY_MEASURED, (
        f"twin ranks {twin_ranks} at root positions {actual_xy}, expected {TWIN_XY_MEASURED} "
        f"(sp80-s14-twinmerge report) -- root model may have changed, do not trust blindly")
    return twin_ranks, TWIN_SIZE_MEASURED


def full_key(pos, driver_id, ammo, merged):
    """s13's full_key + an explicit merged flag -- a merged state must hash
    differently from an unmerged one with the same tracked positions."""
    return (tuple(sorted(pos.items())), ammo, driver_id, merged)


def match_twin_positions(new_xy_list, pos, twin_ranks):
    """Match 2 freshly-read (x,y) positions to the 2 twin ranks by x-order
    against their last TRACKED positions -- identity by physical x-order,
    never by internal id (id-ambiguity is exactly what a merge breaks)."""
    old_sorted = sorted(twin_ranks, key=lambda r: pos[r][0])
    new_sorted = sorted(new_xy_list, key=lambda p: p[0])
    return {old_sorted[i]: new_sorted[i] for i in range(2)}


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


def run_bfs(budget_seconds, fresh):
    env, A, clicker, obs, b0, pos0, sizes, driver0 = sp80_s13.root_state()
    ROOT_ENV = env
    NBODY = len(b0)
    TWIN_RANKS, TWIN_SIZE = compute_twin(sizes, pos0)
    print(f"L4 root: {NBODY} tracked bodies: {b0}", flush=True)
    print(f"root pos0={pos0} sizes={sizes} driver0={driver0} "
          f"TWIN_RANKS={TWIN_RANKS} TWIN_SIZE={TWIN_SIZE}", flush=True)

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

    def recover_or_merge(blobs, known_size):
        """driver_blob_recover()'s tiers (a) exact-size and (b) split pass
        through unchanged -- unrelated occlusion recoveries. Tier (d) fork
        is reclassified: exactly 2 candidates sharing TWIN_SIZE (s14's
        measured signature) -> 'merge'; anything else (the old tier
        (c)/(e) dropped_hard, and any non-twin fork) -> 'dropped_hard'."""
        cands, tag = sp80_s13.driver_blob_recover(blobs, known_size)
        if tag in ("size", "split"):
            return tag, cands
        if tag == "fork" and len(cands) == 2 and cands[0][1] == cands[1][1] == TWIN_SIZE:
            return "merge", cands
        return "dropped_hard", []

    def classify_merge_reading(g):
        """Classify a frame read after an action taken FROM a merged state:
        ('single', pos, size) resolved to one non-twin driver, ('twin',
        [posL, posR], None) still merged, ('other', None, None) genuinely
        unexpected."""
        all_bodies = sp80_s13.bodies(g)
        dp, dsize, cnt = sp80_s13.driver_blob(all_bodies)
        if dp is not None and cnt == 1:
            return "single", dp, dsize
        twins = sorted([(x0, y0) for c, x0, y0, w, h in all_bodies
                         if (w, h) == TWIN_SIZE and c == 9], key=lambda p: p[0])
        if len(twins) == 2:
            return "twin", twins, None
        return "other", None, None

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
        driver_dropped_hard = ckpt["driver_dropped_hard"]
        twin_merged_transitions = ckpt["twin_merged_transitions"]
        print(f"RESUMED expanded={expanded} states={len(seen)} frontier={len(frontier)} "
              f"multi_match={multi_match_count} twin_merged_transitions={twin_merged_transitions}",
              flush=True)
    else:
        seen = {full_key(pos0, driver0, 0, False)}
        frontier = deque([([], 0, pos0, driver0, False)])
        expanded = anomalies = 0
        anomaly_reasons = {"driver_blob_count": 0, "transfer_no_match": 0, "transfer_multi_match": 0}
        multi_match_count = multi_resolved = multi_fork_survivors = multi_fork_forced = 0
        forked = 0
        fire_by_driver = {i: 0 for i in range(NBODY)}
        fire_by_driver[-1] = 0  # fired while merged
        seen_as_driver = set()
        curve = []
        last_curve_states = len(seen)
        last_curve_frontier = len(frontier)
        replay_time_total = 0.0
        win = None
        driver_recovered_size = driver_recovered_split = 0
        driver_dropped_hard = 0
        twin_merged_transitions = 0
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
            driver_dropped_hard=driver_dropped_hard, twin_merged_transitions=twin_merged_transitions,
        ))

    def push(new_pos, new_driver_id, new_ammo, new_merged, path_step):
        k = full_key(new_pos, new_driver_id, new_ammo, new_merged)
        if k in seen:
            return
        seen.add(k)
        frontier.append((seq + [path_step], new_ammo, new_pos, new_driver_id, new_merged))

    try:
        while frontier and win is None and time.time() - t0 < budget_seconds:
            now = time.time()
            if now - last_heartbeat >= HEARTBEAT_S:
                elapsed = now - t0
                rate = expanded / max(1e-9, elapsed)
                print(f"HEARTBEAT expanded={expanded} states={len(seen)} frontier={len(frontier)} "
                      f"rate={rate:.2f}/s multi_match={multi_match_count} "
                      f"recovered_size={driver_recovered_size} recovered_split={driver_recovered_split} "
                      f"twin_merged_transitions={twin_merged_transitions} "
                      f"driver_dropped_hard={driver_dropped_hard} t={elapsed:.0f}s", flush=True)
                last_heartbeat = now

            seq, ammo, pos, driver_id, merged = frontier.popleft()
            if len(seq) >= MAX_DEPTH:
                continue
            if driver_id is not None:
                seen_as_driver.add(driver_id)

            tr0 = time.time()
            node_env, _ = replay(seq)
            replay_time_total += time.time() - tr0

            if not merged:
                # -- plain moves (1..4) --
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
                    blobs = sp80_s13.bodies(g)
                    dp, dsize, cnt = sp80_s13.driver_blob(blobs)
                    if dp is not None:
                        new_pos = dict(pos)
                        new_pos[driver_id] = dp
                        push(new_pos, driver_id, ammo, False, a)
                        continue
                    anomalies += 1
                    anomaly_reasons["driver_blob_count"] += 1
                    kind, cands = recover_or_merge(blobs, sizes.get(driver_id))
                    if kind in ("size", "split"):
                        if kind == "size":
                            driver_recovered_size += 1
                        else:
                            driver_recovered_split += 1
                        for cdp, _ in cands:
                            new_pos = dict(pos)
                            new_pos[driver_id] = cdp
                            push(new_pos, driver_id, ammo, False, a)
                    elif kind == "merge":
                        twin_merged_transitions += 1
                        mapping = match_twin_positions([c[0] for c in cands], pos, TWIN_RANKS)
                        new_pos = dict(pos)
                        new_pos.update(mapping)
                        push(new_pos, None, ammo, True, a)
                    else:
                        driver_dropped_hard += 1
                        print(f"TRIPWIRE dropped_hard (move) seq={seq + [a]} blobs={blobs}", flush=True)
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
                            blobs = sp80_s13.bodies(g) if g is not None else None
                            candidates = []
                            if blobs is not None:
                                dp, dsize, cnt = sp80_s13.driver_blob(blobs)
                                if dp is not None:
                                    candidates = [(dp, dsize)]
                                else:
                                    anomalies += 1
                                    anomaly_reasons["driver_blob_count"] += 1
                                    kind, cands = recover_or_merge(blobs, sizes.get(driver_id))
                                    if kind in ("size", "split"):
                                        if kind == "size":
                                            driver_recovered_size += 1
                                        else:
                                            driver_recovered_split += 1
                                        candidates = cands
                                    elif kind == "merge":
                                        twin_merged_transitions += 1
                                        mapping = match_twin_positions([c[0] for c in cands], pos, TWIN_RANKS)
                                        new_pos = dict(pos)
                                        new_pos.update(mapping)
                                        push(new_pos, None, na, True, 5)
                                    else:
                                        driver_dropped_hard += 1
                                        print(f"TRIPWIRE dropped_hard (fire) seq={seq + [5]} blobs={blobs}",
                                              flush=True)
                            else:
                                anomalies += 1
                                anomaly_reasons["driver_blob_count"] += 1
                                driver_dropped_hard += 1
                            for cdp, csize in candidates:
                                ids_out, reason = sp80_s13.transfer_targets(g, pos, sizes, cdp, csize)
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
                                    push(dict(pos), new_driver_id, na, False, 5)
                if win is not None:
                    break

                # -- click each non-driver body --
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
                    blobs = sp80_s13.bodies(g)
                    dp, dsize, cnt = sp80_s13.driver_blob(blobs)
                    candidates = []
                    if dp is not None:
                        candidates = [(dp, dsize)]
                    else:
                        anomalies += 1
                        anomaly_reasons["driver_blob_count"] += 1
                        kind, cands = recover_or_merge(blobs, sizes.get(driver_id))
                        if kind in ("size", "split"):
                            if kind == "size":
                                driver_recovered_size += 1
                            else:
                                driver_recovered_split += 1
                            candidates = cands
                        elif kind == "merge":
                            twin_merged_transitions += 1
                            mapping = match_twin_positions([c[0] for c in cands], pos, TWIN_RANKS)
                            new_pos = dict(pos)
                            new_pos.update(mapping)
                            push(new_pos, None, ammo, True, ("click", cx, cy))
                        else:
                            driver_dropped_hard += 1
                            print(f"TRIPWIRE dropped_hard (click) seq={seq + [('click', cx, cy)]} "
                                  f"blobs={blobs}", flush=True)
                    for cdp, csize in candidates:
                        ids_out, reason = sp80_s13.transfer_targets(g, pos, sizes, cdp, csize)
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
                            push(dict(pos), new_driver_id, ammo, False, ("click", cx, cy))
                if win is not None:
                    break

            else:
                # ==== MERGED: driver_id is None, both TWIN_RANKS render colour 9 ====
                # -- arrows: lockstep, apply the observed shared delta --
                for a in (1, 2, 3, 4):
                    child = copy.deepcopy(node_env)
                    o = child.step(A[a])
                    if o is None:
                        continue
                    if o.state == GameState.WIN or o.levels_completed > 3:
                        win = (seq + [a], None)
                        print(f"WIN: seq={win[0]} fired_by_id=MERGED state={o.state} "
                              f"lvl={o.levels_completed}", flush=True)
                        break
                    if o.state != GameState.NOT_FINISHED:
                        continue
                    g = swap.grid_of(o)
                    if g is None:
                        continue
                    all_bodies = sp80_s13.bodies(g)
                    twins = sorted([(x0, y0) for c, x0, y0, w, h in all_bodies
                                     if (w, h) == TWIN_SIZE and c == 9], key=lambda p: p[0])
                    if len(twins) == 2:
                        twin_merged_transitions += 1
                        mapping = match_twin_positions(twins, pos, TWIN_RANKS)
                        new_pos = dict(pos)
                        new_pos.update(mapping)
                        push(new_pos, None, ammo, True, a)
                    else:
                        driver_dropped_hard += 1
                        print(f"TRIPWIRE dropped_hard (merged arrow) seq={seq + [a]} "
                              f"twins={twins} all_bodies={all_bodies}", flush=True)
                if win is not None:
                    break

                # -- fire: resolves the merge (re-run driver_blob over the FULL body list) --
                if ammo < 4:
                    child = copy.deepcopy(node_env)
                    o = child.step(A[5])
                    na = ammo + 1
                    fire_by_driver[-1] += 1
                    if o is not None:
                        if o.state == GameState.WIN or o.levels_completed > 3:
                            win = (seq + [5], None)
                            print(f"WIN: seq={win[0]} fired_by_id=MERGED state={o.state} "
                                  f"lvl={o.levels_completed}", flush=True)
                        elif o.state == GameState.NOT_FINISHED:
                            g = swap.grid_of(o)
                            if g is not None:
                                kind, dp, dsize = classify_merge_reading(g)
                                if kind == "single":
                                    twin_merged_transitions += 1
                                    ids_out, reason = sp80_s13.transfer_targets(g, pos, sizes, dp, dsize)
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
                                            push(dict(pos), new_driver_id, na, False, 5)
                                elif kind == "twin":
                                    twin_merged_transitions += 1
                                    push(dict(pos), None, na, True, 5)
                                else:
                                    driver_dropped_hard += 1
                                    print(f"TRIPWIRE dropped_hard (merged fire) seq={seq + [5]}",
                                          flush=True)
                            else:
                                driver_dropped_hard += 1
                                print(f"TRIPWIRE dropped_hard (merged fire, empty frame) "
                                      f"seq={seq + [5]}", flush=True)
                if win is not None:
                    break

                # -- click each non-twin body (click on the twin itself is inert, s14-measured) --
                for oid, (cx, cy) in pos.items():
                    if oid in TWIN_RANKS:
                        continue
                    child = copy.deepcopy(node_env)
                    o = child.step(clicker, data={"x": int(cx), "y": int(cy)})
                    if o is None:
                        continue
                    if o.state == GameState.WIN or o.levels_completed > 3:
                        win = (seq + [("click", cx, cy)], None)
                        print(f"WIN via click: seq={win[0]} state={o.state} lvl={o.levels_completed}",
                              flush=True)
                        break
                    if o.state != GameState.NOT_FINISHED:
                        continue
                    g = swap.grid_of(o)
                    if g is None:
                        continue
                    kind, dp, dsize = classify_merge_reading(g)
                    if kind == "single":
                        twin_merged_transitions += 1
                        ids_out, reason = sp80_s13.transfer_targets(g, pos, sizes, dp, dsize)
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
                            push(dict(pos), new_driver_id, ammo, False, ("click", cx, cy))
                    elif kind == "twin":
                        # inert (s14-measured): same pos/ammo -> same key as the popped
                        # node, push() dedupes it away for free.
                        push(dict(pos), None, ammo, True, ("click", cx, cy))
                    else:
                        driver_dropped_hard += 1
                        print(f"TRIPWIRE dropped_hard (merged click) seq={seq + [('click', cx, cy)]}",
                              flush=True)
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
                      f"anomalies={anomalies} multi_match={multi_match_count} "
                      f"recovered_size={driver_recovered_size} recovered_split={driver_recovered_split} "
                      f"twin_merged_transitions={twin_merged_transitions} "
                      f"driver_dropped_hard={driver_dropped_hard} "
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
    print(f"ids ever seen as driver: {sorted(seen_as_driver)} (root driver id = {driver0})", flush=True)
    print(f"fire attempts tabulated by who-was-driving (-1 = merged): {fire_by_driver}", flush=True)

    print(f"\n== transfer_multi_match resolution breakdown ==", flush=True)
    print(f"count={multi_match_count} resolved_exact={multi_resolved} "
          f"forked_survivors(2+)={multi_fork_survivors} forked_forced(0 survivors)={multi_fork_forced} "
          f"total_extra_branches_forked={forked}", flush=True)

    print(f"\n== driver-reader recovery / twin-merge breakdown ==", flush=True)
    print(f"driver_recovered_size={driver_recovered_size} driver_recovered_split={driver_recovered_split} "
          f"twin_merged_transitions={twin_merged_transitions} driver_dropped_hard={driver_dropped_hard}",
          flush=True)
    if expanded > 0 and driver_dropped_hard / expanded > DROPPED_HARD_WARN_RATIO:
        print(f"\n*** WARNING: driver_dropped_hard/expanded = "
              f"{driver_dropped_hard}/{expanded} = "
              f"{100 * driver_dropped_hard / expanded:.3f}% > {100 * DROPPED_HARD_WARN_RATIO:.1f}% -- "
              f"the twin-merge model is likely WRONG again, see sp80-s14-twinmerge report ***", flush=True)

    if win is None:
        print(f"\nNO WIN: t={elapsed:.0f}s exhausted={exhausted}", flush=True)
    else:
        print(f"\nWIN CONFIRMED", flush=True)

    print(f"\nFINAL expanded={expanded} states={len(seen)} frontier={len(frontier)} "
          f"multi_match={multi_match_count} exhausted={exhausted} win={win_bool} "
          f"driver_recovered_size={driver_recovered_size} driver_recovered_split={driver_recovered_split} "
          f"twin_merged_transitions={twin_merged_transitions} driver_dropped_hard={driver_dropped_hard}",
          flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-seconds", type=int, default=3300)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--control", action="store_true")
    args = ap.parse_args()

    if args.control:
        ok = sp80_s13.positive_control()
        sys.exit(0 if ok else 1)

    run_bfs(args.budget_seconds, args.fresh)
