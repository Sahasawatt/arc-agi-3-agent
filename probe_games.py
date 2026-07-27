"""Measure, per game, whether the assumptions `solver.py` is built on actually hold.

`solver.py` is not generic — it hardcodes ls20's colours and its 5-cell step. Running it
against 25 games would fail everywhere for reasons unrelated to the question. What the
go/no-go actually needs is whether each game satisfies the *structural* assumptions that
make walkable-map + BFS applicable at all:

  H-A  some object moves in response to an action        (there is a piece to plan for)
  H-B  it moves by a constant step                       (the board discretises)
  H-C  terrain splits into bulk fill vs the rest         (there is a map to build)
  H-D  several actions produce distinct movements        (there are directions)
  H-E  the game needs pointer actions                    (BFS over a grid is the wrong model)

Costs ~2 actions per available action per game, so the whole sweep is a few hundred actions.

    uv run python probe_games.py            # all games
    uv run python probe_games.py ls20 ft09  # named games
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import arc_agi
from perception import objects

REPEATS = 2  # presses per action; 2 distinguishes "moved once then blocked" from "no-op"
OUT = Path("results")


def _boxes(objs):
    """(colour, cells) -> top-left, for matching the same object across a step."""
    return {(o["colour"], o["cells"]): (o["x"][0], o["y"][0]) for o in objs}


def _shifts(before, after):
    """Displacements of objects present on both sides, ignoring pure appear/disappear."""
    b, a = _boxes(before), _boxes(after)
    return [(a[k][0] - b[k][0], a[k][1] - b[k][1]) for k in b.keys() & a.keys()
            if a[k] != b[k]]


def probe(game_id, arc):
    env = arc.make(game_id)
    if env is None:
        return {"game": game_id, "error": "make() returned None"}

    obs = env.reset()
    prev, _ = objects(obs.frame)
    grid = np.array(obs.frame)[-1][:60]
    colours, counts = np.unique(grid, return_counts=True)
    bulk = [int(c) for c, n in zip(colours, counts) if n > grid.size * 0.1]

    per_action, complex_actions = {}, []
    for action in env.action_space:
        moves = []
        for _ in range(REPEATS):
            data = {"x": 32, "y": 32} if action.is_complex() else {}
            obs = env.step(action, data=data)
            if obs is None:
                continue
            cur, _ = objects(obs.frame)
            moves += _shifts(prev, cur)
            prev = cur
        per_action[action.value] = moves
        if action.is_complex():
            complex_actions.append(action.value)

    all_moves = [m for mv in per_action.values() for m in mv]
    steps = [abs(v) for m in all_moves for v in m if v]
    step_mode = Counter(steps).most_common(1)[0][0] if steps else None
    constant_step = bool(steps) and all(s % step_mode == 0 for s in steps)
    directions = {tuple(np.sign(m)) for m in all_moves if any(m)}

    return {
        "game": game_id,
        "objects_at_reset": len(prev),
        "bulk_fill_colours": bulk,
        "moved": bool(all_moves),                       # H-A
        "step_size": step_mode,                         # H-B
        "constant_step": constant_step,                 # H-B
        "terrain_separable": 1 <= len(bulk) <= 3,        # H-C
        "distinct_directions": len(directions),          # H-D
        "complex_actions": complex_actions,              # H-E
        "actions_spent": len(env.action_space) * REPEATS,
    }


def verdict(r):
    """Classify a game by which assumption it breaks first. Order matters."""
    if r.get("error"):
        return "ERROR", r["error"]
    if not r["moved"]:
        if r["complex_actions"]:
            return "NEEDS_POINTER", "no keyboard action moved anything; game exposes click actions"
        return "NO_PLAYER_FOUND", "no object moved under any action — perception may not segment it"
    if not r["terrain_separable"]:
        return "NO_MAP", f"no clean bulk-fill terrain (found {len(r['bulk_fill_colours'])} candidates)"
    if not r["constant_step"]:
        return "NOT_GRID_STEPPED", f"movements are not multiples of one step (mode {r['step_size']})"
    if r["distinct_directions"] < 3:
        return "PARTIAL", f"only {r['distinct_directions']} distinct movement direction(s)"
    return "MAZE_LIKE", f"grid-stepped by {r['step_size']}, {r['distinct_directions']} directions, terrain separable"


def main():
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    wanted = sys.argv[1:] or sorted(envs)

    rows = []
    for name in wanted:
        info = envs.get(name)
        if info is None:
            print(f"{name}: unknown game", file=sys.stderr)
            continue
        r = probe(info.game_id, arc)
        r["tags"] = info.tags
        r["levels"] = len(info.baseline_actions)
        r["baseline_actions"] = info.baseline_actions
        r["verdict"], r["reason"] = verdict(r)
        rows.append(r)
        print(f"{name:6s} {r['verdict']:16s} {r['reason']}", flush=True)

    OUT.mkdir(exist_ok=True)
    # encoding is explicit: Windows defaults to cp1252 and mangles the em-dashes below
    (OUT / "generalisation-probe.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    tally = Counter(r["verdict"] for r in rows)
    lines = ["# Generalisation probe — do the solver's assumptions hold?", "",
             f"{len(rows)} games probed, {sum(r['actions_spent'] for r in rows)} actions spent.", "",
             "| game | tags | levels | verdict | step | dirs | why |", "|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["verdict"], r["game"])):
        lines.append(f"| {r['game'].split('-')[0]} | {','.join(r['tags']) or '-'} | {r['levels']} | "
                     f"**{r['verdict']}** | {r.get('step_size') or '-'} | "
                     f"{r.get('distinct_directions', '-')} | {r['reason']} |")
    lines += ["", "## Tally", ""] + [f"- {v}: {n}" for v, n in tally.most_common()]
    lines += ["", "## How much to trust this", "",
              "Every verdict is a **lower bound**. The probe presses each action "
              f"{REPEATS}x from a single reset, so it samples one state — a game whose piece "
              "starts against a wall, or that needs a mode set before anything moves, reads "
              "as if nothing moves. Two independent cross-checks on the run of 2026-07-27:",
              "",
              "- `ft09` came out NEEDS_POINTER, but arXiv 2512.24156 Table 1 reports a "
              "keyboard agent clearing 3 of its levels — a confirmed false negative.",
              "- `cd82` and `sb26` are tagged `keyboard_click` yet no keyboard action moved "
              "anything, which is suspicious for the same reason.",
              "- Games with very high object counts (`bp35` 183, `tu93` 64, `tr87` 56) most "
              "likely fail `constant_step` because perception over-segments and the "
              "colour+size match links the wrong pair, not because the board is not grid-stepped.",
              "",
              "So MAZE_LIKE is the trustworthy number; the failure classes are hypotheses "
              "about *why*, and each needs a per-game follow-up before being believed."]
    (OUT / "generalisation-probe.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(f"{v}: {n}" for v, n in tally.most_common()))


if __name__ == "__main__":
    main()
