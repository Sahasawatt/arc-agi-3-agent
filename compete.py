"""Play the way the competition actually allows, and report what that scores.

Everything else in this repo was measured in a permissive development mode. Competition
mode allows **one `make()` per environment** and turns a game reset into a **level reset**
(docs/competition-rules.md). `play.py` reaches a state by resetting and replaying a prefix
thousands of times per level; after level 1 that would replay level-1 actions against the
level-2 board, silently. Nothing here rewinds.

So there is no try-and-see. Every action is spent for good, the model has to be built from
the actions the agent was going to take anyway, and the only reset used is the one the game
forces when it ends — which is legal, and is a level reset by definition.

    uv run python compete.py            # every playable game
    uv run python compete.py ls20       # one
"""

import json
import sys
from pathlib import Path

import numpy as np
from arcengine import GameState

from discover import (Model, body_box, choose_next, classify_colours, infer_body, infer_dirs,
                      infer_player, infer_step, locate, see, terrain_samples, _shifts)
from perception import HUD_ROW, hud
from plan import route_to, targets
from scoring import environment_score, level_score
from signals import refills
from trace import per_action_keys
from trace import step as trace_step

OUT = Path("results")
PLAYABLE = ["ar25", "cn04", "dc22", "ka59", "ls20", "m0r0", "re86", "sc25", "sp80",
            "bp35", "g50t", "sk48", "tr87", "tu93", "wa30", "cd82", "sb26"]
WARMUP = 24        # actions before the model is worth trusting
BUDGET = 1200      # actions per environment; no rule caps this, 600 RPM and 9h do
REFILL_AT = 0.45   # fraction of the highest clock reading below which a refill comes first


def build_model(records, colours, rows=HUD_ROW):
    """The model as it stands from what has been played so far, or None."""
    player = infer_player(records)
    if player is None:
        return None
    body = infer_body(records, player)
    dirs = infer_dirs(records, player)
    box = None
    for r in reversed(records):
        box = body_box(r["boxes"], body)
        if box is not None:
            break
    if box is None:
        return None
    passable, blocking = classify_colours(terrain_samples(records, player, body, dirs, colours))
    parts = tuple(sorted((colours[k], r["boxes"][k][2], r["boxes"][k][3])
                         for r in [records[-1]] for k in body
                         if k in r["boxes"] and k in colours))
    return Model(player=player, body=body, colour=colours.get(player, -1), parts=parts,
                 box=(box[2], box[3]), dirs=dirs, step=infer_step(dirs),
                 passable=passable, blocking=blocking, rows=rows)


def play(env, budget=BUDGET, rows=HUD_ROW):
    """One environment, forward only. Returns (actions per completed level, trace)."""
    obs = env.reset()
    actions = [a for a in env.action_space if not a.is_complex()]
    if not actions or obs is None:
        return [], []
    by_value = {a.value: a for a in actions}
    values = sorted(by_value)

    prev, colours, tracks, next_id = see(obs.frame, [], 0, rows)
    records, visits, log, seen_max = [], {}, [], 0
    model, plan, last = None, [], None
    done, spent_at_level, per_level = obs.levels_completed, 0, []

    for i in range(budget):
        grid = np.array(obs.frame)[-1][:rows]
        state = grid.tobytes()

        # Follow a route if one is in flight; otherwise explore. Both are forward-only.
        if plan:
            value = plan.pop(0)
        else:
            # Track ids first — they are exact on the board that made them. They die at a
            # level boundary, so a model carried across one falls back to recognising the
            # piece by appearance. Using `locate` unconditionally cost m0r0 its level.
            at = None
            if model and i >= WARMUP:
                at = body_box(prev, model.body) or locate(obs.frame, model)
            value = choose_next(grid, at, model.dirs if model else {},
                                (model.passable | model.blocking) if model else set(),
                                values, last, visits, state)
        visits[(state, value)] = visits.get((state, value), 0) + 1

        before = obs
        obs = env.step(by_value[value])
        spent_at_level += 1
        if obs is None:
            break

        if obs.levels_completed > done:
            per_level.append(spent_at_level)
            done, spent_at_level, plan = obs.levels_completed, 0, []
            # The board is new, so the evidence and the track ids are worthless — but the
            # MECHANICS are not. Within one game the piece and its controls carry across
            # levels, and paying discovery again on every level is paying it where the
            # weights are highest. Keep the model only while it still recognises its own
            # piece; when `locate` fails, the game has changed the piece and it goes.
            records, visits, last = [], {}, None
            prev, colours, tracks, next_id = see(obs.frame, [], 0, rows)
            if model and locate(obs.frame, model) is None:
                model = None
            continue

        # A game over ends the run; the reset the engine gives back is a LEVEL reset, which
        # is what competition mode permits, and the level's action count carries on.
        if np.array(obs.frame).size == 0 or obs.state == GameState.GAME_OVER:
            obs = env.reset()
            if obs is None or np.array(obs.frame).size == 0:
                break
            prev, colours, tracks, next_id = see(obs.frame, [], 0, rows)
            plan, last = [], None
            continue

        cur, seen_c, tracks, next_id = see(obs.frame, tracks, next_id, rows)
        colours.update(seen_c)
        shifts = _shifts(prev, cur)
        records.append({"action": value, "shifts": shifts, "grid": grid,
                        "boxes": prev, "after": set(cur)})
        if model:
            log.append(trace_step(before, obs, value, model))
            last = value if shifts.get(model.player) == model.dirs.get(value) else None
        prev = cur

        if i >= WARMUP and not plan:
            model = build_model(records, colours, rows) or model
            if model and locate(obs.frame, model):
                cands = targets(obs.frame, model)[:6]

                # A clock only falls, so a rise is an event and whatever vanished caused
                # it. That is a refill, and it is the mechanic a level longer than one
                # life's budget cannot be walked without. When the clock is low, go and
                # get one before doing anything else.
                clock = per_action_keys(log)
                low = False
                if clock:
                    here = sum(hud(obs.frame).get(k, 0) for k in clock)
                    seen_max = max(seen_max, here)
                    low = seen_max > 0 and here < REFILL_AT * seen_max
                if low:
                    want = {g[0] for g in refills(log, clock)}
                    cands = [o for o in cands if o["colour"] in want] + cands

                for o in cands:
                    r = route_to(obs.frame, model, o)
                    if r:
                        plan = r
                        break

    return per_level, log


def main():
    import arc_agi
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    rows = []
    for name in sys.argv[1:] or PLAYABLE:
        info = envs[name]
        counts, log = play(arc.make(info.game_id))
        base = info.baseline_actions
        scores = {i + 1: level_score(base[i], n) for i, n in enumerate(counts) if i < len(base)}
        row = {"game": name, "levels": len(counts), "of": len(base), "actions": counts,
               "baseline": base[:len(counts)],
               "environment_score": round(environment_score(scores, len(base)), 3)}
        rows.append(row)
        print(f"{name:6s} {row['levels']}/{row['of']} levels  actions={counts}  "
              f"score={row['environment_score']}%", flush=True)

    if rows:
        OUT.mkdir(exist_ok=True)
        (OUT / "compete.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        # Averaged over every environment, played or not — the competition scores the ones
        # you skip as zeroes too.
        print(f"\nmean over {len(rows)} environments: "
              f"{sum(r['environment_score'] for r in rows) / len(rows):.3f}%")


if __name__ == "__main__":
    main()
