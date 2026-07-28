"""Tests for what a model keeps when the board changes underneath it.

Three separate bugs in this file's subject were each fatal on their own, and all three are
the same shape: the evidence is reset at a level boundary, so the model rebuilt on the new
board knows *less* than the one it replaces — and it replaces it anyway. What a game's
controls do, which colours are solid, and what the piece looks like are properties of the
GAME; only the positions belong to the level.
"""

import numpy as np

from compete import build_model, slid
from discover import Model


PLAYER = ("piece", 25)


def prior(**kw):
    base = dict(player=PLAYER, body={PLAYER}, colour=12, box=(5, 5),
                dirs={1: (0, -5), 2: (0, 5), 3: (-5, 0), 4: (5, 0)}, step=5,
                passable={3}, blocking={4}, rows=60, parts=((12, 5, 2), (9, 5, 3)))
    base.update(kw)
    return Model(**base)


def records(moves, grid=None):
    """Evidence in the shape the play loop records it: one entry per action taken."""
    g = np.full((64, 64), 3) if grid is None else grid
    out = []
    for action, shift in moves:
        out.append({"action": action, "shifts": {PLAYER: shift} if shift else {},
                    "grid": g, "boxes": {PLAYER: (10, 10, 5, 5)}, "after": {PLAYER}})
    return out


def test_a_direction_proven_on_an_earlier_level_survives_a_board_it_was_not_seen_on():
    """`ls20` level 4 rebuilt with two of its four directions, and `walkable` shrank the
    board from 67 reachable positions to three — every route came back None while the piece
    sat still."""
    fresh = records([(2, (0, 5)), (3, (-5, 0)), (2, (0, 5)), (3, (-5, 0))])
    got = build_model(fresh, {PLAYER: 12}, prior=prior())
    assert set(got.dirs) == {1, 2, 3, 4}


def test_the_older_reading_wins_when_the_two_disagree():
    """The prior has already walked three levels. Letting this level override, `infer_dirs`
    read "up" as (-10, -5) off a frame that lied, and the piece sat in a pocket whose only
    exit was up, reporting all four directions blocked."""
    lying = records([(1, (-10, -5)), (1, (-10, -5)), (2, (0, 5)), (2, (0, 5))])
    got = build_model(lying, {PLAYER: 12}, prior=prior())
    assert got.dirs[1] == (0, -5)


def test_a_level_fills_in_a_direction_the_prior_never_saw():
    """Carrying is not freezing: an action the previous level never pressed is still open."""
    fresh = records([(2, (0, 5)), (2, (0, 5)), (5, (0, -5)), (5, (0, -5))])
    got = build_model(fresh, {PLAYER: 12}, prior=prior(dirs={2: (0, 5)}))
    assert got.dirs[5] == (0, -5) and got.dirs[2] == (0, 5)


def test_a_new_board_keeps_the_previous_level_s_walls_until_it_finds_its_own():
    """A model rebuilt from an empty record has seen no blocked move, so `blocking` comes
    back empty and every plan routes straight through a wall — on `ls20` level 2 that turned
    a 16-action walk into a 5-action plan that spent its life bumping into one."""
    fresh = records([(2, (0, 5)), (2, (0, 5))])
    got = build_model(fresh, {PLAYER: 12}, prior=prior())
    assert got.blocking == {4}


def test_the_piece_s_appearance_is_kept_when_the_track_ids_churn():
    """`parts` is how `locate` recognises the piece on a board the model was not built from,
    and it comes out empty whenever the body's track ids churn. A model that cannot find its
    own piece plans nothing at all — fifty actions of `ls20` level 2 spent blind."""
    fresh = records([(2, (0, 5)), (2, (0, 5))])
    for r in fresh:
        r["boxes"] = {}                      # the ids the body is written in are gone
    got = build_model(fresh, {}, prior=prior())
    assert got is None or got.parts == prior().parts


def test_nothing_is_inherited_when_there_is_no_previous_level():
    """The first board of a game has no prior, and must not be handed one by accident."""
    fresh = records([(2, (0, 5)), (2, (0, 5)), (3, (-5, 0)), (3, (-5, 0))])
    got = build_model(fresh, {PLAYER: 12})
    assert set(got.dirs) == {2, 3} and got.blocking == set()


# --- a step that lands somewhere else --------------------------------------------------
# `ls20` level 4 carries the piece past the square the action asked for. The plan behind it
# is then aimed from a square the piece is not on, so it has to be dropped — but only when
# the piece MOVED somewhere unexpected. A piece that did not move at all keeps its plan;
# dropping it there is the rule that cost `cd82` its only level.

def test_a_slide_is_told_from_a_block_and_from_an_ordinary_step():
    m = prior()
    # measured on ls20 level 4: press 4 at (14,35) landed at (19,45), not (19,35)
    assert slid(m, (14, 35, 5, 5), (19, 45, 5, 5), 4)
    # and press 1 at (24,45) landed at (9,40), not (24,40)
    assert slid(m, (24, 45, 5, 5), (9, 40, 5, 5), 1)
    # an ordinary step is not a slide...
    assert not slid(m, (14, 35, 5, 5), (19, 35, 5, 5), 4)
    # ...and neither is a refusal, which is the case that cost `cd82` its only level
    assert not slid(m, (14, 35, 5, 5), (14, 35, 5, 5), 4)
    # a piece the tracker lost is not evidence of anything
    assert not slid(m, None, (14, 35, 5, 5), 4)


# --- confirming a cell that moves the piece ---------------------------------------------
# `ls20` level 4's floor carries the piece from certain cells. A map of them built by
# accident is worse than none: six such cells cut the reachable board from 67 squares to 57
# and put both glyph-changers outside it, while the agent had demonstrably stood on both.

def board():
    g = np.full((64, 64), 4)
    g[1:59, 1:59] = 3
    return g


def test_a_walk_is_planned_that_ends_by_re_aiming_at_the_unvouched_for_cell():
    from compete import confirm
    g, m = board(), prior()
    # (20, 20) sent the piece somewhere once; nothing has confirmed it
    plan = confirm(g, m, (5, 5), once={(20, 20): (0, 10)}, redirects={})
    assert plan, "a route to a square that can aim at the cell must exist on an open board"
    # walking the plan with the plain model must end by aiming exactly at that cell
    pos = (5, 5)
    for a in plan[:-1]:
        dx, dy = m.dirs[a]
        pos = (pos[0] + dx, pos[1] + dy)
    dx, dy = m.dirs[plan[-1]]
    assert (pos[0] + dx, pos[1] + dy) == (20, 20)


def test_a_cell_already_confirmed_is_not_probed_again():
    from compete import confirm
    g, m = board(), prior()
    assert confirm(g, m, (5, 5), once={(20, 20): (0, 10)},
                   redirects={(20, 20): (0, 10)}) is None


def test_nothing_to_confirm_means_no_walk():
    from compete import confirm
    g, m = board(), prior()
    assert confirm(g, m, (5, 5), once={}, redirects={}) is None


def test_a_plan_carries_the_squares_it_is_aimed_from():
    """A plan is only worth its next action while the piece stands where that action was
    aimed from. Carrying the squares is what lets the next step be checked instead of
    assumed — and the trajectory has to account for the cells that carry the piece, or the
    check fires on every step of a route that is going exactly to plan."""
    from compete import trajectory
    m = prior()
    # plain board: three steps right from (5, 5)
    assert trajectory(m, (5, 5, 5, 5), [4, 4, 4]) == [(5, 5), (10, 5), (15, 5)]
    # with (10, 5) known to carry the piece ten further down, the rest is aimed from there
    got = trajectory(m, (5, 5, 5, 5), [4, 4], {(10, 5): (0, 10)})
    assert got == [(5, 5), (10, 15)]


# --- who the piece is ---------------------------------------------------------------------
# A level boundary resets the evidence, so the first model rebuilt on the new board is
# inferred from one or two actions. On `ls20` level 5 that was enough to name a stray 1x1
# pixel as the player: every position the planner read was that pixel's, three cells off the
# five-cell lattice the piece moves on, and 352 planning rounds went to a board that was not
# there. What the piece looks like is a property of the GAME, like what the controls do.

def frame_with_piece(present=True):
    """A frame in the engine's shape, with the two-part piece drawn on an open board."""
    g = np.full((64, 64), 3)
    if present:
        g[10:12, 10:15] = 12          # the 5x2 half
        g[12:15, 10:15] = 9           # the 5x3 half
    return [g.tolist()]


def test_a_thin_new_level_does_not_get_to_rename_the_piece():
    from compete import keep_identity
    fresh = prior(parts=((1, 1, 1),), box=(1, 1))
    assert keep_identity(fresh, prior(), frame_with_piece()) is not fresh


def test_the_new_reading_wins_when_the_prior_can_no_longer_find_its_piece():
    """A game that really does change the piece between levels has to be followed."""
    from compete import keep_identity
    fresh = prior(parts=((1, 1, 1),), box=(1, 1))
    assert keep_identity(fresh, prior(), frame_with_piece(present=False)) is fresh


def test_agreement_needs_no_arbitration():
    from compete import keep_identity
    fresh = prior()
    assert keep_identity(fresh, prior(), frame_with_piece()) is fresh
    assert keep_identity(fresh, None, frame_with_piece()) is fresh


# --- not undoing the last move ------------------------------------------------------------

def test_a_route_may_not_begin_by_stepping_back_where_it_came_from():
    """`ls20` level 5 spent twenty actions bouncing between two squares until it starved: a
    floor cell carried the piece back, and the plain route — which does not believe in the
    carry — walked into it again. Refusing to undo the last move breaks the cycle without
    removing any route, since anything reachable through the previous square is reachable
    without it."""
    from plan import bfs
    g, m = board(), prior()
    assert bfs(g, m, (10, 5), {(5, 5)}) == [3]           # straight back, normally
    path = bfs(g, m, (10, 5), {(5, 5)}, came_from=(5, 5))
    assert path and path[0] != 3, "the first action must not return to where it came from"
    pos = (10, 5)
    for a in path:
        dx, dy = m.dirs[a]
        pos = (pos[0] + dx, pos[1] + dy)
    assert pos == (5, 5), "and it still has to get there"


# --- walking to what has never been stood on ----------------------------------------------
# A cell whose carry has not been seen looks like ordinary floor, so it is already inside
# what the map believes it can reach — a frontier defined against that set comes back empty
# every time. `ls20` level 5's ink-changer sits behind exactly one such cell.

def test_an_unreachable_goal_sends_the_piece_somewhere_it_has_never_been():
    from compete import confirm
    g, m = board(), prior()
    # the goal is walled off: no route reaches it, with or without the map
    goals = {(200, 200)}
    walk = confirm(g, m, (5, 5), once={}, redirects={}, goals=goals,
                   stood={(5, 5), (10, 5)})
    assert walk, "there is plenty of board nobody has stood on"
    pos = (5, 5)
    for a in walk:
        dx, dy = m.dirs[a]
        pos = (pos[0] + dx, pos[1] + dy)
    assert pos not in {(5, 5), (10, 5)}, "it must end somewhere new"


def test_a_reachable_goal_is_not_traded_for_exploring():
    """The walk exists to open a way that is shut. While the goal can be reached, spending
    actions on unseen squares is spending them on nothing."""
    from compete import confirm
    g, m = board(), prior()
    assert confirm(g, m, (5, 5), once={}, redirects={}, goals={(20, 20)},
                   stood={(5, 5)}) is None


def test_without_a_record_of_where_it_has_been_it_does_not_guess():
    from compete import confirm
    g, m = board(), prior()
    assert confirm(g, m, (5, 5), once={}, redirects={}, goals={(200, 200)},
                   stood=None) is None
