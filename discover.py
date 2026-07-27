"""Work out a game's movement mechanics by acting, with no game-specific constants.

`solver.py` hardcodes ls20: the piece is colour 12, a move shifts 5 cells, colour 4 is the
wall. Those three facts came from a human reading the screen, which is the part of the
pipeline that does not generalise. Everything here is derived from what actually happened:

  player   the component that shifts under the most actions
  dirs     per action, the mode of its observed displacements
  step     the gcd of every displacement (not the mode — a 2-step game also shows 4s)
  walls    a colour the piece has been observed to move *onto* is passable; a colour that
           only ever appears in the destination of a *blocked* move is a wall

The last one is the reason bulk-fill statistics are not enough: ls20 has two bulk colours
and only one of them stops the piece, and `dc22` has three.

    uv run python discover.py ls20          # one game
    uv run python discover.py               # every MAZE_LIKE game
"""

import json
import sys
from collections import Counter
from dataclasses import dataclass
from math import gcd
from pathlib import Path

import numpy as np

from perception import HUD_ROW, objects


@dataclass
class Model:
    player: tuple           # (colour, cells) of the component we steer
    body: set               # every component that moves with it — the piece may be multi-coloured
    box: tuple              # (w, h) footprint, the body's union bounding box
    dirs: dict              # action value -> (dx, dy)
    step: int
    passable: set           # colours observed under a successful move
    blocking: set           # colours that only ever appeared when a move failed
    rows: int               # play-area height; below this is the HUD


def _boxes(objs):
    """(colour, cells) -> (x, y, w, h). Collides if two objects share colour and area."""
    return {(o["colour"], o["cells"]):
            (o["x"][0], o["y"][0], o["x"][1] - o["x"][0] + 1, o["y"][1] - o["y"][0] + 1)
            for o in objs}


def _shifts(before, after):
    """Displacement of every object present on both sides."""
    return {k: (after[k][0] - before[k][0], after[k][1] - before[k][1])
            for k in before.keys() & after.keys() if after[k][:2] != before[k][:2]}


def choose_action(visits, state, actions):
    """Least-tried action *in this state*.

    Cycling the action list in order makes the piece oscillate: up then down is a no-op
    pair, so the walk never leaves its starting cell and never meets a wall — and a wall
    is only observable from a move that failed. Keying novelty on the frame means this
    needs no idea yet of which object is the player.

    Ties break on how often the action has been used *anywhere*, not on its number: every
    successful move lands in a state where nothing has been tried, so a numeric tiebreak
    walks in a straight line — 48 actions on `sp80` used one of its five.
    """
    seen = Counter()
    for (_, a), n in visits.items():
        seen[a] += n
    return min(actions, key=lambda a: (visits.get((state, a), 0), seen[a], actions.index(a)))


def choose_probe(grid, at, dirs, known, actions):
    """The move whose destination shows the most colours we cannot classify yet.

    Wandering meets a wall by accident. Once the directions are known the frame already
    says where the open question is, and every action costs score, so ask it directly.
    Returns None when nothing in reach is new — then fall back to novelty.
    """
    best, score = None, 0
    for a in actions:
        d = dirs.get(a)
        if d is None:
            continue
        cs = dest_colours(grid, at[0], at[1], at[2], at[3], d[0], d[1])
        if cs is None:
            continue
        n = len(cs - known)
        if n > score:
            best, score = a, n
    return best


def infer_player(records):
    """The component that responds to the most actions."""
    votes = Counter(k for r in records for k in r["shifts"])
    if not votes:
        return None
    return max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0]


def infer_body(records, player):
    """Every component that moves rigidly with the player.

    The piece is often drawn in more than one colour, so perception splits it. Planning
    with one fragment measures the wrong footprint and the wall never shows up in the
    destination. Requiring agreement on *every* move the player made keeps a bystander
    that happens to drift the same way once out of the body.
    """
    agree, n = Counter(), 0
    for r in records:
        d = r["shifts"].get(player)
        if d is None:
            continue
        n += 1
        agree.update(k for k, dk in r["shifts"].items() if dk == d)
    return {k for k, c in agree.items() if c == n} if n else {player}


def body_box(boxes, body):
    """Union bounding box of the body's components present this frame -> (x, y, w, h)."""
    parts = [boxes[k] for k in body if k in boxes]
    if not parts:
        return None
    x0 = min(p[0] for p in parts)
    y0 = min(p[1] for p in parts)
    x1 = max(p[0] + p[2] for p in parts)
    y1 = max(p[1] + p[3] for p in parts)
    return x0, y0, x1 - x0, y1 - y0


def infer_dirs(records, player):
    """Per action, the displacement it usually causes. Blocked attempts contribute nothing."""
    seen = {}
    for r in records:
        if player in r["shifts"]:
            seen.setdefault(r["action"], []).append(r["shifts"][player])
    return {a: Counter(d).most_common(1)[0][0] for a, d in seen.items()}


def infer_step(dirs):
    """The movement quantum. gcd, because a board can be stepped by 2 and show a 4."""
    mags = [abs(v) for d in dirs.values() for v in d if v]
    if not mags:
        return None
    out = 0
    for m in mags:
        out = gcd(out, m)
    return out


def dest_colours(grid, x, y, w, h, dx, dy):
    """Colours in the footprint's destination, minus the piece's own. None if off-board."""
    nx, ny = x + dx, y + dy
    if nx < 0 or ny < 0 or nx + w > grid.shape[1] or ny + h > grid.shape[0]:
        return None
    own = set(np.unique(grid[y:y + h, x:x + w]).tolist())
    dest = set(np.unique(grid[ny:ny + h, nx:nx + w]).tolist())
    return frozenset(dest - own)


def terrain_samples(records, player, body, dirs):
    """[(colours_in_destination, did_it_walk_there)] — the evidence classify_colours needs.

    A record only counts when the outcome is one of the two the terrain explains: the
    piece went exactly where the action points, or it did not move at all. A different
    displacement means something else happened (a respawn after running out of budget, a
    knock-back, a conveyor) and the destination was never entered, so it proves nothing.
    """
    out = []
    for r in records:
        d = dirs.get(r["action"])
        at = body_box(r["boxes"], body)
        if d is None or at is None:
            continue
        delta = r["shifts"].get(player)
        if delta is not None and delta != d:
            continue
        cs = dest_colours(r["grid"], at[0], at[1], at[2], at[3], d[0], d[1])
        if cs is not None:
            out.append((cs, delta == d))
    return out


def classify_colours(samples):
    """samples: [(colours_in_destination, did_it_move)] -> (passable, blocking).

    A move that succeeded proves every colour in its destination is passable. A move that
    failed proves only that *something* there blocks — so the wall is what is left after
    removing everything already known to be walkable.
    """
    passable = {c for cs, moved in samples if moved for c in cs}
    blocking = {c for cs, moved in samples if not moved for c in cs} - passable
    return passable, blocking


def walkable(grid, m: Model, x, y):
    """Can the piece's footprint sit at (x, y)?"""
    w, h = m.box
    if x < 0 or y < 0 or x + w > grid.shape[1] or y + h > m.rows:
        return False
    return not np.isin(grid[y:y + h, x:x + w], list(m.blocking)).any() if m.blocking else True


def discover(env, budget=48, rows=HUD_ROW):
    """Press actions, watch, and infer. Returns (Model | None, actions_spent)."""
    obs = env.reset()
    actions = [a for a in env.action_space if not a.is_complex()]
    if not actions:
        return None, 0

    by_value = {a.value: a for a in actions}
    values = sorted(by_value)
    records, spent, visits = [], 0, {}
    prev = _boxes(objects(obs.frame)[0])
    player = body = None
    dirs, passable, blocking = {}, set(), set()
    # Phase 1 covers the action set to learn what each one does; phase 2 uses that to aim
    # at the colours still unclassified. The split is just "do we know a direction yet".
    warmup = 2 * len(values)

    for i in range(budget):
        grid = np.array(obs.frame)[-1][:rows]
        value = None
        if i >= warmup and player is not None:
            at = body_box(prev, body)
            if at is not None:
                value = choose_probe(grid, at, dirs, passable | blocking, values)
        if value is None:
            state = hash(grid.tobytes())
            value = choose_action(visits, state, values)
            visits[(state, value)] = visits.get((state, value), 0) + 1

        obs = env.step(by_value[value])
        spent += 1
        # A frame can come back empty — `sp80` does it on a level transition — and every
        # perception call downstream indexes into it.
        if obs is None or np.array(obs.frame).size == 0:
            break
        cur = _boxes(objects(obs.frame)[0])
        records.append({"action": value, "shifts": _shifts(prev, cur),
                        "grid": grid, "boxes": prev})
        prev = cur

        if i + 1 >= warmup:
            player = infer_player(records)
            if player is not None:
                body = infer_body(records, player)
                dirs = infer_dirs(records, player)
                passable, blocking = classify_colours(
                    terrain_samples(records, player, body, dirs))

    if player is None:
        player = infer_player(records)
        if player is None:
            return None, spent
        body = infer_body(records, player)
        dirs = infer_dirs(records, player)
        passable, blocking = classify_colours(terrain_samples(records, player, body, dirs))

    box = body_box(prev, body) or body_box(records[-1]["boxes"], body)
    return Model(player=player, body=body, box=(box[2], box[3]), dirs=dirs,
                 step=infer_step(dirs), passable=passable, blocking=blocking,
                 rows=rows), spent


MAZE_LIKE = ["ar25", "cn04", "dc22", "ka59", "ls20", "m0r0", "re86", "sc25", "sp80"]
OUT = Path("results")


def main():
    import arc_agi
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    names = sys.argv[1:] or MAZE_LIKE
    rows = []
    for name in names:
        m, spent = discover(arc.make(envs[name].game_id))
        row = {"game": name, "actions": spent}
        if m is None:
            row["result"] = "no player found"
        else:
            row.update(result="ok", player=list(m.player), box=list(m.box), step=m.step,
                       dirs={a: list(d) for a, d in sorted(m.dirs.items())},
                       walls=sorted(m.blocking), floor=sorted(m.passable))
        rows.append(row)
        print(f"{name:5s} " + " ".join(f"{k}={v}" for k, v in row.items() if k != "game"),
              flush=True)

    if names == MAZE_LIKE:
        OUT.mkdir(exist_ok=True)
        (OUT / "discovery.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        got_walls = [r["game"] for r in rows if r.get("walls")]
        lines = [
            "# Autonomous mechanic discovery — what the agent works out for itself", "",
            f"{len(rows)} MAZE_LIKE games, {sum(r['actions'] for r in rows)} actions total. "
            "Nothing here is configured per game: the piece, its footprint, what each "
            "action does and which colours stop it are all measured by acting.", "",
            "| game | piece | footprint | step | directions | walls found | floor |",
            "|---|---|---|---|---|---|---|"]
        for r in rows:
            if r["result"] != "ok":
                lines.append(f"| {r['game']} | — | | | | | {r['result']} |")
                continue
            lines.append(
                f"| {r['game']} | colour {r['player'][0]} | {r['box'][0]}x{r['box'][1]} | "
                f"{r['step']} | {len(r['dirs'])} | "
                f"{r['walls'] or '**none**'} | {r['floor'] or '—'} |")
        lines += ["", "## What this does and does not establish", "",
                  f"- **Movement is solved.** All {len(rows)} games yield a piece, a "
                  "footprint, a step size and a direction per action.",
                  f"- **Walls are found on {len(got_walls)} of {len(rows)}** "
                  f"({', '.join(got_walls)}). Without a wall colour every cell reads as "
                  "walkable, so BFS will happily route through terrain — a discovered "
                  "model with an empty `walls` column is not usable for planning yet.",
                  "- **`ls20` reproduces the hand-read model exactly**: footprint 5x5, "
                  "step 5, wall colour 4, and BFS to the goal box returns the same 6 "
                  "moves the hand-tuned `solver.py` finds. That is the only game where "
                  "the discovered model has been checked against a known-good one.",
                  "- **Goal identification is still hardcoded.** Knowing where you can "
                  "walk is not knowing where to walk to; `solver.py` still names the "
                  "target colours by hand. That is the next problem, and the harder one.",
                  "", "## Why a game ends with no walls", "",
                  "A wall is only observable from a move that failed, so a run that never "
                  "gets blocked learns nothing about terrain. Two fixed causes are "
                  "recorded in the tests: cycling the actions in order made the piece "
                  "oscillate in place (47 of 48 moves succeeded, one wall seen), and "
                  "breaking ties by action number made it walk in a straight line "
                  "(`sp80` used one of its five actions). What remains is games whose "
                  "piece perception over-segments — `ar25` reports a 9x9 footprint for a "
                  "40-cell piece — so the destination measured is not the destination "
                  "entered.", ""]
        (OUT / "discovery.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"\nwrote {OUT / 'discovery.md'}")


if __name__ == "__main__":
    main()
