r"""B55 step 3 -- is the early-level efficiency edge made of RECOVERABLE WASTE?

Steps 1 and 2 established, on the per-level census, that within a game the deeper run is
usually the cheaper one on the prefix both cleared, and that this survives a control for
"A is simply the better run". What the census cannot say is WHY a run is cheap, because it
holds no trajectories -- only totals. Step 3 is the first question that needs them.

The mechanism under test is the only one that would PORT to the hidden set. Hidden is 110
games nobody has seen, so a cached opening is worthless there; what ports is a game-agnostic
habit. The cheapest such habit is memory of the agent's own actions: never re-take an action
that already did nothing from this exact board. If the cheap run is cheap because it does not
cycle, that lever costs no game knowledge and works on any game. If it is not, the edge is in
which action gets picked -- game knowledge -- and it does not port.

DATA. Every Kaggle run wrote a raw-event sidecar per game (`<game>-<id>_p0_events.jsonl`,
one JSON object per event) into its kernel output, and those outputs are still served even
for runs whose LOGS now return the nbconvert stub. They were never parsed. Fetch with
`KaggleApi().kernels_output(slug, dest, file_pattern=r"_p0_events\.jsonl$")`.

BUCKETS, over EXECUTED actions only (`type == "action"`), reset at every level boundary:
  noop          `board_changed` false -- the action moved nothing
  repeat_noop   a noop from a (state, action) pair that ALREADY produced a noop this level.
                This is the provably removable class: memory alone deletes it, no game
                knowledge required, and it is the honest size of the memory lever.
  repeat_pair   any (state, action) pair taken twice this level (a superset -- re-walking a
                known path to reach a frontier is legitimate, so this OVERSTATES waste)
  revisit       the board returned to a state already seen this level (also an overstatement:
                `board_ascii` cannot see hidden counters, so distinct states can collide)

Every overstatement points the same way, which is the direction that makes a negative result
safe: if even the inflated buckets are too small to explain the gap, the tight one is too.

CONTROLS, all of which must pass before any number here means anything:
  C1  per run, actions summed over the 25 sidecars == the census's own action total, and
      levels cleared == the census's own level count. This is what identifies a kernel slug
      as a census run; `sahasawatt/taaf-duck-v10` is census `v10cal` because it closes at
      1597/28 and nothing else does.
  C2  the paired machinery below, run on SPEND, must reproduce the step-1/2 direction on
      these runs. A harness that cannot re-find the known signal cannot be trusted to report
      its absence in the waste column.

FIXTURE. The sidecars are ~60 MB per run and cannot live in the repo, and this campaign has
already lost one data source exactly this way -- the retitle push turned every yocybercode/
kernel's log into an 800-char stub and `per-level-census.json` is the only surviving copy.
So `--emit` banks the derived per-level rows (a few hundred KB) and the probe reads either a
directory of sidecars or that JSON. C1 still runs against the census either way, so a fixture
that drifted from the run it claims cannot be used silently.

    python eval/trajectory_probe.py <traj-root>                    # subdir per run, no network
    python eval/trajectory_probe.py <traj-root> --emit <out.json>  # bank the derived rows
    python eval/trajectory_probe.py eval/fixtures/trajectory-rows.json
"""
from __future__ import annotations

import collections
import glob
import hashlib
import json
import os
import statistics as st
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CENSUS = os.path.join(HERE, "fixtures", "per-level-census.json")

# kernel slug -> the census run it is. Proven by C1, not by the name: `taaf-duck-v10` closes
# on `v10cal`, and thui-v6-0 is post-census so it has no census row to close against.
SLUG_TO_RUN = {
    "taaf-duck-v10": "v10cal",
    "taaf-duck-v14": "v14",
    "taaf-duck-v16": "v16",
    "taaf-duck-v18": "v18",
    "taaf-duck-v19": "v19",
    "taaf-duck-v22": "v22",
    "taaf-duck-v23": "v23",
    "taaf-duck-v24": "v24",
    "taaf-duck-v25": "v25",
    "taaf-duck-v26": "v26",
}

BUCKETS = ("noop", "repeat_noop", "repeat_pair", "revisit")

# Not a waste bucket -- the other half of the question. If the cheaper run is not cheaper by
# wasting less, the remaining way to be cheap is to commit to more actions per decision.
# WARNING: an `analysis_step` is NOT one model call. pub CLAUDE.md measured up to 14 `analysis`
# events inside a single step, shaped `[analysis]* action* [analysis]`, over all 200 event logs.
# So this counts the steps that ACTED, and actions/step is how much one decision commits to.
# Reading it as a call count would overstate the model's efficiency by up to an order of magnitude.
EXTRA = ("acting_steps",)


def _h(s: str) -> str:
    return hashlib.blake2b(s.encode("utf-8"), digest_size=8).hexdigest()


def read_game(path: str) -> list[dict]:
    """Per-level rows for one game: actions spent and each waste bucket, in level order."""
    acts = []
    start_board = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            e = json.loads(line)
            if e.get("type") == "action":
                acts.append(e)
            elif e.get("type") == "initial" and start_board is None:
                start_board = e.get("board_ascii") or ""

    rows: list[dict] = []
    cur = object()
    seen_noop: set = set()
    seen_pair: set = set()
    seen_state: set = set()
    steps: set = set()
    # The board a level STARTS on is the post-state of the action that cleared the one before,
    # so `prev_state` is carried across level boundaries and never reset -- a None here would
    # make the first action of every level unmatchable against an identical situation one event
    # later, which UNDER-counts repeat_noop by up to one per level, in the direction that
    # flatters this probe's own headline. The selftest is what caught that.
    prev_state = _h(start_board) if start_board is not None else None
    for e in acts:
        # `level` on an action event is the level AFTER it, so the action that clears level N
        # arrives carrying N+1 and `level_completed`. Splitting rows on the raw field puts that
        # action -- and the clear -- on the next level's row, which leaves every per-level count
        # off by one action and every `cleared` flag one row late. Totals per game still close,
        # which is why C1 as originally written passed straight over it; C1b below compares the
        # per-LEVEL split against the census and is what actually catches this.
        lv = e.get("level")
        if e.get("level_completed") and isinstance(lv, int):
            lv -= 1
        if lv != cur:
            cur = lv
            seen_noop, seen_pair, seen_state, steps = set(), set(), set(), set()
            rows.append({"level": lv, "actions": 0, "cleared": False,
                         **{b: 0 for b in BUCKETS}, **{x: 0 for x in EXTRA}})
        r = rows[-1]
        step = e.get("analysis_step")
        if step not in steps:
            steps.add(step)
            r["acting_steps"] += 1
        key = (prev_state, e.get("action_name"))
        state = _h(e.get("board_ascii") or "")
        r["actions"] += 1
        if not e.get("board_changed"):
            r["noop"] += 1
            if key in seen_noop:
                r["repeat_noop"] += 1
            seen_noop.add(key)
        if key in seen_pair:
            r["repeat_pair"] += 1
        seen_pair.add(key)
        if state in seen_state:
            r["revisit"] += 1
        seen_state.add(state)
        if e.get("level_completed"):
            r["cleared"] = True
        prev_state = state
    return rows


def selftest() -> int:
    """Positive control for the waste detector itself.

    The headline of this probe is a NEAR-ZERO reading, and a near-zero reading from a detector
    with no positive control is indistinguishable from a detector that never fires. So feed it
    a synthetic trajectory whose waste is known by construction and require the exact counts.
    Two levels: level 1 has one repeat_noop and is cleared by an action that (as the real
    harness does) arrives carrying the NEXT level number; level 2 has two.
    """
    def ev(level, name, ascii_, changed, step, cleared=False):
        return {"type": "action", "level": level, "action_name": name, "board_ascii": ascii_,
                "board_changed": changed, "analysis_step": step, "level_completed": cleared}

    fake = [
        ev(1, "A", "s1", True, 1),
        ev(1, "B", "s1", False, 1),      # first noop from (s1, B)
        ev(1, "B", "s1", False, 2),      # SAME pair again -> repeat_noop 1
        ev(2, "C", "s2", True, 2, True),  # clears level 1, carries level 2
        ev(2, "D", "s2", False, 3),      # first noop from (s2, D)
        ev(2, "D", "s2", False, 3),      # repeat_noop 2
        ev(2, "D", "s2", False, 4),      # repeat_noop 3
    ]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "zz00-deadbeef_p0_events.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            for e in fake:
                fh.write(json.dumps(e) + "\n")
        rows = read_game(p)

    want = [
        {"level": 1, "actions": 4, "cleared": True, "noop": 2, "repeat_noop": 1,
         "repeat_pair": 1, "revisit": 2, "acting_steps": 2},
        {"level": 2, "actions": 3, "cleared": False, "noop": 3, "repeat_noop": 2,
         "repeat_pair": 2, "revisit": 2, "acting_steps": 2},
    ]
    bad = []
    if len(rows) != 2:
        bad.append(f"expected 2 level rows, got {len(rows)}: {rows}")
    else:
        for i, (got, exp) in enumerate(zip(rows, want)):
            for k, v in exp.items():
                if got[k] != v:
                    bad.append(f"row {i} {k}: got {got[k]}, want {v}")
    for b in bad:
        print("  [FAIL] selftest", b)
    if bad:
        return 1
    print("selftest OK -- the detector finds 3 planted repeat_noops, splits the clearing action "
          "onto the level it cleared, and counts 2 acting steps per level")
    return 0


def read_run(root: str) -> dict[str, list[dict]]:
    files = sorted(glob.glob(os.path.join(root, "**", "*_p0_events.jsonl"), recursive=True))
    return {os.path.basename(f).split("-")[0]: read_game(f) for f in files}


def prefix(rows: list[dict], k: int, field: str) -> int | None:
    """Total of `field` over levels 1..k, or None if this run cannot cover k.

    Deliberately the same shape as `transfer_probe.prefix_spend` -- first k rows by INDEX,
    not "the first k rows flagged cleared". The two agree because a run's cleared levels come
    first and it dies on the next one, but writing it the other way would leave the step-3
    numbers unable to be set against the step-1/2 numbers without an argument about the
    definition. C0 below is what makes the index safe to use.
    """
    if k > len(rows) or not all(r["cleared"] for r in rows[:k]):
        return None
    return sum(r[field] for r in rows[:k])


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python eval/trajectory_probe.py <traj-root|rows.json> [--emit out.json]",
              file=sys.stderr)
        return 2
    if sys.argv[1] == "--selftest":
        return selftest()
    if selftest():
        print("  refusing to report: the detector failed its own positive control",
              file=sys.stderr)
        return 1
    root = sys.argv[1]
    emit = sys.argv[sys.argv.index("--emit") + 1] if "--emit" in sys.argv else None
    census = json.loads(open(CENSUS, encoding="utf-8").read())["runs"]

    runs, fails = {}, []
    if root.endswith(".json"):
        runs = json.loads(open(root, encoding="utf-8").read())["runs"]
        print(f"rows from fixture {root}")
    else:
        for d in sorted(os.listdir(root)):
            p = os.path.join(root, d)
            if not os.path.isdir(p):
                continue
            games = read_run(p)
            if games:
                runs[d] = games
    if emit:
        with open(emit, "w", encoding="utf-8") as fh:
            json.dump({"source": "per-game raw-event sidecars from each kernel's output, "
                                 "read by eval/trajectory_probe.py; C1 binds every run to its "
                                 "census row per game", "runs": runs}, fh)
        print(f"emitted {emit}")

    # ---- C0: the row model. `prefix` indexes rows, so the rows have to BE the levels in
    # order. ONLY_RESET_LEVELS keeps the level across a RESET, so a level must never be
    # re-entered; if one is, a row is a visit rather than a level and every index is wrong.
    bad = []
    for slug, games in sorted(runs.items()):
        for game, rows in games.items():
            lv = [r["level"] for r in rows]
            if any(x is None for x in lv) or lv != sorted(set(lv)):
                bad.append(f"{slug}/{game} levels={lv}")
    print(f"C0  level rows strictly increasing per game: "
          f"{'OK' if not bad else 'VIOLATED ' + str(bad[:3])}")
    if bad:
        fails.append(f"C0: {len(bad)} game(s) re-enter a level -- rows are not levels")

    # ---- C1: every run closes against the census row it claims
    print("C1  closure against the census")
    closed = 0
    for slug, games in sorted(runs.items()):
        a = sum(r["actions"] for g in games.values() for r in g)
        c = sum(1 for g in games.values() for r in g if r["cleared"])
        name = SLUG_TO_RUN.get(slug)
        if name is None or name not in census:
            print(f"    {slug:16s} games={len(games):2d} actions={a:5d} cleared={c:3d}  "
                  f"[no census row -- not usable for the paired test]")
            continue
        ea = sum(x["actions"] for x in census[name].values())
        ec = sum(x["levels"] for x in census[name].values())
        # PER GAME, not only summed: a truncated sidecar and an over-counted one cancel in a
        # total, and 25 exact equalities is what makes the slug->run identification a proof.
        off = []
        for game, rows in games.items():
            cr = census[name].get(game)
            if cr is None:
                off.append(f"{game}:no-census-row")
                continue
            ga = sum(r["actions"] for r in rows)
            gc = sum(1 for r in rows if r["cleared"])
            if ga != cr["actions"] or gc != cr["levels"]:
                off.append(f"{game}:{ga}/{gc} vs {cr['actions']}/{cr['levels']}")
                continue
            # C1b -- the per-LEVEL split, which a per-game total cannot see. The census's
            # `per_level` is SPENT per level in level order, so row i must equal per_level[i]
            # for every level this run actually entered.
            per = [p[0] for p in cr["per_level"]]
            mine = [r["actions"] for r in rows]
            if mine != per[:len(mine)]:
                off.append(f"{game}:per-level {mine} vs {per[:len(mine)]}")
        ok = (a == ea and c == ec and not off and len(games) == 25)
        closed += ok
        print(f"    {slug:16s} -> {name:8s} actions {a:5d} vs {ea:5d}   "
              f"cleared {c:3d} vs {ec:3d}   games {len(games):2d}   "
              f"per-game off {len(off):2d}   {'OK' if ok else 'MISMATCH'}")
        if not ok:
            fails.append(f"C1 {slug}: does not match census {name}; first offenders {off[:3]}")
    if closed < 2:
        fails.append(f"C1: only {closed} run(s) closed -- the paired test needs at least 2")
    if fails:
        for f in fails:
            print("  [FAIL]", f)
        return 1

    usable = {SLUG_TO_RUN[s]: g for s, g in runs.items() if s in SLUG_TO_RUN}
    print(f"\nruns usable for pairing: {len(usable)}  {sorted(usable)}")

    # ---- the paired test, same shape as transfer_probe.q2
    per_game: dict[str, list[tuple[str, list[dict]]]] = {}
    for name, games in usable.items():
        for game, rows in games.items():
            per_game.setdefault(game, []).append((name, rows))

    fields = ("actions",) + BUCKETS + EXTRA
    res = {f: collections.Counter() for f in fields}
    rate = {b + "/act": collections.Counter() for b in BUCKETS}
    share = []
    npairs = 0
    for game, xs in per_game.items():
        for i in range(len(xs)):
            for j in range(len(xs)):
                if i == j:
                    continue
                ra, rb = xs[i][1], xs[j][1]
                da = sum(1 for r in ra if r["cleared"])
                db = sum(1 for r in rb if r["cleared"])
                if da <= db or db < 1:
                    continue
                sa, sb = prefix(ra, db, "actions"), prefix(rb, db, "actions")
                if sa is None or sb is None:
                    continue
                npairs += 1
                for f in fields:
                    va, vb = prefix(ra, db, f), prefix(rb, db, f)
                    if va < vb:
                        res[f]["deeper_lower"] += 1
                    elif va > vb:
                        res[f]["deeper_higher"] += 1
                    else:
                        res[f]["tie"] += 1
                # RATES, not counts. A run that spends less mechanically revisits fewer states,
                # so a count column leaning the right way is a consequence of the spend gap and
                # not an independent lever. Only per-action rates can tell the two apart.
                for b in BUCKETS:
                    va, vb = prefix(ra, db, b) / sa, prefix(rb, db, b) / sb
                    k = b + "/act"
                    if va < vb:
                        rate[k]["deeper_lower"] += 1
                    elif va > vb:
                        rate[k]["deeper_higher"] += 1
                    else:
                        rate[k]["tie"] += 1
                if sa != sb:
                    wa = prefix(ra, db, "repeat_noop")
                    wb = prefix(rb, db, "repeat_noop")
                    share.append(abs(wb - wa) / abs(sb - sa))

    print(f"\npairs (deeper run vs shallower, shared prefix at least 1 level): {npairs}")
    print(f"{'field':13s} {'deeper LOWER':>12s} {'deeper HIGHER':>13s} {'tie':>5s}   share")
    for f in fields:
        c = res[f]
        n = c["deeper_lower"] + c["deeper_higher"]
        s = f"{c['deeper_lower']/n:.3f}" if n else "  n/a"
        tag = "  <- C2, must reproduce step 1/2" if f == "actions" else ""
        print(f"{f:13s} {c['deeper_lower']:12d} {c['deeper_higher']:13d} {c['tie']:5d}   {s}{tag}")
    print("  -- the same buckets as a RATE per action, which is the form that separates a lever")
    print("     from a consequence of having spent less --")
    for k, c in rate.items():
        n = c["deeper_lower"] + c["deeper_higher"]
        s = f"{c['deeper_lower']/n:.3f}" if n else "  n/a"
        print(f"{k:13s} {c['deeper_lower']:12d} {c['deeper_higher']:13d} {c['tie']:5d}   {s}")

    if res["actions"]["deeper_lower"] <= res["actions"]["deeper_higher"]:
        print("\n  [FAIL] C2: the harness does not reproduce the step-1/2 direction on SPEND; "
              "its reading of the waste columns cannot be trusted")
        return 1
    print("\nC2  OK -- spend reproduces the step-1/2 direction on these runs")

    tot_act = sum(r["actions"] for g in usable.values() for gg in g.values() for r in gg)
    print(f"\nwaste budget over every action in every usable run  (n={tot_act})")
    for b in BUCKETS:
        v = sum(r[b] for g in usable.values() for gg in g.values() for r in gg)
        print(f"  {b:12s} {v:5d}  {100.0*v/tot_act:5.2f}%")

    print("\nper run: depth, spend, waste share, and how much one acting step commits to")
    for name in sorted(usable, key=lambda n: -sum(1 for g in usable[n].values()
                                                  for r in g if r["cleared"])):
        rr = [r for g in usable[name].values() for r in g]
        a = sum(r["actions"] for r in rr)
        c = sum(1 for r in rr if r["cleared"])
        calls = sum(r["acting_steps"] for r in rr)
        rn = sum(r["repeat_noop"] for r in rr)
        rv = sum(r["revisit"] for r in rr)
        print(f"  {name:8s} levels {c:3d}  actions {a:5d}  repeat_noop {100.0*rn/a:4.1f}%  "
              f"revisit {100.0*rv/a:4.1f}%  actions/acting-step {a/calls:4.2f}")
    if share:
        print(f"\nfor the {len(share)} pairs with a non-zero spend gap, the repeat_noop gap is")
        print(f"  median {100*st.median(share):5.2f}%  mean {100*st.mean(share):5.2f}%  "
              f"of the spend gap it would have to explain")
    return 0


if __name__ == "__main__":
    sys.exit(main())
