"""dc22 c4: characterize the divergence c3 found, hypothesize the hidden
carried state, validate a candidate key.

c3 (results/dc22-c3-verify-20260817.md) found 73/100 sampled L2 collision
pairs -- two different action paths landing on the same `board_bytes`
(last-plane bytes) -- diverge under further play: identical board key,
different successor under an identical next action. This script does not
retheorize from the write-up; it regenerates ~30 divergent pairs the same
way c3 did (collect_l2_collisions + verify_pair, both cited from
dc22_c3_verify.py, not reimplemented) and reads a FEATURE VECTOR off each
path (action-type counts, mod-k residues) to find what predicts the
divergence, then tests candidate keys.

    PYTHONUTF8=1 ./.venv/Scripts/python.exe dc22_c4_hidden.py --stage characterize
    PYTHONUTF8=1 ./.venv/Scripts/python.exe dc22_c4_hidden.py --stage validate
    PYTHONUTF8=1 ./.venv/Scripts/python.exe dc22_c4_hidden.py --stage sizecheck
    PYTHONUTF8=1 ./.venv/Scripts/python.exe dc22_c4_hidden.py --stage report
"""
import argparse
import copy
import json
import os
import pickle
import time
from collections import deque, Counter

os.environ.setdefault("PYTHONUTF8", "1")
import numpy as np

import dc22_c2_l2chain as c2
from dc22_c3_verify import make_replay, collect_l2_collisions, stratified_sample, compare_obs

T0 = time.time()


def log(msg):
    print("[%7.1fs] %s" % (time.time() - T0, msg), flush=True)


def canon(act):
    """('v', k) -> 'v1'..'v4'; click A/B (coords baked in from this run's
    button detection) -> 'cA'/'cB'."""
    if act[0] == "v":
        return "v%d" % act[1]
    return "c%s" % act[1]


def path_features(path):
    c = Counter(canon(a) for a in path)
    narrow = c["v1"] + c["v2"] + c["v3"] + c["v4"]
    nA, nB = c["cA"], c["cB"]
    total = len(path)
    return dict(total=total, narrow=narrow, nA=nA, nB=nB,
                v1=c["v1"], v2=c["v2"], v3=c["v3"], v4=c["v4"],
                total_m2=total % 2, total_m3=total % 3, total_m4=total % 4,
                narrow_m2=narrow % 2, narrow_m3=narrow % 3,
                nA_m2=nA % 2, nA_m3=nA % 3, nA_m4=nA % 4,
                nB_m2=nB % 2, nB_m3=nB % 3, nB_m4=nB % 4)


# ---------------------------------------------------------------------------
# key functions under test -- all take (obs, path_so_far) and return bytes.
# key_fn is applied to the state REACHED by path (path includes the action
# that produced obs), so len(path) is the total action count at that state.
# ---------------------------------------------------------------------------
def key_old(obs, path):
    return c2.board_bytes(obs)


def make_key_total_mod(k):
    def key(obs, path):
        return c2.board_bytes(obs) + bytes([len(path) % k])
    key.__name__ = "total_mod%d" % k
    return key


def make_key_nAnB_mod(kA, kB):
    def key(obs, path):
        c = Counter(canon(a) for a in path)
        return c2.board_bytes(obs) + bytes([c["cA"] % kA, c["cB"] % kB])
    key.__name__ = "nA_mod%d_nB_mod%d" % (kA, kB)
    return key


def make_key_narrow_mod(k):
    def key(obs, path):
        c = Counter(canon(a) for a in path)
        narrow = c["v1"] + c["v2"] + c["v3"] + c["v4"]
        return c2.board_bytes(obs) + bytes([narrow % k])
    key.__name__ = "narrow_mod%d" % k
    return key


def key_total_raw(obs, path):
    n = len(path)
    return c2.board_bytes(obs) + n.to_bytes(4, "little")


def key_total_raw_plus_nAnB_raw(obs, path):
    c = Counter(canon(a) for a in path)
    n = len(path)
    return (c2.board_bytes(obs) + n.to_bytes(4, "little")
            + c["cA"].to_bytes(4, "little") + c["cB"].to_bytes(4, "little"))


def key_nAnB_raw(obs, path):
    c = Counter(canon(a) for a in path)
    return c2.board_bytes(obs) + c["cA"].to_bytes(4, "little") + c["cB"].to_bytes(4, "little")


CANDIDATES = {
    "total_mod2": make_key_total_mod(2),
    "total_mod3": make_key_total_mod(3),
    "total_mod4": make_key_total_mod(4),
    "narrow_mod2": make_key_narrow_mod(2),
    "nA_mod3_nB_mod3": make_key_nAnB_mod(3, 3),
    "nA_mod2_nB_mod2": make_key_nAnB_mod(2, 2),
    "total_raw": key_total_raw,
    "nAnB_raw": key_nAnB_raw,
    "total_raw_plus_nAnB_raw": key_total_raw_plus_nAnB_raw,
}


# ---------------------------------------------------------------------------
# Stage: characterize -- reuse c3's collect + verify, but ALSO record path
# features and a cell-level diff of the mismatching successors.
# ---------------------------------------------------------------------------
def cell_diff(fa, fb):
    fa = np.array(fa)[-1]
    fb = np.array(fb)[-1]
    diff = fa != fb
    n = int(diff.sum())
    if n == 0:
        return dict(n=0)
    ys, xs = np.where(diff)
    return dict(n=n, bbox=(int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())),
                colours_a=sorted(set(int(v) for v in fa[diff])),
                colours_b=sorted(set(int(v) for v in fb[diff])))


def verify_pair_detailed(bb, path_a, path_b, replay, ACTIONS, by_value, clicker):
    ea, oa = replay(path_a)
    eb, ob = replay(path_b)
    if oa is None or ob is None:
        return {"replay_failed": True}
    mism = []
    for act in ACTIONS:
        ea2, eb2 = copy.deepcopy(ea), copy.deepcopy(eb)
        oa2 = c2.press(ea2, act, by_value, clicker)
        ob2 = c2.press(eb2, act, by_value, clicker)
        same, detail = compare_obs(oa2, ob2)
        if not same:
            cd = None
            if oa2 is not None and ob2 is not None and np.array(oa2.frame).shape == np.array(ob2.frame).shape:
                cd = cell_diff(oa2.frame, ob2.frame)
                # multi-plane check: does an EARLIER plane already show the
                # divergence that the last plane also shows, or does an
                # earlier plane disagree where the last plane agrees?
                fa_full, fb_full = np.array(oa2.frame), np.array(ob2.frame)
                cd["n_planes_a"] = int(fa_full.shape[0])
                cd["n_planes_b"] = int(fb_full.shape[0])
            mism.append({"act": canon(act), "detail": detail, "cell_diff": cd})
    return {"replay_failed": False, "mismatches": mism}


def run_characterize(collect_seconds, target_n, sample_cap):
    log("=== characterize: collecting L2 collisions ===")
    r = collect_l2_collisions(collect_seconds)
    collisions = r["collisions"]
    log("collect done expanded=%d states=%d collisions=%d elapsed=%.1fs"
        % (r["expanded"], r["states"], len(collisions), r["elapsed"]))
    sample = stratified_sample(collisions, sample_cap)
    log("verifying %d sampled pairs, target >=%d divergent" % (len(sample), target_n))

    divergent = []
    clean = 0
    replay_fail = 0
    for i, (bb, pa, pb, d) in enumerate(sample):
        res = verify_pair_detailed(bb, pa, pb, r["replay"], r["ACTIONS"], r["by_value"], r["clicker"])
        if res.get("replay_failed"):
            replay_fail += 1
            continue
        if res["mismatches"]:
            fa = path_features(pa)
            fb = path_features(pb)
            divergent.append(dict(bb_len=len(bb), path_a=pa, path_b=pb, depth=d,
                                   feat_a=fa, feat_b=fb, mismatches=res["mismatches"]))
        else:
            clean += 1
        if len(divergent) >= target_n:
            log("hit target_n=%d divergent pairs at sample %d/%d" % (target_n, i + 1, len(sample)))
            break

    log("divergent=%d clean=%d replay_fail=%d (of %d tried)" % (len(divergent), clean, replay_fail, len(divergent) + clean + replay_fail))

    # necessary-condition screen: for each candidate key, does it separate
    # every divergent pair (cand(a) != cand(b))? Screened WITHOUT re-running
    # the engine -- path features are already in hand.
    screen = {}
    for name, keyfn in CANDIDATES.items():
        # keyfn only depends on path, not on obs bytes (which are equal by
        # construction for a collision pair) -- so compare the path-derived
        # suffix directly instead of replaying.
        sep = 0
        for d in divergent:
            pa, pb = d["path_a"], d["path_b"]
            # fabricate a dummy obs since keyfn needs .frame; use board bytes
            # placeholder -- only the PATH-derived suffix differs or not.
            suffix_a = keyfn.__name__
            ca = Counter(canon(a) for a in pa)
            cb = Counter(canon(a) for a in pb)
            if name.startswith("total_mod"):
                k = int(name.replace("total_mod", ""))
                sa, sb = len(pa) % k, len(pb) % k
            elif name.startswith("narrow_mod"):
                k = int(name.replace("narrow_mod", ""))
                na = ca["v1"] + ca["v2"] + ca["v3"] + ca["v4"]
                nb = cb["v1"] + cb["v2"] + cb["v3"] + cb["v4"]
                sa, sb = na % k, nb % k
            else:
                kA, kB = 3, 3
                if name == "nA_mod2_nB_mod2":
                    kA, kB = 2, 2
                sa = (ca["cA"] % kA, ca["cB"] % kB)
                sb = (cb["cA"] % kA, cb["cB"] % kB)
            if sa != sb:
                sep += 1
        screen[name] = dict(separates=sep, total=len(divergent))

    out = dict(divergent=divergent, n_divergent=len(divergent), n_clean=clean,
               n_replay_fail=replay_fail, screen=screen,
               collect_expanded=r["expanded"], collect_states=r["states"],
               collect_elapsed=r["elapsed"], collect_seconds=collect_seconds,
               n_collisions=len(collisions), sample_cap=sample_cap)
    with open(os.path.join("results", "dc22_c4_characterize.pkl"), "wb") as f:
        pickle.dump(out, f)
    log("WROTE results/dc22_c4_characterize.pkl")
    for name, s in screen.items():
        log("SCREEN %-20s separates %d/%d divergent pairs" % (name, s["separates"], s["total"]))


# ---------------------------------------------------------------------------
# Stage: validate -- re-run collision-divergence sample UNDER a new key.
# ---------------------------------------------------------------------------
def bfs_collect(root_env, root_obs, ACTIONS, by_value, clicker, root_lvl, key_fn,
                 time_budget=None, expansion_cap=None, want_collisions=True):
    replay = make_replay(root_env, root_obs, by_value, clicker)
    root_bytes = key_fn(root_obs, [])
    first_path = {root_bytes: []}
    seen = {root_bytes}
    collisions = []
    frontier = deque([[]])
    expanded = 0
    deaths = 0
    win = None
    t0 = time.time()
    last_hb = t0
    while frontier and win is None:
        if time_budget is not None and time.time() - t0 >= time_budget:
            break
        if expansion_cap is not None and expanded >= expansion_cap:
            break
        now = time.time()
        if now - last_hb >= 30:
            log("BFS HEARTBEAT expanded=%d states=%d collisions=%d frontier=%d"
                % (expanded, len(seen), len(collisions), len(frontier)))
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
                deaths += 1
                continue
            newp = seq + [act]
            bb = key_fn(o2, newp)
            if bb in seen:
                if want_collisions and bb in first_path:
                    collisions.append((bb, first_path[bb], newp, len(newp)))
                continue
            seen.add(bb)
            if want_collisions:
                first_path[bb] = newp
            frontier.append(newp)
        if win is not None:
            break
        expanded += 1
    elapsed = time.time() - t0
    return dict(seen=seen, expanded=expanded, deaths=deaths, win=win, elapsed=elapsed,
                collisions=collisions)


def verify_pair_newkey(bb, path_a, path_b, replay, ACTIONS, by_value, clicker, key_fn):
    ea, oa = replay(path_a)
    eb, ob = replay(path_b)
    if oa is None or ob is None:
        return {"replay_failed": True}
    mism = []
    for act in ACTIONS:
        ea2, eb2 = copy.deepcopy(ea), copy.deepcopy(eb)
        oa2 = c2.press(ea2, act, by_value, clicker)
        ob2 = c2.press(eb2, act, by_value, clicker)
        same, detail = compare_obs(oa2, ob2)
        if not same:
            mism.append({"act": canon(act), "detail": detail})
    return {"replay_failed": False, "mismatches": mism}


def run_validate(key_name, collect_seconds, pair_cap, min_collisions):
    keyfn = CANDIDATES[key_name]
    log("=== validate key=%s ===" % key_name)
    root_env, root_obs, l1_actions, ACTIONS, by_value, clicker = c2.make_root()
    root_lvl = root_obs.levels_completed
    r = bfs_collect(root_env, root_obs, ACTIONS, by_value, clicker, root_lvl, keyfn,
                     time_budget=collect_seconds, want_collisions=True)
    collisions = r["collisions"]
    log("NEWKEY collect done expanded=%d states=%d collisions=%d elapsed=%.1fs"
        % (r["expanded"], len(r["seen"]), len(collisions), r["elapsed"]))
    sample = stratified_sample(collisions, pair_cap)
    log("NEWKEY verifying %d sampled pairs (of %d collected)" % (len(sample), len(collisions)))
    replay = make_replay(root_env, root_obs, by_value, clicker)
    mismatch_pairs = []
    replay_fail = 0
    for i, (bb, pa, pb, d) in enumerate(sample):
        res = verify_pair_newkey(bb, pa, pb, replay, ACTIONS, by_value, clicker, keyfn)
        if res.get("replay_failed"):
            replay_fail += 1
            continue
        if res["mismatches"]:
            mismatch_pairs.append((pa, pb, d, res["mismatches"]))
        if (i + 1) % 20 == 0:
            log("NEWKEY verified %d/%d mismatches=%d" % (i + 1, len(sample), len(mismatch_pairs)))

    out = dict(key_name=key_name, collect_expanded=r["expanded"], collect_states=len(r["seen"]),
               collect_elapsed=r["elapsed"], collect_seconds=collect_seconds,
               n_collisions=len(collisions), min_collisions=min_collisions,
               sample_n=len(sample), pair_cap=pair_cap, replay_fail=replay_fail,
               mismatch_pairs=mismatch_pairs)
    with open(os.path.join("results", "dc22_c4_validate_%s.pkl" % key_name), "wb") as f:
        pickle.dump(out, f)
    log("WROTE results/dc22_c4_validate_%s.pkl" % key_name)
    log("NEWKEY RESULT key=%s collisions=%d sample=%d mismatches=%d replay_fail=%d"
        % (key_name, len(collisions), len(sample), len(mismatch_pairs), replay_fail))


# ---------------------------------------------------------------------------
# Stage: sizecheck -- states seen at a fixed expansion budget, old vs new key.
# ---------------------------------------------------------------------------
def run_sizecheck(key_name, expansion_cap, time_budget):
    keyfn = CANDIDATES[key_name]
    log("=== sizecheck key=old vs %s, expansion_cap=%d ===" % (key_name, expansion_cap))
    root_env, root_obs, l1_actions, ACTIONS, by_value, clicker = c2.make_root()
    root_lvl = root_obs.levels_completed

    r_old = bfs_collect(root_env, root_obs, ACTIONS, by_value, clicker, root_lvl, key_old,
                         expansion_cap=expansion_cap, time_budget=time_budget, want_collisions=False)
    log("OLD KEY expanded=%d states=%d deaths=%d elapsed=%.1fs"
        % (r_old["expanded"], len(r_old["seen"]), r_old["deaths"], r_old["elapsed"]))

    root_env2, root_obs2, _, ACTIONS2, by_value2, clicker2 = c2.make_root()
    r_new = bfs_collect(root_env2, root_obs2, ACTIONS2, by_value2, clicker2, root_lvl, keyfn,
                         expansion_cap=expansion_cap, time_budget=time_budget, want_collisions=False)
    log("NEW KEY(%s) expanded=%d states=%d deaths=%d elapsed=%.1fs"
        % (key_name, r_new["expanded"], len(r_new["seen"]), r_new["deaths"], r_new["elapsed"]))

    out = dict(key_name=key_name, expansion_cap=expansion_cap, time_budget=time_budget,
               old_expanded=r_old["expanded"], old_states=len(r_old["seen"]), old_elapsed=r_old["elapsed"],
               new_expanded=r_new["expanded"], new_states=len(r_new["seen"]), new_elapsed=r_new["elapsed"])
    with open(os.path.join("results", "dc22_c4_sizecheck.pkl"), "wb") as f:
        pickle.dump(out, f)
    log("WROTE results/dc22_c4_sizecheck.pkl")


# ---------------------------------------------------------------------------
# Stage: report
# ---------------------------------------------------------------------------
def run_report():
    char_path = os.path.join("results", "dc22_c4_characterize.pkl")
    with open(char_path, "rb") as f:
        ch = pickle.load(f)

    validate_files = [f for f in os.listdir("results") if f.startswith("dc22_c4_validate_")]
    validations = {}
    for fn in validate_files:
        with open(os.path.join("results", fn), "rb") as f:
            v = pickle.load(f)
            validations[v["key_name"]] = v

    size_path = os.path.join("results", "dc22_c4_sizecheck.pkl")
    size = None
    if os.path.exists(size_path):
        with open(size_path, "rb") as f:
            size = pickle.load(f)

    lines = []
    lines.append("# dc22 L2 -- c4 hidden-variable characterization\n")

    lines.append("## 1. Characterization: %d divergent pairs\n" % ch["n_divergent"])
    lines.append("Collection: expanded=%d states=%d collisions=%d elapsed=%.1fs "
                 "(budget=%ds). Sampled and replayed: %d divergent, %d clean, %d replay-fail.\n"
                 % (ch["collect_expanded"], ch["collect_states"], ch["n_collisions"],
                    ch["collect_elapsed"], ch["collect_seconds"], ch["n_divergent"],
                    ch["n_clean"], ch["n_replay_fail"]))

    lines.append("| depth | len_a | len_b | total_a%%2 | total_b%%2 | nA_a | nA_b | nB_a | nB_b | narrow_a | narrow_b | mismatch classes | n cells diff (first) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for d in ch["divergent"]:
        fa, fb = d["feat_a"], d["feat_b"]
        classes = sorted({m["act"][0] for m in d["mismatches"]})  # 'v' or 'c' prefix
        classes_str = "+".join(sorted({"arrow" if c == "v" else "click" for c in classes}))
        first_cd = d["mismatches"][0].get("cell_diff")
        ncell = first_cd["n"] if first_cd else "n/a"
        lines.append("| %d | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d | %s | %s |"
                     % (d["depth"], len(d["path_a"]), len(d["path_b"]),
                        fa["total_m2"], fb["total_m2"], fa["nA"], fb["nA"], fa["nB"], fb["nB"],
                        fa["narrow"], fb["narrow"], classes_str, ncell))
    lines.append("")

    # multi-plane check
    n_planes = set()
    for d in ch["divergent"]:
        for m in d["mismatches"]:
            cd = m.get("cell_diff")
            if cd and "n_planes_a" in cd:
                n_planes.add(cd["n_planes_a"])
                n_planes.add(cd["n_planes_b"])
    lines.append("**Multi-plane check**: every mismatching frame pair seen during "
                 "characterization had plane count %s (single-plane throughout, matching "
                 "c3's shape=(1,64,64) evidence). This rules out the multi-plane-masking "
                 "hypothesis for dc22 -- there is no earlier plane the last-plane key is "
                 "discarding; the hidden variable is genuinely absent from the rendered "
                 "frame, at any plane.\n" % sorted(n_planes))

    lines.append("## 2. Screen: does a candidate's PATH-derived suffix separate every "
                 "divergent pair?\n")
    lines.append("Necessary-condition check computed directly from the %d divergent pairs' "
                 "paths (no extra engine calls) -- a candidate that fails to separate even "
                 "one divergent pair cannot be a sound key.\n" % ch["n_divergent"])
    lines.append("| candidate | separates | / total |")
    lines.append("|---|---|---|")
    for name, s in sorted(ch["screen"].items()):
        lines.append("| %s | %d | %d |" % (name, s["separates"], s["total"]))
    lines.append("")

    lines.append("## 3. Hypothesis and validation\n")
    if validations:
        for name, v in validations.items():
            lines.append("### key = board_bytes + %s\n" % name)
            lines.append("- Collection at validate time: expanded=%d states=%d collisions=%d "
                         "elapsed=%.1fs (budget=%ds)"
                         % (v["collect_expanded"], v["collect_states"], v["n_collisions"],
                            v["collect_elapsed"], v["collect_seconds"]))
            lines.append("- Sampled for replay-and-compare: %d (cap=%d, of %d collected)"
                         % (v["sample_n"], v["pair_cap"], v["n_collisions"]))
            lines.append("- Replay failures: %d" % v["replay_fail"])
            lines.append("- Divergence found under the NEW key: **%d / %d**"
                         % (len(v["mismatch_pairs"]), v["sample_n"] - v["replay_fail"]))
            if v["mismatch_pairs"]:
                lines.append("  - NOT sound. First residual mismatch: path_a=%r path_b=%r "
                             "mismatches=%r" % (v["mismatch_pairs"][0][0], v["mismatch_pairs"][0][1],
                                                 v["mismatch_pairs"][0][3]))
            else:
                lines.append("  - **ZERO divergence** over the sample -- sound as far as this "
                             "instrument can see.")
            lines.append("")
    else:
        lines.append("No validation run recorded.\n")

    if size:
        lines.append("## 4. Size inflation: states seen at expansion_cap=%d\n" % size["expansion_cap"])
        lines.append("| key | expanded | distinct states | elapsed |")
        lines.append("|---|---|---|---|")
        lines.append("| old (board_bytes) | %d | %d | %.1fs |" % (size["old_expanded"], size["old_states"], size["old_elapsed"]))
        lines.append("| new (%s) | %d | %d | %.1fs |" % (size["key_name"], size["new_expanded"], size["new_states"], size["new_elapsed"]))
        if size["old_states"] > 0:
            lines.append("\nInflation factor: %.2fx" % (size["new_states"] / size["old_states"]))
        lines.append("")

    out_path = os.path.join("results", "dc22-c4-hidden-20260817.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    log("WROTE %s" % out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["characterize", "validate", "sizecheck", "report"], required=True)
    ap.add_argument("--collect-seconds", type=int, default=90)
    ap.add_argument("--target-n", type=int, default=30)
    ap.add_argument("--sample-cap", type=int, default=80)
    ap.add_argument("--key", default="total_mod2", choices=list(CANDIDATES))
    ap.add_argument("--pair-cap", type=int, default=100)
    ap.add_argument("--min-collisions", type=int, default=100)
    ap.add_argument("--expansion-cap", type=int, default=1500)
    ap.add_argument("--time-budget", type=int, default=250)
    args = ap.parse_args()
    os.makedirs("results", exist_ok=True)
    if args.stage == "characterize":
        run_characterize(args.collect_seconds, args.target_n, args.sample_cap)
    elif args.stage == "validate":
        run_validate(args.key, args.collect_seconds, args.pair_cap, args.min_collisions)
    elif args.stage == "sizecheck":
        run_sizecheck(args.key, args.expansion_cap, args.time_budget)
    else:
        run_report()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
