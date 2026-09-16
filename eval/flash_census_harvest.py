r"""flash_census_harvest.py -- put the shipped chassis into the per-level census (R57's "next action", 0 slot, 0 GPU).

Every pricing instrument in eval/ reads eval/fixtures/per-level-census.json, and until now it held 21 runs and zero
Flash-Next rows, so the chassis we actually submit was invisible to all of them (R57 §convergence). This script adds
Flash-Next runs to that fixture in the SAME schema, from two sources, with the controls that decide whether a row may
be written at all:

  log    -- the run's `[finished] <game> ... actions=N tokens=T per-level=S/H,... note="tokens=G"` lines.
  events -- the run's `<game>_p0_events.jsonl`: per-level SPENT is re-derived by attributing each action to the level
            it was PLAYED on (a level_completed event carries the NEXT level in its `level` field -- verified on tr87,
            the same fault that made eval/stall_detector.py read every episode as never-cleared). HUMAN per level and
            the level total are per-game constants (asserted identical across all 21 banked runs) and come from the
            fixture. Tokens are not in the events, so an events-only game carries counted/generated = null.

Why two sources, and which one to trust: the copy of a log that `KaggleApi().kernels_logs()` returns is SHORT ONE
[finished] LINE in three of four full-25 runs fetched 2026-09-14 (fast-v0 d2 lost cd82, l1-v0 lost tu93, l1-ctl lost
lp85 -- 24/25 each, no duplicated blocks). The kernel's OWN log file inside its output directory
(`kernels_output(slug, dest)` -> `<slug>.log`) carries all 25 for every one of the same runs, with the same audit
total. So the drop is an artefact of the logs endpoint, not of the run, and the output-dir log is the source here;
the events path exists so that a run with no output-dir log can still be harvested, and above all as control P.

The handoff (R57 / next-session-prompt) named two traps for this harvest -- "kernels_logs has no version argument"
and "the animfast log repeats 14 blocks" -- and did not name this one, which bit first. Neither of those two fired on
these five runs (0 duplicated games in every log); the version trap is real and is why thui-fast-v0 DRAW 1 (3,925
actions) is not here: only the slug's latest version is served, and that is draw 2.

CONTROLS, all fail-closed, all printed:
  P  positive -- on every game present in BOTH sources the events-derived SPENT vector must equal the log's, exactly.
                 fast-v0 d2 gives 24 such games for free. Zero agreeing pairs = the events path is unproven -> refuse.
  A  audit    -- the 25-game action sum must equal the run's own PUBLIC25_AUDIT total AND the LEDGER's actions column.
                 A mismatch means the log served is not the run the LEDGER row describes (the B52 trap) -> refuse.
  S  schema   -- per game: len(per_level) == total and sum(SPENT) == actions, the census's own asserts.
  I  identity -- after writing, every pre-existing run's row must be byte-identical to before -> refuse the write.

    python eval/flash_census_harvest.py --dry-run        # print rows + controls, write nothing
    python eval/flash_census_harvest.py                  # write, then re-open and re-verify
"""
import argparse
import collections
import glob
import json
import os
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "per-level-census.json"
SCRATCH = pathlib.Path(os.environ.get("ARC_SCRATCH", HERE.parent.parent))

FINISHED = re.compile(
    r"\[finished\] (\S+) state=(\S+) level=(\d+)/(\d+) score=([\d.]+) actions=(\d+) tokens=(\d+) "
    r"per-level=([\d/,]+)(?:.*?note=\\\"tokens=(\d+)\\\")?"
)
AUDIT = re.compile(r"PUBLIC25_AUDIT runs=(\d+) actions=(\d+)")

# key -> sources + the two independent action totals the row must reproduce. LEDGER = notes/LEDGER-all-runs.md
# actions column at origin/master 4a565e2 (Flash-Next family) or our own uncommitted rows where noted.
RUNS = {
    # "log" = the kernel's own log from its OUTPUT directory (complete); "events" = per-game event files, used for
    # control P on every game present in both, and as the fallback source for a game the log lacks.
    "thui-fast-v0-d2": {
        "log": "kout-sa-thui-fast-v0-d2/thui-fast-v0.log",
        "events": "kout-sa-thui-fast-v0-d2/diag/artifacts",
        "ledger_actions": 3553, "public": 9.32, "hidden": 3.21, "owner": "sahasawatt",
    },
    "thui-a7-v1-d2": {
        "log": "kout-sa-thui-a7-v1-d2/thui-a7-v1.log",
        "events": "kout-sa-thui-a7-v1-d2/artifacts",
        "ledger_actions": 3466, "public": 8.23, "hidden": None, "owner": "sahasawatt",
    },
    "thui-a7-full25-r1": {
        "log": "kout-yo-thui-a7-full25-r1/thui-a7-full25-r1.log",
        "events": None,
        "ledger_actions": 3843, "public": 8.2491, "hidden": 3.32, "owner": "yocybercode",
    },
    "thui-l1-v0-full25-r1": {
        "log": "kout-yo-thui-l1-v0-full25-r1/thui-l1-v0-full25-r1.log",
        "events": "kout-yo-thui-l1-v0-full25-r1/artifacts",
        "ledger_actions": 3522, "public": 10.9337, "hidden": 3.60, "owner": "yocybercode",
    },
    "thui-l1-ctl-full25-r1": {
        "log": "kout-yo-thui-l1-ctl-full25-r1/thui-l1-ctl-full25-r1.log",
        "events": "kout-yo-thui-l1-ctl-full25-r1/artifacts",
        "ledger_actions": 3528, "public": 8.6427, "hidden": None, "owner": "yocybercode",
    },
    # the two runs that answered 403 on 2026-09-14 15:1x and 200 at 21:45 (fetched then); LEDGER actions at origin/master 4a565e2
    "thui-animfast-b71-full25-r1": {
        "log": "kout-wa-thui-animfast-b71-full25-r1/thui-animfast-b71-full25-r1.log",
        "events": "kout-wa-thui-animfast-b71-full25-r1/artifacts",
        "ledger_actions": 2008, "public": 9.5584, "hidden": 3.74, "owner": "yocybercode",
    },
    "thui-fast-b78-mtp0-full25-r1": {
        "log": "kout-wa-thui-fast-b78-mtp0-full25-r1/thui-fast-b78-mtp0-full25-r1.log",
        "events": "kout-wa-thui-fast-b78-mtp0-full25-r1/artifacts",
        "ledger_actions": 4049, "public": 6.9609, "hidden": 3.49, "owner": "yocybercode",
    },
    # wipe-guard full-25 A/B draw r1, 2026-09-15 (both ~01:35-05:45 same day). No LEDGER row yet: ledger_actions = each run's own
    # PUBLIC25_AUDIT total, public = the harness's final "mean score" line (the same quantity the LEDGER column records).
    "thui-wm-v0-full25-r1": {
        "log": "kout-sa-thui-wm-v0-full25-r1/thui-wm-v0-full25-r1.log",
        "events": "kout-sa-thui-wm-v0-full25-r1/artifacts",
        "ledger_actions": 3100, "public": 7.4384, "hidden": None, "owner": "sahasawatt",
    },
    "thui-wm-ctl-full25-r1": {
        "log": "kout-sa-thui-wm-ctl-full25-r1/thui-wm-ctl-full25-r1.log",
        "events": "kout-sa-thui-wm-ctl-full25-r1/artifacts",
        "ledger_actions": 3517, "public": 8.3212, "hidden": None, "owner": "sahasawatt",
    },
    # MTP-0 / KV 7 GiB / seqs 20 serving profile (thui-m0), NOT the shipped profile -- keep out of the FLASH list unless the owner folds it
    "thui-m0-s20-full25-r1": {
        "log": "kout-sa-thui-m0-s20-full25-r1/thui-m0-s20-full25-r1.log",
        "events": "kout-sa-thui-m0-s20-full25-r1/artifacts",
        "ledger_actions": 5722, "public": 5.6228, "hidden": None, "owner": "sahasawatt",
    },
    # anim harness (jakobbrggen anim-20260807 bundle) on the shipped serving profile -- same composition as thui-animfast-b71, draw 2
    "thui-anim-full25-r2": {
        "log": "kout-sa-thui-anim-full25-r2/thui-anim-full25-r2.log",
        "events": "kout-sa-thui-anim-full25-r2/artifacts",
        "ledger_actions": 2557, "public": 10.5600, "hidden": None, "owner": "sahasawatt",
    },
}


def log_lines(path):
    out = []
    for line in open(path, encoding="utf-8"):
        m = re.search(r'"data":"(.*?)"\}$', line.strip().rstrip(","))
        if m:
            out.append(m.group(1).encode().decode("unicode_escape"))
    return out


def parse_log(path):
    """game4 -> row, plus the audit total. Uses the LAST [finished] line per game (the duplicate-block trap)."""
    rows, audit = {}, None
    for d in log_lines(path):
        m = FINISHED.search(d)
        if m:
            gid, state, lv, tot, score, acts, toks, per, gen = m.groups()
            pairs = [[int(a), int(b)] for a, b in (p.split("/") for p in per.split(","))]
            rows[gid[:4]] = {
                "levels": int(lv), "total": int(tot), "actions": int(acts),
                "counted_tokens": int(toks), "generated_tokens": int(gen) if gen else int(toks),
                "per_level": pairs, "from": "log",
            }
        a = AUDIT.search(d)
        if a:
            audit = (int(a.group(1)), int(a.group(2)))
    return rows, audit


def level_of(a):
    return int(a["level"]) - (1 if a.get("level_completed") in (True, "True") else 0)


def spent_from_events(path, total):
    """SPENT per level 1..total from the events file, and the levels cleared."""
    spent = collections.Counter()
    cleared = 0
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d.get("type") != "action":
            continue
        spent[level_of(d)] += 1
        if d.get("level_completed") in (True, "True"):
            cleared += 1
    return [spent.get(i, 0) for i in range(1, total + 1)], cleared


def constants(fixture_runs):
    human, total = {}, {}
    for run, byg in fixture_runs.items():
        for g, d in byg.items():
            h = tuple(x for _, x in d["per_level"])
            assert human.setdefault(g, h) == h, (run, g, "HUMAN varies")
            assert total.setdefault(g, d["total"]) == d["total"], (run, g, "total varies")
    assert len(human) == 25
    return human, total


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", nargs="*", help="run keys to harvest (default: all)")
    a = ap.parse_args(argv)

    before = FIXTURE.read_bytes()
    fx = json.loads(before)
    human, total = constants(fx["runs"])
    games = sorted(human)
    fails, new_rows, pos_pairs = [], {}, 0

    for key, spec in RUNS.items():
        if a.only and key not in a.only:
            continue
        rows, audit = parse_log(SCRATCH / spec["log"])
        src = {g: "log" for g in rows}
        # --- fill missing games from events, and run the positive control on the overlap
        ev_dir = SCRATCH / spec["events"] if spec["events"] else None
        ev_files = {os.path.basename(p)[:4]: p for p in glob.glob(str(ev_dir / "*_p0_events.jsonl"))} if ev_dir else {}
        for g in games:
            if g in ev_files:
                spent, cleared = spent_from_events(ev_files[g], total[g])
                if g in rows:
                    if spent != [s for s, _ in rows[g]["per_level"]]:
                        fails.append(f"{key}/{g}: CONTROL P FAILED events {spent} != log {[s for s, _ in rows[g]['per_level']]}")
                    else:
                        pos_pairs += 1
                else:
                    rows[g] = {"levels": cleared, "total": total[g], "actions": sum(spent),
                               "counted_tokens": None, "generated_tokens": None,
                               "per_level": [[s, h] for s, h in zip(spent, human[g])], "from": "events"}
                    src[g] = "events"
        missing = [g for g in games if g not in rows]
        if missing:
            fails.append(f"{key}: games with neither log line nor events: {missing}")
            continue
        # --- schema + audit controls
        for g in games:
            d = rows[g]
            if len(d["per_level"]) != d["total"]:
                fails.append(f"{key}/{g}: CONTROL S len(per_level)={len(d['per_level'])} != total={d['total']}")
            if sum(p[0] for p in d["per_level"]) != d["actions"]:
                fails.append(f"{key}/{g}: CONTROL S sum(SPENT) != actions")
            if [h for _, h in d["per_level"]] != list(human[g]):
                fails.append(f"{key}/{g}: HUMAN baseline differs from the fixture constant")
        tot_actions = sum(rows[g]["actions"] for g in games)
        if audit is None:
            fails.append(f"{key}: no PUBLIC25_AUDIT line in the log")
        elif audit != (25, tot_actions):
            fails.append(f"{key}: CONTROL A audit={audit} != (25, {tot_actions})")
        if tot_actions != spec["ledger_actions"]:
            fails.append(f"{key}: CONTROL A LEDGER actions {spec['ledger_actions']} != harvested {tot_actions}")
        n_ev = sum(1 for g in games if src[g] == "events")
        lv = sum(rows[g]["levels"] for g in games)
        print(f"{key:24s} games=25 actions={tot_actions} (audit {audit[1] if audit else '-'}, LEDGER {spec['ledger_actions']}) "
              f"levels={lv} from_events={n_ev}{' [' + ','.join(g for g in games if src[g] == 'events') + ']' if n_ev else ''}")
        new_rows[key] = {g: {k: v for k, v in rows[g].items() if k != "from"} for g in games}
        for g in games:
            if src[g] == "events":
                new_rows[key][g]["source"] = "events"

    print(f"\nCONTROL P: {pos_pairs} log/events pairs agreed exactly on the SPENT vector"
          + ("  <- ZERO pairs: the events path is unproven, refusing" if pos_pairs == 0 else ""))
    if pos_pairs == 0:
        fails.append("CONTROL P: no overlapping game to prove the events derivation")
    if fails:
        print("\nREFUSED:\n  " + "\n  ".join(fails))
        return 1
    if a.dry_run:
        print(f"\n--dry-run: {len(new_rows)} runs would be added: {sorted(new_rows)}")
        return 0

    for key in new_rows:
        assert key not in fx["runs"], f"{key} already in the fixture; refusing to overwrite"
    fx["runs"].update(new_rows)
    fx.setdefault("source_flash", (
        "Flash-Next rows added 2026-09-14 by eval/flash_census_harvest.py from kernels_logs() + per-game "
        "_p0_events.jsonl (one game per log had its [finished] line dropped by Kaggle's capture; that game's SPENT "
        "is re-derived from events, tokens null). Controls P/A/S/I passed at write time; see the script."))
    FIXTURE.write_text(json.dumps(fx, indent=1) + "\n", encoding="utf-8")
    # --- CONTROL I: pre-existing rows byte-identical
    after = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old = json.loads(before)
    for run in old["runs"]:
        if json.dumps(after["runs"][run], sort_keys=True) != json.dumps(old["runs"][run], sort_keys=True):
            FIXTURE.write_bytes(before)
            print(f"CONTROL I FAILED on {run}; fixture restored byte-for-byte")
            return 1
    print(f"\nwrote {len(new_rows)} runs -> {FIXTURE.name}; {len(old['runs'])} pre-existing rows byte-identical (CONTROL I ok)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
