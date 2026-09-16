"""restart_read.py -- the thui-rs smoke oracle (rule 2), read from a run's events (0 GPU).

Per game, walks the analysis rows in order, tracking the level and the distinct analysis_step count since the level last changed;
a restart is where that count reaches K (20) with fewer than 2 restarts on the level -- the graft's own rule, replayed -- so the
reader works on ANY run: on a v0 run it reproduces where THUI_RS_RESTART fired (cross-check against the log's marker count), on a
control run it says where a restart WOULD have fired. For each restart it then asks: was this level cleared later (a later analysis
row at a higher level)? That is the causal read -- a clear AFTER a restart that the pre-restart context did not reach in its 20 turns.

    python thui-rs/restart_read.py <run-dir> [<run-dir> ...]      # each dir holds artifacts/*_p0_events.jsonl
"""
import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
K, CAP = 20, 2


def read_run(run_dir):
    out = []
    for path in sorted(glob.glob(os.path.join(run_dir, "artifacts", "*_p0_events.jsonl"))):
        g = os.path.basename(path)[:4]
        rows = [json.loads(l) for l in open(path, encoding="utf-8")]
        an = [(int(r.get("level") or 1), r.get("analysis_step")) for r in rows if r.get("type") == "analysis"]
        acts = [r for r in rows if r.get("type") == "action"]
        max_level = max((int(r.get("level") or 1) for r in acts), default=1)
        level, steps, restarts, fired = None, set(), 0, []   # fired: (level, at_step_index, turns_before)
        for i, (lv, step) in enumerate(an):
            if lv != level:
                level, steps, restarts = lv, set(), 0
            if step is not None:
                steps.add(step)
            if len(steps) >= K and restarts < CAP:
                fired.append((lv, i, len(steps)))
                restarts += 1
                steps = {step} if step is not None else set()
        cleared_after = [(lv, i) for lv, i, _ in fired if any(l2 > lv for l2, _ in an[i + 1:])]
        levels = max_level - 1
        out.append((g, len(an), levels, fired, cleared_after))
    return out


def main(argv):
    if not argv:
        print(__doc__); return 2
    for d in argv:
        rows = read_run(d)
        if not rows:
            print(f"{os.path.basename(d.rstrip('/\\\\'))}: no event files"); continue
        tot_f = sum(len(r[3]) for r in rows); tot_c = sum(len(r[4]) for r in rows)
        print(f"{os.path.basename(d.rstrip('/\\\\')):34s} games={len(rows)} restarts(rule)={tot_f} cleared-after-restart={tot_c} levels={sum(r[2] for r in rows)}")
        for g, n, lv, fired, ca in rows:
            if fired:
                print(f"    {g}: turns {n:3d} levels {lv}  restarts " + ", ".join(f"L{l}@turn{i + 1}" for l, i, _ in fired)
                      + (f"  -> cleared after restart: " + ", ".join(f"L{l}" for l, _ in ca) if ca else "  -> no clear after restart"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
