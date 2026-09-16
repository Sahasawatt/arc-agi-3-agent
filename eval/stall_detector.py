"""stall_detector.py — B80 L2 pre-read: would an AVO-style supervisor have SEEN our stalls, and in TIME? (0 GPU)

  python eval/stall_detector.py <events_dir> --signal novelty [--window N] [--theta F]
  python eval/stall_detector.py <events_dir> --signal dwell --sweep

AVO reports 100 % RHAE on the public set with a supervisor that watches the trajectory for stagnation and redirects the
agent. B73 already established that we stall. That is not the question L2 has to win. The two that are:

  1. can a CAUSAL detector see the stall from what is on the trajectory at the time, and
  2. does it see it while there is still budget to redirect into?

Two signals, because the first one is measured blind here and the finding is worth keeping:

  novelty — over a sliding window of the last W board-changing actions on the current level, the fraction reaching a
            board state this game has never been in. Below theta = re-treading. **Measured 2026-09-11: blind on our
            runs.** Our stall levels are 94-97 % novel (tn36 L1 241/251, vc33 L4 97/103, s5i5 L3 63/65, su15 L2 71/75) —
            the agent generates new states relentlessly while converging on nothing, so a supervisor watching for state
            revisits sees nothing to redirect.

  dwell   — actions spent on the current level without clearing it. Trivially able to fire on a stall; the whole
            question is what it costs, so `--sweep` prices it instead of picking a threshold: for each candidate T it
            reports how many never-cleared level-episodes reach T (what a supervisor could act on), how much wall is
            left when they do, and how many EVENTUALLY-CLEARED episodes needed more than T actions — every one of those
            is a redirect fired into a solve that was going to land.

Every reading is causal: a fire is stamped with the wall clock at that action and never uses the level's outcome.
Classification of a fire is the outcome and is applied afterwards: **target** (level never cleared), **slow** (cleared
more than `soon` actions later), **false** (cleared within `soon`).
"""
import argparse, collections, glob, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")

# B73's measured stalls, as (game, level). The positive control: a usable detector must fire on these.
# RUN-SCOPED: B73 measured them on `thui-fast-v0` draw 2 ONLY. Another run reaches different levels on the same
# games (a7 clears su15 further, for one), so a MISS on any other events dir is the control being drawn from the
# wrong population, not the detector going blind. Read this control on fast-v0-d2; read the other runs as a
# replication of the target/FP counts, not of the control.
B73_STALLS = {("s5i5", 3), ("ft09", 4), ("sb26", 2), ("su15", 2), ("tn36", 1), ("vc33", 4)}


def wall_seconds(events):
    """action_num -> seconds since the game's first turn, from the analysis transcripts' own clock headers."""
    stamps = []
    for d in events:
        if d.get("type") != "analysis":
            continue
        m = re.match(r"--- analysis_step=\d+ \| action=(\d+) \| (\d\d):(\d\d):(\d\d) \|", d["transcript"])
        if m:
            a = int(m.group(1))
            h, mi, s = map(int, m.groups()[1:])
            stamps.append((a, h * 3600 + mi * 60 + s))
    if not stamps:
        return {}, 0
    base, out, prev, day = stamps[0][1], {}, None, 0
    for a, t in stamps:
        if prev is not None and t + day * 86400 - base < prev:      # wall clock crossed midnight
            day += 1
        v = t + day * 86400 - base
        out[a], prev = v, v
    return out, max(out.values()) if out else 0


def read_game(path):
    ev = [json.loads(l) for l in open(path, encoding="utf-8")]
    acts = [d for d in ev if d.get("type") == "action"]
    clock, wall = wall_seconds(ev)
    return acts, clock, wall


def level_of(a):
    """The level an action was PLAYED on. A clearing action carries the NEXT level in its `level` field --
    verified on tr87 d2 (i=61 level_field=2 prev=1, and three more), and it is the difference between an
    episode reading as never-cleared and reading as cleared in 0 actions."""
    return int(a["level"]) - (1 if a.get("level_completed") in (True, "True") else 0)


def episodes(acts):
    """(level -> {start,n,cleared_at,idx}) in visit order; cleared_at is the index of the clearing action."""
    per = collections.OrderedDict()
    for i, a in enumerate(acts):
        lv = level_of(a)
        d = per.setdefault(lv, {"start": i, "n": 0, "cleared_at": None, "idx": []})
        d["n"] += 1
        d["idx"].append(i)
        if a.get("level_completed") in (True, "True"):
            d["cleared_at"] = i
    return per


def at(clock, action_num):
    ks = [k for k in clock if k <= action_num]
    return clock[max(ks)] if ks else 0


def fire_novelty(acts, window, theta):
    seen, fires = set(), []
    win, cur = collections.deque(maxlen=window), None
    for i, a in enumerate(acts):
        lv = int(a["level"])
        if lv != cur:
            cur, win = lv, collections.deque(maxlen=window)
        if a.get("board_changed") in (True, "True"):
            k = hash(a["board_ascii"])
            win.append(0 if k in seen else 1)
            seen.add(k)
        if len(win) == window and not any(f["level"] == lv for f in fires):
            frac = sum(win) / window
            if frac <= theta:
                fires.append({"level": lv, "i": i, "action_num": int(a["action_num"]), "score": frac})
    return fires


def fire_dwell(acts, thresh, clock=None, wall=0, min_left=0.0):
    """Fire the first time `thresh` actions have been spent on the current level without a clear.

    `min_left` is a BUDGET guard, not a fitted one: a fire with less than that fraction of the wall remaining
    cannot be redirected into anything, so firing there is noise in every direction. It is definitional and has
    no free parameter beyond the operator's own answer to "how much wall does a redirect need".
    """
    fires, per = [], episodes(acts)
    for lv, d in per.items():
        if len(d["idx"]) < thresh:
            continue
        i = d["idx"][thresh - 1]
        if d["cleared_at"] is not None and d["cleared_at"] < i:
            continue                                   # already cleared before reaching the threshold
        if min_left and wall and clock is not None:
            if 1 - at(clock, int(acts[i]["action_num"])) / wall < min_left:
                continue
        fires.append({"level": lv, "i": i, "action_num": int(acts[i]["action_num"]), "score": thresh})
    return fires


def load(events_dir):
    games = []
    for p in sorted(glob.glob(os.path.join(events_dir, "*_p0_events.jsonl"))):
        acts, clock, wall = read_game(p)
        if acts:
            games.append((os.path.basename(p)[:4], acts, clock, wall))
    return games


def classify(games, fire_fn, soon):
    rows, tot = [], collections.Counter()
    for g, acts, clock, wall in games:
        per = episodes(acts)
        for f in fire_fn(acts, clock, wall):
            lv, i = f["level"], f["i"]
            cleared = per[lv]["cleared_at"]
            kind = "target" if cleared is None else ("false" if cleared - i <= soon else "slow")
            t = at(clock, f["action_num"])
            rows.append({"game": g, "level": lv, "kind": kind, "action_num": f["action_num"], "t_s": t,
                         "wall_s": wall, "left_frac": round(1 - t / wall, 3) if wall else None,
                         "score": f["score"], "level_actions": per[lv]["n"]})
            tot[kind] += 1
        for lv, d in per.items():                       # negative control: fast solves must not fire
            if d["cleared_at"] is not None and d["cleared_at"] - d["start"] <= soon:
                tot["fast_solves"] += 1
    fired = {(r["game"], r["level"]) for r in rows}
    for r in rows:
        if r["kind"] == "false":
            tot["fast_solve_fires"] += 0                # counted via kind; kept for the printout's shape
    return rows, tot, fired


def sweep(games, soon, lo, hi, step, min_left=0.0):
    print(f"{'T':>5} {'target':>7} {'slow':>5} {'false':>6} {'FPclear':>8} {'medLeft':>8}  <- FPclear = episodes CLEARED that needed >T actions")
    for T in range(lo, hi + 1, step):
        rows, tot, _ = classify(games, lambda a, c, w, T=T: fire_dwell(a, T, c, w, min_left), soon)
        fp_clear = 0
        for g, acts, clock, wall in games:
            for lv, d in episodes(acts).items():
                if d["cleared_at"] is not None and (d["cleared_at"] - d["start"]) >= T:
                    fp_clear += 1
        lf = sorted(r["left_frac"] for r in rows if r["kind"] == "target" and r["left_frac"] is not None)
        med = lf[len(lf) // 2] if lf else None
        print(f"{T:>5} {tot['target']:>7} {tot['slow']:>5} {tot['false']:>6} {fp_clear:>8} {str(med):>8}")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("events_dir")
    ap.add_argument("--signal", choices=("novelty", "dwell"), default="novelty")
    ap.add_argument("--window", type=int, default=10)
    ap.add_argument("--theta", type=float, default=0.10)
    ap.add_argument("--thresh", type=int, default=40, help="dwell: actions on a level before firing")
    ap.add_argument("--soon", type=int, default=20)
    ap.add_argument("--min-left", type=float, default=0.0, dest="min_left",
                    help="budget guard: refuse to fire when less than this fraction of the wall remains")
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args(argv)

    games = load(a.events_dir)
    print(f"# stall_detector signal={a.signal} soon={a.soon} dir={a.events_dir} ({len(games)} games)")
    if a.sweep:
        sweep(games, a.soon, 10, 200, 10, a.min_left)
        return 0

    fn = ((lambda acts, c, w: fire_novelty(acts, a.window, a.theta)) if a.signal == "novelty"
          else (lambda acts, c, w: fire_dwell(acts, a.thresh, c, w, a.min_left)))
    rows, tot, fired = classify(games, fn, a.soon)
    pos_hit = sorted(s for s in B73_STALLS if s in fired)
    pos_miss = sorted(s for s in B73_STALLS if s not in fired)
    print(f"params: window={a.window} theta={a.theta}" if a.signal == "novelty"
          else f"params: thresh={a.thresh} min_left={a.min_left}")
    print(f"fires: target={tot['target']} slow={tot['slow']} false={tot['false']}")
    print(f"CONTROL positive (B73 stalls, {len(B73_STALLS)}): fired {len(pos_hit)} -> {pos_hit}")
    print(f"CONTROL positive MISSED -> the detector is blind, its zeroes are not evidence: {pos_miss}"
          if pos_miss else "CONTROL positive: all six fired")
    print(f"CONTROL negative: {tot['fast_solves']} episodes solved within {a.soon} actions; "
          f"{tot['false']} fires landed on a level cleared within {a.soon} actions of the fire")
    lf = sorted(r["left_frac"] for r in rows if r["kind"] == "target" and r["left_frac"] is not None)
    if lf:
        print(f"wall left at a fire on a NEVER-CLEARED level: median {lf[len(lf)//2]}, min {lf[0]}, max {lf[-1]}")
    print()
    print(f"{'game':6} {'lv':>3} {'kind':7} {'act#':>6} {'t_s':>7} {'left':>6} {'score':>6} {'lv_acts':>8}")
    for r in sorted(rows, key=lambda r: (r["kind"], -(r["left_frac"] or 0))):
        print(f"{r['game']:6} {r['level']:>3} {r['kind']:7} {r['action_num']:>6} {r['t_s']:>7} "
              f"{str(r['left_frac']):>6} {str(r['score']):>6} {r['level_actions']:>8}")
    if a.json:
        json.dump({"params": vars(a), "rows": rows, "totals": dict(tot),
                   "control_positive_hit": pos_hit, "control_positive_miss": pos_miss},
                  open(a.json, "w", encoding="utf-8"), indent=1)
        print(f"\nwrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
