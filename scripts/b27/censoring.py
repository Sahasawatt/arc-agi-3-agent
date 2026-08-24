"""Is the corpus RIGHT-CENSORED on depth? -- the measurement E1 turns on.

Every one of the 125 run-games ended `gave_up` at max_runtime_s_per_game=7920
(benchmark.json: min 7920.2, max 7970.3, zero games under 98% of the cap). So the
budget was spent in full every time and no game stopped on its own logic. That makes
"the agent was finished" and "the agent was cut" indistinguishable from the score.

This asks whether the level-up process was still running when the wall arrived, using
only artifacts already on disk. It does NOT establish that the rate continues past the
observed window -- that is precisely what censoring makes unobservable, and it is why
E1 needs a run rather than another probe.

Prints its own positive control (125 run-games / 7,938 actions, matching R29 and
scripts/b27/plateau.py) before any measurement.
"""
import sys, os, statistics, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corpus import RUNS5, game_files, load_game, game_key

CAP_S = 7920.0


def load():
    games = []
    for run in RUNS5:
        for path in game_files(run):
            actions = [e for e in load_game(path) if e.get("type") == "action"]
            if not actions:
                continue
            games.append({
                "run": run,
                "game": game_key(path),
                "n": len(actions),
                "ups": [i for i, e in enumerate(actions, 1) if e.get("level_completed")],
            })
    return games


def control(games):
    n_games, n_acts = len(games), sum(g["n"] for g in games)
    print("CONTROL run-games={} (R29: 125) match={}".format(n_games, n_games == 125))
    print("CONTROL actions={} (plateau.py: 7,938) match={}".format(n_acts, n_acts == 7938))
    if n_games != 125 or n_acts != 7938:
        sys.exit("control failed -- the corpus is not the one these numbers describe")
    print()


def last_up_position(cleared):
    fracs = [g["ups"][-1] / g["n"] for g in cleared]
    buckets = collections.Counter(min(int(f * 10), 9) for f in fracs)
    print("position of each cleared game's LAST level-up, as a fraction of its own actions")
    for b in range(10):
        print("  [{:.1f},{:.1f})  {:3d}  {}".format(b / 10, (b + 1) / 10, buckets[b], "#" * buckets[b]))
    print("  median={:.3f}  final 10%: {}/{} = {:.1%}  final 20%: {}/{} = {:.1%}".format(
        statistics.median(fracs), buckets[9], len(cleared), buckets[9] / len(cleared),
        buckets[8] + buckets[9], len(cleared), (buckets[8] + buckets[9]) / len(cleared)))
    tails = [g["n"] - g["ups"][-1] for g in cleared]
    print("  actions after last level-up: median={:.0f} mean={:.1f} max={}".format(
        statistics.median(tails), statistics.mean(tails), max(tails)))
    print("  tail <= 5 actions (still scoring at the wall): {}/{}".format(
        sum(1 for t in tails if t <= 5), len(cleared)))
    print("  tail > 114 (the longest inter-level gap plateau.py found): {}/{}".format(
        sum(1 for t in tails if t > 114), len(cleared)))
    print()


def gaps_per_level(games):
    print("gap to each successive level-up (actions)")
    print("{:>7s} {:>8s} {:>7s} {:>7s} {:>5s}".format("level#", "n games", "median", "mean", "max"))
    for k in range(1, 6):
        gs = [g["ups"][k - 1] - (g["ups"][k - 2] if k >= 2 else 0) for g in games if len(g["ups"]) >= k]
        if gs:
            print("{:>7d} {:>8d} {:>7.0f} {:>7.1f} {:>5d}".format(
                k, len(gs), statistics.median(gs), statistics.mean(gs), max(gs)))
    print()


def hazard(games, window=20):
    print("hazard: of games at action i with no level-up for K actions,")
    print("        what fraction level up within the next {}?".format(window))
    for K in (10, 20, 30, 40, 60):
        at_risk = hits = 0
        for g in games:
            ups = set(g["ups"])
            last = 0
            for i in range(1, g["n"] + 1):
                if i in ups:
                    last = i
                    continue
                if i - last == K and i + window <= g["n"]:
                    at_risk += 1
                    if any(i < u <= i + window for u in g["ups"]):
                        hits += 1
        print("  K={:2d}  at-risk={:4d}  hits={:3d}  = {}".format(
            K, at_risk, hits, "{:.1%}".format(hits / at_risk) if at_risk else "n/a"))
    print()


def halves(games):
    total = sum(len(g["ups"]) for g in games)
    acts = sum(g["n"] for g in games)
    first = sum(1 for g in games for u in g["ups"] if u <= g["n"] / 2)
    print("decay within the observed window -- the reading E1 rests on")
    print("  corpus rate: {} level-ups / {} actions = 1 per {:.1f}".format(total, acts, acts / total))
    print("  first half of each game's actions:  {}/{} = {:.1%}".format(first, total, first / total))
    print("  second half:                        {}/{} = {:.1%}".format(
        total - first, total, (total - first) / total))
    print("  a flat split is NOT evidence the rate continues past the wall. It is evidence")
    print("  that nothing in the observed window says it stops.")


if __name__ == "__main__":
    games = load()
    control(games)
    cleared = [g for g in games if g["ups"]]
    print("cleared >=1 level: {}   never cleared: {}   total level-ups: {}\n".format(
        len(cleared), len(games) - len(cleared), sum(len(g["ups"]) for g in games)))
    last_up_position(cleared)
    gaps_per_level(games)
    hazard(games)
    halves(games)
