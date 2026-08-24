"""Aggregate plateau-tail and counterfactual stopping measurements."""

import collections
import json
import os
import statistics
import sys

from corpus import RUNS5, game_files, game_key, load_game


KS = tuple(range(10, 121, 10))


def controls():
    counts = {}
    total_games = 0
    total_turns = 0
    for run in RUNS5:
        games = turns = 0
        for path in game_files(run):
            games += 1
            turns += sum(1 for event in load_game(path) if event.get("type") == "analysis")
        counts[run] = (games, turns)
        total_games += games
        total_turns += turns
    pair_turns = counts["v10cal"][1] + counts["thuiv1"][1]
    return counts, total_games, total_turns, pair_turns


def benchmark(run):
    path = os.path.expanduser("~/Claude/arc-artifacts/{}/benchmark.json".format(run))
    with open(path) as stream:
        data = json.load(stream)
    return {entry["game_id"]: entry for entry in data["game_runs"]}


def records():
    for run in RUNS5:
        timing = benchmark(run)
        for path in game_files(run):
            events = load_game(path)
            actions = [event for event in events if event.get("type") == "action"]
            actions.sort(key=lambda event: event["action_num"])
            ups = [event["action_num"] for event in actions if event.get("level_completed")]
            final = actions[-1]["action_num"]
            game = game_key(path)
            bench = timing[game]
            history = bench["history"]
            if len(history) != len(actions):
                raise ValueError("benchmark history/action count mismatch for {} {}".format(run, game))
            yield {
                "run": run,
                "game": game,
                "actions": actions,
                "ups": ups,
                "final": final,
                "last": ups[-1] if ups else None,
                "levels": len(ups),
                "history": history,
                "final_seconds": bench["final_wallclock_seconds"],
            }


def pct(n, d):
    return "{:.2f}%".format(100 * n / d) if d else "n/a"


def quantile(values, q):
    ordered = sorted(values)
    return ordered[int(q * (len(ordered) - 1))]


def fire(record, k):
    """Return (fire action index, later level-up action index), or (None, None)."""
    last_up = 0
    streak = 0
    for action in record["actions"]:
        if action.get("level_completed"):
            last_up = action["action_num"]
            streak = 0
        else:
            streak += 1
            if streak >= k:
                later = next((u for u in record["ups"] if u > action["action_num"]), None)
                return action["action_num"], later
    return None, None


def q1(rows):
    cleared = [row for row in rows if row["last"] is not None]
    never = [row for row in rows if row["last"] is None]
    tails = [(row["final"] - row["last"]) / row["final"] for row in cleared]
    print("\nQ1 — TAIL SIZE (units: action indices and actions; no seconds)")
    print("run-games={} cleared={} never-cleared={}".format(len(rows), len(cleared), len(never)))
    level_counts = collections.Counter(row["levels"] for row in rows)
    print("levels_cleared distribution (levels:run-games): {}".format(
        ", ".join("{}:{}".format(level, level_counts[level]) for level in sorted(level_counts))))
    print("tail_frac distribution among cleared: min={:.3f} p25={:.3f} median={:.3f} p75={:.3f} p90={:.3f} max={:.3f}".format(
        min(tails), quantile(tails, .25), statistics.median(tails), quantile(tails, .75),
        quantile(tails, .90), max(tails)))
    print("tail_frac bins among cleared: 0={}, (0,.25]={}, (.25,.50]={}, (.50,.75]={}, >.75={}".format(
        sum(t == 0 for t in tails), sum(0 < t <= .25 for t in tails),
        sum(.25 < t <= .50 for t in tails), sum(.50 < t <= .75 for t in tails),
        sum(t > .75 for t in tails)))
    print("thresholds among cleared: >.25={} >.50={} >.75={}".format(
        sum(t > .25 for t in tails), sum(t > .50 for t in tails), sum(t > .75 for t in tails)))
    print("never-cleared convention: last_level_up=N/A; tail_frac=N/A; all final actions are reported separately, not included below.")
    print("run headline: fraction of actions after own last level-up (cleared games only)")
    print("run       after_actions/total_actions  fraction   never_actions")
    pooled_after = pooled_total = pooled_never = 0
    for run in RUNS5:
        group = [row for row in cleared if row["run"] == run]
        ns = [row for row in never if row["run"] == run]
        after = sum(row["final"] - row["last"] for row in group)
        total = sum(row["final"] for row in group)
        never_actions = sum(row["final"] for row in ns)
        pooled_after += after
        pooled_total += total
        pooled_never += never_actions
        print("{:<8} {:>7}/{:<7} {:>8} {:>13}".format(run, after, total, pct(after, total), never_actions))
    print("pooled    {:>7}/{:<7} {:>8} {:>13}".format(pooled_after, pooled_total, pct(pooled_after, pooled_total), pooled_never))


def q2(rows):
    between = []
    worst = None
    for row in rows:
        for first, second in zip(row["ups"], row["ups"][1:]):
            gap = second - first - 1
            between.append(gap)
            if worst is None or gap > worst[0]:
                worst = (gap, row["run"], row["game"], first, second)
    print("\nQ2 — DETECTOR OUTCOMES (units: actions)")
    print("K range: 10..120 actions, by 10; this spans common gaps and exceeds the 114-action corpus hard floor.")
    print("longest gap between successive level-ups: {} no-level actions ({} {}, level-up actions {} -> {})".format(*worst))
    print("K   fires_correct  fires_wrong  false_positive_delay_actions(min/median/max)")
    for k in KS:
        correct = wrong = 0
        delays = []
        for row in rows:
            fired, later = fire(row, k)
            if fired is None:
                continue
            if later is None:
                correct += 1
            else:
                wrong += 1
                delays.append(later - fired)
        delay = "n/a" if not delays else "{}/{}/{}".format(min(delays), statistics.median(delays), max(delays))
        print("{:>3} {:>13} {:>12} {:>32}".format(k, correct, wrong, delay))


def q3(rows):
    print("\nQ3 — COUNTERFACTUAL ACTIONS/SECONDS FREED")
    print("Stopping point: the Kth consecutive no-level-up action; seconds are per-game wall-clock seconds from benchmark history, summed across games (not shared wall time).")
    print("K   run       freed_actions/total_actions  fraction   freed_seconds")
    for k in KS:
        for run in RUNS5:
            group = [row for row in rows if row["run"] == run]
            freed_actions = 0
            freed_seconds = 0.0
            total = sum(row["final"] for row in group)
            for row in group:
                fired, _ = fire(row, k)
                if fired is not None:
                    freed_actions += row["final"] - fired
                    freed_seconds += row["final_seconds"] - row["history"][fired - 1]["wallclock_seconds"]
            print("{:>3} {:<8} {:>7}/{:<7} {:>8} {:>14.2f}".format(k, run, freed_actions, total, pct(freed_actions, total), freed_seconds))
        group = rows
        freed_actions = freed_seconds = 0
        total = sum(row["final"] for row in group)
        for row in group:
            fired, _ = fire(row, k)
            if fired is not None:
                freed_actions += row["final"] - fired
                freed_seconds += row["final_seconds"] - row["history"][fired - 1]["wallclock_seconds"]
        print("{:>3} {:<8} {:>7}/{:<7} {:>8} {:>14.2f}".format(k, "pooled", freed_actions, total, pct(freed_actions, total), freed_seconds))


def main():
    counts, games, turns, pair = controls()
    for run in RUNS5:
        print("{} games={} analysis_turns={}".format(run, counts[run][0], counts[run][1]))
    print("PAIR v10cal+thuiv1 turns={} expected=1973 match={}".format(pair, pair == 1973))
    print("ALL5 turns={} expected=5052 match={}".format(turns, turns == 5052))
    print("ALL5 run-games={} expected=125 match={}".format(games, games == 125))
    if (pair, turns, games) != (1973, 5052, 125):
        print("STOP: positive control did not match; no analysis performed.")
        return 1
    rows = list(records())
    q1(rows)
    q2(rows)
    q3(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
