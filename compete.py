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
import os
import sys
from collections import deque
from pathlib import Path

import numpy as np
from arcengine import GameState

from discover import (Model, body_box, choose_next, classify_colours, infer_body, infer_dirs,
                      infer_player, infer_step, locate, see, terrain_samples, walkable, _shifts)
from gate import Gate, cycle
from perception import HUD_ROW, hud
from plan import (bfs, bfs_all, footprints_touching, route_to, slides, step_to,
                  targets)
from scoring import environment_score, level_score
from signals import actions_left, drain, refills
from trace import step as trace_step

OUT = Path("results")
PLAYABLE = ["ar25", "cn04", "dc22", "ka59", "ls20", "m0r0", "re86", "sc25", "sp80",
            "bp35", "g50t", "sk48", "tr87", "tu93", "wa30", "cd82", "sb26"]
WARMUP = 24        # actions before the model is worth trusting, at the outside
CONTROLS = 4       # directions that make a model worth planning on
BUDGET = 2000      # actions per environment; no rule caps this, 600 RPM and 9h do.
                   # Doubling it was measured and reverted once: level 6 spent 1,708
                   # actions (65% in the confirm-probe rung) and did not fall — the
                   # block was structural then. With the moving-changer planner the
                   # accounting shows monotone progress per action (edges learned,
                   # doors opened), and the run ends at the cap mid-choreography, so
                   # the budget is the binding constraint for the first time.
CANDIDATES = 6     # targets considered per plan, rarest first
CLOCK_WINDOW = 20  # actions of history the clock's rate is measured over
MARGIN = 2         # actions of slack between reaching a refill and starving
TRAIL = 3          # squares of memory a route may not step back into
STUCK = 30         # rounds with nothing left to watch before going to look elsewhere
LEARN = 3          # entries a plan buys for a changer whose cycle is not known yet
ACCT = os.environ.get("ARC_ACCT")  # action-accounting JSONL path, opt-in
L6 = os.environ.get("ARC_L6")      # gate-view JSONL for level index 5 (ls20 level 6), opt-in


def build_model(records, colours, rows=HUD_ROW, prior=None):
    """The model as it stands from what has been played so far, or None.

    `prior` is the model as it stood at the end of the PREVIOUS level — not the one built an
    action ago. Its terrain is kept until this level finds a wall of its own: the evidence is
    reset at a level boundary, so the first model rebuilt on a new board has seen no blocked
    move yet and therefore has **no walls**, and `walkable` with an empty `blocking` lets
    every plan route straight through them. On `ls20` level 2 that turned a 16-action walk to
    the glyph-changer into a 5-action plan that spent its life bumping into a wall.

    Inheriting from the *current* model instead makes the terrain monotone within a level,
    which is a different and worse thing: `classify_colours` retracts a colour once it stops
    being the sole unexplained thing in the way, and accumulating keeps every colour it has
    ever suspected. Measured, that alone cost `cd82` its 812-action level — a game that never
    reaches a second level, so the carry-over could only ever hurt it.
    """
    player = infer_player(records)
    if player is None:
        return None
    body = infer_body(records, player)
    dirs = infer_dirs(records, player)
    if prior is not None:
        # What each control does is a property of the GAME, like which colours are solid, so
        # a direction proven on an earlier level still holds — and the older reading wins,
        # because it is the one that has already walked three levels. This level only fills
        # in the actions the prior never saw.
        #
        # Both halves are measured. Rebuilt from scratch, `ls20` level 4 got two of its four
        # directions and `walkable` shrank the board from 67 reachable positions to three.
        # Letting this level's evidence override instead, `infer_dirs` read "up" as
        # (-10, -5) from a frame that lied, and the piece sat in a pocket whose only exit
        # was up, reporting all four directions blocked.
        dirs = {**dirs, **prior.dirs}
    box = None
    for r in reversed(records):
        box = body_box(r["boxes"], body)
        if box is not None:
            break
    if box is None:
        return None
    passable, blocking = classify_colours(terrain_samples(records, player, body, dirs, colours))
    if prior is not None and not blocking:
        passable = passable | prior.passable
        blocking = prior.blocking - passable
    parts = tuple(sorted((colours[k], r["boxes"][k][2], r["boxes"][k][3])
                         for r in [records[-1]] for k in body
                         if k in r["boxes"] and k in colours))
    if not parts and prior is not None:
        # `parts` is how `locate` recognises the piece on a board the model was not built
        # from, and it comes out empty whenever the body's track ids churn. A model that
        # cannot find its own piece plans nothing at all, and it was replacing one that
        # could — 50 actions of `ls20` level 2 spent blind, mid-level.
        parts = prior.parts
    return Model(player=player, body=body, colour=colours.get(player, -1), parts=parts,
                 box=(box[2], box[3]), dirs=dirs, step=infer_step(dirs),
                 passable=passable, blocking=blocking, rows=rows)


def slid(model, before, after, action):
    """Did the board move the piece somewhere the action did not ask for?

    Three outcomes, and the middle one is the whole point: a piece that did not move is
    **blocked** and its plan still holds; a piece that moved exactly one step is walking; a
    piece that moved anywhere else has been **carried**, and every action left in the plan
    is now aimed from a square it is not on. `ls20` level 4 does this — measured, `press 4`
    at (14, 35) landed at (19, 45) and `press 1` at (24, 45) landed at (9, 40).
    """
    if before is None or after is None:
        return False
    if (after[0], after[1]) == (before[0], before[1]):
        return False
    step = model.dirs.get(action)
    return bool(step) and (after[0] - before[0], after[1] - before[1]) != step


def _lands(grid, model, at, route, redirects=None):
    """Where a route ends up, stopping at the last square the piece could stand on.

    `_after` walks the map blind. A route the map could not plan — the plain fallback —
    carries the piece somewhere the route never assumed, and applying the map to it can
    walk the prediction clean off the board: `ls20` level 5 costed a leg whose end it
    believed was `(64, 40)` on a board 60 squares wide. A prediction that cannot happen is
    worse than a short one, because the order search costs plans against it.
    """
    pos = (at[0], at[1])
    for a in route:
        nxt = step_to(model, pos, a, redirects)
        if not walkable(grid, model, nxt[0], nxt[1]):
            return pos
        pos = nxt
    return pos


def _after(model, at, route, redirects=None):
    """Where a route ends up. The model says what each action displaces, so a plan's
    destination is known before a single action of it is spent — and a cell known to carry
    the piece is part of what the model says."""
    pos = (at[0], at[1])
    for a in route:
        pos = step_to(model, pos, a, redirects)
    return pos


def stage(grid, model, gate, at, left, full, door, refills, redirects=None, stood=()):
    """A whole trip that finishes the level as (actions, marks), or None.

    The rungs in `choose` each pick the best next thing; a level with two locks and two
    refills needs the *order* picked instead. On `ls20` level 3 the two squares that move
    the display are twenty actions apart, the door is nine past one of them, a life is
    twenty-one, and the refills only come back when a life is lost — which also resets the
    display, so the whole level is one chain of lives on one set of refills. Spending the
    refill ten actions from the second changer on the way to the first is the difference
    between a route and none, and no rung can see that: it is two legs away.

    So enumerate the orders. There are at most a handful of waypoints, the search is over
    which changer to turn first and which refill to spend before which leg.

    The whole trip is committed, not the first leg — re-running the search every round is
    where `ls20` level 5 spent most of its 250+ planning rounds — but it is not committed
    BLIND: committing blind cost level 3 fifty-five actions, because walking one leg at a
    time is how that level notices the display moving under it and finds its second
    changer. `marks` carries the trip's prediction, per action, of whether the display
    changes on that action (an entry onto a changer) or not (a walking step); the play loop
    drops the trip the moment reality disagrees either way, which is exactly the moment
    every press still in the plan is counted against a panel that is not there.
    """
    turns = gate.turns_for(door)
    if not turns:
        return None
    # What each wrong half needs is a SEQUENCE of squares, not a square. `ls20` level 5 has
    # two that write the shape, six states round one and four round the other, and the glyph
    # its goal box asks for is in neither — it exists only where the two interleave. Planned
    # as one square per half, the order search came back empty in 378 of 383 rounds there:
    # not for want of fuel, but because the plan it was asked to find cannot be written down
    # in that shape.
    #
    # `known` is half of what decides how much of the trip to commit — see the return.
    known = True
    legs = {}
    for h, pos in turns.items():
        path = gate.path_for(door, h)
        if not path:
            known = False
            path = gate.learning_path(door, h)
        if not path:
            # Nothing known gets this half where the door wants it, so the plan has to buy
            # the watching that would. Costing it at one press is what keeps it unknown:
            # the piece walks over with fuel for a single entry, sees one edge of the cycle,
            # and starves — and a death puts the display back, so the next life sees the
            # same first edge again. `ls20` level 5's ink runs 12 -> 9 -> 14 -> 8 and the
            # agent has watched 12 -> 9 -> 14 across two hundred rounds without once
            # standing there long enough to close it.
            need = gate.presses_for(door, h, pos) or LEARN
            path = [(pos, need)]
        legs[h] = tuple(path)

    goals = {("door", None): footprints_touching(grid, model, door)}
    for path in legs.values():
        for square, _ in path:
            goals[("turn", square)] = {square}
    for n, f in enumerate(refills):
        goals[("fuel", n)] = footprints_touching(grid, model, f)

    memo = {}

    def hop(pos, key):
        """(actions, where it leaves the piece) from `pos` to a waypoint, or None.

        On the map, and on the plain board when the map cannot find a way — the same rule
        the router walks by. Costed without it, every distance on a board that carries the
        piece is fiction, and the order search rejects plans that fit and accepts ones that
        do not.
        """
        if (pos, key) not in memo:
            r = (bfs(grid, model, pos, goals[key], redirects)
                 or bfs(grid, model, pos, goals[key]))
            memo[(pos, key)] = (None if r is None
                                else (len(r), _lands(grid, model, pos, r, redirects), r))
        return memo[(pos, key)]

    ways_out = [k for k in goals if k[0] == "fuel"] + [("door", None)]

    def escape(pos):
        """Cheapest way from `pos` to a refill or to the door, or None if there is neither.

        Arriving is not the job. A turn that leaves the piece on the changer with an empty
        tank throws the level away: `ls20` level 5 reaches its ink cluster with four actions
        left and needs four to close the cycle, so it starves on the entry that would have
        told it what 14 turns into — and a death puts the whole display back where it
        started, so the next life watches the same first edge again. Every leg has to leave
        a way out.
        """
        costs = [got[0] for k in ways_out if (got := hop(pos, k)) is not None]
        return min(costs) if costs else None

    best = [None]

    # Everything the door wants, or only the halves a square is known for. A plan that
    # cannot finish the level still turns what it can — and walking to the door at the end
    # of it would only be refused.
    whole = set(turns) >= gate.wrong_halves(door)

    # How much of the trip to commit. The default is the FIRST HOP's route — exactly what
    # this search always committed — because a level under discovery lives on re-planning
    # and on the changer bookkeeping the ordinary rungs do: entries executed inside a trip
    # never book `gate.cycled()`, so a changer that has stopped paying is never forgotten,
    # and committed whole `ls20` level 4 looped on one such square for 864 actions and lost
    # the level (measured at every widening tried: whole trips, first-leg-with-presses).
    # The whole trip is committed only when it is a *recipe with a chain in it*: every leg
    # from a watched cycle (`known`), and some leg needing two or more entries — `ls20`
    # level 5's ink, three entries that must land inside one life or a death resets the
    # panel and the same first edge is watched forever. A single-entry trip has no chain to
    # protect, so committing it whole buys nothing and pays anyway: measured, `known` alone
    # re-costs level 3 its 55 actions through exactly such trips (an unmapped carry throws
    # the piece mid-walk and the rest of the committed walk starves the life), and gating
    # on interleave alone (a half with two legs) never fires at all — level 5's ink is one
    # leg, and level 5 is the level this exists for.
    commit_whole = known and any(n >= 2 for p in legs.values() for _, n in p)

    lean = [False]   # second pass: no chain slack, because the alternative is starving

    def walk(pos, clock, todo, fuel, spent, acts, marks, cut):
        if spent >= (best[0][0] if best[0] else 10 ** 6):
            return
        if not any(todo.values()):
            if not whole:
                if acts:
                    best[0] = (spent, acts, marks, cut)
                return
            got = hop(pos, ("door", None))
            if got and got[0] <= clock:
                best[0] = (spent + got[0], acts + got[2],
                           marks + [False] * len(got[2]), cut or len(got[2]))
            return
        for h, rest in todo.items():
            if not rest:
                continue
            square, presses = rest[0]
            got = hop(pos, ("turn", square))
            if not got:
                continue
            # The extra entries are a step off the square and back on, planned into the
            # acts only when the whole trip is being committed — a square with no way off
            # and back is then a leg the trip cannot write down. A truncated commit leaves
            # the entries to the standing-on-the-changer rungs, which book each attempt.
            pair = cycle(grid, model, square, redirects) \
                if commit_whole and presses > 1 else []
            if commit_whole and presses > 1 and not pair:
                continue
            cost = got[0] + 2 * (presses - 1)
            out = escape(got[1])
            # A chain leg gets three MARGINs of slack on top of its escape, a single
            # entry none. An exact fit is how the committed ink chain starves two actions
            # short of its last press: `ls20` level 5 carries the piece off the route a
            # couple of times per crossing at 2-3 actions a bounce, and a life is 21. The
            # slack is what pushes the search to put a refill in FRONT of the chain —
            # a chain walked from a full tank is the one that affords the bounces. It is a
            # preference, not a wall: with the recipe one leg from done at left=8, slack
            # returned nothing and the piece starved anyway — an exact fit that might land
            # beats a certain death, so a search that finds nothing runs again without it.
            slack = 3 * MARGIN if commit_whole and presses > 1 and not lean[0] else 0
            if cost <= clock and out is not None and cost + out + slack <= clock:
                leg_acts = got[2] + pair * (presses - 1)
                # The last step of the route ENTERS the square, and so does the second
                # action of every off/on pair — those are where the display must move.
                leg_marks = (([False] * (len(got[2]) - 1) + [True]) if got[2] else []) \
                    + ([False, True] * (presses - 1) if pair else [])
                walk(got[1], clock - cost, {**todo, h: rest[1:]}, fuel,
                     spent + cost, acts + leg_acts, marks + leg_marks,
                     cut or len(got[2]))
        for n in fuel:
            got = hop(pos, ("fuel", n))
            if got and got[0] <= clock:
                walk(got[1], full, todo, fuel - {n}, spent + got[0],
                     acts + got[2], marks + [False] * len(got[2]),
                     cut or len(got[2]))

    walk(at, left, legs, frozenset(range(len(refills))), 0, [], [], 0)
    if not best[0] and commit_whole:
        lean[0] = True
        walk(at, left, legs, frozenset(range(len(refills))), 0, [], [], 0)
    if not best[0]:
        return None
    _, acts, marks, cut = best[0]
    if not commit_whole:
        acts, marks = acts[:cut], marks[:cut]
    return acts, marks


def trajectory(model, at, route, redirects=None):
    """Where the piece must be standing before each action of `route`.

    A plan is a sequence of actions aimed from a sequence of squares, and it is only worth
    anything while the piece is on them. Carrying the squares with the plan is what lets the
    next step be checked instead of assumed.
    """
    pos, out = (at[0], at[1]), []
    for a in route:
        out.append(pos)
        pos = step_to(model, pos, a, redirects)
    return out


def _probe(grid, model, at, aim, redirects):
    """A walk that ends standing where one more press aims at `aim`, or None."""
    for act, (dx, dy) in model.dirs.items():
        src = (aim[0] - dx, aim[1] - dy)
        if not walkable(grid, model, src[0], src[1]):
            continue
        leg = bfs(grid, model, at, {src}, redirects) or bfs(grid, model, at, {src})
        if leg is not None:
            return leg + [act]
    return None


def confirm(grid, model, at, once, redirects, goals=None, stood=None,
            blind=False, refused=(), tried=()):
    """A walk that ends by re-aiming at a cell seen to redirect once, to find out if it is real.

    Waiting to trip over the same cell again does not happen: a redirect drops the plan, the
    next route goes somewhere else, and the sighting is never repeated — measured, the
    confirmed map stayed empty for a whole run. So the confirmation is deliberate. It is
    affordable because the levels this matters on are the deep ones, where a level is worth
    several times what the actions cost.
    """
    # Plan first, then learn what the plan needs. Confirming the nearest unvouched-for cell
    # settles a question nobody asked; the ones that matter are the cells the route to the
    # target aims at, so those go first and everything else is the fallback.
    open_cells = [a for a in (once or {}) if a not in (redirects or {})]
    on_route = []
    if goals:
        route = bfs(grid, model, at, goals)
        pos = at
        for a in route or []:
            dx, dy = model.dirs[a]
            aim = (pos[0] + dx, pos[1] + dy)
            if aim in open_cells:
                on_route.append(aim)
            pos = step_to(model, pos, a, redirects)
    for aim in on_route + [a for a in open_cells if a not in on_route]:
        if aim in (redirects or {}):
            continue
        walk = _probe(grid, model, at, aim, redirects)
        if walk is not None:
            return walk

    # Nothing seen once is still open, and the target is not reachable on the map as it
    # stands. Then the cell in the way has never been stepped on at all, and waiting for it
    # to turn up is waiting for something the router is actively avoiding: `ls20` level 5's
    # ink-changer sits behind one cell, `(34, 5)`, which throws the piece twenty cells down
    # to the changer's doorstep. Without it the map says the changer cannot be reached, so
    # every route goes elsewhere and the cell is never learned.
    #
    # "Unknown" has to mean *never stood on*, not *not reachable*: a cell whose carry has
    # not been seen looks like ordinary floor to the router, so it is already inside what
    # the map thinks it can reach, and a frontier defined against that set comes back empty
    # — measured, 280 times in a row. Walking to the nearest square the piece has never
    # actually occupied is what found `(34, 5)` by hand.
    blocked = goals and bfs(grid, model, at, goals, redirects) is None
    if stood is not None and (blocked or blind):
        known = bfs_all(grid, model, at, redirects)
        # Toward the goal, not merely nearby. Walking to the nearest square nobody has stood
        # on fills in the neighbourhood the piece is already in and never gets to the one
        # cell that matters: `ls20` level 5's ink-changer is reached only through `(34, 5)`,
        # and over 655 planning rounds and 34 squares that cell was never so much as aimed
        # at. Scoring a candidate by what it costs to reach PLUS how far it leaves the goal
        # sweeps along the corridor to the target instead of around the starting room.
        # Aimed along the corridor when the board is what blocks; nearest-first when the
        # display is, because the square that writes the missing half could be anywhere.
        away = bfs_all(grid, model, min(goals)) if (blocked and goals) else {}
        fresh = [(len(r) + (len(away.get(p, [])) + (0 if p in away else 999) if away else 0),
                  p) for p, r in known.items()
                 if p not in stood and p not in refused and r]
        if fresh:
            return known[min(fresh)[1]]
    return None


def coherent(dirs):
    """Are these four controls a believable set — two axes, each with both signs?

    Waiting a fixed 24 actions before planning costs `ls20` level 1 sixteen of the
    thirty-nine it spends on a goal box seven steps away. Not waiting at all costs `ar25`
    its only level: that game answers ACTION3 with *right* and ACTION4 with *left*, so a
    model built from a couple of presses can hold a direction with the wrong sign and every
    route walks away from where it meant to go. What separates a usable early reading from
    a lucky one is not how many actions have been spent but whether the readings agree with
    each other: four displacements, on two perpendicular axes, opposite in pairs.
    """
    seen = [d for d in dirs.values() if d != (0, 0)]
    if len(seen) < CONTROLS:
        return False
    return all(any(o == (-d[0], -d[1]) for o in seen) for d in seen) and         len({(abs(d[0]) > 0, abs(d[1]) > 0) for d in seen}) == 2


def keep_identity(fresh, prior, frame):
    """Which of two models to believe about what the piece IS.

    A level boundary resets the evidence, so the first model rebuilt on a new board is
    inferred from one or two actions — and on `ls20` level 5 that is enough to name a stray
    1x1 pixel as the player. Every position the planner then read was that pixel's, three
    cells off the five-cell lattice the piece actually moves on, and 352 planning rounds
    went to a board that was not there.

    Its SIZE is half of that identity and has to be checked separately: `parts` comes from
    the body's components and `box` from their bounding box, and level 5 produced a model
    that agreed about the components and still reported a 1x1 piece. `walkable` tests a
    w-by-h footprint, so a 1x1 box makes the whole board look passable and every reading of
    the clock, the refills and the targets came back empty for 411 planning rounds.

    What the piece LOOKS LIKE is a property of the game, like what the controls do. So the
    prior wins any disagreement — unless it can no longer find its own piece on this board,
    which is the one case where the game really has changed the piece underneath it.
    """
    if fresh is None or prior is None or not prior.parts:
        return fresh
    if (fresh.parts, fresh.box) == (prior.parts, prior.box):
        return fresh
    return prior if locate(frame, prior) is not None else fresh


def choose(frame, model, log, gate, left, full, redirects=None, once=None,
           came_from=None, stood=None, refused=(), tried=(), sure=None):
    """Where to walk next, as (actions, the target it is for).

    Each rung is here because the one above it was not enough on `ls20` level 2:

    * **a door the display says is open ends the level**, so nothing outranks it — and
      rarity, which used to decide this, picks the glyph-changer over the goal box every
      time and turns the match back off as fast as it was turned on.
    * **a door out of reach is a door to refuel for.** What is in the way is the clock,
      not the walls, and the level's two refills are what make a route exist at all.
    * **the clock, while a refill is still reachable.** Running out is the one failure
      with no recovery: the life ends, the level restarts, and the display goes back to
      what it said at the start, so nothing a life accumulated survives it.
    * **then change the display — but only if this life can still get from the changer to
      the door.** Without that check the agent walks 17 actions to the changer, turns the
      glyph to the one the goal box wants, and starves on the action it matched.
    * **then the old rule** — rarest first, as long as the clock covers the walk.
    """
    grid = np.array(frame)[-1][:model.rows]
    gate.trip = None   # only a staged plan carries a display prediction
    at = locate(frame, model)
    # Rarest first, plus any marked place that order left out. A plate is somewhere the
    # board has drawn a shape, and there are one or two per board — but rarity ranks by
    # colour, and a goal box painted in the same colour as the border and the status strip
    # sorts tenth. They go on the end, so nothing above them changes.
    seen = targets(frame, model)
    cands = seen[:CANDIDATES] + [o for o in seen[CANDIDATES:] if gate.marked(o)]
    doors = [o for o in cands if gate.matched(o)]
    locked = [o for o in cands if gate.locked(o)]

    # Changers that MOVE want a different planner, and they want it FIRST: `ls20` level
    # 6's crosses patrol the corridors, so a "press" is the footprint overlapping one
    # after a move and the panel churns under every walk — matching first and walking
    # after is how two matched panels were wasted there, and the confirm-probe below
    # spent 207 of one run's actions settling carries a moving board does not turn on.
    # `route_moving` plans over position x patrol phase x panel and arrives wearing the
    # ask. It answers None unless a patroller with a known period has been seen to move
    # a half of the display, which no board with square changers has — the rung is
    # silent everywhere else by mechanism. A door already entered that did not end the
    # level is a passage, not a goal.
    if at and gate.movers and gate.displays:
        here = (at[0], at[1])
        tank6 = {g[0] for g in refills(log, set(drain(log[-CLOCK_WINDOW:])))}
        fuels = [o for o in seen if o["colour"] in tank6]
        if os.environ.get("ARC_FUELS") and getattr(gate, "lvl", -1) == 6:
            print("[fu] at=%s tank=%s fuels=%d left=%s" % (
                here, sorted(tank6), len(fuels), left), flush=True)
        # Of the doors a plan exists for, take the one whose plan passes the MOST
        # checked gates: a door with another door behind it is entered en route, and
        # entering the shallow one as the goal strands the piece there with no fuel
        # for the deep one — measured, three lives in a row.
        best6 = None
        for o in cands:
            if not gate.marked(o) or gate.entered(o):
                continue
            got = gate.route_moving(grid, model, here, o, fuels, full, left, redirects)
            if got and got[0] and (best6 is None or got[2] > best6[2]):
                best6 = got
        if best6:
            gate.trip = best6[1]
            gate.rung = "moving"
            return best6[0], None
        # No door is plannable, which on a patrolled board usually means an EDGE is
        # missing, not a route: the plan can only press values it has watched, and a
        # door can ask for a glyph several presses down an alphabet nobody walked. So
        # go and press what is NOT known, walking there through what is — the same
        # search, with the goal inverted. Aiming only at the edge out of the value
        # the panel is showing right now is not enough: level 6's ask sits several
        # unwatched presses away, and 483 of its 1,187 actions went to the
        # square-changer rungs filling that gap with trips to positions that are not
        # places.
        for o in cands:
            if not gate.marked(o) or gate.entered(o):
                continue
            got = gate.route_moving(grid, model, here, o, fuels, full, left,
                                    redirects, learn=True)
            if got and got[0]:
                gate.trip = got[1]
                gate.rung = "moving-learn"
                return got[0], None
        # Tried here and measured back out: when neither planner has an answer, top the
        # tank up instead of falling through to the square-changer rungs below (whose
        # trips are to footprint-overlap positions, not places — 317 of level 6's 844
        # actions). It reads right and it **loses level 6 outright**, 5/7 at 22.446%:
        # the freed rounds went to the confirm-probe rung instead (40 -> 329 actions)
        # and the refuelling never bought a plan, because what those rounds are short of
        # is a watched EDGE, not fuel. The square-changer trips are not idle after all —
        # they walk the piece across the corridors, which is how presses get watched at
        # all on a board where walking is pressing.
        #
        # Retried with a discriminator — refuel only when the same search finds a plan
        # the tank is the only thing blocking — and the discriminator never once fired:
        # in all 121 rounds that reach here, no marked door has a plan at a tank of 200
        # actions either, against a real tank of 42. So a stuck round on this board is
        # never waiting for fuel; the rung is dead code by measurement, and the way down
        # is teaching the alphabet faster (`results/l6-fueldbg3.log`).

    if at and locked:
        # The board carries the piece somewhere the map cannot vouch for. Settle it before
        # routing on it: an unconfirmed cell is either the way through or a phantom, and the
        # two are indistinguishable from here.
        #
        # Only on a board with a lock, which is the only place the walk has to end on an
        # exact square. Firing it wherever the floor carries the piece instead costs `cd82`
        # and `m0r0` their only level. `ls20` level 5 looked like a counter-example — 352
        # planning rounds with no display ever seen — but that was the planner reading a
        # stray 1x1 pixel as the piece, and it went away with `keep_identity`.
        # Which goal the probe should be clearing a path to. The locked target itself is
        # usually already reachable — what is not is the changer that opens it, and on a
        # board where no changer for a wrong half has been found yet, the only name for it
        # is "a candidate the router keeps picking and never arrives at". So prefer the
        # first candidate the map says is unreachable while the plain board says it is not.
        here = (at[0], at[1])
        stuck = None
        for o in cands[:CANDIDATES]:
            foot = footprints_touching(grid, model, o)
            if (foot and bfs(grid, model, here, foot, redirects) is None
                    and bfs(grid, model, here, foot) is not None):
                stuck = foot
                break
        # A half that has been watched through several values and still cannot be brought
        # to what the door wants: another square writes it, and nobody knows where. Aiming
        # the sweep anywhere in particular would be a guess, so it goes back to nearest-first.
        #
        # Tried and measured out: firing when the half's known graph has no unwatched edge
        # left (`path_for` and `learning_path` both empty), which reads as the sharper test
        # and costs `ls20` level 4 — that board's changer walks a short alphabet, so its
        # graph is exhausted long before the level is.
        # A half whose target has been out of reach of everything known for a long time.
        # Not "the graph has nothing left to watch" — a changer that walks a long alphabet
        # always has another edge to go and see, so that condition never fires and the agent
        # presses the one square it knows forever. And not the bare condition either: it is
        # true from the first round, and leaving to wander then costs `ls20` level 4. What
        # separates a board that needs a second changer from one that is merely early is how
        # LONG the target stays unreachable.
        empty = any(gate.path_for(locked[0], h) is None
                    for h in gate.wrong_halves(locked[0]))
        gate.stuck = gate.stuck + 1 if empty else 0
        blind = gate.stuck >= STUCK or             any(gate.exhausted(locked[0], h) for h in gate.wrong_halves(locked[0]))
        probe = confirm(grid, model, here, once, redirects,
                        stuck or footprints_touching(grid, model, locked[0]), stood, blind,
                        refused, tried)
        if probe and (left is None or len(probe) <= left):
            # A BLIND probe is a walk into the unknown, and it was budgeted only one way.
            # The accounting run put a probe immediately before 13 of level 6's 32 deaths
            # and 4 of level 5's five, and level 6 spent 1,115 of 1,708 actions — 65% —
            # inside this rung: the walk out fitted the tank, the walk back to any refill
            # did not, and a death resets the panel the probes exist to serve. So a blind
            # probe has to afford the way back to a refill too. Only the blind ones:
            # demanding it of the targeted probes as well was measured and costs level 3
            # twenty-six actions (99 -> 125), spent by the rungs that fill the gap when a
            # short, useful probe is refused. And only when a refill is known — before the
            # first one has been seen there is nothing to budget against.
            tank0 = {g[0] for g in refills(log, set(drain(log[-CLOCK_WINDOW:])))}
            fuel0 = [o for o in targets(frame, model) if o["colour"] in tank0]
            ok = left is None or not fuel0 or not blind
            if not ok:
                end = _after(model, here, probe, redirects)
                outs = [r for o in fuel0
                        if (r := bfs(grid, model, end,
                                     footprints_touching(grid, model, o),
                                     redirects)) is not None]
                ok = bool(outs) and len(probe) + len(min(outs, key=len)) <= left
            if ok:
                gate.rung = "probe"
                return probe, None
    if doors:
        # The changer is the one place not to go while a door is open: walking over it
        # turns the display, and the door with it.
        #
        # Keeping the piece off changers the rest of the time is what `ls20` level 3 wants —
        # it was four actions from the second changer with the ink already right when rarity
        # sent it back over the square that recolours it — and it was measured twice and
        # reverted twice, because it costs `ls20` level 2: walking to the changer because it
        # is the rarest thing on the board is how the first turn of the glyph happens, and
        # gating the exclusion on "something is locked" does not save it, since by then the
        # goal box is locked and the cross is the only way to unlock it.
        cands = [o for o in cands if o in doors or not gate.changing(o, model.box)]
    tank = {g[0] for g in refills(log, set(drain(log[-CLOCK_WINDOW:])))}

    # Several rungs below ask about the same targets on the same frame, and `route_to` reads
    # nothing but its arguments, so asking twice is pure waste. Measured, a route is 2-3ms
    # and a full pass over six candidates 15-21ms — worth removing, and not where the time
    # goes: a 1200-action game is 30-90s, most of it per-frame perception.
    known = {}

    def routed(o):
        k = (o["colour"], o["x"][0], o["y"][0])
        if k not in known:
            known[k] = route_to(frame, model, o, redirects, came_from, sure)
        return known[k]

    def route(o):
        r = routed(o)
        return r if r and (left is None or len(r) <= left) else None

    def onward(pos, o):
        """Actions from a position the piece has not reached yet to `o`, or None."""
        return bfs(grid, model, pos, footprints_touching(grid, model, o))

    def refuel(goals):
        """A refill this life can still reach, the one that leaves `goals` nearest.

        Which refill matters as much as whether: `ls20` level 3 puts one 10 actions from
        the glyph-changer and one 18 away, and a life is 21 against a 9-action walk from
        the changer to the door. Taking the first one that happens to be reachable strands
        the piece at the changer with three actions left, every time.
        """
        best = None
        for f in cands:
            if f["colour"] not in tank:
                continue
            leg = routed(f)
            if not leg or (left is not None and len(leg) > left):
                continue
            rest = bfs(grid, model, _after(model, at, leg), goals)
            if rest is not None and (best is None or len(rest) < best[0]):
                best = (len(rest), leg, f)
        return (best[1], best[2]) if best else (None, None)

    for o in doors:
        if (r := route(o)):
            gate.rung = "door"
            return r, o

    if doors and at:
        leg, f = refuel(footprints_touching(grid, model, doors[0]))
        if leg:
            gate.rung = "door-fuel"
            return leg, f

    # A refill is not something to do when the tank reads "low" — a fraction of full needs
    # to know what full is, and the same bar means 21 actions on one level and 42 on
    # another. It is something to do while it is still *reachable*: one action later the
    # only chance this life had is out of range.
    #
    # Reserving them for the plan instead — taking one only to reach a door or a changer —
    # is what `ls20` level 3 seems to want, and it was measured and reverted: with nothing
    # locked yet there is nothing to refuel *towards*, so the agent never crosses the board,
    # never finds a changer, and never learns what the level wants in the first place.
    if left is not None and at:
        # Over every refill on the BOARD, not the rarity shortlist — `cands` is ranked by
        # rarity and a refill is rarely rare, so the nearest one is exactly the object most
        # likely to have been cut, and the rung then walks to a far one it cannot reach:
        # every one of level 5's ten deaths was a plan issued longer than the tank
        # (`len=11 left=6`, `len=9 left=0`). Of the ones that still FIT, the nearest; a
        # refill that does not fit is not a refill, it is a place to die en route to.
        near = [(len(r), o) for o in seen
                if o["colour"] in tank and (r := routed(o)) and len(r) <= left]
        if near and min(near, key=lambda t: t[0])[0] + MARGIN >= left:
            o = min(near, key=lambda t: t[0])[1]
            gate.rung = "near-fuel"
            return routed(o), o

    # With more than one half wrong the question is an ORDER, and the rung below cannot
    # ask it: it walks to a changer for whichever wrong half its dict happens to name first.
    # On `ls20` level 5 that is always the cross, so the ink cluster is entered twice in six
    # hundred rounds and the ink half is never worked at all. One wrong half has no order to
    # get wrong, and level 2 needs the rung below — it costs a changer one extra turn there,
    # and that level needs three.
    if (at and not doors and locked and full and left is not None
            and len(gate.wrong_halves(locked[0])) > 1):
        here = (at[0], at[1])
        fuel = [o for o in cands if o["colour"] in tank]
        if not fuel and tank:
            fuel = sorted((o for o in seen if o["colour"] in tank),
                          key=lambda o: abs(o["x"][0] - here[0])
                          + abs(o["y"][0] - here[1]))[:3]
        staged = stage(grid, model, gate, here, left, full, locked[0], fuel,
                       redirects, stood)
        if staged and staged[0]:
            gate.trip = staged[1]
            gate.rung = "stage1"
            return staged[0], None

    if at and not doors and locked and (turn := gate.changer_for(locked[0])):
        here = (at[0], at[1])
        leg = [] if here == turn else bfs(grid, model, here, {turn})
        # One more turn of the display, and then somewhere this life can still get to:
        # the door it is opening, or a refill. Demanding the DOOR is too strict — it is 20
        # actions away on `ls20` level 2 and a life is 21, which is what the refills are
        # for — and demanding nothing at all walks 17 actions to the changer, turns the
        # glyph to the one the goal box wants, and starves on the action it matched.
        outs = [locked[0]] + [o for o in cands if o["colour"] in tank]
        rest = None if leg is None else \
            min((len(r) for o in outs if (r := onward(turn, o)) is not None),
                default=None)
        if leg is not None and rest is not None \
                and (left is None or len(leg) + 2 + rest <= left):
            if here == turn:
                # The changer this rung PICKED, not the last one seen to pay out. With one
                # changer they are the same square; with three — `ls20` level 5 has a cross,
                # a quarter-turn and an ink cluster — the piece walks to one, finds itself
                # standing somewhere `gate.changer` does not name, and leaves again without
                # turning anything. Standing on it and stepping off and back on is also how
                # the cycle gets learned: with two entries of the ink cluster on record,
                # `path_for` knows 12 -> 9 and nothing else, and cannot plan its way to 8.
                #
                # Book the attempt against the square we are standing on: `cycled` forgets
                # a changer that has stopped paying out, and reading it back afterwards
                # reads None.
                gate.cycled()
                gate.rung = "cycle-on-turn"
                return cycle(grid, model, here, redirects), None
            gate.rung = "turn-walk"
            return leg, None

        # Turning it now does not fit this life, so the question is what to do first — and
        # that is an ordering question the rungs cannot answer, because the refill that
        # matters is two legs away. Only asked here: run ahead of the check above and the
        # planner decides `ls20` level 2 as well, where it is wrong, because it costs a
        # changer at one extra turn and that level needs three.
        # Every refill on the board, not the ones that happened to make the shortlist.
        # `cands` is ranked by rarity and a refill is rarely rare, so the order search was
        # handed an empty list on `ls20` level 5 and asked to fit a plan into one tank —
        # 378 of 383 rounds came back with nothing, on a level whose whole shape is weaving
        # three refills through two changers and a door.
        # The order search can only weave in the refills it is handed, and they come off
        # `cands` — which is ranked by rarity, and a refill is rarely rare. On `ls20` level 5
        # that list is empty and the search is asked to fit two changers and a door into one
        # tank: 378 of 383 rounds came back with nothing, on a level whose whole shape is
        # weaving three refills through them. Handing it every object of the tank's colour
        # instead costs levels 3 and 4, at four refills and at two — so widen only where it
        # would otherwise search with none, and take the nearest, because the search
        # enumerates their orders and that is factorial in how many it is given.
        fuel = [o for o in cands if o["colour"] in tank]
        if not fuel and tank:
            fuel = sorted((o for o in seen if o["colour"] in tank),
                          key=lambda o: abs(o["x"][0] - here[0])
                          + abs(o["y"][0] - here[1]))[:3]
        staged = stage(grid, model, gate, here, left, full, locked[0], fuel,
                       redirects, stood) if full else None
        if staged and staged[0]:
            # The whole trip, watched rather than trusted: the play loop checks the
            # piece's square before every action and the display against `marks` after
            # every action, and drops the trip the moment either disagrees. Re-running
            # this search every round is where level 5's planning time went; committing
            # blind is what cost level 3 its second-changer discovery.
            gate.heading = _after(model, here, staged[0])
            gate.trip = staged[1]
            gate.rung = "stage2"
            return staged[0], None
        if gate.heading and gate.heading != here:
            # The plan disappeared for a step — a display reads back differently for one
            # frame and the search finds nothing. Keep walking to where it was going rather
            # than hand the wheel to rarity, which on `ls20` level 3 walks straight back
            # over the square that recolours the ink and undoes the half already set.
            leg = bfs(grid, model, here, {gate.heading})
            if leg:
                gate.rung = "heading"
                return leg[:1], None

        # Failing that, the changer is simply the thing to refuel *for*. Which refill still
        # decides the level: from the near one `ls20` level 3 is 10 to the changer and 9 on
        # to the door, inside one 21-action life; from the far one it is 18.
        top, f = refuel({turn})
        if top:
            gate.rung = "turn-fuel"
            return top, f

    # Last resort before wandering: the piece is standing on a changer for a half that is
    # wrong, nothing above found a plan that fits, and a turn costs two actions. What the
    # turn buys outlives the life it is spent in — a death puts the DISPLAY back but not
    # the record of what the changer was seen to do, and that record is what makes the
    # level plannable at all. Measured on `ls20` level 5: the piece stood on the ink
    # cluster showing 14, one entry from the 8 the door wants, with four actions in the
    # tank and every refill already spent — and walked nine actions to something else and
    # starved, so the edge 14 -> 8 was never watched and the ink half never had a plan.
    #
    # Only while that half's cycle is unknown. Once it is known the presses are counted
    # and the walk is the thing to spend a life on; without that guard `ls20` level 2
    # stands on its cross for 434 extra actions.
    if at and locked and (left is None or left >= 2):
        here = (at[0], at[1])
        for h, square in gate.turns_for(locked[0]).items():
            if square == here and gate.path_for(locked[0], h) is None:
                gate.cycled()
                gate.rung = "cycle-last"
                return cycle(grid, model, here, redirects), None

    for o in cands:
        if not gate.locked(o) and (r := route(o)):
            gate.rung = "cand"
            return r, o

    # Nothing fits the clock. Walking somewhere is still better than wandering — a short
    # route may end on a refill, and a wander ends on the level restarting.
    routes = [(len(r), n) for n, o in enumerate(cands)
              if not gate.locked(o) and (r := routed(o))]
    if routes:
        o = cands[min(routes, key=lambda t: (cands[t[1]]["colour"] not in tank, t[0]))[1]]
        gate.rung = "desperate"
        return routed(o), o
    gate.rung = None
    return [], None


def stitch(obs, world, at, model, rows=HUD_ROW):
    """Remember every non-fog cell, and paint what is remembered back into the fog.

    The windows stitch because the coordinates are FIXED. What that buys is the level:
    `ls20` level 7's lock is a plate at x28-34 y49-55 that physically refuses the piece,
    and no window from the start reaches it — which is why `plates()` read zero there and
    the level was written up as a lock with no keyhole.

    The piece's own footprint is never remembered: it moves, and a remembered cell of it
    smears piece-coloured litter across the fog. The live frame always wins, so the world
    only fills in what the window is not currently showing.
    """
    grid = np.array(obs.frame)[-1]
    if world is None:
        world = [np.full(grid.shape, -1), np.zeros(grid.shape, bool)]
    known, dirty = world
    seen = grid[:rows] != 5
    if at is not None:
        w, h = model.box
        seen[max(0, at[1]):at[1] + h, max(0, at[0]):at[0] + w] = False
    # A cell that comes back DIFFERENT is not terrain: something moves there. Painting a
    # remembered copy of a moving object into the fog is worse than leaving the fog — the
    # tracker then follows a ghost standing still at the last place the object was seen,
    # and on level 7 that is why 25 to 61 objects were tracked with full histories and not
    # one of them ever earned a period.
    dirty[:rows] |= seen & (known[:rows] >= 0) & (known[:rows] != grid[:rows])
    known[:rows][seen] = grid[:rows][seen]
    fog = (grid[:rows] == 5) & (known[:rows] >= 0) & ~dirty[:rows]
    out = grid.copy()
    out[:rows][fog] = known[:rows][fog]
    obs.frame[-1] = out
    return world


def windowed_step(before, after, moved, rows=HUD_ROW):
    """Is this frame a WINDOW that slid with the piece, rather than a board that redrew?

    Not "did a lot change". That is true of any board that redraws, and latching on it cost
    `cd82`, `m0r0` and `ar25` their only level each — measured twice, on one sighting and on
    three consecutive, with 1,981 of 2,000 actions then spent wandering a board painted from
    the memory of a board that had been redrawn underneath it.

    What is specific to a window is WHERE the change is. The fog is everything outside a box
    around the piece, so the fog SET translates by exactly the piece's displacement while the
    content underneath stays in world coordinates (measured on `ls20` level 7: consecutive
    frames match best at dx=dy=0, and the non-fog extent is the piece ± (-18, +21)). A board
    that merely redraws has no reason to agree with the piece's own step, so the test is
    whether the candidate colour's mask, SHIFTED by that step, predicts the next frame better
    than leaving it where it was.
    """
    dx, dy = moved
    if not dx and not dy:
        return False
    a, b = np.array(before.frame), np.array(after.frame)
    if a.size == 0 or b.size == 0 or a.shape != b.shape:
        return False
    a, b = a[-1][:rows], b[-1][:rows]
    h, w = a.shape
    # Only a colour that reaches the frame's edge can be the outside of anything.
    edge = {int(v) for v in np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])}
    dst = (slice(max(0, dy), h + min(0, dy)), slice(max(0, dx), w + min(0, dx)))
    src = (slice(max(0, -dy), h + min(0, -dy)), slice(max(0, -dx), w + min(0, -dx)))
    for c in edge:
        fa, fb = a == c, b == c
        if fa.sum() < 200 or fb.sum() < 200:
            continue                        # a border stripe is not a fog
        if fa[src].size < 500:
            continue
        slid = float((fa[src] == fb[dst]).mean())
        still = float((fa == fb).mean())
        if slid > 0.97 and slid > still + 0.02:
            return True
    return False


def play(env, budget=BUDGET, rows=HUD_ROW):
    """One environment, forward only. Returns (actions per completed level, trace)."""
    obs = env.reset()
    actions = [a for a in env.action_space if not a.is_complex()]
    if not actions or obs is None:
        return [], []
    by_value = {a.value: a for a in actions}
    values = sorted(by_value)
    world, windowed, run = None, False, 0   # a frame that is a window: see `stitch`
    prev_raw5 = None      # last step's fog mask, for the trace filter below

    prev, colours, tracks, next_id = see(obs.frame, [], 0, rows)
    records, visits, log = [], {}, []
    model, plan, last, carried, door = None, [], None, None, None
    cur_goal = None   # the object the plan in flight is walking to, None for lock work
    last_pos = None
    expect = []  # where the piece must be before each remaining action of the plan
    trip = []    # the staged plan's per-action display prediction, [] for any other plan
    full = 0        # actions a refill buys, as the largest this level has read
    trail = deque(maxlen=TRAIL)   # the squares just occupied; a route may not step back into them
    stood = set()     # squares the piece has actually occupied on this level
    refused = set()   # squares a press aimed at and the piece did not enter
    button = {}       # (square, action) -> where that press landed, seen twice
    tried = set()     # (square, action) pairs the piece has actually pressed
    sure = set()      # of those, the ones that landed where they were predicted
    read = {}         # carry cells read straight off the frame, before walking
    button_once = {}  # the same, seen once and not believed yet
    redirects, once = {}, {}  # a cell that sends the piece on -> its offset, confirmed / seen
    gate = Gate()
    done, spent_at_level, per_level = obs.levels_completed, 0, []
    acct = open(ACCT, "w", encoding="utf-8") if ACCT else None
    l6 = open(L6, "w", encoding="utf-8") if L6 else None
    psrc = "wander"  # which rung emitted the plan in flight, for the accounting

    for i in range(budget):
        grid = np.array(obs.frame)[-1][:rows]
        state = grid.tobytes()

        # Follow a route if one is in flight; otherwise explore. Both are forward-only.
        # A plan is only worth its next action while the piece is standing where that action
        # was aimed from — check, do not assume. `ls20` level 4 moves the piece for reasons
        # of its own, and the rest of a plan executed from the wrong square is worse than no
        # plan: it spends real actions walking a route that stopped being true.
        # Only where the walk has to be exact. A board with a lock has a square the piece
        # must stand on and a door that will refuse anything else; a board without one is
        # walking to objects, where the next action is usually still worth taking and
        # dropping the plan costs `m0r0` its only level.
        # Only where the walk has to be exact. Measured three ways: checked on every board,
        # `cd82` clears in 820 actions instead of 1,034 but `m0r0` needs 144 instead of 73;
        # narrowed to "moved somewhere unexpected but not merely refused" — which reads as
        # the careful version — `cd82` loses its level outright. Gated on the board having a
        # display, every game keeps its best.
        if plan and model and expect and gate.displays:
            here = locate(obs.frame, model)
            if here is not None and (here[0], here[1]) != expect[0]:
                plan, expect, trip = [], [], []
        here_now = locate(obs.frame, model) if model else None
        if here_now is not None:
            stood.add((here_now[0], here_now[1]))

        # Watch the tank WHILE walking, not only when a new plan is chosen. Every one of
        # level 5's ten deaths had the same shape: a long plan was walked while the fuel
        # fell, and by the time the planner looked again the nearest refill was further away
        # than the actions left — `len=11 left=6` — so the refuel it then ordered was a walk
        # it could not finish, and a death puts the whole display back. The interrupt fires
        # only on a board with a lock (a death costs nothing worth guarding elsewhere), only
        # while the tank is readable, and never on the walk into an open door.
        # …and only an ordinary object walk. Lock work — a changer leg, a cycle, a stage
        # plan — arrives with no goal object, is short, and is already budgeted; diverting
        # it cost level 3 seventy-nine actions from two interrupts. A refill walk is
        # already going where the interrupt would send it.
        tankc = {g[0] for g in refills(log, set(drain(log[-CLOCK_WINDOW:])))}
        walk_goal = (cur_goal is not None and plan
                     and cur_goal.get("colour") not in tankc)
        # Lock work is exempt — its rungs budget their own way out, and diverting it cost
        # level 3 seventy-nine actions from two interrupts — EXCEPT when the plan in flight
        # is longer than the fuel, which no budget can excuse: walking it is a death and a
        # death puts the display back. A staged trip is exempt from that exception too: it
        # weaves its own refills, so its length against the tank means nothing, and its
        # mispredictions are caught by the square and display checks instead.
        lock_doomed = (cur_goal is None and plan and model and gate.displays
                       and not trip)
        if lock_doomed:
            lnow0 = actions_left(obs.frame, log, CLOCK_WINDOW)
            lock_doomed = lnow0 is not None and len(plan) > lnow0
        if plan and model and gate.displays and door is None                 and (walk_goal or lock_doomed) and here_now is not None:
            lnow = actions_left(obs.frame, log, CLOCK_WINDOW)
            if lnow is not None:
                tankc = {g[0] for g in refills(log, set(drain(log[-CLOCK_WINDOW:])))}
                fuels = [o for o in targets(obs.frame, model) if o["colour"] in tankc]
                routes_f = [r for o in fuels
                            if (r := bfs(grid, model, (here_now[0], here_now[1]),
                                         footprints_touching(grid, model, o),
                                         redirects)) is not None]
                if routes_f:
                    nearest = min(routes_f, key=len)
                    # Only when the NEXT step would cross the point of no return. "The
                    # refill is far" is not that — it is true the whole way back from a far
                    # refill, and diverting on it walks level 3 in 178 actions instead of
                    # 99. Walking toward the fuel keeps the margin constant; walking away
                    # shrinks it, and the last safe moment is the step before the walk back
                    # stops fitting.
                    nxt = step_to(model, (here_now[0], here_now[1]), plan[0],
                                  {**read, **redirects, **button})
                    after = [r for o in fuels
                             if (r := bfs(grid, model, nxt,
                                          footprints_touching(grid, model, o),
                                          redirects)) is not None]
                    if (not after or lnow - 1 < len(min(after, key=len)))                             and len(nearest) <= lnow:
                        plan, expect, trip = list(nearest), [], []
                        psrc = "fuel-int"
        if here_now is not None and (not trail or trail[-1] != (here_now[0], here_now[1])):
            trail.append((here_now[0], here_now[1]))
        mark = None   # what the staged trip says this action does to the display
        if plan:
            value = plan.pop(0)
            if trip:
                mark = trip.pop(0)
            if expect:
                expect.pop(0)
        else:
            psrc = "wander"
            # Track ids first — they are exact on the board that made them. They die at a
            # level boundary (numbering carries on there, so the old ids are never handed
            # out again), and a model carried across one falls back to recognising the
            # piece by appearance. Using `locate` unconditionally cost m0r0 its level.
            at = None
            if model and (i >= WARMUP or coherent(model.dirs)):
                at = body_box(prev, model.body) or locate(obs.frame, model)
            value = choose_next(grid, at, model.dirs if model else {},
                                (model.passable | model.blocking) if model else set(),
                                values, last, visits, state)
        visits[(state, value)] = visits.get((state, value), 0) + 1

        before = obs
        obs = env.step(by_value[value])
        spent_at_level += 1
        if acct:
            acct.write(json.dumps({"i": i, "lvl": done, "src": psrc, "v": value}) + chr(10))
        if obs is None:
            break

        if obs.levels_completed > done:
            per_level.append(spent_at_level)
            done, spent_at_level, plan, door = obs.levels_completed, 0, [], None
            expect, trip = [], []
            # The mechanic carries across a level boundary; the plates and the square that
            # changes them are drawn somewhere else on the new board, so they do not — but
            # the game's ink alphabet does (see Gate.legacy).
            gate, carried, full, redirects, once = Gate(gate.legacy), model, 0, {}, {}
            stood, refused = set(), set()   # a new board; nothing known of it
            world, windowed, run = None, False, 0   # ...including whether it is a window
            button, button_once, tried, sure = {}, {}, set(), set()
            read = {}
            # The board is new, so the evidence and the track ids are worthless — but the
            # MECHANICS are not. Within one game the piece and its controls carry across
            # levels, and paying discovery again on every level is paying it where the
            # weights are highest. Keep the model only while it still recognises its own
            # piece; when `locate` fails, the game has changed the piece and it goes.
            #
            # Numbering carries on rather than restarting: the ids the new board hands out
            # would otherwise be the same integers the old model's body is written in, so
            # `body_box` answers with whatever the new board happened to call 0 and 1 and
            # the agent steers a decoration. On `ls20` level 3 that read the piece as
            # standing still for 1,070 actions while it pressed a direction into a wall.
            records, visits, last = [], {}, None
            prev, colours, tracks, next_id = see(obs.frame, [], next_id, rows)
            if model and locate(obs.frame, model) is None:
                model = None
            continue

        # A game over ends the run; the reset the engine gives back is a LEVEL reset, which
        # is what competition mode permits, and the level's action count carries on.
        if np.array(obs.frame).size == 0 or obs.state == GameState.GAME_OVER:
            if acct:
                acct.write(json.dumps({"event": "gameover", "lvl": done}) + chr(10))
            obs = env.reset()
            if obs is None or np.array(obs.frame).size == 0:
                break
            # Numbering restarts here and not at a level boundary, because this is the same
            # board again: the tracker walks the same objects in the same order and hands
            # out the same ids, so the model's body still names the piece. A new level is
            # the case where those ids would land on something else entirely.
            prev, colours, tracks, next_id = see(obs.frame, [], 0, rows)
            plan, last, door = [], None, None
            expect, trip = [], []
            # The tracker restarting hands the patrollers new ids too: histories keyed
            # on the old ones would report stale phases forever. Their periods are cheap
            # to re-learn; a stale one plans routes against patrollers that are not there.
            gate.movers.clear()
            # The EDGES go with them, and it reads like waste: an edge is a fact about
            # the game's alphabet, level 6 refuses 555 of its 723 planning rounds with a
            # search that finds no route (a missing edge every time), and `ls20` reaches
            # a game over twice a run, so the alphabet is thrown away twice a level. The
            # argument for keeping it is the comment above — same board, same objects in
            # the same order, so the ids the edges are filed under are the ids about to
            # be issued again. Measured, it **loses level 6 outright** (5/7, 22.419%):
            # whatever the ids land on after a game over, edges filed under them plan
            # presses that do not happen, and a wrong edge costs more than an absent one.
            gate.mover_edges.clear()
            gate.mover_p.clear()   # periods are keyed on ids that are about to be reused
            gate._laps.clear()
            gate.opened.clear()
            gate.reset = gate.ticks
            continue

        # Before anything reads this frame: on a board whose frame is a WINDOW, fold it
        # into the world and paint the world back into the fog, so every reader below sees
        # a board that holds still. Latched on two steps running, and only on a fog that
        # slid by the piece's own displacement. A game over keeps the world — same board,
        # same coordinates; a level boundary throws it away.
        if model is not None and np.array(obs.frame).size and not np.array(before.frame).size == 0:
            if not windowed:
                w0, w1 = locate(before.frame, model), locate(obs.frame, model)
                if w0 and w1:
                    run = run + 1 if windowed_step(
                        before, obs, (w1[0] - w0[0], w1[1] - w0[1]), rows) else 0
                    windowed = run >= 2
            raw5 = (np.array(obs.frame)[-1][:rows] == 5) if windowed else None
            if windowed:
                world = stitch(obs, world, locate(obs.frame, model), model, rows)
            gate.windowed = windowed

        # On a board whose frame is a WINDOW, an object out of view is not gone: it is
        # behind the fog, and it comes back. Two frames of patience kills every patroller
        # the piece walks away from, and a new id on its return is why level 7 tracks
        # dozens of objects and earns one period. Only where the fog is known to slide.
        cur, seen_c, tracks, next_id = see(obs.frame, tracks, next_id, rows,
                                           max_missed=200 if windowed else 2)
        colours.update(seen_c)
        shifts = _shifts(prev, cur)
        records.append({"action": value, "shifts": shifts, "grid": grid,
                        "boxes": prev, "after": set(cur)})
        if model:
            log.append(trace_step(before, obs, value, model))
            # On a windowed board, an object whose square is FOG now did not vanish — it
            # slid out of view — and one whose square was fog last step did not appear.
            # Without this the refill detector unlearns the one refill colour it has: the
            # ring drops off the window's edge on nearly every walk, `seen_without` for
            # colour 11 outgrows `seen_with`, and `refills()` withdraws it — measured at
            # tank=[] in 384 of level 7's 415 planning rounds, with 31 rounds of [11] in
            # between (the window after the first pickup, before the ratio tipped). Every
            # learn trip was then planned with no fuel to weave, and one run starved
            # nineteen times. `raw5` is the fog BEFORE the stitch painted memory into it.
            if windowed and raw5 is not None and log:
                row = log[-1]
                row["gone"] = [g for g in row["gone"]
                               if not (0 <= g[2] < rows and raw5[g[2]][g[1]])]
                if prev_raw5 is not None:
                    row["new"] = [n for n in row["new"]
                                  if not (0 <= n[2] < rows and prev_raw5[n[2]][n[1]])]
            prev_raw5 = raw5

        # Read the plates after EVERY action, not once per plan. A changer is credited to
        # the square the piece was standing on when the display changed, so the credit is
        # only as sharp as how often this is looked at: on `ls20` level 5, where a route
        # runs a dozen actions, both changers were credited to the refill the piece
        # happened to be walking past when the next plan was made, and the two squares that
        # actually write the shape were never learned at all.
        if model is not None and np.array(obs.frame).size:
            here_after = locate(obs.frame, model)
            if here_after is not None:
                # A press the piece did not move for says the square it aimed at cannot be
                # entered right now. The explorer below hunts squares nobody has stood on,
                # and the inside of a shut goal box is one it can NEVER stand on — so it is
                # picked, walked to, pressed into, refused, and picked again: 598 of `ls20`
                # level 5's planning rounds went to that one square. Cleared whenever a
                # display changes, because that is exactly when a door can open.
                was_here = locate(before.frame, model)
                if was_here is not None and was_here[:2] == here_after[:2]:
                    step = model.dirs.get(value)
                    if step:
                        refused.add((was_here[0] + step[0], was_here[1] + step[1]))
                # `walked` means an object moved by exactly the action's displacement, so a
                # step the floor CARRIES reports False — and on a board where the changers
                # are reached through carries that means no changer is ever credited: 64
                # display changes on `ls20` level 5, one of them attributed. What the guard
                # is actually for is not crediting a death, which rewrites the display and
                # teleports the piece to the spawn. A death is what puts the clock UP, so
                # ask that instead: the piece moved, and nothing refilled.
                moved = (was_here is not None
                         and was_here[:2] != here_after[:2])
                fresh = not any(hud(obs.frame).get(k, 0) > hud(before.frame).get(k, 0)
                                for k in drain(log[-CLOCK_WINDOW:]))
                # Changers that MOVE tick on the piece moving — a refused press freezes
                # them (measured, `ls20` level 6) — so their positions are recorded on
                # exactly those ticks and nothing else.
                gate.track(cur, model.body, moved, here_after)
                # What this button did from THIS square. The cell map says "anything aiming
                # at that square ends up there", which is what `ls20` level 4 measured and
                # is the right rule for a floor that carries. It cannot say "this button
                # does nothing from here" — a wall, or a door that is shut. Recording that
                # too freezes the board: something standing in the way for one action reads
                # as a wall for the rest of the level, and `ls20` drops from four levels to
                # one. So only a press that MOVED the piece somewhere the model did not
                # predict is written down, and the table stays the size of the surprises.
                # Only when the step was an honest one: a death teleports the piece
                if was_here is not None and fresh:
                # to the spawn, and written down that reads as a button that teleports.
                    src = (was_here[0], was_here[1])
                    got = (here_after[0], here_after[1])
                    d = model.dirs.get(value)
                    # A value the model has no direction for cannot be scored as a
                    # surprise — `step_to` reads `model.dirs[value]` and dies on it.
                    # tr87 pressed one 1,343 actions in, which no run under the old
                    # 1,200 budget had lived long enough to reach.
                    if d is not None:
                        aim = (src[0] + d[0], src[1] + d[1])
                        if aim in read and got != step_to(model, src, value, {**read}):
                            del read[aim]      # the board's marking, refuted by a walk
                        if got != src and got != step_to(model, src, value, redirects):
                            # Believed on the second sighting, the same bar a cell rule
                            # has to clear. Believed on the first, the router starts
                            # steering by it before the deliberate re-probe that the map
                            # is built on has run, and `ls20` level 4 stops clearing.
                            key = (src, value)
                            if button_once.get(key) == got:
                                button[key] = got
                            button_once[key] = got
                state_was = gate.state()
                changed = gate.observe(obs.frame, here_after,
                                       bool(log and log[-1]["walked"]) or (moved and fresh))
                if acct and changed:
                    acct.write(json.dumps({"event": "chg", "lvl": done}) + chr(10))
                # Per-action movement + display line for the level-6 press-rule measurement:
                # which steps actually press is the transition model a phase-counting
                # planner has to get right, and it cannot be derived from the per-round view.
                if l6 and done == 5:
                    l6.write(json.dumps({
                        "a": i, "was": list(was_here[:2]) if was_here else None,
                        "now": list(here_after[:2]), "chg": bool(changed),
                        "state": sorted(map(list, gate.state())),
                        "edges": sum(len(v) for v in gate.mover_edges.values()),
                        "keys": len(gate.mover_edges),
                        "ready": sum(1 for k in gate.movers
                                     if gate.mover_period(k) and gate.movers[k].get("halves")),
                        "mute": sum(1 for k in gate.movers
                                    if gate.mover_period(k) and not gate.movers[k].get("halves")),
                    }, default=str) + chr(10))
                if changed:
                    # A door that was shut may now be open, so what the buttons pointing
                    # into it did is no longer what they do.
                    refused.clear()
                    button = {k: v for k, v in button.items() if v != k[0]}
                    button_once = {k: v for k, v in button_once.items()
                                   if v != k[0]}
                elif was_here is not None and here_after is not None                         and was_here[:2] != here_after[:2] and state_was:
                    # The piece ENTERED a square the table claims changes the display, and
                    # the display did not move: the edge lied. A changer credited off a
                    # death plants exactly this phantom, and `path_for` then routes every
                    # plan through a press that does nothing — level 5 sat on a computed
                    # three-leg recipe for thirty rounds because leg one was a phantom.
                    # Refutation costs one entry, the same as belief did.
                    sq = (here_after[0], here_after[1])
                    for val in state_was:
                        for h, v in enumerate(val):
                            step = gate.cycles.get((sq, h))
                            if step and step.get(v) is not None and step[v] != v:
                                del step[v]
                                gate.rotates.discard((sq, h))
                            # A legacy ink edge that lied is dropped the same way: this
                            # game's levels do not share the alphabet after all.
                            if isinstance(v, int):
                                gate.legacy.pop(v, None)

                # Mid-flight validation of a staged trip. The trip predicted, per action,
                # whether the display moves — an entry onto a changer — or holds — a
                # walking step. Reality disagreeing EITHER way ends the trip: a change the
                # plan did not schedule means the route crossed a changer nobody planned
                # for (which is how level 3 finds its second one), and a scheduled press
                # that moved nothing is a phantom edge. From here on every press left in
                # the plan is counted against a panel that is not there, so the honest
                # move is to drop it and plan from what the board now says.
                if mark is not None and changed != mark:
                    plan, expect, trip = [], [], []

            last = value if shifts.get(model.player) == model.dirs.get(value) else None
        prev = cur

        # A step that lands somewhere the model did not predict makes the rest of the plan
        # meaningless: every action after it is aimed from a square the piece is not on.
        # `ls20` level 4 carries the piece further than the action it was given — measured,
        # `press 4` at (14, 35) landed at (19, 45) and `press 1` at (24, 45) landed at
        # (9, 40) — so 83 plans in one run ended somewhere they never meant to go.
        #
        # A move that *did not happen at all* is the other case and is deliberately left
        # alone: dropping the plan there is the rule that cost `cd82` its only level. The
        # piece standing still keeps the plan; the piece being carried does not.
        if model:
            was, now = locate(before.frame, model), locate(obs.frame, model)
            if slid(model, was, now, value):
                # Learn the cell that did it, keyed on the square the press aimed at. Losing
                # a life also moves the piece somewhere it did not ask for and refills the
                # clock as it does; that is a teleport, not a property of a cell.
                dx, dy = model.dirs[value]
                aim = (was[0] + dx, was[1] + dy)
                clock_rose = any(hud(obs.frame).get(k, 0) > hud(before.frame).get(k, 0)
                                 for k in (drain(log[-CLOCK_WINDOW:]) if log else {}))
                if acct:
                    acct.write(json.dumps({"event": "silentdeath" if clock_rose
                                           else "slid", "lvl": done}) + chr(10))
                if clock_rose:
                    # A death puts the panel back, and with it every door that had been
                    # passed while matched: `opened` describes a life, not the level.
                    gate.opened.clear()
                    # The PATROLLERS go back too, so entries from before a death
                    # contradict the ones after at the same phase and every period is
                    # lost — measured, on the exact action a life ended. Clearing the
                    # histories there to re-earn them in one lap instead of three was
                    # tried and **loses level 6** (5/7, 22.419%): the contradicting
                    # entries are not only noise, they are what keeps a period from
                    # being re-read too eagerly off a handful of post-respawn frames,
                    # and a wrong period sends every planned press to the wrong tick.
                    #
                    # What a death actually invalidates is the PHASE, not the period.
                    # Marking the tick lets `mover_period` keep the period it already
                    # earned — checked against this life's frames, never re-read off
                    # them — while `mover_at` answers from this life's sightings only.
                    gate.reset = gate.ticks
                if not clock_rose:
                    off = (now[0] - aim[0], now[1] - aim[1])
                    # Twice, or not at all. A cell that sends every piece the same way is a
                    # property of the board; a shove from something that happened to be
                    # passing is not, and routing through one of those costs `m0r0` its only
                    # level. The confirmation is affordable because the router keeps walking
                    # the plain route while the map is incomplete, so a real cell is hit
                    # again almost immediately.
                    if once.get(aim) == off:
                        redirects[aim] = off
                    once[aim] = off
                # A carry the PLAN already predicted is not a surprise: a moving-changer
                # trip is planned through the known carries, and dropping it for being
                # right costs the whole choreography — the timing against the patrol
                # clock is the plan. ONLY the moving planner's trips earn this: extending
                # the keep to every trip with a correct prediction was measured and cost
                # level 5 forty-seven actions (292 -> 339), through the same replanning
                # the staged chains were tuned around.
                if not (psrc == "moving" and trip and expect
                        and (now[0], now[1]) == expect[0]):
                    plan, expect, trip = [], [], []

        # Two ways of reacting to a move that did not happen were built here and both were
        # measured out again, which is worth more written down than the code was:
        #
        # * **Abandon the plan.** A blocked move leaves the piece one square behind where
        #   the rest of the route assumes it is, so the remaining actions are aimed from
        #   the wrong place — sound reasoning, and it cost `cd82` its only level while
        #   buying `m0r0` three actions. Its 812-action clear depends on walking the rest
        #   of a route that no longer means what it meant.
        # * **Remember which target refused, and stop walking to it.** That cost `m0r0` its
        #   level and bought `ls20` nothing: a refusal has to expire on something, the only
        #   thing available is the displays, and before one has been seen to change there is
        #   nothing to expire against — so the first bump into a mis-modelled wall
        #   blacklists the goal for the rest of the level. Reading the glyph makes it
        #   unnecessary anyway: a shut door is known to be shut before the walk, not after.

        # The one move worth reacting to: a door the display said was open, refusing the
        # piece at the threshold. Two glyphs compare equal once their bitmaps are collapsed
        # to be comparable across scales, and that is a hypothesis — the engine settles it.
        if door is not None and log and not log[-1]["walked"] and model                 and locate(before.frame, model) == locate(obs.frame, model):
            gate.reject(door)
            plan, door, expect, trip = [], None, [], []

        # Warm up until the CONTROLS are known, not for a fixed count. The 24-action wait
        # is a worst case, not a price: `ls20` level 1 has its goal box seven actions from
        # the opening square and spent thirty-nine getting there, because planning could not
        # start until the counter said so. Measured across nine games, the fourth direction
        # is usually known long before that — and the games do not agree on which button is
        # which (`ar25` swaps left and right) or on the step size (2 to 5 cells), so the
        # convention cannot simply be assumed either.
        if not plan and model is None and CONTROLS <= i < WARMUP:
            # Try to build early — the gate cannot ask whether the controls are known while
            # nothing has been built to ask.
            early = build_model(records, colours, rows, prior=carried)
            if early is not None and coherent(early.dirs):
                model = early
        ready = (model is not None and coherent(model.dirs)) or i >= WARMUP
        if ready and not plan:
            model = keep_identity(
                build_model(records, colours, rows, prior=carried), carried, obs.frame) or model
            if model and locate(obs.frame, model):
                # Only this level's steps. The rate belongs to the LEVEL — the same
                # 84-cell bar spends 2 cells an action on `ls20` level 1 and 4 on level 2 —
                # and a window that still holds the previous level's steps reads the most
                # common fall off the wrong board. On level 5 that made a life look 40
                # actions long instead of 21, `full` is the largest reading ever taken, so
                # it stayed wrong for the whole level, and every plan the order search
                # costed against a refill was costed against a tank twice the real size.
                left = actions_left(obs.frame, log[-spent_at_level:] if spent_at_level
                                    else log, CLOCK_WINDOW)
                if left is not None:
                    full = max(full, left)
                # The board MARKS its carrying cells — a bar one cell thick and one
                # step long beside each — and the piece entering one is thrown away from
                # the bar until something blocks it. Read off the frame, `ls20` level 5's
                # eight cells are all there before the first step; walked into, they cost
                # a few hundred actions and arrive too late to plan with. A reading a walk
                # contradicts is dropped on the spot, so a marker-shaped object that is not
                # a carry costs one wasted step, not a broken map.
                # …but as a HYPOTHESIS, not as the map. Believed outright it costs `ls20`
                # level 4 outright — some marker-shaped object on those boards is not a
                # carry — so each reading is filed as a first sighting instead, and the
                # confirmation the map already runs promotes it the first time a walk
                # agrees. That halves the cost of learning a real one and costs nothing for
                # a false one.
                for cell, off in slides(obs.frame, grid, model).items():
                    once.setdefault(cell, off)
                rules = {**redirects, **button}
                plan, goal = choose(obs.frame, model, log, gate, left, full, rules, once,
                                    frozenset(list(trail)[:-1]), stood, refused, tried, sure)
                here = locate(obs.frame, model)
                expect = trajectory(model, here, plan, rules) if (plan and here) else []
                trip = list(gate.trip) if (plan and gate.trip) else []
                gate.lvl = done
                psrc = (gate.rung or "none") if plan else "wander"
                cur_goal = goal
                door = goal if goal is not None and gate.matched(goal) else None
                # Level-6 gate view, one line per planning round. Measurement only: what
                # the marked plates wear, what the panel says, which squares are proven
                # rotators, and the fuel picture — the inputs a phase-counting planner
                # would plan from, written down before one is built.
                if l6 and done == 5:
                    marked6 = [{"colour": o["colour"], "x": o["x"], "y": o["y"],
                                "marks": sorted(map(list, gate._marks(o))),
                                "locked": gate.locked(o), "matched": gate.matched(o)}
                               for o in targets(obs.frame, model) if gate.marked(o)]
                    l6.write(json.dumps({
                        "i": i, "at": list(here[:2]) if here else None,
                        "left": left, "full": full, "rung": psrc,
                        "tank": sorted(map(list, refills(
                            log, set(drain(log[-CLOCK_WINDOW:]))))),
                        "state": sorted(map(list, gate.state())),
                        "marked": marked6,
                        "rotates": sorted(str(r) for r in gate.rotates),
                        "changers": {str(k): sorted(v) for k, v in gate.changers.items()},
                        "cycles": {str(k): {str(a): str(b) for a, b in v.items()}
                                   for k, v in gate.cycles.items()},
                        "legacy": {str(a): b for a, b in gate.legacy.items()},
                        "redirects": {str(k): list(v) for k, v in redirects.items()},
                        "movers": {str(k): {"p": (p := gate.mover_period(k)),
                                            "halves": sorted(gate.movers[k].get("halves", [])),
                                            "edges": {str(h): len(v) for (kk, h), v
                                                      in gate.mover_edges.items() if kk == k},
                                            "cov": (sorted({t % p for t, _ in
                                                            gate.movers[k]["hist"]
                                                            if t > gate.ticks - 3 * p})
                                                    if p else None),
                                            "last": gate.movers[k]["hist"][-1]
                                            if gate.movers[k]["hist"] else None}
                                   for k in gate.movers
                                   if gate.mover_period(k) or gate.movers[k].get("halves")},
                        "opened": len(gate.opened),
                        "once": {str(k): list(v) for k, v in once.items()
                                 if isinstance(k, tuple) and len(k) == 2
                                 and not isinstance(k[0], tuple)},
                    }, default=str) + chr(10))

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
