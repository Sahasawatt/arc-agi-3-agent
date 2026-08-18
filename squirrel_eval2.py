"""squirrel_eval2.py -- run Squirrel v2 on all 17 local games, foreground.

    ./.venv/Scripts/python.exe squirrel_eval2.py > results/squirrel-eval-2.txt

Same harness as squirrel_eval.py (500 actions/game, 120s wall cap/game,
scoring.py). Prints a v2-vs-v1-vs-wave14 table; v1 numbers are parsed back
out of results/squirrel-eval-1.txt (same "name squirrel L/T levels ..."
line shape squirrel_eval.py already writes) so this file never hand-copies
a score. Any game where v2 clears a level neither v1 nor the wave14 driver
stack clears is flagged FIRST LINE IN CAPS and its win events are extracted
to results/squirrel-v2-win-<game>.json, same shape as g50t_w1.py's replay
log (RESET / int action value / ["click", y, x] events + win_event_idx) so
g50t_w2.py's replay pattern can verify any of them later.
"""
import json
import re
import time
from pathlib import Path

import arc_agi

from scoring import environment_score, level_score
from squirrel import Squirrel

PLAYABLE = ["ar25", "cn04", "dc22", "ka59", "ls20", "m0r0", "re86", "sc25", "sp80",
            "bp35", "g50t", "sk48", "tr87", "tu93", "wa30", "cd82", "sb26"]
MAX_ACTIONS = 500
WALL_CAP_S = 120


def parse_levels(path):
    """{'ar25': (levels, total), ...} from a 'ar25  ... L/T levels ...' line."""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(\w+)\s+(?:squirrel\s+)?(\d+)/(\d+) levels", line)
        if m:
            out[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return out


def play(env, seed=0, record=False, stop_after_first_level=False):
    """Drive Squirrel v2 for one game. Returns (levels_completed,
    actions_per_level, total_actions, note, events_or_None, win_event_idx).
    win_event_idx is set only when record and stop_after_first_level and a
    level-up actually happens -- the index of the event that caused it."""
    events = [] if record else None
    obs = env.reset()
    if record:
        events.append("RESET")

    def logged_reset():
        if record:
            events.append("RESET")
        return env.reset()

    agent = Squirrel(list(env.action_space), max_actions=MAX_ACTIONS,
                      reset_fn=logged_reset, seed=seed)
    level_actions, since_level = [], 0
    prev_level = obs.levels_completed
    t0 = time.time()
    note = ""
    win_event_idx = None
    while True:
        if time.time() - t0 > WALL_CAP_S:
            note = "WALL_CAP"
            break
        try:
            action = agent.act(obs)
        except StopIteration:
            break
        data = agent.pending_data
        if record:
            events.append(["click", data["y"], data["x"]] if data is not None else int(action.value))
        obs = env.step(action, data=data)
        since_level += 1
        if obs is None:
            note = "obs=None"
            break
        if obs.levels_completed > prev_level:
            level_actions.append(since_level)
            since_level = 0
            prev_level = obs.levels_completed
            if record and win_event_idx is None:
                win_event_idx = len(events) - 1
            if stop_after_first_level:
                break
    return prev_level, level_actions, agent.n_actions, note, events, win_event_idx


def extract_win(name, seed=0):
    """Re-run one game with event recording, stopping at the FIRST level-up,
    and write results/squirrel-v2-win-<name>.json in the g50t_w1.py shape
    (RESET / int action value / ["click", y, x] events + win_event_idx) so
    g50t_w2.py's replay pattern can verify it later."""
    arc = arc_agi.Arcade()
    env = arc.make(name, seed=seed)
    levels, level_actions, n_actions, note, events, win_event_idx = play(
        env, seed=seed, record=True, stop_after_first_level=True)
    out = {"seed": seed, "game": name, "win_event_idx": win_event_idx,
           "levels_completed": levels, "level_actions": level_actions,
           "n_events": len(events), "events": events}
    path = Path(f"results/squirrel-v2-win-{name}.json")
    path.write_text(json.dumps(out), encoding="utf-8")
    return path


def main():
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    v1 = parse_levels(Path("results/squirrel-eval-1.txt"))
    wave14 = parse_levels(Path("results/sweep-wave14.log"))

    rows = []
    new_wins = []
    for name in PLAYABLE:
        info = envs[name]
        base = info.baseline_actions
        try:
            levels, level_actions, n_actions, note, _, _ = play(arc.make(info.game_id), seed=0)
        except Exception as e:  # a crashing game must not sink the sweep
            levels, level_actions, n_actions, note = 0, [], 0, f"EXC:{type(e).__name__}:{e}"
        scores = {i + 1: level_score(base[i], n) for i, n in enumerate(level_actions) if i < len(base)}
        score = environment_score(scores, len(base))
        v1_levels, v1_total = v1.get(name, (None, None))
        w_levels, w_total = wave14.get(name, (None, None))
        rows.append({"name": name, "levels": levels, "total_levels": len(base),
                     "level_actions": level_actions, "n_actions": n_actions,
                     "score": score, "note": note,
                     "v1_levels": v1_levels, "wave14_levels": w_levels})
        v1s = f"{v1_levels}/{v1_total}" if v1_levels is not None else "?"
        wvs = f"{w_levels}/{w_total}" if w_levels is not None else "?"

        # the g50t pattern: v2 clears a level NEITHER v1 NOR wave14 clears
        clears_new = w_levels is not None and levels > w_levels and (v1_levels is None or levels > v1_levels)
        line = (f"{name:5s} squirrel-v2 {levels}/{len(base)} levels  actions={level_actions}  "
                f"score={score:.3f}%  v1={v1s}  wave14={wvs}  {note}")
        if clears_new:
            line = "NEW WIN BEYOND THE DRIVER STACK -- " + line.upper()
            new_wins.append(name)
        print(line, flush=True)

    print()
    print(f"mean squirrel-v2 score over {len(rows)} environments: "
          f"{sum(r['score'] for r in rows) / len(rows):.3f}%")
    v1_scored = [r for r in rows if r["v1_levels"] is not None]
    beats_v1 = sum(1 for r in rows if r["v1_levels"] is not None and r["levels"] > r["v1_levels"])
    matches_v1 = sum(1 for r in rows if r["v1_levels"] is not None and r["levels"] == r["v1_levels"])
    loses_v1 = sum(1 for r in rows if r["v1_levels"] is not None and r["levels"] < r["v1_levels"])
    print(f"vs v1 ({len(v1_scored)} games matched): beats={beats_v1} matches={matches_v1} loses={loses_v1}")
    w_scored = [r for r in rows if r["wave14_levels"] is not None]
    beats_w = sum(1 for r in rows if r["wave14_levels"] is not None and r["levels"] > r["wave14_levels"])
    matches_w = sum(1 for r in rows if r["wave14_levels"] is not None and r["levels"] == r["wave14_levels"])
    loses_w = sum(1 for r in rows if r["wave14_levels"] is not None and r["levels"] < r["wave14_levels"])
    print(f"vs wave14 ({len(w_scored)} games matched): beats={beats_w} matches={matches_w} loses={loses_w}")

    for name in new_wins:
        path = extract_win(name)
        print(f"extracted win line -> {path}", flush=True)


if __name__ == "__main__":
    main()
