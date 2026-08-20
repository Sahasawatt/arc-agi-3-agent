"""dc22 c3: two independent verifications of c2's L2-exhaustion claim.

c2 (dc22_c2_l2chain.py) reported L2 EXHAUSTED: expanded=28,495 states=28,495
frontier=0 deaths=2,744 win=False -- the entire reachable space under the
6-action alphabet {4 arrows, click-A, click-B} from the L2 root, drained,
with zero win. c2 has ZERO divergence checking, and this campaign has twice
watched a merging state key report a false exhaustion (CLAUDE.md: ar25 L5,
sp80 L3). This script does not trust the closure until it survives two
independent probes, both required:

  1. POSITIVE CONTROL: the identical key function / node handling / 6-action
     search (board_bytes, press, path-frontier BFS -- reused from c2, not
     reimplemented) run from the L1 ENTRY (levels_completed==0) must FIND a
     win (bridge.py's own greedy solve reaches levels_completed>=1 in 25
     actions -- proof a win exists; our BFS must find ITS OWN route there).
     If the machinery cannot find a known win, the L2 null means nothing.
  2. COLLISION-DIVERGENCE SAMPLE: re-run a bounded L2 BFS (same code) that
     records the FIRST path to reach each board key; every time a DIFFERENT
     path reaches an already-seen key, save the pair. Sample the pairs,
     replay both on fresh deepcopies, press every alphabet action from both,
     and byte-compare every successor's frame + levels_completed + state.
     Any mismatch is state the board key cannot see -- the key merges, and
     c2's exhaustion is void by the same mechanism that voided ar25/sp80.

Death policy is NOT re-measured here -- it is c2's own measured finding
(death_continues=False, 3/3 runs, "env terminates" -- results/dc22-c2-
engineering-20260817.md), reused as a constant. That is not new search
semantics; it is the same conclusion, cited.

    PYTHONUTF8=1 ./.venv/Scripts/python.exe dc22_c3_verify.py
"""
import argparse
import copy
import time
from collections import deque

import os
os.environ.setdefault("PYTHONUTF8", "1")
import numpy as np
import arc_agi

from bridge import components, read
import dc22_c2_l2chain as c2  # reuse: last, board_bytes, press (byte-identical)

T0 = time.time()
DEATH_CONTINUES = False  # c2's measured finding, cited not re-derived


def log(msg):
    print("[%7.1fs] %s" % (time.time() - T0, msg), flush=True)


# ---------------------------------------------------------------------------
# Shared: replay a path from a fresh deepcopy of a root env (c2's own pattern)
# ---------------------------------------------------------------------------
def make_replay(root_env, root_obs, by_value, clicker):
    def replay(seq):
        e = copy.deepcopy(root_env)
        o = root_obs
        for act in seq:
            o = c2.press(e, act, by_value, clicker)
            if o is None:
                return e, None
        return e, o
    return replay


# ---------------------------------------------------------------------------
# Control 1: L1-entry root + button detection (identical filter to c2's
# make_root, applied to the L1 reset frame instead of the post-replay L2
# frame -- bridge.py's Bridge class is built to run per-level, so the same
# panel/button structure is expected at L1).
# ---------------------------------------------------------------------------
def make_l1_root():
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    env = arc.make(envs["dc22"].game_id)
    obs = env.reset()
    actions = [a for a in env.action_space if not a.is_complex()]
    by_value = {a.value: a for a in actions}
    clicker = next((a for a in env.action_space if a.is_complex()), None)
    root_lvl = obs.levels_completed
    log("L1 root: levels_completed=%s" % root_lvl)

    root_last = c2.last(obs)
    b0 = read(root_last)
    assert b0 is not None, "read() failed at L1 root"
    panel = root_last[:, b0["panel"][0]:b0["panel"][1] + 1]
    wide = panel.shape[1] - 1
    btn = []
    for c in components(panel, b0["nbg"]):
        if c[5] < 20 or c[0] == 0 or c[1] >= wide:
            continue
        x0, x1 = c[0] + b0["panel"][0], c[1] + b0["panel"][0]
        y0, y1 = c[2], c[3]
        at = ((x0 + x1) // 2, (y0 + y1) // 2)
        if at not in [e["at"] for e in btn]:
            btn.append({"at": at, "bbox": (x0, x1, y0, y1), "colour": c[4], "size": c[5]})
    assert len(btn) == 2, "expected exactly 2 buttons at L1, got %r" % (btn,)
    BTN_A, BTN_B = btn[0], btn[1]
    ACT_A = ("c", "A", BTN_A["at"][0], BTN_A["at"][1])
    ACT_B = ("c", "B", BTN_B["at"][0], BTN_B["at"][1])
    ACTIONS = [("v", 1), ("v", 2), ("v", 3), ("v", 4), ACT_A, ACT_B]
    log("L1 buttons: A=%s B=%s" % (BTN_A, BTN_B))
    return env, obs, ACTIONS, by_value, clicker, root_lvl


def control1_l1_win(budget_seconds):
    """Same key fn / node handling / alphabet as c2, rooted at L1 entry.
    Returns (win_path_or_None, expanded, states, deaths, elapsed)."""
    root_env, root_obs, ACTIONS, by_value, clicker, root_lvl = make_l1_root()
    replay = make_replay(root_env, root_obs, by_value, clicker)

    root_bytes = c2.board_bytes(root_obs)
    frontier = deque([[]])
    seen = {root_bytes}
    expanded = 0
    deaths = 0
    win = None
    t0 = time.time()
    last_hb = t0
    while frontier and win is None and time.time() - t0 < budget_seconds:
        now = time.time()
        if now - last_hb >= 30:
            log("CONTROL1 HEARTBEAT expanded=%d states=%d frontier=%d deaths=%d"
                % (expanded, len(seen), len(frontier), deaths))
            last_hb = now
        seq = frontier.popleft()
        node_env, node_obs = replay(seq)
        if node_obs is None:
            deaths += 1
            continue
        for act in ACTIONS:
            b2 = copy.deepcopy(node_env)
            o2 = c2.press(b2, act, by_value, clicker)
            if o2 is None:
                deaths += 1
                continue
            if o2.levels_completed > root_lvl:
                win = seq + [act]
                break
            st = str(o2.state)
            if st != "GameState.NOT_FINISHED":
                if not DEATH_CONTINUES:
                    deaths += 1
                    continue
            bb = c2.board_bytes(o2)
            if bb in seen:
                continue
            seen.add(bb)
            frontier.append(seq + [act])
        if win is not None:
            break
        expanded += 1
    elapsed = time.time() - t0
    return win, expanded, len(seen), deaths, elapsed, root_lvl


# ---------------------------------------------------------------------------
# Control 2: bounded L2 BFS with collision recording, then adversarial
# replay-and-compare on a sample of the collisions.
# ---------------------------------------------------------------------------
def collect_l2_collisions(budget_seconds):
    root_env, root_obs, l1_actions, ACTIONS, by_value, clicker = c2.make_root()
    replay = make_replay(root_env, root_obs, by_value, clicker)
    root_lvl = root_obs.levels_completed

    root_bytes = c2.board_bytes(root_obs)
    first_path = {root_bytes: []}
    collisions = []  # (board_key, path_a, path_b, depth_b)
    frontier = deque([[]])
    expanded = 0
    deaths = 0
    win = None
    t0 = time.time()
    last_hb = t0
    while frontier and time.time() - t0 < budget_seconds:
        now = time.time()
        if now - last_hb >= 30:
            log("CONTROL2-COLLECT HEARTBEAT expanded=%d keys=%d collisions=%d frontier=%d"
                % (expanded, len(first_path), len(collisions), len(frontier)))
            last_hb = now
        seq = frontier.popleft()
        node_env, node_obs = replay(seq)
        if node_obs is None:
            deaths += 1
            continue
        for act in ACTIONS:
            b2 = copy.deepcopy(node_env)
            o2 = c2.press(b2, act, by_value, clicker)
            if o2 is None:
                deaths += 1
                continue
            if o2.levels_completed > root_lvl:
                win = seq + [act]
                continue
            st = str(o2.state)
            if st != "GameState.NOT_FINISHED":
                if not DEATH_CONTINUES:
                    deaths += 1
                    continue
            bb = c2.board_bytes(o2)
            new_path = seq + [act]
            if bb in first_path:
                collisions.append((bb, first_path[bb], new_path, len(new_path)))
            else:
                first_path[bb] = new_path
                frontier.append(new_path)
        expanded += 1
    elapsed = time.time() - t0
    return dict(collisions=collisions, expanded=expanded, states=len(first_path),
                deaths=deaths, elapsed=elapsed, win=win, root_env=root_env,
                root_obs=root_obs, ACTIONS=ACTIONS, by_value=by_value,
                clicker=clicker, replay=replay)


def stratified_sample(collisions, cap):
    """Spread the verify sample across depths rather than taking the first N
    (which would all be shallow, since BFS is FIFO)."""
    if len(collisions) <= cap:
        return list(collisions)
    by_depth = {}
    for c in collisions:
        by_depth.setdefault(c[3], []).append(c)
    depths = sorted(by_depth)
    out = []
    i = 0
    while len(out) < cap:
        d = depths[i % len(depths)]
        bucket = by_depth[d]
        if bucket:
            out.append(bucket.pop(0))
        i += 1
        if all(not by_depth[d] for d in depths):
            break
    return out


def verify_pair(bb, path_a, path_b, replay, ACTIONS, by_value, clicker):
    ea, oa = replay(path_a)
    eb, ob = replay(path_b)
    if oa is None or ob is None:
        return {"replay_failed": True}
    assert c2.board_bytes(oa) == bb and c2.board_bytes(ob) == bb, \
        "replay did not reproduce the collision key -- non-determinism?"
    mismatches = []
    for act in ACTIONS:
        ea2, eb2 = copy.deepcopy(ea), copy.deepcopy(eb)
        oa2 = c2.press(ea2, act, by_value, clicker)
        ob2 = c2.press(eb2, act, by_value, clicker)
        same, detail = compare_obs(oa2, ob2)
        if not same:
            mismatches.append({"act": act, "detail": detail})
    return {"replay_failed": False, "mismatches": mismatches}


def compare_obs(oa, ob):
    if oa is None and ob is None:
        return True, None
    if (oa is None) != (ob is None):
        return False, "one obs is None, the other is not"
    fa, fb = np.array(oa.frame), np.array(ob.frame)
    if fa.shape != fb.shape:
        return False, "frame SHAPE mismatch a=%s b=%s" % (fa.shape, fb.shape)
    if not np.array_equal(fa, fb):
        n_diff = int(np.sum(fa != fb))
        return False, "frame CONTENT mismatch, same shape %s, %d cells differ" % (fa.shape, n_diff)
    if oa.levels_completed != ob.levels_completed:
        return False, "levels_completed a=%s b=%s" % (oa.levels_completed, ob.levels_completed)
    if str(oa.state) != str(ob.state):
        return False, "state a=%s b=%s" % (oa.state, ob.state)
    return True, None


C1_PKL = os.path.join("results", "dc22_c3_control1.pkl")
C2_PKL = os.path.join("results", "dc22_c3_control2.pkl")


def run_stage_control1(budget_seconds):
    import pickle
    log("=== CONTROL 1: L1-entry positive control ===")
    win, expanded, states, deaths, elapsed, root_lvl = control1_l1_win(budget_seconds)
    log("CONTROL1 DONE win=%s expanded=%d states=%d deaths=%d elapsed=%.1fs"
        % (win is not None, expanded, states, deaths, elapsed))
    with open(C1_PKL, "wb") as f:
        pickle.dump(dict(win=win, expanded=expanded, states=states, deaths=deaths,
                          elapsed=elapsed, root_lvl=root_lvl, budget=budget_seconds), f)
    log("WROTE %s" % C1_PKL)


def run_stage_control2(collect_seconds, pair_cap, min_collisions):
    import pickle
    log("=== CONTROL 2: L2 collision-divergence sample ===")
    r = collect_l2_collisions(collect_seconds)
    collisions = r["collisions"]
    log("CONTROL2-COLLECT DONE expanded=%d states=%d collisions=%d deaths=%d elapsed=%.1fs"
        % (r["expanded"], r["states"], len(collisions), r["deaths"], r["elapsed"]))

    sample = stratified_sample(collisions, pair_cap)
    log("CONTROL2 verifying %d sampled pairs (of %d collected)" % (len(sample), len(collisions)))
    mismatch_pairs = []
    replay_fail = 0
    for i, (bb, pa, pb, d) in enumerate(sample):
        res = verify_pair(bb, pa, pb, r["replay"], r["ACTIONS"], r["by_value"], r["clicker"])
        if res.get("replay_failed"):
            replay_fail += 1
            continue
        if res["mismatches"]:
            mismatch_pairs.append((bb, pa, pb, d, res["mismatches"]))
        if (i + 1) % 20 == 0:
            log("CONTROL2 verified %d/%d, mismatches so far=%d" % (i + 1, len(sample), len(mismatch_pairs)))

    depths_seen = sorted({c[3] for c in collisions})
    depths_sampled = sorted({c[3] for c in sample})
    with open(C2_PKL, "wb") as f:
        pickle.dump(dict(
            n_collisions=len(collisions), expanded=r["expanded"], states=r["states"],
            deaths=r["deaths"], elapsed=r["elapsed"], collect_seconds=collect_seconds,
            sample_n=len(sample), pair_cap=pair_cap, min_collisions=min_collisions,
            replay_fail=replay_fail, mismatch_pairs=mismatch_pairs,
            depths_seen=depths_seen, depths_sampled=depths_sampled,
        ), f)
    log("WROTE %s" % C2_PKL)


def run_stage_report():
    import pickle
    with open(C1_PKL, "rb") as f:
        c1 = pickle.load(f)
    with open(C2_PKL, "rb") as f:
        c2r = pickle.load(f)

    out_path = os.path.join("results", "dc22-c3-verify-20260817.md")
    lines = []
    win, expanded, states, deaths, elapsed = c1["win"], c1["expanded"], c1["states"], c1["deaths"], c1["elapsed"]
    l1_budget = c1["budget"]
    collisions_n = c2r["n_collisions"]
    mismatch_pairs = c2r["mismatch_pairs"]
    sample_n = c2r["sample_n"]
    depths_seen = c2r["depths_seen"]
    depths_sampled = c2r["depths_sampled"]
    replay_fail = c2r["replay_fail"]
    pair_cap = c2r["pair_cap"]
    min_collisions = c2r["min_collisions"]
    l2_collect_seconds = c2r["collect_seconds"]
    r = dict(expanded=c2r["expanded"], states=c2r["states"], deaths=c2r["deaths"], elapsed=c2r["elapsed"])

    exhaustion_void = (win is None) or (len(mismatch_pairs) > 0)
    verdict = "EXHAUSTION_VOID" if exhaustion_void else "EXHAUSTION_VERIFIED"

    lines.append("# dc22 L2 exhaustion -- c3 independent verification\n")
    lines.append("Verdict: **%s**\n" % verdict)
    lines.append("")
    lines.append("## Control 1 -- positive control on a known L1 win\n")
    lines.append("Same board-key function (`board_bytes` = last-plane bytes), same node "
                 "handling (path-frontier BFS, replay-from-root on pop, dedup on board key, "
                 "death dropped per c2's measured `death_continues=False`), same 6-action "
                 "alphabet shape (4 arrows + click-A + click-B, buttons detected with the "
                 "identical filter c2/c1 use), imported byte-identical from `dc22_c2_l2chain.py` "
                 "and run from the L1 ENTRY (`env.reset()`, `levels_completed=0`) instead of "
                 "the L2 root.\n")
    lines.append("")
    lines.append("- Known win exists: `bridge.py`'s own greedy `Bridge` driver reaches "
                 "`levels_completed>=1` in 25 actions (`results/dc22-c2-engineering-20260817.md` "
                 "smoke (a): `L2 root at i=25 l1_actions=25`).")
    lines.append("- This BFS's own result: **win=%s**, path length=%s"
                 % (win is not None, len(win) if win else "n/a"))
    lines.append("- Census: expanded=%d states=%d deaths=%d elapsed=%.1fs budget=%ds"
                 % (expanded, states, deaths, elapsed, l1_budget))
    if win:
        lines.append("- Win action sequence: `%r`" % (win,))
    lines.append("")
    if win is not None:
        lines.append("**PASS** -- the identical search machinery independently found a win "
                     "from L1 entry. The machinery is capable of finding a win when one exists.")
    else:
        lines.append("**FAIL** -- the identical search machinery did NOT find the known L1 win "
                     "within budget=%ds (expanded=%d nodes). Either the budget was too small "
                     "or the machinery cannot find this class of win -- in both cases the c2 "
                     "L2 null is uninterpretable: a search that cannot find a win it is known "
                     "to be reachable from cannot be trusted to report the absence of one "
                     "elsewhere." % (l1_budget, expanded))
    lines.append("")

    lines.append("## Control 2 -- collision-divergence sample on L2\n")
    lines.append("Re-ran the bounded L2 BFS (same `board_bytes`/`press`, same node handling, "
                 "same alphabet, same `death_continues=False`) recording the FIRST path to "
                 "reach each board key; every later path landing on an already-seen key is "
                 "logged as a collision pair.\n")
    lines.append("")
    lines.append("- Collection run: expanded=%d distinct-keys=%d deaths=%d elapsed=%.1fs "
                 "budget=%ds" % (r["expanded"], r["states"], r["deaths"], r["elapsed"], l2_collect_seconds))
    lines.append("- Collisions collected: **%d** (target >= %d; %s), spread across depths %s"
                 % (collisions_n, min_collisions,
                    "met" if collisions_n >= min_collisions else "NOT MET -- reporting all collected",
                    depths_seen if len(depths_seen) <= 30 else "%s..%s (%d distinct depths)" % (depths_seen[0], depths_seen[-1], len(depths_seen))))
    lines.append("- Sampled for full replay-and-compare: **%d** (cap=%d), spread across depths %s"
                 % (sample_n, pair_cap, depths_sampled if len(depths_sampled) <= 30 else "%s..%s (%d distinct)" % (depths_sampled[0], depths_sampled[-1], len(depths_sampled))))
    lines.append("- Replay failures (path no longer replays cleanly): %d" % replay_fail)
    lines.append("- Divergence found (any successor mismatch under any alphabet action): "
                 "**%d / %d verified pairs**" % (len(mismatch_pairs), sample_n - replay_fail))
    lines.append("")
    if not collisions_n:
        lines.append("**NO COLLISIONS OBSERVED** within the collection budget -- the BFS did "
                     "not yet revisit any board key. This is a WEAKER instrument than intended "
                     "(no divergence sample could be built); it does not by itself confirm or "
                     "refute soundness. Widen `--l2-collect-seconds` to get a sample.")
    elif mismatch_pairs:
        lines.append("**VOID** -- at least one collision pair produced a byte-different "
                     "successor (frame, `levels_completed`, or `state`) under an identical "
                     "action from an identical board key. Evidence:\n")
        for bb, pa, pb, d, mism in mismatch_pairs[:10]:
            lines.append("  - depth=%d path_a=%r path_b=%r" % (d, pa, pb))
            for m in mism:
                lines.append("      action=%r %s" % (m["act"], m["detail"]))
        if len(mismatch_pairs) > 10:
            lines.append("  ... and %d more mismatched pairs (truncated)." % (len(mismatch_pairs) - 10))
    else:
        lines.append("**PASS** -- zero mismatches over the sample. As far as this instrument "
                     "can see, the board-key function does not merge distinguishable states on "
                     "L2.")
    lines.append("")

    lines.append("## Scope statement\n")
    lines.append("This closure (c2's `L2 EXHAUSTED`) covers exactly the **6-action alphabet** "
                 "{UP, DOWN, LEFT, RIGHT, click-A, click-B} from the L2 root -- the same "
                 "alphabet this verification reused. The other 49 clickable objects on this "
                 "board were separately measured inert, per the b/c-series cited in "
                 "`results/dc22-L2-ratchet-20260817.md` and `results/dc22-c2-engineering-"
                 "20260817.md`; that inertness was measured at a **bounded set of button "
                 "states** (cycle-detect stopped at 40 presses per button, true periods "
                 "measured only as \">40, unresolved\"), and neither this script nor c2 widens "
                 "or narrows that scope -- an object inert at the sampled button states has "
                 "not been re-tested at states beyond press 40.\n")
    lines.append("")
    lines.append("Death policy used throughout this script (`death_continues=False`) is c2's "
                 "own measured finding (3/3 runs, `results/dc22-c2-engineering-20260817.md`), "
                 "reused as a constant rather than re-measured here -- an assumption, stated "
                 "plainly, not a new measurement.\n")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    log("WROTE %s" % out_path)
    print("VERDICT: %s" % verdict, flush=True)
    print("DONE", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["control1", "control2", "report"], required=True)
    ap.add_argument("--l1-budget-seconds", type=int, default=300)
    ap.add_argument("--l2-collect-seconds", type=int, default=300)
    ap.add_argument("--pair-cap", type=int, default=100)
    ap.add_argument("--min-collisions", type=int, default=150)
    args = ap.parse_args()
    os.makedirs("results", exist_ok=True)
    if args.stage == "control1":
        run_stage_control1(args.l1_budget_seconds)
    elif args.stage == "control2":
        run_stage_control2(args.l2_collect_seconds, args.pair_cap, args.min_collisions)
    else:
        run_stage_report()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
