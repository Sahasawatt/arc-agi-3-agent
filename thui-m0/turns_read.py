"""turns_read.py -- the thui-m0 MECHANISM reader (rule 1): did the faster server give the harness more turns?

Per game, from artifacts/*_p0_events.jsonl: analysis turns = rows of type "analysis"; wall per turn = the gap between
consecutive analysis rows' transcript timestamps (`--- analysis_step=N | action=M | HH:MM:SS | tool-agent ---`), day
wrap handled; actions = rows of type "action". Prints one line per run (medians over games) and the per-game table.

    python thui-m0/turns_read.py <run-dir> [<run-dir> ...]

Shipped chassis reads ~52 turns/game at ~152 s/turn (frontier-5 diagnosis, 2026-09-15); the pre-registered gate for
thui-m0 is median turns > 60 AND median wall/turn < 100 s. Below that the chassis did not deliver and the draw is VOID
for the score question.
"""
import glob
import json
import os
import re
import statistics
import sys

sys.stdout.reconfigure(encoding="utf-8")
TS = re.compile(r"\| (\d\d):(\d\d):(\d\d) \|")


def read_run(run_dir):
    rows = []
    for path in sorted(glob.glob(os.path.join(run_dir, "artifacts", "*_p0_events.jsonl"))):
        g = os.path.basename(path)[:4]
        ev = [json.loads(l) for l in open(path, encoding="utf-8")]
        an = [r for r in ev if r.get("type") == "analysis"]
        acts = [r for r in ev if r.get("type") == "action"]
        stamps = []
        for r in an:
            m = TS.search(str(r.get("transcript", ""))[:200])
            if m:
                stamps.append(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)))
        gaps = []
        for a, b in zip(stamps, stamps[1:]):
            d = b - a
            if d < 0:
                d += 86400
            gaps.append(d)
        levels = max((int(r.get("level") or 1) for r in acts), default=1) - 1
        rows.append((g, len(an), len(acts), statistics.median(gaps) if gaps else None, levels))
    return rows


def main(argv):
    if not argv:
        print(__doc__); return 2
    for d in argv:
        rows = read_run(d)
        if not rows:
            print(f"{os.path.basename(d.rstrip('/\\\\'))}: no event files"); continue
        turns = [r[1] for r in rows]; walls = [r[3] for r in rows if r[3] is not None]; acts = [r[2] for r in rows]
        print(f"{os.path.basename(d.rstrip('/\\\\')):36s} games={len(rows)} turns/game median={statistics.median(turns):.0f} "
              f"(min {min(turns)} max {max(turns)}) wall/turn median={statistics.median(walls):.0f}s "
              f"actions total={sum(acts)} levels={sum(r[4] for r in rows)}")
        for g, t, a, w, lv in rows:
            print(f"    {g}: turns {t:3d} actions {a:4d} wall/turn {w if w is not None else '-':>4}s levels {lv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
