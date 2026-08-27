"""B38 -- the family-brake sweep, widened from R38's n=1 to every run on disk.

R38 section 3 measured the brake on `clock-2x-v1` alone and published k=20 as
"speaks on 25.9% of decisions, destroys 0 of 30 level-ups", flagging its own
margin as ONE (`lp85` L3->L4 fired a family 19 deep at the moment it cleared).
R38 section 5.1 names re-running that sweep across the other runs as the first
thing to do, free and code-free.  This is that sweep.

The quantity, exactly as R38 defines it:
  * a FAMILY is (MOUSE, row) for a click -- the row only, never the column --
    and (KEY, name) for everything else.
  * a family's count is its fires SINCE THE LAST LEVEL-UP, within one game.
  * at threshold k the brake SPEAKS on a decision when that family has already
    fired >= k times; a level-up whose own action the brake would have refused
    is DESTROYED.

Counting is prior-fires, so the level-up at depth 19 survives k=20 and dies at
k=15 -- which is what reproduces R38's published table.

CONTROLS (a failing control prints no numbers -- the instrument is not trusted
to report its own blindness):
  1  every action row is classified into a family; no row is silently dropped
  2  k=0 speaks on 100% of decisions        (the mechanism can fire at all)
  3  k=huge speaks on 0% and destroys 0     (the mechanism can decline)
  4  destroyed(k) is monotone non-increasing in k, reach(k) likewise
  5  EXTERNAL: clock2x at k=20 reproduces R38's 25.9% reach and 0 of 30
     level-ups destroyed.  This is the only control that can say the
     reimplementation measures the same thing the design measured.

Usage:  python scripts/b27/b38_sweep.py [--root ~/Claude/arc-artifacts] [--json out.json]
        python scripts/b27/b38_sweep.py --selftest      (no corpus needed)
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys

KS = (10, 15, 20, 25, 30, 60)
MOUSE_RE = re.compile(r"^MOUSE\(row=(-?\d+)")

# R38 section 3's published clock2x readings, for CONTROL 5.
R38_CLOCK2X = {10: (45.5, 5), 15: (34.2, 5), 20: (25.9, 0),
               25: (20.4, 0), 30: (17.0, 0), 60: (9.7, 0)}
R38_CLOCK2X_LEVELUPS = 30


def family(row):
    """R38's key: clicks by ROW alone, everything else by action name."""
    disp = row.get("action_display")
    if isinstance(disp, str):
        m = MOUSE_RE.match(disp)
        if m:
            return ("MOUSE", int(m.group(1)))
    name = row.get("action_name")
    if name is None:
        return None
    return ("KEY", str(name))


def sweep_game(rows, ks, drop_reset=False):
    """One game. Returns per-k {spoke, destroyed} plus totals.

    `rows` must already be in execution order.  The ledger empties on a
    level-up, which is the reset signal the harness itself carries.
    """
    seen = collections.Counter()
    spoke = {k: 0 for k in ks}
    destroyed = {k: 0 for k in ks}
    fam_at_levelup = []
    decisions = 0
    unclassified = 0

    for r in rows:
        fam = family(r)
        if fam is None:
            unclassified += 1
            continue
        if drop_reset and fam == ("KEY", "RESET"):
            continue
        prior = seen[fam]          # fires BEFORE this one, since the last level-up
        decisions += 1
        for k in ks:
            if prior >= k:
                spoke[k] += 1
        if r.get("level_completed"):
            fam_at_levelup.append(prior)
            for k in ks:
                if prior >= k:
                    destroyed[k] += 1
            seen.clear()           # the level-up empties the ledger
        else:
            seen[fam] = prior + 1

    return {"spoke": spoke, "destroyed": destroyed, "decisions": decisions,
            "levelups": len(fam_at_levelup), "fam_at_levelup": fam_at_levelup,
            "unclassified": unclassified}


def read_game(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("type") == "action":
                rows.append(r)
    rows.sort(key=lambda r: (r.get("action_num") or 0))
    return rows


def sweep_run(run_dir, ks, drop_reset=False):
    games = {}
    for path in sorted(glob.glob(os.path.join(run_dir, "artifacts", "*_events.jsonl"))):
        gid = os.path.basename(path).split("_p0_events")[0]
        games[gid] = sweep_game(read_game(path), ks, drop_reset)
    agg = {"spoke": {k: 0 for k in ks}, "destroyed": {k: 0 for k in ks},
           "decisions": 0, "levelups": 0, "unclassified": 0,
           "fam_at_levelup": [], "zero_action_games": [], "games": games}
    for gid, g in games.items():
        for k in ks:
            agg["spoke"][k] += g["spoke"][k]
            agg["destroyed"][k] += g["destroyed"][k]
        agg["decisions"] += g["decisions"]
        agg["levelups"] += g["levelups"]
        agg["unclassified"] += g["unclassified"]
        agg["fam_at_levelup"].extend(g["fam_at_levelup"])
        if g["decisions"] == 0:
            agg["zero_action_games"].append(gid)
    return agg


def controls(runs, ks):
    """Returns (ok, [lines]).  Any False and the caller prints no numbers."""
    out = []
    ok = True

    # 1 -- nothing silently dropped
    unc = sum(r["unclassified"] for r in runs.values())
    good = unc == 0
    ok &= good
    out.append(f"  [{'PASS' if good else 'FAIL'}] 1 every action row classified "
               f"(unclassified={unc}, want 0)")

    # 2 / 3 -- the mechanism can both fire and decline
    probe_ks = (0, 10 ** 6)
    tot_dec = sum(r["decisions"] for r in runs.values())
    p = {k: 0 for k in probe_ks}
    d = {k: 0 for k in probe_ks}
    for rd in runs:
        pass
    # recompute the two probe thresholds over the same corpus
    for name, rd in runs.items():
        s = rd["_probe"]
        for k in probe_ks:
            p[k] += s["spoke"][k]
            d[k] += s["destroyed"][k]
    good = p[0] == tot_dec
    ok &= good
    out.append(f"  [{'PASS' if good else 'FAIL'}] 2 k=0 speaks on every decision "
               f"({p[0]}/{tot_dec})")
    good = p[10 ** 6] == 0 and d[10 ** 6] == 0
    ok &= good
    out.append(f"  [{'PASS' if good else 'FAIL'}] 3 k=1e6 never speaks "
               f"(spoke={p[10 ** 6]}, destroyed={d[10 ** 6]}, want 0/0)")

    # 4 -- monotone in k
    mono = True
    for rd in runs.values():
        for a, b in zip(ks, ks[1:]):
            if rd["spoke"][a] < rd["spoke"][b] or rd["destroyed"][a] < rd["destroyed"][b]:
                mono = False
    ok &= mono
    out.append(f"  [{'PASS' if mono else 'FAIL'}] 4 reach and destroyed are "
               f"non-increasing in k")

    # 5 -- EXTERNAL: reproduce R38's clock2x table
    c2 = runs.get("clock2x")
    if c2 is None:
        ok = False
        out.append("  [FAIL] 5 clock2x absent -- R38's published reading cannot be reproduced")
    else:
        bad = []
        if c2["levelups"] != R38_CLOCK2X_LEVELUPS:
            bad.append(f"levelups {c2['levelups']} != {R38_CLOCK2X_LEVELUPS}")
        for k, (reach, dest) in R38_CLOCK2X.items():
            got = 100.0 * c2["spoke"][k] / c2["decisions"] if c2["decisions"] else 0.0
            if abs(got - reach) > 0.6:
                bad.append(f"k={k} reach {got:.1f}% != {reach}%")
            if c2["destroyed"][k] != dest:
                bad.append(f"k={k} destroyed {c2['destroyed'][k]} != {dest}")
        good = not bad
        ok &= good
        out.append(f"  [{'PASS' if good else 'FAIL'}] 5 clock2x reproduces R38 section 3"
                   + ("" if good else "  -- " + "; ".join(bad)))
    return ok, out


def selftest():
    """Six mutations, each must redden a case.  No corpus required."""
    def mk(disp, name, lvl=False):
        return {"action_display": disp, "action_name": name, "level_completed": lvl}

    fails = []

    # a -- a click family is the ROW, so differing columns are ONE family
    rows = [mk(f"MOUSE(row=56, col={c})", "ACTION6") for c in (10, 20, 30)]
    r = sweep_game(rows, (2,))
    if r["spoke"][2] != 1:
        fails.append(f"a row-keyed clicks: spoke={r['spoke'][2]} want 1")

    # b -- a different row is a different family
    rows = [mk(f"MOUSE(row={n}, col=1)", "ACTION6") for n in (56, 57, 58)]
    r = sweep_game(rows, (2,))
    if r["spoke"][2] != 0:
        fails.append(f"b distinct rows: spoke={r['spoke'][2]} want 0")

    # c -- counting is PRIOR fires: depth 19 survives k=20 and dies at k=15
    rows = [mk("UP", "ACTION1") for _ in range(19)] + [mk("UP", "ACTION1", lvl=True)]
    r = sweep_game(rows, (15, 20))
    if r["destroyed"][20] != 0 or r["destroyed"][15] != 1:
        fails.append(f"c margin: destroyed@20={r['destroyed'][20]} (want 0) "
                     f"@15={r['destroyed'][15]} (want 1)")
    if r["fam_at_levelup"] != [19]:
        fails.append(f"c depth: {r['fam_at_levelup']} want [19]")

    # d -- a level-up empties the ledger
    rows = ([mk("UP", "ACTION1") for _ in range(5)] + [mk("UP", "ACTION1", lvl=True)]
            + [mk("UP", "ACTION1") for _ in range(3)])
    r = sweep_game(rows, (4,))
    if r["spoke"][4] != 2:
        fails.append(f"d reset: spoke={r['spoke'][4]} want 2")

    # e -- keyboard keys by name, so two names never merge
    rows = [mk("UP", "ACTION1"), mk("DOWN", "ACTION2")] * 3
    r = sweep_game(rows, (2,))
    if r["spoke"][2] != 2:
        fails.append(f"e keyboard: spoke={r['spoke'][2]} want 2")

    # f -- an unkeyable row is COUNTED as unclassified, never dropped silently
    r = sweep_game([{"action_display": None, "action_name": None}], (2,))
    if r["unclassified"] != 1 or r["decisions"] != 0:
        fails.append(f"f unclassified: {r['unclassified']}/{r['decisions']} want 1/0")

    for f in fails:
        print(f"  [FAIL] {f}")
    if not fails:
        print("  [PASS] selftest 6/6")
    return not fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.expanduser("~/Claude/arc-artifacts"))
    ap.add_argument("--json")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--drop-reset", action="store_true",
                    help="exclude RESET actions from families (sensitivity check)")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(0 if selftest() else 1)

    ks = KS
    runs = {}
    for d in sorted(os.listdir(a.root)):
        p = os.path.join(a.root, d)
        if d.startswith("_") or not os.path.isdir(p):
            continue
        if not glob.glob(os.path.join(p, "artifacts", "*_events.jsonl")):
            continue
        runs[d] = sweep_run(p, ks, a.drop_reset)
        runs[d]["_probe"] = sweep_run(p, (0, 10 ** 6), a.drop_reset)

    if not runs:
        print(f"no runs under {a.root}", file=sys.stderr)
        sys.exit(2)

    print(f"corpus: {len(runs)} runs -- {', '.join(sorted(runs))}")
    print("\ncontrols:")
    ok, lines = controls(runs, ks)
    for line in lines:
        print(line)
    if not ok:
        print("\na control failed -- no numbers printed.", file=sys.stderr)
        sys.exit(1)

    tot_dec = sum(r["decisions"] for r in runs.values())
    tot_lvl = sum(r["levelups"] for r in runs.values())
    print(f"\npooled: {tot_dec} decisions, {tot_lvl} level-ups, "
          f"{len(runs)} runs x 25 games")

    print(f"\n{'k':>4}  {'reach':>7}  {'destroyed':>12}  per-run destroyed")
    for k in ks:
        sp = sum(r["spoke"][k] for r in runs.values())
        de = sum(r["destroyed"][k] for r in runs.values())
        per = " ".join(f"{n}:{runs[n]['destroyed'][k]}" for n in sorted(runs))
        print(f"{k:>4}  {100.0 * sp / tot_dec:>6.1f}%  {de:>4} of {tot_lvl:<5}  {per}")

    depths = sorted((d for r in runs.values() for d in r["fam_at_levelup"]), reverse=True)
    print(f"\ndeepest family counts at a real level-up (the margin): {depths[:12]}")
    print(f"  n={len(depths)} level-ups; R38 saw max 19 on n=1 run")

    print("\nper-run reach at k=20:")
    for n in sorted(runs):
        r = runs[n]
        pct = 100.0 * r["spoke"][20] / r["decisions"] if r["decisions"] else 0.0
        print(f"  {n:<12} {pct:>5.1f}%  {r['decisions']:>5} decisions  "
              f"{r['levelups']:>3} level-ups  zero-action games: "
              f"{len(r['zero_action_games'])}")

    # B40: a game that fires no actions is invisible to a repeat-based brake.
    zero = collections.Counter()
    for n, r in runs.items():
        for g in r["zero_action_games"]:
            zero[g] += 1
    if zero:
        print("\nB40 -- games invisible to the brake (zero actions), run count:")
        for g, c in zero.most_common():
            print(f"  {g}: {c} of {len(runs)} runs")
    else:
        print("\nB40 -- no zero-action games in this corpus")

    conc = collections.Counter()
    for r in runs.values():
        for gid, g in r["games"].items():
            conc[gid] += g["spoke"][20]
    tot_sp = sum(conc.values())
    print("\nconcentration of k=20 suppressions (R38: tr87+ls20 were 379 of 682):")
    top = conc.most_common(6)
    print(f"  top 6 = {100.0 * sum(c for _, c in top) / tot_sp:.1f}% of all suppressions")
    for gid, c in top:
        print(f"    {gid:<16} {c:>6}  ({100.0 * c / tot_sp:.1f}%)")

    if a.json:
        with open(a.json, "w") as fh:
            json.dump({n: {kk: vv for kk, vv in r.items() if kk != "_probe"}
                       for n, r in runs.items()}, fh, indent=1, default=str)
        print(f"\nwrote {a.json}")


if __name__ == "__main__":
    main()
