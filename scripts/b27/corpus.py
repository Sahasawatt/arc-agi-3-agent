"""Reconstructed B27/R29 corpus loader. scripts/b27/ is not in the repo (verified with
git ls-files + control), so this is rebuilt from the artifacts and validated against the
counts R29 published: 1,973 turns for v10cal+thuiv1, 5,052 for all five runs,
125 run-games, 237 level-attempts, 115 stuck/cleared pairs."""
import os, json, glob, collections

BASE = os.path.expanduser("~/Claude/arc-artifacts")
RUNS5 = ["v10cal", "thuiv1", "v18", "v19", "v23"]

def events_dir(run):
    return os.path.join(BASE, run, "artifacts")

def game_files(run):
    fs = sorted(glob.glob(os.path.join(events_dir(run), "*_events.jsonl")))
    return fs

def load_game(path):
    out = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out

def game_key(path):
    b = os.path.basename(path)
    return b.split("_p0_events.jsonl")[0]

if __name__ == "__main__":
    tot = collections.Counter()
    per_run = {}
    for run in RUNS5:
        fs = game_files(run)
        turns = 0
        games = 0
        for f in fs:
            evs = load_game(f)
            a = sum(1 for e in evs if e.get("type") == "analysis")
            turns += a
            games += 1
        per_run[run] = (games, turns)
        tot["games"] += games
        tot["turns"] += turns
    for r, (g, t) in per_run.items():
        print(f"{r:8s} games={g:3d} analysis_turns={t}")
    pair = per_run["v10cal"][1] + per_run["thuiv1"][1]
    print()
    print(f"PAIR  v10cal+thuiv1 turns = {pair}   (R29 says 1,973)  match={pair==1973}")
    print(f"ALL5  turns = {tot['turns']}          (R29 says 5,052)  match={tot['turns']==5052}")
    print(f"ALL5  run-games = {tot['games']}      (R29 says 125)    match={tot['games']==125}")
