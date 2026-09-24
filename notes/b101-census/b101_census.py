"""B101 census: deaths and the six world-model slots around each death, read from banked duck-harness kernel output.

usage: python b101_census.py <run-dir> [<run-dir> ...] [--t 1800,3600,7920]

Two lanes, both 0 GPU:
- USER PROMPT lane: the harness renders every turn's [USER PROMPT] into transcripts/<game>_p0.txt. A death is the
  FIRST prompt containing "The game is over." whose previous prompt does not (inspection-only turns re-show the last
  step summary, so counting every such prompt double-counts). Slots before / after = the "Working world model carried
  from earlier turns: ... end of world model" section of the previous prompt / of that prompt, ignoring Cross-level
  notes. On a B101 arm a kept slot shows up as a non-empty section in the first post-death prompt.
- events lane: artifacts/<game>_p0_events.jsonl, type == "action" and game_over is True (a bool in B81-era runs; a
  string filter silently returns 0). Counts deaths the model may not see (some fall mid-batch).
Timing: the death prompt's "Current state: step N" -> benchmark.json game_runs[].history[N-1].wallclock_seconds.
"""
import glob, json, os, re, sys

SPLIT = re.compile(r"\n(?=\[(?:SYSTEM PROMPT|USER PROMPT|MODEL RESPONSE META|THINKING|ASSISTANT|ANALYZER STATUS|TOOL RESULT[^\]]*)\]\n)")
SEC = re.compile(r"Working world model carried from earlier turns:\n(.*?)end of world model", re.S)
SLOT = re.compile(r"^- (World model|Goal model|Action model|Recent findings|Open questions|Plan|Cross-level notes): (.+)$", re.M)
STEP = re.compile(r"Current state: step (\d+), level (\d+)")
GO = "The game is over."


def six(prompt):
    m = SEC.search(prompt)
    return {} if not m else {k: v for k, v in SLOT.findall(m.group(1)) if v.strip() and k != "Cross-level notes"}


def census(run):
    bench = {g["game_id"][:13]: g for g in json.load(open(os.path.join(run, "benchmark.json"), encoding="utf-8"))["game_runs"]}
    deaths = []  # (game, level, seconds or None, slots_before, slots_after)
    for f in sorted(glob.glob(os.path.join(run, "transcripts", "*_p0.txt"))):
        game = os.path.basename(f)[:13]
        hist = bench[game]["history"]
        ups = [b for b in SPLIT.split(open(f, encoding="utf-8", errors="replace").read()) if b.startswith("[USER PROMPT]")]
        for k in range(1, len(ups)):
            if GO in ups[k] and GO not in ups[k - 1]:
                m = STEP.search(ups[k])
                step = int(m.group(1)) if m else 0
                t = hist[step - 1]["wallclock_seconds"] if 0 < step <= len(hist) else None
                deaths.append((game, int(m.group(2)) if m else None, t, bool(six(ups[k - 1])), bool(six(ups[k]))))
    events = sum(1 for f in glob.glob(os.path.join(run, "artifacts", "*_events.jsonl")) for line in open(f, encoding="utf-8")
                 if (lambda d: d.get("type") == "action" and d.get("game_over") is True)(json.loads(line)))
    return deaths, events


def main():
    args = sys.argv[1:]
    ts = [1800, 3600, 7920]
    if "--t" in args:
        i = args.index("--t"); ts = [int(x) for x in args[i + 1].split(",")]; del args[i:i + 2]
    for run in args:
        deaths, events = census(run)
        lost = [d for d in deaths if d[3]]
        print(f"{run}: deaths seen {len(deaths)} (events lane {events}); slots non-empty before {len(lost)}; "
              f"of those, non-empty right after {sum(d[4] for d in lost)} (0 on an unmodified control); "
              f"untimed {sum(d[2] is None for d in deaths)}")
        for t in ts:
            games = sorted({d[0][:4] for d in lost if d[2] is not None and d[2] <= t})
            print(f"  by {t:>5} s: game-runs with a death after non-empty slots = {len(games)} {games}")


if __name__ == "__main__":
    main()
