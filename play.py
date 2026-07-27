"""Play a game with no human in the loop.

Discovery says how the piece moves. Nothing says what ends a level, so the agent finds
out the only way available: walk onto each candidate object and watch `levels_completed`.
The engine runs locally at ~2,000 FPS and a reset is free, so a wrong guess costs
wall-clock, not score — the sequence that worked is what gets replayed for the record.

    uv run python play.py ls20
    uv run python play.py                 # every MAZE_LIKE game
"""

import json
import sys

import numpy as np
from pathlib import Path

from arcengine import GameState

from discover import MAZE_LIKE, discover, locate
from goal_llm import propose
from perception import hud, objects
from plan import bfs_all, route_to, signature, targets
from signals import directions, meters, score
from trace import per_action_keys, save, step, summarise
from scoring import environment_score, level_score

OUT = Path("results")
LEARNED = OUT / "learned.json"
TRY_LIMIT = 12          # candidate objects to test per level, cheapest route first
BREADTH = 10            # sequences kept per depth, shortest total actions first
DEPTH = 3               # objects visited in one level's plan
SWEEP_CAP = 600         # reachable squares tried when nothing else works
SCOUT = 3               # objects walked onto to build a trace before asking the model
CLIMB_CAP = 60          # actions spent following the progress meter
TRACES, GAME = {}, {}   # frame-by-frame record, written to results/traces/<game>.jsonl


def load_learned():
    """What previous runs worked out, per game.

    Discovery costs 400 actions and the search costs thousands more, and none of it
    changes between runs of the same game. Writing down what was found makes the second
    run free — and in the scored setting, where exploration is charged at the same rate
    as play, the difference between knowing and re-deriving is the whole score.
    """
    if LEARNED.exists():
        return json.loads(LEARNED.read_text(encoding="utf-8"))
    return {}


def save_learned(store):
    OUT.mkdir(exist_ok=True)
    LEARNED.write_text(json.dumps(store, indent=2, sort_keys=True), encoding="utf-8")


def replay(env, actions, space, model=None, log=None):
    """Step through `actions`. With a model and a log, record every action's consequence."""
    obs = None
    for a in actions:
        before = obs
        obs = env.step(space[a])
        if obs is None or obs.state == GameState.GAME_OVER:
            return obs
        if log is not None and model is not None and before is not None:
            log.append(step(before, obs, a, model))
    return obs


def at_state(env, space, actions, model=None, log=None):
    """Reset and replay, returning the observation there (None if the run died)."""
    obs = env.reset()
    if actions:
        obs = replay(env, actions, space, model, log)
    if obs is None or obs.state == GameState.GAME_OVER:
        return None
    return obs


def reacts(o, before, after):
    """Did touching THAT object do anything — is it gone, or did the HUD move?

    Comparing total object counts does not work: perception's list fluctuates by a
    couple of components between frames, so every candidate on `sc25` reported a change
    of exactly 2 including ones on the far side of the board. That is a noise detector,
    not a response detector. Ask about the object that was touched.
    """
    gone = not any(signature(x) == signature(o)
                   and x["x"][0] == o["x"][0] and x["y"][0] == o["y"][0]
                   for x in objects(after.frame)[0])
    return gone or hud(after.frame) != hud(before.frame)


def collect_all(env, model, space, prefix, sig, level_start, cap=40):
    """Visit every object of one kind, nearest first, replanning after each pickup.

    Five of the nine games answer a touch — an object vanishes, or the HUD moves — and
    still do not end the level after three of them. "Collect all of these" is the obvious
    rule that fits, and it needs a tour rather than a deeper search: the kind is already
    chosen by evidence, so there is nothing to enumerate.
    """
    acts = []
    for _ in range(cap):
        obs = at_state(env, space, prefix + acts)
        if obs is None:
            return None
        if obs.levels_completed > level_start:
            return acts
        routes = [(len(r), r) for o in targets(obs.frame, model) if signature(o) == sig
                  for r in [route_to(obs.frame, model, o)] if r]
        if not routes:
            return None
        acts += min(routes)[1]
    return None


def try_plan(env, model, space, prefix, plan, targets_now, level_start):
    """Walk the piece onto each object in `plan`, in order. Returns actions or None."""
    acts = []
    for i in plan:
        obs = at_state(env, space, prefix + acts)
        if obs is None:
            return None
        here = targets(obs.frame, model)
        # The board changes as the plan runs, so match the object by what it looked like
        # when the plan was made rather than by its position in a stale list.
        want = signature(targets_now[i])
        cands = [(len(r), r) for o in here if signature(o) == want
                 for r in [route_to(obs.frame, model, o)] if r]
        if not cands:
            return None
        acts += min(cands)[1]
    obs = at_state(env, space, prefix + acts)
    return acts if obs is not None and obs.levels_completed > level_start else None


def sweep(env, model, space, prefix, level_start, cap=SWEEP_CAP):
    """Try standing on every reachable square, nearest first.

    The object list is a hypothesis about where the goal is. This is the space itself —
    a level that ends by reaching a spot with nothing drawn on it is invisible to the
    object search and obvious here. Returns (actions, positions tried).
    """
    obs = at_state(env, space, prefix)
    if obs is None:
        return None, 0
    at = locate(obs.frame, model)
    if at is None:
        return None, 0
    grid = np.array(obs.frame)[-1][:model.rows]
    paths = bfs_all(grid, model, (at[0], at[1]))
    ordered = sorted(paths.values(), key=len)[:cap]
    for i, acts in enumerate(ordered, 1):
        if not acts:
            continue
        got = at_state(env, space, prefix + acts)
        if got is not None and got.levels_completed > level_start:
            return acts, i
    return None, len(ordered)


def sense_meters(env, model, space, prefix, n=24):
    """Walk a continuous line and read the game's own counters -> (colours, directions).

    It has to be ONE walk. Sampling independent replays of increasing length made the
    budget bar look like progress, because it only changed when the replay got longer.
    """
    obs = at_state(env, space, prefix)
    if obs is None:
        return [], {}
    frames, order = [obs.frame], sorted(model.dirs)
    for i in range(n):
        obs = env.step(space[order[i % len(order)]])
        if obs is None or np.array(obs.frame).size == 0 or obs.state == GameState.GAME_OVER:
            break
        frames.append(obs.frame)
    prog = [c for c, kind in meters(frames).items() if kind == "progress"]
    return prog, directions(frames, prog)


def climb(env, model, space, prefix, level_start, prog, way, cap=CLIMB_CAP):
    """Follow the game's own progress meter, one target at a time.

    Every earlier strategy had to guess the whole goal in one shot, because
    `levels_completed` is a single bit that only flips at the end. A meter that moves part
    way is a gradient: take the step that moves it most per action, then look again.
    """
    if not prog:
        return None
    acts = []
    while len(acts) < cap:
        obs = at_state(env, space, prefix + acts)
        if obs is None:
            return None
        if obs.levels_completed > level_start:
            return acts
        here = score(obs.frame, prog, way)
        best = None
        for o in targets(obs.frame, model)[:TRY_LIMIT]:
            r = route_to(obs.frame, model, o)
            if not r or len(acts) + len(r) > cap:
                continue
            nxt = at_state(env, space, prefix + acts + r)
            if nxt is None:
                continue
            if nxt.levels_completed > level_start:
                return acts + r
            gain = (score(nxt.frame, prog, way) - here) / len(r)
            if gain > 0 and (best is None or gain > best[0]):
                best = (gain, r)
        if best is None:
            return None
        acts += best[1]
    return None


def clear_level(env, model, space, prefix, level_start, depth=DEPTH, use_llm=True):
    """Shortest action sequence that advances the level, or None.

    One object is rarely the whole answer: on ls20 the piece must touch the marker
    before the goal box will take it, so walking the 6 moves straight into the box does
    nothing and the human's route is 14. So this searches SEQUENCES of objects, shortest
    total first — the engine is local and a reset is free, so a wrong guess costs
    wall-clock rather than score.
    """
    tried = 0

    # A local model is a prior over what a goal looks like; the search has none and picks
    # by route length, which is a guess. It never acts on the answer — the planner routes
    # and `levels_completed` judges, and a wrong guess costs a free replay.
    # Scout first, always: walk onto the nearest few objects and record what each action
    # did. The capture is the deliverable whether or not a model reads it — every attempt
    # before this was judged by one bit and threw the rest away.
    base = at_state(env, space, prefix)
    history = ""
    if base is not None:
        cands = targets(base.frame, model)[:TRY_LIMIT]
        log = []
        for o in cands[:SCOUT]:
            r = route_to(base.frame, model, o)
            if r:
                at_state(env, space, prefix, model, log)
                replay(env, r, space, model, log)
        if log:
            TRACES.setdefault(GAME.get("name", "?"), []).extend(log)
            history = summarise(log, per_action_keys(log))

        # A local model is a prior over what a goal looks like; the search has none and
        # picks by route length, which is a guess. It never acts on the answer — the
        # planner routes and `levels_completed` judges, and a wrong guess is a free replay.
        if use_llm:
            for plan in propose(model, cands, hud(base.frame), level_start + 1,
                                history=history):
                tried += 1
                acts = try_plan(env, model, space, prefix, plan, cands, level_start)
                if acts:
                    return acts, tried

    frontier = [[]]
    for _ in range(depth):
        scored = []
        for acts in frontier:
            obs = at_state(env, space, prefix + acts)
            if obs is None:
                continue
            for o in targets(obs.frame, model)[:TRY_LIMIT]:
                r = route_to(obs.frame, model, o)
                if r:
                    scored.append((len(acts) + len(r), acts + r))
        scored.sort(key=lambda t: t[0])

        nxt = []
        for _, acts in scored[:BREADTH]:
            tried += 1
            obs = at_state(env, space, prefix + acts)
            if obs is None:
                continue
            if obs.levels_completed > level_start:
                return acts, tried
            nxt.append(acts)
        if not nxt:
            break
        frontier = nxt

    # Nothing short worked. Anything that answered a touch is a candidate for "collect
    # them all" — try a tour of each such kind, most-reactive kind first.
    base = at_state(env, space, prefix)
    if base is None:
        return None, tried
    kinds = []
    for o in targets(base.frame, model)[:TRY_LIMIT]:
        r = route_to(base.frame, model, o)
        if not r:
            continue
        after = at_state(env, space, prefix + r)
        if after is not None and reacts(o, base, after):
            kinds.append(signature(o))
    for sig in dict.fromkeys(kinds):
        tried += 1
        acts = collect_all(env, model, space, prefix, sig, level_start)
        if acts:
            obs = at_state(env, space, prefix + acts)
            if obs is not None and obs.levels_completed > level_start:
                return acts, tried

    prog, way = sense_meters(env, model, space, prefix)
    acts = climb(env, model, space, prefix, level_start, prog, way)
    if acts:
        return acts, tried + 1

    acts, n = sweep(env, model, space, prefix, level_start)
    return (acts, tried + n) if acts else (None, tried + n)


def play(env, model, space, max_levels=8, use_llm=True):
    """Clear levels one after another. Returns (prefix, per-level action counts)."""
    prefix, counts = [], []
    for _ in range(max_levels):
        obs = env.reset()
        replay(env, prefix, space)
        done = obs.levels_completed if not prefix else len(counts)
        actions, _ = clear_level(env, model, space, prefix, done, use_llm=use_llm)
        if actions is None:
            break
        prefix += actions
        counts.append(len(actions))
    return prefix, counts


def main():
    import arc_agi
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    rows = []
    store = load_learned()
    relearn = "--relearn" in sys.argv
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or MAZE_LIKE
    for name in names:
        info = envs[name]
        GAME["name"] = name
        env = arc.make(info.game_id)
        space = {a.value: a for a in env.action_space}

        known = store.get(name) if not relearn else None
        if known and known.get("actions"):
            prefix, counts, spent = known["solution"], known["actions"], 0
            obs = at_state(env, space, prefix)
            reused = obs is not None and obs.levels_completed >= len(counts)
            if not reused:                      # the note was wrong; earn it again
                known = None
        if not known or not known.get("actions"):
            model, spent = discover(env, budget=400)
            if model is None:
                print(f"{name}: no model", flush=True)
                continue
            prefix, counts = play(env, model, space, use_llm="--no-llm" not in sys.argv)
            store[name] = {"solution": prefix, "actions": counts,
                           "discovery_actions": spent,
                           "piece": {"colour": model.colour, "parts": [list(p) for p in model.parts],
                                     "box": list(model.box), "step": model.step},
                           "dirs": {str(a): list(d) for a, d in sorted(model.dirs.items())},
                           "walls": sorted(model.blocking)}
            save_learned(store)

        base = info.baseline_actions
        scores = {i + 1: level_score(base[i], n) for i, n in enumerate(counts) if i < len(base)}
        row = {"game": name, "levels": len(counts), "of": len(base), "actions": counts,
               "baseline": base[:len(counts)], "discovery_actions": spent,
               "level_scores": {str(k): round(v, 2) for k, v in scores.items()},
               "environment_score": round(environment_score(scores, len(base)), 3)}
        rows.append(row)
        row["from_memory"] = spent == 0
        print(f"{name:6s} cleared {row['levels']}/{row['of']} levels  "
              f"actions={counts} vs baseline={row['baseline']}  "
              f"score={row['environment_score']}%"
              + ("   [from memory, 0 discovery actions]" if spent == 0 else ""), flush=True)

    for game, steps in TRACES.items():
        if steps:
            print(f"  trace: {save(game, steps)} ({len(steps)} actions)", flush=True)

    if rows:
        OUT.mkdir(exist_ok=True)
        (OUT / "play.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        total = sum(r["environment_score"] for r in rows) / len(rows)
        print(f"\nmean environment score over {len(rows)} games: {total:.3f}%")


if __name__ == "__main__":
    main()
