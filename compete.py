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
from gate import Gate, cycle, turned
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
L6 = os.environ.get("ARC_L6")      # gate-view JSONL for one level (index ARC_L6LVL, default 5), opt-in
L6LVL = int(os.environ.get("ARC_L6LVL", "5"))


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


def tank_colours(log, gate):
    """Refill colours to plan fuel with — `refills()`'s answer, latched on a WINDOWED board.

    `refills()` re-derives its with/without ratio from the trace every round, and on a
    board whose frame slides the ratio decays toward empty whenever the piece spends a
    while away from a ring — measured at tank=[] in 149 of level 7's 345 planning rounds
    after the trace filters, all of them early-level or post-death, which are exactly the
    rounds a learn trip starves in. A refill colour is a property of the level, so once
    earned it holds for the level: the latch lives on the Gate, which dies at the level
    boundary, so nothing leaks to the next board. Windowed only — everywhere else
    `refills()` is already stable and the withdraw-on-doubt behaviour is what guards
    against a false pickup (`ls20` level 5's white cross).
    """
    got = {g[0] for g in refills(log, set(drain(log[-CLOCK_WINDOW:])))}
    if getattr(gate, "windowed", False):
        gate.tank |= got
        return set(gate.tank)
    return got


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
    learn6 = None   # a windowed board's learn trip, held back for the square rungs
    if at and gate.movers and gate.displays:
        here = (at[0], at[1])
        tank6 = tank_colours(log, gate)
        fuels = [o for o in seen if o["colour"] in tank6]
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
                # On a WINDOWED board the learn trip is a fallback, not the answer: the
                # movers it aims at are mostly ghosts (no press here is ever credited to
                # the thing pressed — the changers are spatially static, so no period is
                # ever earned; see results/l7-model.md), while every walked press has
                # been landing in `gate.changers`/`gate.cycles` under its SQUARE. Stash
                # the plan and let the square rungs below have the round first.
                if not getattr(gate, "windowed", False):
                    gate.trip = got[1]
                    gate.rung = "moving-learn"
                    return got[0], None
                learn6 = got
                break
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

    # The held-back learn trip jumps the queue when the square graph is CLOSED: every
    # wrong half watched through five or more states with the ask still unreachable
    # means no amount of pressing the known squares can open the door — the missing
    # edge is on something unwatched, which is exactly what the learn trip walks to.
    # Without this the reordered square rungs churn the closed ring forever and the
    # east half of the board is never explored (measured: 1,029 bfs-exhausted rounds,
    # cycle-last 148 actions, the x54 rotators never learned in-run).
    # ANY wrong half being exhausted is enough: the panel must match in every half at
    # once, so one half the known squares cannot reach blocks the whole plan no matter
    # how fixable the others are (`all` here never fired — the ink half is always
    # fixable, so it vetoed the yield while the shape half sat closed).
    if learn6 and locked and os.environ.get("ARC_YDBG"):
        wh = gate.wrong_halves(locked[0])
        print("[yd] lvl=%s wrong=%s exh=%s path=%s state=%s" % (
            getattr(gate, "lvl", -1), sorted(wh),
            {h: gate.exhausted(locked[0], h) for h in wh},
            {h: (p if (p := gate.path_for(locked[0], h)) is None else len(p))
             for h in wh},
            sorted(map(str, gate.state()))[:1]))
    # Yield to exploration ONLY when pressing what is already known teaches nothing:
    # `learning_path` finds a walk to a state with an unwatched edge, and while one
    # exists the square rungs below should have the round — the ring completes, and a
    # complete ring plus the x54 rotators is exactly the ask (verified offline:
    # path_for returns [((19,40),5), ((54,30),2)] the moment all six ring edges are in).
    if learn6 and locked and any(
            gate.exhausted(o, h) and gate.learning_path(o, h) is None
            for o in locked for h in gate.wrong_halves(o)):
        # The missing edge is usually OFF-MAP, not on a tracked ghost: measured, 598
        # actions of learn trips pressed the west changers' own fragments while the
        # east half of the board — and the changer the ask needs — stayed fog. On a
        # windowed board the unexplored set IS the colour-5 region, so walk to the
        # nearest never-stood position whose neighbourhood still holds fog, and fall
        # back to the learn trip only when no frontier fits the tank.
        if at is not None and left is not None:
            here5 = (at[0], at[1])
            w5, h5 = model.box
            dists5 = bfs_all(grid, model, here5, redirects)

            def poky(pos):
                """A direction never poked whose plain target no route can reach."""
                for a5, s5 in model.dirs.items():
                    tgt = (pos[0] + s5[0], pos[1] + s5[1])
                    if (tgt not in dists5 and tgt not in refused
                            and (a5, pos) not in gate.poked):
                        return a5
                return None

            # Standing at a dead end of the ROUTABLE map, press into it: one action
            # buys a wall (recorded, never repeated) or a carry — and a carry is the
            # only way into a region no route can aim at. Level 7's east half hangs
            # entirely on the (34,20) warp, which `slides` cannot read off a marker.
            if left > 6 and (a5 := poky(here5)):
                gate.poked.add((a5, here5))
                gate.rung = "fog-poke"
                return [a5], None
            best5, far5 = None, False
            for pos, route5 in sorted(dists5.items(), key=lambda t: len(t[1])):
                if not route5:
                    continue
                x5, y5 = pos
                fogy = (pos not in stood
                        and (grid[max(0, y5 - 1):y5 + h5 + 1,
                                  max(0, x5 - 1):x5 + w5 + 1] == 5).any())
                if len(route5) > left - 2:
                    # A frontier the tank cannot reach is still the frontier — note it
                    # and refuel below rather than giving the round to the ghosts. The
                    # east half of level 7 is 20+ actions out on a 21-action life, so
                    # without this the far frontier is simply never visited.
                    if fogy or poky(pos):
                        far5 = True
                        break
                    continue
                if fogy:
                    gate.rung = "fog-explore"
                    return route5, None
                if best5 is None and poky(pos):
                    best5 = route5
            if best5:
                gate.rung = "fog-explore"
                return best5, None
            if far5:
                tank5 = tank_colours(log, gate)
                legs5 = [r for o in targets(frame, model) if o["colour"] in tank5
                         and (r := bfs(grid, model, here5,
                                       footprints_touching(grid, model, o),
                                       redirects)) is not None and len(r) <= left]
                if legs5:
                    gate.rung = "fog-fuel"
                    return min(legs5, key=len), None
        gate.trip = learn6[1]
        gate.rung = "moving-learn"
        return learn6[0], None

    if at and locked and not (getattr(gate, "windowed", False)
                              and gate.turns_for(locked[0])):
        # The board carries the piece somewhere the map cannot vouch for. Settle it before
        # routing on it: an unconfirmed cell is either the way through or a phantom, and the
        # two are indistinguishable from here.
        # On a WINDOWED board the probe yields whenever a square that writes a wrong half
        # is already known: probes took 516 of level 7's 1,154 actions while the recorded
        # changers sat unpressed, because this rung sits above the square press rungs.
        # Everywhere else the order stays as measured on levels 2-5.
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
            tank0 = tank_colours(log, gate)
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
    tank = tank_colours(log, gate)

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

        Over every refill SEEN, not the rarity shortlist — the same widening `stage`'s
        fuel already has, for the same reason ("a refill is rarely rare"): on level 7
        the ring three steps from the shape changer was cut from `cands`, so
        `turn-fuel` refuelled at whichever far ring survived the ranking and walked
        the piece between the northern rings for the whole life — twenty consecutive
        lives ended fuel-walk -> cand -> desperate -> death without one press.
        """
        def _spent(f):
            return any(f["x"][0] <= sx + 4 and f["x"][1] >= sx
                       and f["y"][0] <= sy + 4 and f["y"][1] >= sy
                       for sx, sy in getattr(gate, "spent", ()))

        best = None
        for f in seen:
            if f["colour"] not in tank or _spent(f):
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

    # QUARTER-TRIP: the panel's shape is k quarter-turns from the door's ask.
    # The ring cannot turn it — steps stay within a rotation family — only the
    # patroller can, and its lap is remembered (`gate.lapmem`) long after the track
    # died. Walk into the lap: each footprint overlap after a move presses one
    # quarter; the ring press (drivable at any parity now) re-sets the shape if the
    # count overshoots, and the loop converges mod 4. The ink half is deliberately
    # not required: the patroller turns only the shape.
    if (at is not None and not doors and locked and left is not None
            and getattr(gate, "windowed", False) and gate.state()):
        cur2 = min(gate.state())
        ask_q = None
        # against EVERY locked target — locked[0] is often the refill-ring plate,
        # not the door (the lesson ARC_YDBG already taught the exhausted-yield)
        for o2 in locked:
            marks2 = gate._marks(o2)
            if not marks2:
                continue
            want2 = min(marks2)
            for hh2, (wv, cv) in enumerate(zip(want2, cur2)):
                if isinstance(wv, str) and isinstance(cv, str) and wv != cv:
                    orb2 = turned(cv)
                    if orb2 and wv in orb2:
                        ask_q = orb2.index(wv)
            if ask_q:
                break
        if os.environ.get("ARC_QTDBG"):
            print("[qt] at=%s ask_q=%s x=%s left=%s state=%s lapmem=%d" % (
                tuple(at[:2]), ask_q, getattr(gate, "x_target", None), left,
                sorted(map(str, gate.state()))[:1], len(gate.lapmem)))
        if ask_q:
            # Seed the lap-overlap squares as VIRTUAL ROTATORS: entering one turns
            # the shape a quarter (the x55 patroller's measured act), so `path_for`
            # can compose ring presses + quarter turns into one plan and the STAGE
            # search — the only machinery that weaves multiple refills into a
            # multi-leg trip — owns the choreography. Wrong squares refute at
            # execution like any wrong edge.
            h_sh = next((h for (p, h) in gate.cycles
                         if any(isinstance(a, str) for a in gate.cycles[(p, h)])),
                        None)
            if h_sh is not None:
                # ...and the LIVE track matching the lap gets the same virtual law
                # as the squares: halves + one quarter edge make it a ROTATOR for
                # `_mover_step`, and `route_moving`'s phase-counting BFS — level
                # 6's measured machinery — can finally time a chase press instead
                # of sampling phases blind. Refutable at execution like the rest.
                for k9, info9 in gate.movers.items():
                    hist9 = info9.get("hist") or []
                    boxes9 = {b for _, b in hist9}
                    if len(boxes9) < 3:
                        continue
                    xs9 = [b[0] for b in boxes9]; ys9 = [b[1] for b in boxes9]
                    sx9, sy9 = max(xs9) - min(xs9), max(ys9) - min(ys9)
                    if not ((sx9 <= 5 and sy9 >= 15) or (sy9 <= 5 and sx9 >= 15)):
                        continue
                    info9.setdefault("halves", set()).add(h_sh)
                    step9 = gate.mover_edges.setdefault((k9, h_sh), {})
                    if not step9:
                        cv9 = min(gate.state())[h_sh]
                        if isinstance(cv9, str) and turned(cv9):
                            step9[cv9] = turned(cv9)[1]
                for bx, by, bw, bh in gate.lapmem:
                    px0 = bx - ((bx - at[0]) % 5)
                    py0 = by - ((by - at[1]) % 5)
                    for dx in (-5, 0, 5):
                        for dy in (-5, 0, 5):
                            px, py = px0 + dx, py0 + dy
                            if (px < bx + bw and px + 5 > bx
                                    and py < by + bh and py + 5 > by
                                    and walkable(grid, model, px, py)):
                                gate.rotates.add(((px, py), h_sh))
        # the bootstrap trip's purpose is SIGHTING, not quarters — with no lap
        # known yet it should fire on any shape-wrong round, not wait for the
        # panel to reach an ask-orbit state (that wait is why the whole
        # choreography first aligned at a~1900 of 2,000)
        shape_wrong = any(
            isinstance(wv3, str) and isinstance(cv3, str) and wv3 != cv3
            for o3 in locked for m3 in [gate._marks(o3)] if m3
            for wv3, cv3 in zip(min(m3), min(gate.state())))
        if (ask_q or (shape_wrong and not gate.lapmem))                 and not getattr(gate, "qt_out", False):
            here_q = (at[0], at[1])
            # `refused` expires on display changes; what persists is tried-minus-
            # sure — every press that never landed where it aimed. Self-healing:
            # a door that later opens records a success and leaves the set.
            walls_q = {(sq[0] + model.dirs[a][0], sq[1] + model.dirs[a][1])
                       for (sq, a) in tried
                       if (sq, a) not in sure and a in model.dirs} | set(refused)
            body_c = set(getattr(model, "colours", ()) or ()) | {
                c for c in (getattr(model, "player", None),) if c is not None}
            def _lappy(info2):
                c2 = info2.get("c")
                if c2 is not None and (c2 in tank or c2 in body_c):
                    return False   # a ring's flicker or the piece's own fragment
                boxes = {bb for _, bb in info2.get("hist") or []}
                if len(boxes) < 3:
                    return False
                xs = [b[0] for b in boxes]; ys = [b[1] for b in boxes]
                # a real lap is a LINE — one axis pinned, the other spanning the
                # board. Fragment junk clusters 2D near the piece, and a track that
                # churned across a death-teleport scatters 2D across the board.
                sx, sy = max(xs) - min(xs), max(ys) - min(ys)
                return (sx <= 5 and sy >= 15) or (sy <= 5 and sx >= 15)
            lap = [b for k2, info2 in gate.movers.items()
                   for _, b in (info2.get("hist") or [])[-16:]
                   if _lappy(info2)]
            newlap = {(int(b[0]), int(b[1]), int(b[2]), int(b[3])) for b in lap}
            if os.environ.get("ARC_QTDBG") and newlap - gate.lapmem:
                print("[lap] add=%s" % sorted(newlap - gate.lapmem))
            gate.lapmem |= newlap
            # hygiene: a lap is ONE line — keep only the largest collinear
            # cluster (fixed axis within +-2 of its median); junk that slipped
            # in through a linear-looking track elsewhere poisons the chase,
            # which was measured following a ring flicker at (50,6) west
            # while the patroller paced x55.
            if len(gate.lapmem) >= 3:
                import statistics as _st
                xs_l = sorted(b[0] for b in gate.lapmem)
                ys_l = sorted(b[1] for b in gate.lapmem)
                spread_x = xs_l[-1] - xs_l[0]
                spread_y = ys_l[-1] - ys_l[0]
                if spread_x <= spread_y:
                    mx = _st.median(xs_l)
                    gate.lapmem = {b for b in gate.lapmem if abs(b[0] - mx) <= 2}
                else:
                    my = _st.median(ys_l)
                    gate.lapmem = {b for b in gate.lapmem if abs(b[1] - my) <= 2}
            # The lap itself is void — the patroller floats where the piece cannot
            # stand. The press is footprint OVERLAP, so aim at every walkable
            # lattice position whose 5x5 footprint reaches a lap box.
            cells = set()
            for bx, by, bw, bh in gate.lapmem:
                # candidate stand-positions live on the PIECE's lattice, which is
                # offset from the raw grid (x = 4, 9, ... on this board, not 0, 5)
                px0 = bx - ((bx - at[0]) % 5)
                py0 = by - ((by - at[1]) % 5)
                for dx in (-5, 0, 5):
                    for dy in (-5, 0, 5):
                        px = px0 + dx
                        py = py0 + dy
                        if (px < bx + bw and px + 5 > bx
                                and py < by + bh and py + 5 > by
                                and walkable(grid, model, px, py)
                                and (stood is None or (px, py) not in stood)):
                            # the piece's own column-pacing ghost passes every
                            # geometry filter; the real lap is somewhere the
                            # piece has never stood
                            cells.add((px, py))
            # The lap itself can sit beyond the composite's walkable map at plan
            # time (fog) — a route often exists only as far as a known carry's
            # LANDING. Take the stone: once east, the next round replans with
            # local sight and the lap is a short hop.
            stones = {(int(a[0] + o[0]), int(a[1] + o[1]))
                      for a, o in redirects.items() if isinstance(a[0], int)}
            stones = {c for c in stones if walkable(grid, model, c[0], c[1])}
            goals2 = cells
            leg3 = bfs(grid, model, here_q, cells, redirects,
                       avoid=walls_q) if cells else None
            if leg3 is None and stones:
                # No lap known yet (or unroutable): BOOTSTRAP — ride to the carry
                # landing FARTHEST from the changers, which is the unexplored side
                # the patroller lives on; the window sees the lap from there and
                # the next trip aims true. Nearest-stone goes north and learns
                # nothing.
                cx = sum(p[0] for p in gate.changers) / max(1, len(gate.changers))
                cy = sum(p[1] for p in gate.changers) / max(1, len(gate.changers))
                far = max(stones, key=lambda c: abs(c[0] - cx) + abs(c[1] - cy))
                goals2 = {far}
                leg3 = bfs(grid, model, here_q, {far}, redirects, avoid=walls_q)
            if os.environ.get("ARC_QTDBG"):
                print("[qt2] cells=%d stones=%d leg=%s left=%s tank=%s" % (
                    len(cells), len(stones),
                    None if leg3 is None else len(leg3), left, sorted(tank)))
            if goals2:
                if leg3 and len(leg3) + 8 <= left:
                    gate.rung = "quarter-trip"
                    # a 1-step "trip" that a wall refuses should not latch the
                    # outbound flag — home would walk for nothing and the retry
                    # would wait a whole lap
                    gate.qt_out = len(leg3) >= 5
                    # Arrived at the lap, CHASE along its axis away from home:
                    # following the patroller's own line is what overlaps every
                    # tick (the hand solution's recipe), and the walk past the
                    # lap's far end is what first SIGHTS the east refill ring —
                    # without it in `seen`, stage can never weave east fuel and
                    # every trip dies out here with its quarters.
                    ext = [leg3[-1]] * 2
                    if gate.lapmem:
                        xs = [b[0] for b in gate.lapmem]
                        ys = [b[1] for b in gate.lapmem]
                        cx2 = sum(p[0] for p in gate.changers) / max(1, len(gate.changers))
                        cy2 = sum(p[1] for p in gate.changers) / max(1, len(gate.changers))
                        vert = (max(ys) - min(ys)) >= (max(xs) - min(xs))
                        mid = (sum(ys) / len(ys)) if vert else (sum(xs) / len(xs))
                        home_c = cy2 if vert else cx2
                        away = 5 if mid >= home_c else -5
                        want = (0, away) if vert else (away, 0)
                        a_ax = next((a2 for a2, st2 in model.dirs.items()
                                     if tuple(st2) == want), None)
                        if a_ax is not None:
                            # patrol the column as long as the tank affords: the
                            # longer the piece stays in sight of the lap, the more
                            # sightings the track banks toward a PERIOD, and every
                            # step is another y-alignment chance at a press
                            n_ax = max(3, min(8, left - len(leg3) - 5))
                            ext = [a_ax] * n_ax
                    return leg3 + ext, None
                top3, f3 = refuel(goals2)
                if top3:
                    gate.rung = "quarter-fuel"
                    return top3, f3

    # REACTIVE CHASE: east, outbound, the lap's track in sight THIS tick. The
    # phase cannot be planned from the west (it is unknowable there within a
    # life), so the chase is closed-loop at execution: step along the lap toward
    # the patroller's live position; the play loop counts footprint overlaps —
    # the measured press law — and `qt_need` pays down without ever reading the
    # display. When paid, fall through: quarter-home walks back to read.
    chase_need = 0
    if (at is not None and getattr(gate, "windowed", False) and gate.lapmem
            and locked and gate.state()):
        cur_c = min(gate.state())
        for o_c in locked:
            m_c = gate._marks(o_c)
            if not m_c:
                continue
            w_c = min(m_c)
            for hh_c, (wv_c, cv_c) in enumerate(zip(w_c, cur_c)):
                if isinstance(wv_c, str) and isinstance(cv_c, str) and wv_c != cv_c:
                    orb_c = turned(cv_c)
                    if orb_c and wv_c in orb_c:
                        chase_need = orb_c.index(wv_c)
            if chase_need:
                break
        # validated LIVE against the kept panel: a standing demand set at an
        # earlier panel paid itself at the wrong state — the chase turned
        # rot^2 of `#.#/#.#/###` instead of rot^2 of the ask's own family
        if chase_need != gate.qt_need:
            gate.qt_need, gate.qt_hits = chase_need, 0
    if (at is not None and getattr(gate, "windowed", False)
            and gate.qt_need > gate.qt_hits
            and gate.lapmem):
        ys_l = [L[1] for L in gate.lapmem]; xs_l = [L[0] for L in gate.lapmem]
        vert_l = (max(ys_l) - min(ys_l)) >= (max(xs_l) - min(xs_l))
        lo_l = (min(ys_l) if vert_l else min(xs_l)) - 5
        hi_l = (max(ys_l) if vert_l else max(xs_l)) + 8
        fresh_tracks = [(k9, info9["hist"][-1][1]) for k9, info9 in gate.movers.items()
                        if info9.get("hist") and info9["hist"][-1][0] >= gate.ticks - 1
                        and any(info9["hist"][-1][1][0] < L[0] + L[2]
                                and info9["hist"][-1][1][0] + info9["hist"][-1][1][2] > L[0]
                                for L in gate.lapmem)
                        and lo_l <= (info9["hist"][-1][1][1] if vert_l
                                     else info9["hist"][-1][1][0]) <= hi_l]
        if fresh_tracks:
            k9, b9 = fresh_tracks[0]
            # LEAD the target: at equal speeds a follow never closes — the hand
            # chase put the piece where the patroller was GOING and let it walk
            # into the footprint. Aim two ticks ahead along its own velocity.
            h9 = gate.movers[k9].get("hist") or []
            if len(h9) >= 2:
                pb = h9[-2][1]
                dvx, dvy = b9[0] - pb[0], b9[1] - pb[1]
                if abs(dvx) <= 5 and abs(dvy) <= 5 and (dvx or dvy):
                    b9 = (b9[0] + 2 * dvx, b9[1] + 2 * dvy, b9[2], b9[3])
            xs9 = [L[0] for L in gate.lapmem]; ys9 = [L[1] for L in gate.lapmem]
            vert9 = (max(ys9) - min(ys9)) >= (max(xs9) - min(xs9))
            # chase only FROM the lap's own line — starting it early, a home-
            # carry yanked the piece west mid-chase and it died pressing a wall
            lap_axis = (sum(xs9) / len(xs9)) if vert9 else (sum(ys9) / len(ys9))
            on_line = abs((at[0] if vert9 else at[1]) + 2 - lap_axis) <= 7
            if not on_line:
                fresh_tracks = []
        if fresh_tracks:
            # overlap needs the piece ON the adjacent column (footprint spans
            # +4): from one column further out it tracks the patroller forever
            # and never touches it — measured, a whole chase ridden at x49
            # against a lap at x55-57
            off_ax = (b9[0] - 1 - (at[0] + 2)) if vert9 else (b9[1] - 1 - (at[1] + 2))
            if abs(off_ax) > 3:
                want9 = ((5 if off_ax > 0 else -5, 0) if vert9
                         else (0, 5 if off_ax > 0 else -5))
            else:
                dy9 = (b9[1] + b9[3] // 2) - (at[1] + 2) if vert9 else                       (b9[0] + b9[2] // 2) - (at[0] + 2)
                want9 = ((0, 5 if dy9 > 0 else -5) if vert9
                         else (5 if dy9 > 0 else -5, 0))
            a9 = next((aa for aa, st9 in model.dirs.items()
                       if tuple(st9) == want9), None)
            if a9 is not None:
                gate.rung = "chase"
                if os.environ.get("ARC_QTDBG"):
                    print("[ch] step at=%s target=%s hits=%d/%d"
                          % (tuple(at[:2]), b9, gate.qt_hits, gate.qt_need))
                return [a9], None

    # QUARTER-HOME: the piece is beyond every display's reading range — the
    # quarters a trip just pressed are INVISIBLE until the panel is read from the
    # west, and a death out here resets the shape and wastes them. Head home to
    # the changer squares (the panel comes into view on the way); refuel first if
    # the walk does not fit — the east ring is the only fuel on this side.
    if (at is not None and left is not None and getattr(gate, "windowed", False)
            and getattr(gate, "qt_out", False)
            and gate.displays and gate.changers and locked):
        if any(b[0] >= at[0] - 18 and b[1] <= at[0] + 21
               and b[2] >= at[1] - 18 and b[3] <= at[1] + 21
               for b in gate.displays):
            gate.qt_out = False    # home: the panel is in view again
        else:
            homes = {p for p in gate.changers if isinstance(p[0], int)}
            walls_h = {(sq[0] + model.dirs[a][0], sq[1] + model.dirs[a][1])
                       for (sq, a) in tried
                       if (sq, a) not in sure and a in model.dirs} | set(refused)
            leg_h = bfs(grid, model, (at[0], at[1]), homes, redirects,
                        avoid=walls_h)
            if leg_h and len(leg_h) <= left:
                gate.rung = "quarter-home"
                return leg_h, None
            top_h, f_h = refuel(homes)
            if top_h:
                gate.rung = "quarter-home-fuel"
                return top_h, f_h

    # With more than one half wrong the question is an ORDER, and the rung below cannot
    # ask it: it walks to a changer for whichever wrong half its dict happens to name first.
    # On `ls20` level 5 that is always the cross, so the ink cluster is entered twice in six
    # hundred rounds and the ink half is never worked at all. One wrong half has no order to
    # get wrong, and level 2 needs the rung below — it costs a changer one extra turn there,
    # and that level needs three.
    if (at and not doors and locked and full and left is not None
            and len(gate.wrong_halves(locked[0])) > 1):
        here = (at[0], at[1])
        def _spent_o(o):
            return any(o["x"][0] <= sx + 4 and o["x"][1] >= sx
                       and o["y"][0] <= sy + 4 and o["y"][1] >= sy
                       for sx, sy in getattr(gate, "spent", ()))

        fuel = [o for o in cands if o["colour"] in tank and not _spent_o(o)]
        if not fuel and tank:
            fuel = sorted((o for o in seen if o["colour"] in tank and not _spent_o(o)),
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
        leg = [] if here == turn else bfs(grid, model, here, {turn},
                                          avoid=refused)
        # One more turn of the display, and then somewhere this life can still get to:
        # the door it is opening, or a refill. Demanding the DOOR is too strict — it is 20
        # actions away on `ls20` level 2 and a life is 21, which is what the refills are
        # for — and demanding nothing at all walks 17 actions to the changer, turns the
        # glyph to the one the goal box wants, and starves on the action it matched.
        outs = [locked[0]] + [o for o in cands if o["colour"] in tank]
        rest = None if leg is None else \
            min((len(r) for o in outs if (r := onward(turn, o)) is not None),
                default=None)
        if os.environ.get("ARC_TWDBG"):
            print("[tw] at=%s turn=%s leg=%s rest=%s left=%s outs=%d wrong=%s" % (
                (at[0], at[1]), turn, None if leg is None else len(leg), rest, left,
                len(outs), sorted(gate.wrong_halves(locked[0]))))
        if leg is not None and rest is not None \
                and (left is None or len(leg) + 2 + rest <= left):
            parked = False
            if getattr(gate, "windowed", False) and gate.state():
                cur_state = min(gate.state())
                for hh in gate.wrong_halves(locked[0]):
                    if not isinstance(cur_state[hh], str):
                        continue
                    tables = gate._edges(hh)
                    if (cur_state[hh] not in {a for t in tables.values() for a in t}
                            and cur_state[hh] in {b for t in tables.values()
                                                  for b in t.values()}):
                        parked = True
            if os.environ.get("ARC_PWDBG") and gate.state():
                print("[pw] at=%s parked=%s left=%s state=%s wrongs=%s" % (
                    at[:2] if at is not None else None, parked, left,
                    sorted(map(str, gate.state()))[:1],
                    sorted(gate.wrong_halves(locked[0]))))
            if parked and left is not None:
                # The panel wears a value no press has ever moved (seen as a TO,
                # no outgoing edge). Measured law: this press fires only on an
                # EVEN patroller phase; every walked arrival here has ODD
                # moves-since-death (the lattice is bipartite, and a death resets
                # the patroller's lap); the only parity-flipper is a carry of ODD
                # length. Walk into one — or refuel toward one — and come back.
                # The stored offset is measured from the AIM cell, one step past
                # the square the piece stood on — total displacement is one step
                # PLUS the offset, so an odd carry is one whose offset is EVEN.
                odd_cells = [c for src2 in (redirects, once or {})
                             for c, off in src2.items()
                             if isinstance(c[0], int)
                             and ((abs(off[0]) + abs(off[1])) // 5) % 2 == 0]
                for cell in sorted(set(odd_cells),
                                   key=lambda c: abs(c[0] - at[0]) + abs(c[1] - at[1])):
                    leg2 = bfs(grid, model, (at[0], at[1]), {cell}, redirects)
                    if leg2 and len(leg2) + 8 <= left:
                        gate.rung = "parity-walk"
                        return leg2, None
                if odd_cells:
                    top2, f2 = refuel(set(odd_cells))
                    if top2:
                        gate.rung = "parity-fuel"
                        return top2, f2
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
                steps = cycle(grid, model, here, redirects)
                # On a windowed board a changer can be phase-gated: the ring press
                # fires every second MOVE, so a single bounce landing on the wrong
                # tick changes nothing — while continuous oscillation walks the whole
                # six-state ring without one no-op (`results/l7-hashpress.txt`). While
                # a wrong half is unplannable but its graph is still OPEN, commit
                # three bounces instead of one: the round-churn after a lone no-op
                # bounce is what left the ring unclosed at 4 edges for 800 ticks.
                if steps and getattr(gate, "windowed", False) and left is not None:
                    wrong = gate.wrong_halves(locked[0])
                    blind = any(gate.path_for(locked[0], h) is None
                                and not gate.exhausted(locked[0], h) for h in wrong)
                    if blind and 3 * len(steps) + rest <= left:
                        return steps * 3, None
                return steps, None
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
        def _spent_o(o):
            return any(o["x"][0] <= sx + 4 and o["x"][1] >= sx
                       and o["y"][0] <= sy + 4 and o["y"][1] >= sy
                       for sx, sy in getattr(gate, "spent", ()))

        fuel = [o for o in cands if o["colour"] in tank and not _spent_o(o)]
        if not fuel and tank:
            fuel = sorted((o for o in seen if o["colour"] in tank and not _spent_o(o)),
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

    # The held-back learn trip (windowed boards only): every square rung above had its
    # chance at this round and none had a plan, so go and press something unwatched
    # rather than fall to rarity.
    if learn6:
        gate.trip = learn6[1]
        gate.rung = "moving-learn"
        return learn6[0], None

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


def stitch(obs, world, at, model, rows=HUD_ROW, boxes=()):
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
        # A display's OFF pixels are state, not fog. A glyph pixel that turns off goes
        # non-5 → 5, which the dirty test below (non-5 → different non-5) cannot see,
        # so the remembered ON pixel was painted back INSIDE the window and the
        # indicator read as the UNION of its states on the press tick itself
        # (reproduced raw-vs-composite in `results/ug-repro.txt`; a "late report"
        # suppressor keyed on the box re-entering reading range was byte-identical
        # three times because that is not when the garble happens). Both WHOLE-WINDOW
        # repairs measure worse than the disease — in-window paint-back is legitimate
        # behind walls ("clipped by the world's own walls", measured at y17/y22) —
        # so the rule is scoped to the plate boxes the gate knows, fully in view:
        # record their 5s as KNOWN 5s, and painting 5 into 5 is a no-op forever.
    else:
        # No piece found on this frame means no way to keep its own cells out of the
        # memory — and a remembered piece cell is LITTER: one colour-12 pixel beside
        # the bare indicator merges into its glyph, the garble reads as a shape
        # CHANGE, and the phantom edge lands under whatever square the piece stood
        # on (the ink block once carried five shape edges that way, and the planner
        # then pressed it ninety times to fix the shape half). Absorb nothing.
        seen[:] = False
    # A cell that comes back DIFFERENT is not terrain: something moves there. Painting a
    # remembered copy of a moving object into the fog is worse than leaving the fog — the
    # tracker then follows a ghost standing still at the last place the object was seen,
    # and on level 7 that is why 25 to 61 objects were tracked with full histories and not
    # one of them ever earned a period.
    dirty[:rows] |= seen & (known[:rows] >= 0) & (known[:rows] != grid[:rows])
    known[:rows][seen] = grid[:rows][seen]
    for x0, x1, y0, y1 in boxes:
        if at is not None and x0 >= at[0] - 18 and x1 <= at[0] + 21 \
                and y0 >= at[1] - 18 and y1 <= at[1] + 21:
            reg = (slice(y0, min(y1 + 1, rows)), slice(x0, x1 + 1))
            known[reg][grid[reg] == 5] = 5
    fog = (grid[:rows] == 5) & (known[:rows] >= 0) & ~dirty[:rows]
    if os.environ.get("ARC_UGDBG") and at is not None:
        win = np.zeros_like(fog)
        win[max(0, at[1] - 18):at[1] + 22, max(0, at[0] - 18):at[0] + 22] = True
        inwin = fog & win
        if inwin.any():
            ys, xs = np.nonzero(inwin)
            print("[ug] at=%s paintback-in-window n=%d cells=%s"
                  % (at[:2], len(xs), list(zip(xs.tolist(), ys.tolist()))[:14]))
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
                if os.environ.get("ARC_PDBG"):
                    print("[pd] i=%d src=%s reason=expect here=%s wanted=%s left=%d"
                          % (i, psrc, (here[0], here[1]), expect[0], len(plan)))
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
        tankc = tank_colours(log, gate)
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
                tankc = tank_colours(log, gate)
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
            gate._fresh.clear()    # a kept reading from before the reset spans it
            gate.spent.clear()     # the rings respawn with the life
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
                # displays ONLY, not every icon: a STATIC plate's fogged pixels are
                # exactly what the paint-back stabilises (the door's ask-picture is
                # partially fogged from positions the ±18/21 test calls readable —
                # measured: its (32,53) pixel is visible at dx=13 and fog at dx=18,
                # the window is wall-clipped, not square). Recording those as OFF
                # made the box flicker with the piece, 85 phantom edges in one run.
                # A box that has actually CHANGED is the one whose off-pixels are
                # state — and it changes ink before it ever changes shape, so it is
                # in `displays` before the first union pixel can exist.
                world = stitch(obs, world, locate(obs.frame, model), model, rows,
                               boxes=gate.displays)
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
                # ...and an object that vanished UNDER the piece while the clock did not
                # rise is occluded, not gone: the piece walking past a refill ring hides
                # it for a step, and each of those counted against colour 11 until
                # `seen_without` outgrew `seen_with` and the detector withdrew the one
                # refill colour it had — with=58 against without=68 by the end of a run.
                # A pickup is occlusion WITH the clock rising, so those keep counting.
                falls = set(drain(log[-CLOCK_WINDOW:]))
                rose = any(row["hud"].get(str(k), [0, 0])[1] > row["hud"].get(str(k), [0, 0])[0]
                           for k in falls)
                pat = locate(obs.frame, model)
                if pat is not None and not rose:
                    px, py = pat[0], pat[1]
                    pw, ph = (pat[2], pat[3]) if len(pat) > 3 else (5, 5)
                    row["gone"] = [g for g in row["gone"]
                                   if not (px - 4 <= g[1] <= px + pw + 4
                                           and py - 4 <= g[2] <= py + ph + 4)]
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
                gate.track(cur, model.body, moved, here_after, colours)
                # pay down the chase: a footprint overlap with the lap's track after a
                # move IS a press (the measured law); counted live, no display needed
                # INTERCEPT: unpaid quarters, on the lap line, live track in
                # sight — drop whatever plan is running so the chase rung gets
                # the round; a multi-action plan otherwise holds the executor
                # through the whole traversal and the chase can never steer.
                if (gate.qt_need > gate.qt_hits and here_after is not None
                        and getattr(gate, "lapmem", None) and plan):
                    xs_i = [L[0] for L in gate.lapmem]
                    ys_i = [L[1] for L in gate.lapmem]
                    vert_i = (max(ys_i) - min(ys_i)) >= (max(xs_i) - min(xs_i))
                    ax_i = (sum(xs_i) / len(xs_i)) if vert_i else (sum(ys_i) / len(ys_i))
                    on_i = abs((here_after[0] if vert_i else here_after[1]) + 2 - ax_i) <= 7
                    _lo3 = (min(ys_i) if vert_i else min(xs_i)) - 5
                    _hi3 = (max(ys_i) if vert_i else max(xs_i)) + 8
                    if on_i and any(
                            _inf.get("hist") and _inf["hist"][-1][0] >= gate.ticks - 1
                            and any(_inf["hist"][-1][1][0] < L[0] + L[2]
                                    and _inf["hist"][-1][1][0] + _inf["hist"][-1][1][2] > L[0]
                                    for L in gate.lapmem)
                            and _lo3 <= (_inf["hist"][-1][1][1] if vert_i
                                         else _inf["hist"][-1][1][0]) <= _hi3
                            for _inf in gate.movers.values()):
                        plan, expect, trip = [], [], []
                if gate.qt_need > gate.qt_hits and here_after is not None:
                    for _k, _info in gate.movers.items():
                        _h = _info.get("hist") or []
                        # an overlap COVERS the patroller, so the sighting that
                        # would prove the hit is exactly the one perception
                        # loses — project the last sighting forward by its own
                        # velocity instead of demanding one this tick
                        if _h and _h[-1][0] >= gate.ticks - 2:
                            _b = _h[-1][1]
                            _age = gate.ticks - _h[-1][0]
                            if _age and len(_h) >= 2:
                                _pb = _h[-2][1]
                                _dx, _dy = _b[0] - _pb[0], _b[1] - _pb[1]
                                if abs(_dx) <= 5 and abs(_dy) <= 5:
                                    _b = (_b[0] + _age * _dx, _b[1] + _age * _dy,
                                          _b[2], _b[3])
                            _ls = getattr(gate, "lapmem", ())
                            _ok_span = False
                            if _ls:
                                _ys = [L[1] for L in _ls]; _xs = [L[0] for L in _ls]
                                _v = (max(_ys) - min(_ys)) >= (max(_xs) - min(_xs))
                                _lo = (min(_ys) if _v else min(_xs)) - 5
                                _hi = (max(_ys) if _v else max(_xs)) + 8
                                _ok_span = _lo <= (_b[1] if _v else _b[0]) <= _hi
                            if (_ok_span
                                    and here_after[0] < _b[0] + _b[2] and here_after[0] + 5 > _b[0]
                                    and here_after[1] < _b[1] + _b[3] and here_after[1] + 5 > _b[1]
                                    and any(_b[0] < L[0] + L[2] and _b[0] + _b[2] > L[0]
                                            for L in _ls)):
                                gate.qt_hits += 1
                                if gate.qt_hits >= gate.qt_need:
                                    # paid — go HOME and READ before trusting
                                    # it: a projected-box hit is a count, not a
                                    # confirmed press, and the door judges the
                                    # ENGINE's panel, not ours
                                    gate.qt_out = True
                                if os.environ.get("ARC_QTDBG"):
                                    print("[ch] HIT a=%d at=%s box=%s hits=%d/%d"
                                          % (i, here_after[:2], _b,
                                             gate.qt_hits, gate.qt_need))
                                break
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
                if l6 and done == L6LVL:
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
                # ...unless the display itself is under the fog of a windowed board:
                # a press out there really does move the panel, and `plates` really
                # cannot see it, so disagreement is blindness rather than refutation.
                # The position check below still validates every step of the walk.
                seen_disp = True
                if windowed and raw5 is not None:
                    for (x0, x1, y0, y1) in gate.displays:
                        if raw5[y0:y1 + 1, x0:x1 + 1].any():
                            seen_disp = False
                            break
                if mark is not None and changed != mark and seen_disp:
                    if os.environ.get("ARC_PDBG"):
                        print("[pd] i=%d src=%s reason=display left=%d" % (i, psrc, len(plan)))
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
            # A refill eaten is spent for the rest of this LIFE (they respawn with the
            # next one). The clock rising on an ordinary walked step is a pickup —
            # rising on a teleport is a death, which the slid branch below handles.
            if getattr(gate, "windowed", False) and log and log[-1].get("walked")                     and now is not None:
                _falls = set(drain(log[-CLOCK_WINDOW:]))
                if any(hud(obs.frame).get(k, 0) > hud(before.frame).get(k, 0)
                       for k in _falls):
                    gate.spent.add((now[0], now[1]))
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
                    # And the fresh-read ledger: a display reading from before this
                    # death must never be the OLD half of a booked edge (the panel
                    # reset would be folded into the transition — the phantom shape
                    # edges the ink square kept collecting, equality-hole included:
                    # a death on a blocked action leaves `ticks` flat, so a tick
                    # comparison cannot see it).
                    gate._fresh.clear()
                    gate.spent.clear()
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
                    if os.environ.get("ARC_PDBG") and plan:
                        print("[pd] i=%d src=%s reason=slid now=%s left=%d"
                              % (i, psrc, (now[0], now[1]), len(plan)))
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
            if os.environ.get("ARC_PDBG") and plan:
                print("[pd] i=%d src=%s reason=refused left=%d" % (i, psrc, len(plan)))
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
                if l6 and done == L6LVL:
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
