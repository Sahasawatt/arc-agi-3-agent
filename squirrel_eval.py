"""squirrel_eval.py -- run Squirrel on all 17 local games, foreground.

    ./.venv/Scripts/python.exe squirrel_eval.py > results/squirrel-eval-1.txt

Per-game try/except + a 120s wall cap (a hung game must not sink the sweep),
max_actions=500 per game (comparable to compete's per-game budgets). Scores
with the same offline reimplementation compete.py uses (scoring.py), so the
number is directly comparable to results/sweep-wave13.log's column.
"""
import re
import sys
import time
from pathlib import Path

import arc_agi

from scoring import environment_score, level_score
from squirrel import Squirrel

PLAYABLE = ["ar25", "cn04", "dc22", "ka59", "ls20", "m0r0", "re86", "sc25", "sp80",
            "bp35", "g50t", "sk48", "tr87", "tu93", "wa30", "cd82", "sb26"]
MAX_ACTIONS = 500
WALL_CAP_S = 120


def parse_wave13(path):
    """{'ar25': (4, 8), ...} from a 'ar25   4/8 levels  ...' line."""
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(\w+)\s+(\d+)/(\d+) levels", line)
        if m:
            out[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return out


def play(env):
    """Drive Squirrel for one game. Returns (levels_completed, actions_per_level,
    total_actions, note)."""
    obs = env.reset()
    agent = Squirrel(list(env.action_space), max_actions=MAX_ACTIONS, reset_fn=env.reset)
    level_actions, since_level = [], 0
    prev_level = obs.levels_completed
    t0 = time.time()
    note = ""
    while True:
        if time.time() - t0 > WALL_CAP_S:
            note = "WALL_CAP"
            break
        try:
            action = agent.act(obs)
        except StopIteration:
            break
        obs = env.step(action, data=agent.pending_data)
        since_level += 1
        if obs is None:
            note = "obs=None"
            break
        if obs.levels_completed > prev_level:
            level_actions.append(since_level)
            since_level = 0
            prev_level = obs.levels_completed
    return prev_level, level_actions, agent.n_actions, note


def main():
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    wave13 = parse_wave13(Path("results/sweep-wave13.log"))

    rows = []
    for name in PLAYABLE:
        info = envs[name]
        base = info.baseline_actions
        try:
            levels, level_actions, n_actions, note = play(arc.make(info.game_id))
        except Exception as e:  # a crashing game must not sink the sweep
            levels, level_actions, n_actions, note = 0, [], 0, f"EXC:{type(e).__name__}:{e}"
        scores = {i + 1: level_score(base[i], n) for i, n in enumerate(level_actions) if i < len(base)}
        score = environment_score(scores, len(base))
        w_levels, w_total = wave13.get(name, (None, None))
        rows.append({"name": name, "levels": levels, "total_levels": len(base),
                     "level_actions": level_actions, "n_actions": n_actions,
                     "score": score, "note": note,
                     "wave13_levels": w_levels, "wave13_total": w_total})
        wv = f"{w_levels}/{w_total}" if w_levels is not None else "?"
        print(f"{name:5s} squirrel {levels}/{len(base)} levels  actions={level_actions}  "
              f"score={score:.3f}%  wave13={wv}  {note}", flush=True)

    print()
    print(f"mean squirrel score over {len(rows)} environments: "
          f"{sum(r['score'] for r in rows) / len(rows):.3f}%")
    wv_scored = [r for r in rows if r["wave13_levels"] is not None]
    beats = sum(1 for r in rows if r["wave13_levels"] is not None and r["levels"] > r["wave13_levels"])
    matches = sum(1 for r in rows if r["wave13_levels"] is not None and r["levels"] == r["wave13_levels"])
    loses = sum(1 for r in rows if r["wave13_levels"] is not None and r["levels"] < r["wave13_levels"])
    print(f"vs wave13 ({len(wv_scored)} games matched): beats={beats} matches={matches} loses={loses}")


if __name__ == "__main__":
    main()
