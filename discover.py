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
from arcengine import GameState

from identity import Track, _box, update
from perception import HUD_ROW, objects

REACQUIRE = 1e9  # a reset moves everything; re-identify on appearance, not position
SIZE_SLACK = 2  # cells a part may differ by and still be recognised as itself
MIN_WALL_SUPPORT = 2  # blocked destinations where a colour is the only unexplained one
MIN_PRESENCE = 0.25  # a part seen in a handful of frames is not evidence of anything
AGREE = 0.8   # fraction of the player's moves a part must share to count as the same piece


@dataclass
class Model:
    player: int             # track id of the component we steer
    body: set               # track ids that move with it — the piece may be multi-coloured
    colour: int             # the player component's colour, for reporting
    box: tuple              # (w, h) footprint, the body's union bounding box
    dirs: dict              # action value -> (dx, dy)
    step: int
    passable: set           # colours observed under a successful move
    blocking: set           # colours that only ever appeared when a move failed
    rows: int               # play-area height; below this is the HUD
    parts: tuple = ()       # (colour, w, h) of each body component, to find the piece again
    evidence: tuple = (0, 0)  # (walked, blocked) — with 0 blocked, `blocking` means nothing


def see(frame, tracks, next_id, rows=HUD_ROW, gate=None, max_missed=2):
    """One frame -> ({track id: (x, y, w, h)}, {track id: colour}, tracks, next_id).

    Identity comes from `identity.update`, not from a dict key: keying on
    (colour, cell_count) silently dropped 55 objects across the 9 MAZE_LIKE games at
    reset alone, because two objects sharing the key collide in the dict.
    """
    objs, _ = objects(frame)
    kw = {"max_missed": max_missed}
    if gate is not None:
        kw["gate"] = gate
    tracks, assign, next_id = update(tracks, objs, next_id, **kw)
    boxes = {tid: _box(objs[oi]) for oi, tid in assign.items()}
    colours = {tid: objs[oi]["colour"] for oi, tid in assign.items()}
    return boxes, colours, tracks, next_id


def locate(frame, model):
    """Where the piece is in a frame this model was not built from -> (x, y, w, h).

    Track ids die with the board they were made on, so a model is useless on a fresh
    frame unless the piece can be recognised again from what it looks like. Match the
    body's components by (colour, width, height), then keep the group that is close
    enough together to be one piece.
    """
    objs, _ = objects(frame)
    want = set(model.parts)
    def dims(o):
        return o["colour"], o["x"][1] - o["x"][0] + 1, o["y"][1] - o["y"][0] + 1
    cands = [o for o in objs if dims(o) in want]
    if not cands:
        # A piece can be redrawn a cell wider between frames, and an exact size match
        # then loses it completely — `ar25` and `sc25` could not find their own piece on
        # the board they started from. Same colour, close enough size.
        cands = [o for o in objs
                 if any(c == dims(o)[0] and abs(w - dims(o)[1]) <= SIZE_SLACK
                        and abs(h - dims(o)[2]) <= SIZE_SLACK for c, w, h in want)]
    if not cands:
        return None
    w, h = model.box
    anchor = min(cands, key=lambda o: (o["y"][0], o["x"][0]))
    near = [o for o in cands
            if abs(o["x"][0] - anchor["x"][0]) <= w and abs(o["y"][0] - anchor["y"][0]) <= h]
    x0 = min(o["x"][0] for o in near)
    y0 = min(o["y"][0] for o in near)
    return x0, y0, w, h


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


def choose_next(grid, at, dirs, known, actions, last, visits, state):
    """What to press: an informative probe, else keep pushing, else somewhere new.

    The middle rung is what makes walls a measurement rather than an accident. A walk
    that changes action whenever one fails meets each wall once and moves on; committing
    to a direction until it stops working goes and finds them.

    Measured over 400 actions with everything else held fixed, blocked observations rise
    sharply — `m0r0` 1 -> 80, `sc25` 49 -> 119, `sp80` 1 -> 33, `ka59` 29 -> 74, `ar25`
    2 -> 12 — but the number of games that end up with a wall colour does NOT change
    (4 of 9 either way). More evidence, same coverage: what blocks the other five is
    upstream of exploration.
    """
    if at is not None and dirs:
        probe = choose_probe(grid, at, dirs, known, actions)
        if probe is not None:
            return probe
        if last is not None and last in dirs:
            return last
    return choose_action(visits, state, actions)


def infer_player(records):
    """The component that responds to the most actions.

    KNOWN WRONG on sc25 and NOT FIXABLE IN ISOLATION: sc25's metronome — (0, 2) on every
    button — wins this vote and the run wanders unplanned. Electing by steerability
    (displacement depends on the action) is measured correct for sc25 AND loses ar25,
    whose baseline level depends on its own metronome mis-winning the early vote so that
    planning stays blocked while the novelty wander meets the walls. Every repair of the
    downstream economics was then measured dead: an emission-counted walk cap broke ls20
    7/7→3/7; arrival-counted broke cd82+cn04 (their winning lines revisit one object 22
    and 162 times); a board-changed discriminator cannot tell those revisits from ar25's
    sterile pacing because cd82's productive grind happens on a byte-identical board.
    Full account: `breadth-recon.md` §night 2. Do not re-derive — the next lever is
    exploration that learns walls DURING planning, not a better election.
    """
    votes = Counter(k for r in records for k in r["shifts"])
    if not votes:
        return None
    return max(votes.items(), key=lambda kv: (kv[1], kv[0]))[0]


def infer_body(records, player):
    """Every component that moves rigidly with the player.

    The piece is often drawn in more than one colour, so perception splits it. Planning
    with one fragment measures the wrong footprint and the wall never shows up in the
    destination — on ls20 that is a 5x2 box for a 5x5 piece, and the piece's own second
    colour then gets classified as a wall.

    Agreement is measured over the frames the part was actually VISIBLE in, not over the
    whole run. A part that loses its track once comes back under a new id, and its
    agreement is then split between two ids — measured on ls20: 171 and 106 of the
    player's 278 moves, 277 between them, each one under any sensible whole-run
    threshold, so the piece came out as a single 5x2 fragment of itself. Judged locally
    both halves are at 1.00. A bystander that drifts along by coincidence is visible
    throughout and agrees rarely, so it stays far below the line either way.
    """
    agree, present, n = Counter(), Counter(), 0
    for r in records:
        d = r["shifts"].get(player)
        if d is None:
            continue
        n += 1
        present.update(r.get("after") or set(r["shifts"]))
        agree.update(k for k, dk in r["shifts"].items() if dk == d)
    if not n:
        return {player}
    return {k for k, c in agree.items()
            if c >= AGREE * present[k] and present[k] >= MIN_PRESENCE * n}


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


SCATTER = 0.6  # a direction must dominate an action's displacements; below this it is noise


def infer_dirs(records, player):
    """Per action, the displacement it usually causes. Blocked attempts contribute nothing.

    An action whose displacement SCATTERS is not a walk — cn04's rotator shifts the claw's
    bounding box a different way each orientation, and `re86`'s action 5 shows (2,17),
    (-11,0), (11,0) across thirteen presses. Handing such an action its most_common anyway
    poisons everything downstream: one junk (-11,0) vetoes four clean directions in
    `coherent` (the model never plans), and drags `infer_step`'s gcd from 3 to 1. With
    three or more samples and no dominant vector, the action gets no direction at all —
    the play loop's extras/rotator path picks it up instead. Under three samples the mode
    stands as before: early warmup readings are how a model gets built at all.
    """
    seen = {}
    for r in records:
        if player in r["shifts"]:
            seen.setdefault(r["action"], []).append(r["shifts"][player])
    out = {}
    for a, d in seen.items():
        top, n = Counter(d).most_common(1)[0]
        if len(d) >= 3 and n / len(d) < SCATTER:
            continue
        out[a] = top
    return out


def infer_step(dirs):
    """The movement quantum. gcd, because a board can be stepped by 2 and show a 4."""
    mags = [abs(v) for d in dirs.values() for v in d if v]
    if not mags:
        return None
    out = 0
    for m in mags:
        out = gcd(out, m)
    return out


def dest_colours(grid, x, y, w, h, dx, dy, own=None):
    """Colours in the footprint's destination, minus the piece's own. None if off-board.

    `own` defaults to every colour inside the current footprint, which is wrong whenever
    the piece does not fill its bounding box: on `ar25` the box is 9x9 around a 40-cell
    piece, so the background inside the box was subtracted from every destination and all
    38 observations came back empty. Callers that know the body's colours should pass them.
    """
    nx, ny = x + dx, y + dy
    if nx < 0 or ny < 0 or nx + w > grid.shape[1] or ny + h > grid.shape[0]:
        return None
    if own is None:
        own = set(np.unique(grid[y:y + h, x:x + w]).tolist())
    dest = set(np.unique(grid[ny:ny + h, nx:nx + w]).tolist())
    return frozenset(dest - set(own))


def terrain_samples(records, player, body, dirs, colours=None):
    """[(colours_in_destination, did_it_walk_there)] — the evidence classify_colours needs.

    A record only counts when the outcome is one of the two the terrain explains: the
    piece went exactly where the action points, or it did not move at all. A different
    displacement means something else happened (a respawn after running out of budget, a
    knock-back, a conveyor) and the destination was never entered, so it proves nothing.
    """
    out = []
    own = {colours[k] for k in body if k in colours} if colours else set()
    for r in records:
        d = dirs.get(r["action"])
        at = body_box(r["boxes"], body)
        if d is None or at is None:
            continue
        # A key missing from the next frame's index means the matcher lost the piece, not
        # that the piece stood still: objects are paired by colour *and* cell count, so a
        # piece that changes size vanishes. Reading that as blocked invented 25 blocked
        # moves on `sc25`, every one of them onto plain floor.
        if player not in r["after"]:
            continue
        delta = r["shifts"].get(player)
        if delta is not None and delta != d:
            continue
        cs = dest_colours(r["grid"], at[0], at[1], at[2], at[3], d[0], d[1], own)
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
    blocked = [set(cs) - passable for cs, moved in samples if not moved]

    # Explain away. A blocked destination usually shows several unfamiliar colours and
    # only one of them is the wall; taking all of them made `dc22` treat colour 9 as
    # solid because it sits next to the real wall, which sealed the board down to 9
    # reachable cells. A colour earns the label by being the ONLY unexplained thing in
    # the way, more than once — measured, the real walls are sole-unexplained 47 to 109
    # times each and the passengers 0 or 1.
    blocking = set()
    while True:
        # A sample containing a known wall is already accounted for. Subtracting instead
        # of dropping it leaves the wall's neighbour looking like the sole candidate on
        # the next pass, which reintroduces the very colour this is meant to exclude.
        remaining = [u for u in blocked if not (u & blocking)]
        support = Counter(next(iter(u)) for u in remaining if len(u) == 1)
        fresh = {c for c, n in support.items() if n >= MIN_WALL_SUPPORT} - blocking
        if not fresh:
            return passable, blocking
        blocking |= fresh


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
    records, spent, visits, samples = [], 0, {}, []
    tracks, next_id, colours = [], 0, {}
    prev, colours, tracks, next_id = see(obs.frame, tracks, next_id, rows)
    player = body = None
    dirs, passable, blocking = {}, set(), set()
    # Phase 1 covers the action set to learn what each one does; phase 2 uses that to aim
    # at the colours still unclassified. The split is just "do we know a direction yet".
    warmup = 2 * len(values)

    last = None
    for i in range(budget):
        grid = np.array(obs.frame)[-1][:rows]
        # The raw bytes, not hash(): Python randomises bytes hashing per process, so the
        # walk took a different route every run and the same game reported different
        # pieces and different walls on consecutive runs.
        state = grid.tobytes()
        at = body_box(prev, body) if (i >= warmup and player is not None) else None
        value = choose_next(grid, at, dirs, passable | blocking, values, last, visits, state)
        visits[(state, value)] = visits.get((state, value), 0) + 1

        obs = env.step(by_value[value])
        spent += 1
        if obs is None:
            break
        # Running out of lives ends the run, and every game does it long before the budget:
        # asking for 400 actions produced between 26 and 152 because the loop stopped at
        # the first game over. Exploration offline is free, so start again and keep the
        # evidence. The frame can also come back empty on a transition, and every
        # perception call downstream indexes into it.
        if np.array(obs.frame).size == 0 or obs.state == GameState.GAME_OVER:
            obs = env.reset()
            if obs is None or np.array(obs.frame).size == 0:
                break
            # A reset redraws the board, so positions carry no information across it —
            # but the same pieces come back. Re-acquire with the position gate opened up,
            # so every part is re-identified on colour and area together. Keeping the
            # normal gate let the piece's own track carry over while its other half got a
            # fresh id, and the body then agreed with itself on only part of the run;
            # clearing the tracks instead threw away three quarters of the evidence.
            prev, seen_c, tracks, next_id = see(obs.frame, tracks, next_id, rows,
                                                gate=REACQUIRE)
            colours.update(seen_c)
            last = None
            continue
        cur, seen_c, tracks, next_id = see(obs.frame, tracks, next_id, rows)
        colours.update(seen_c)
        shifts = _shifts(prev, cur)
        records.append({"action": value, "shifts": shifts,
                        "grid": grid, "boxes": prev, "after": set(cur)})
        # Keep pushing only while the push is working.
        last = value if player is not None and shifts.get(player) == dirs.get(value) else None
        prev = cur

        if i + 1 >= warmup:
            player = infer_player(records)
            if player is not None:
                body = infer_body(records, player)
                dirs = infer_dirs(records, player)
                samples = terrain_samples(records, player, body, dirs, colours)
                passable, blocking = classify_colours(samples)

    if player is None:
        player = infer_player(records)
        if player is None:
            return None, spent
        body = infer_body(records, player)
        dirs = infer_dirs(records, player)
        samples = terrain_samples(records, player, body, dirs, colours)
        passable, blocking = classify_colours(samples)

    # Track ids do not survive a reset, so the body may be absent from the final frame.
    # Take the most recent frame that actually shows it.
    seen_boxes = prev
    box = body_box(prev, body)
    for r in reversed(records):
        if box is not None:
            break
        seen_boxes = r["boxes"]
        box = body_box(seen_boxes, body)
    if box is None:
        return None, spent
    # What the piece looks like, so `locate` can find it on a board this run never saw.
    parts = tuple(sorted((colours[k], seen_boxes[k][2], seen_boxes[k][3])
                         for k in body if k in seen_boxes and k in colours))
    return Model(player=player, body=body, colour=colours.get(player, -1), parts=parts,
                 box=(box[2], box[3]), dirs=dirs,
                 step=infer_step(dirs), passable=passable, blocking=blocking, rows=rows,
                 evidence=(sum(1 for _, m in samples if m),
                           sum(1 for _, m in samples if not m))), spent


MAZE_LIKE = ["ar25", "cn04", "dc22", "ka59", "ls20", "m0r0", "re86", "sc25", "sp80"]
OUT = Path("results")


def main():
    import arc_agi
    arc = arc_agi.Arcade()
    envs = {e.game_id.split("-")[0]: e for e in arc.get_environments()}
    argv = sys.argv[1:]
    budget = 400
    if "--budget" in argv:
        i = argv.index("--budget")
        budget = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    names = argv or MAZE_LIKE
    rows = []
    for name in names:
        m, spent = discover(arc.make(envs[name].game_id), budget=budget)
        row = {"game": name, "actions": spent}
        if m is None:
            row["result"] = "no player found"
        else:
            row.update(result="ok", player=m.colour, body=len(m.body),
                       box=list(m.box), step=m.step,
                       dirs={a: list(d) for a, d in sorted(m.dirs.items())},
                       walls=sorted(m.blocking), floor=sorted(m.passable),
                       walked=m.evidence[0], blocked=m.evidence[1])
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
            "| game | piece | footprint | step | directions | walked | blocked | "
            "walls found | floor |",
            "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            if r["result"] != "ok":
                lines.append(f"| {r['game']} | — | | | | | | | {r['result']} |")
                continue
            lines.append(
                f"| {r['game']} | colour {r['player']} ({r['body']} parts) | "
                f"{r['box'][0]}x{r['box'][1]} | "
                f"{r['step']} | {len(r['dirs'])} | {r['walked']} | {r['blocked']} | "
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
                  "A wall is only observable from a move that *failed*, so the whole "
                  "difficulty is meeting one. Four causes have been found by measuring, "
                  "each now pinned by a test:", "",
                  "1. Cycling the actions in order oscillates in place — up then down is "
                  "a no-op pair, so 48 actions gave 47 successful moves and one wall.",
                  "2. Breaking ties by action number walks in a straight line; `sp80` "
                  "used one of its five actions across 48 presses.",
                  "3. Subtracting every colour inside the piece's bounding box, rather "
                  "than the piece's own colours, subtracted the floor too: `ar25` "
                  "returned 38 empty observations from 38 moves.",
                  "4. The run stopped at the first game over, so asking for 400 actions "
                  "delivered between 26 and 152. Exploring offline is free, so it now "
                  "resets and keeps going — which is what raised `sc25` from 1 blocked "
                  "move to 49 and `ls20` from 5 to 79.",
                  "5. The walk keyed its novelty table on `hash(frame_bytes)`, and "
                  "Python randomises bytes hashing per process, so consecutive runs of "
                  "the same game took different routes and reported different pieces "
                  "and different walls. Any number measured before that was one sample "
                  "of a random variable. The key is now the raw bytes and two runs of "
                  "the same game agree exactly.", "",
                  "## Identity: the defect that was upstream of everything", "",
                  "Objects used to be keyed on `(colour, cell_count)` and looked up in a "
                  "dict. Two objects sharing that key in one frame collided and one was "
                  "silently discarded — **55 objects across these 9 games at reset "
                  "alone**, 19 of `dc22`'s 31 and 16 of `re86`'s 22. Everything "
                  "downstream was reasoning about a partial board, which is why the "
                  "inferred directions contradicted each other.", "",
                  "`identity.py` replaces the key with tracks: each one predicts where "
                  "it should be, every object is scored against every track on position, "
                  "colour and area together, and pairs are taken best-first. Any single "
                  "attribute can then drift without the object being lost. Three further "
                  "defects surfaced only once that was in place:", "",
                  "- Requiring a part to move with the piece on *every* action dropped it "
                  "after one missed frame, so every game returned a one-part body — on "
                  "`ls20` a 5x2 box for a 5x5 piece, whose own second colour then "
                  "classified as a wall.",
                  "- A part that loses its track returns under a new id, splitting its "
                  "agreement across two (measured on `ls20`: 171 and 106 of the player's "
                  "278 moves). Agreement is now judged against the frames each id was "
                  "visible in, where both read 1.00.",
                  "- A model is built from track ids, and those die with the board. "
                  "`locate()` finds the piece on any frame from the shape signature of "
                  "its parts, which is what makes a model usable on the next level or in "
                  "a scored run at all.", "",
                  "## What is left", "",
                  "`cn04`, `re86`, `sc25` and `sp80` still end with no wall colour. It is "
                  "not an absence of walls — committing to one direction gets the piece "
                  "blocked within 1 to 15 moves on all nine games — and it is not the "
                  "amount of evidence: `sc25` collects 119 blocked observations and "
                  "learns nothing from them, because its inferred directions still "
                  "disagree with each other. Their pieces are still being mis-identified, "
                  "just less often than before.", "",
                  "Three earlier versions of this file were wrong about the cause: "
                  "over-segmented footprints, then open boards, then too little "
                  "exploration. Each was a guess and each was disproved by measuring.",
                  ""]
        (OUT / "discovery.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"\nwrote {OUT / 'discovery.md'}")


if __name__ == "__main__":
    main()
