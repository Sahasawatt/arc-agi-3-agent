"""Tests for autonomous mechanic discovery.

The inference functions are pure — they take recorded observations and return a model —
so they can be tested against hand-built evidence with no engine running. Each expected
value here is worked out by hand from the fixture, not by calling the code under test.
"""

import numpy as np
import pytest

from discover import (Model, body_box, choose_action, classify_colours, dest_colours,
                      choose_next, choose_probe, infer_body, infer_dirs, infer_player, infer_step,
                      locate, terrain_samples, walkable)


# --- infer_player ------------------------------------------------------------------

def test_player_is_the_thing_that_moves():
    """Two objects on screen; only one ever shifts."""
    records = [
        {"action": 1, "shifts": {("orange", 25): (0, -5)}},
        {"action": 2, "shifts": {("orange", 25): (0, 5)}},
    ]
    assert infer_player(records) == ("orange", 25)


def test_player_beats_a_distractor_that_moves_once():
    """A patrolling enemy or an animated tile also moves. The player moves under *every*
    action, so it wins on count."""
    records = [
        {"action": 1, "shifts": {("hero", 9): (0, -3), ("enemy", 4): (3, 0)}},
        {"action": 2, "shifts": {("hero", 9): (0, 3)}},
        {"action": 3, "shifts": {("hero", 9): (-3, 0)}},
    ]
    assert infer_player(records) == ("hero", 9)


def test_no_player_when_nothing_moved():
    assert infer_player([{"action": 1, "shifts": {}}]) is None


# --- choose_action -----------------------------------------------------------------
# Cycling the actions in order is worse than useless on a grid game: up, down, left,
# right returns the piece to where it started, so 48 actions produced 47 successful
# moves and met a wall once. Walls are only learnable from blocked moves, so the walk
# has to actually go somewhere.

def test_chooser_takes_an_untried_action_first():
    assert choose_action({}, "stateA", [1, 2, 3, 4]) == 1


def test_chooser_moves_on_from_an_action_already_tried_here():
    assert choose_action({("stateA", 1): 1}, "stateA", [1, 2, 3, 4]) == 2


def test_chooser_spreads_across_the_action_set_in_a_fresh_state():
    """Every successful move lands somewhere nothing has been tried, so breaking the tie
    on the action's number walks in a straight line — 48 actions on `sp80` used one of
    its five and never learned what the other four do."""
    assert choose_action({("stateA", 1): 3}, "stateB", [1, 2, 3, 4]) == 2


def test_state_novelty_outranks_global_coverage():
    """Action 2 is the more-used one overall, but it is untried *here*, and what is
    untried here is what can still surprise us."""
    visits = {("stateA", 1): 1, ("stateC", 2): 3}
    assert choose_action(visits, "stateA", [1, 2]) == 2


def test_chooser_repeats_only_once_everything_here_is_tried():
    visits = {("stateA", a): 1 for a in (1, 2, 3, 4)}
    visits[("stateA", 1)] = 2
    assert choose_action(visits, "stateA", [1, 2, 3, 4]) == 2


# --- choose_probe ------------------------------------------------------------------
# Wandering finds walls only by accident: with the action set covered evenly the piece
# moves freely and 48 actions produced walls on 2 of 9 games. Once the directions are
# known the map itself says where the unanswered question is.

def _open(colour=7, size=10):
    return np.full((size, size), colour, dtype=int)


def test_probe_prefers_the_direction_showing_an_unclassified_colour():
    grid = _open()
    grid[:, 4] = 3                       # unknown colour to the right of a piece at x=2
    dirs = {1: (0, -1), 4: (1, 0)}
    assert choose_probe(grid, (2, 2, 2, 2), dirs, known={7}, actions=[1, 4]) == 4


def test_probe_declines_when_everything_in_reach_is_already_known():
    assert choose_probe(_open(), (2, 2, 2, 2), {1: (0, -1), 4: (1, 0)},
                        known={7}, actions=[1, 4]) is None


def test_probe_skips_actions_with_no_known_direction_and_off_board_moves():
    grid = _open()
    grid[:, 4] = 3
    dirs = {4: (1, 0), 9: (1, 0)}        # 9 has a direction; 5 does not
    assert choose_probe(grid, (8, 2, 2, 2), dirs, known={7}, actions=[5]) is None


# --- choose_next -------------------------------------------------------------------
# Probe first, then keep pushing, then go somewhere new. The middle rung is what turns
# walls from an accident into a measurement.

def test_next_prefers_an_informative_probe_over_momentum():
    grid = _open()
    grid[:, 4] = 3
    got = choose_next(grid, (2, 2, 2, 2), {1: (0, -1), 4: (1, 0)}, known={7},
                      actions=[1, 4], last=1, visits={}, state="s")
    assert got == 4


def test_next_keeps_pushing_when_nothing_is_left_to_probe():
    """Changing action whenever one fails meets each wall once; committing to a direction
    until it stops working is how a wall gets found on purpose."""
    got = choose_next(_open(), (2, 2, 2, 2), {1: (0, -1), 4: (1, 0)}, known={7},
                      actions=[1, 4], last=4, visits={}, state="s")
    assert got == 4


def test_next_falls_back_to_novelty_before_the_directions_are_known():
    got = choose_next(_open(), None, {}, known=set(), actions=[1, 4],
                      last=None, visits={("s", 1): 1}, state="s")
    assert got == 4


def test_next_does_not_repeat_an_action_with_no_known_direction():
    """Novelty here prefers 1, so momentum firing on 4 would be visible."""
    got = choose_next(_open(), (2, 2, 2, 2), {1: (0, -1)}, known={7}, actions=[1, 4],
                      last=4, visits={("s", 4): 1}, state="s")
    assert got == 1


# --- infer_body --------------------------------------------------------------------
# The piece can be drawn in several colours, so perception splits it into several
# components. Planning with only one of them measures the wrong footprint: on ls20 the
# orange half is 5x2 while the piece that collides with walls is 5x5.

def _body_rec(shifts, present=None):
    return {"action": 1, "shifts": shifts, "after": set(present or shifts)}


def test_body_is_just_the_player_when_nothing_co_moves():
    p = ("hero", 9)
    records = [_body_rec({p: (0, -3)})]
    assert infer_body(records, p) == {p}


def test_body_absorbs_a_component_that_always_moves_identically():
    p, half = ("orange", 10), ("blue", 15)
    records = [_body_rec({p: (0, -5), half: (0, -5)}),
               _body_rec({p: (5, 0), half: (5, 0)})]
    assert infer_body(records, p) == {p, half}


def test_body_excludes_a_component_that_only_sometimes_agrees():
    """An enemy drifting the same way once is a coincidence, not part of the piece."""
    p, enemy = ("hero", 9), ("enemy", 4)
    records = [_body_rec({p: (0, -3), enemy: (0, -3)}, present=[p, enemy]),
               _body_rec({p: (0, -3)}, present=[p, enemy]),
               _body_rec({p: (3, 0), enemy: (0, -3)}, present=[p, enemy])]
    assert infer_body(records, p) == {p}


def test_body_survives_a_single_frame_where_perception_missed_a_part():
    """Demanding agreement on *every* move is too strict once identity is tracked: one
    frame where a part is not matched dropped it forever, and every game came back with
    a one-part body — on ls20 that shrank the footprint from 5x5 to 5x2 and then
    reported the piece's own second colour as a wall."""
    p, half = ("orange", 10), ("blue", 15)
    records = [_body_rec({p: (0, -5), half: (0, -5)}) for _ in range(9)]
    records.append(_body_rec({p: (0, -5)}, present=[p, half]))   # one miss in ten
    assert infer_body(records, p) == {p, half}


def test_body_keeps_a_part_whose_track_split_into_two_ids():
    """The measured ls20 failure. The piece's second half lost its track once and came
    back under a new id, so its agreement was split 171/106 across the player's 278
    moves — neither half clears any whole-run threshold, and the 5x5 piece was reported
    as a 5x2 fragment whose own second colour then read as a wall. Judged against the
    frames each id was visible in, both are at 1.00."""
    p, first, second = ("orange", 10), ("blue-a", 15), ("blue-b", 15)
    records = [_body_rec({p: (0, -5), first: (0, -5)}, present=[p, first]) for _ in range(6)]
    records += [_body_rec({p: (0, -5), second: (0, -5)}, present=[p, second]) for _ in range(4)]
    assert infer_body(records, p) == {p, first, second}


def test_body_still_excludes_a_bystander_that_is_always_visible():
    """The guard on the rule above: presence-relative scoring must not let something that
    is on screen the whole time and rarely agrees sneak in."""
    p, drifter = ("hero", 9), ("cloud", 4)
    records = [_body_rec({p: (0, -3), drifter: (0, -3)}, present=[p, drifter])]
    records += [_body_rec({p: (0, -3)}, present=[p, drifter]) for _ in range(9)]
    assert infer_body(records, p) == {p}


def test_body_box_is_the_union_bounding_box():
    boxes = {("orange", 10): (10, 20, 5, 2), ("blue", 15): (10, 22, 5, 3)}
    assert body_box(boxes, {("orange", 10), ("blue", 15)}) == (10, 20, 5, 5)


def test_body_box_ignores_a_member_that_is_off_screen_this_frame():
    boxes = {("orange", 10): (10, 20, 5, 2)}
    assert body_box(boxes, {("orange", 10), ("gone", 3)}) == (10, 20, 5, 2)


# --- infer_dirs / infer_step -------------------------------------------------------

def test_dirs_take_the_mode_not_the_last_value():
    """One noisy sample (a knock-back, a mis-matched object) must not redefine an action."""
    p = ("hero", 9)
    records = [
        {"action": 1, "shifts": {p: (0, -3)}},
        {"action": 1, "shifts": {p: (0, -3)}},
        {"action": 1, "shifts": {p: (0, -9)}},   # outlier
        {"action": 4, "shifts": {p: (3, 0)}},
    ]
    assert infer_dirs(records, p) == {1: (0, -3), 4: (3, 0)}


def test_blocked_attempts_do_not_define_a_direction():
    p = ("hero", 9)
    records = [{"action": 2, "shifts": {}}, {"action": 2, "shifts": {p: (0, 2)}}]
    assert infer_dirs(records, p) == {2: (0, 2)}


@pytest.mark.parametrize("dirs, expected", [
    ({1: (0, -5), 2: (0, 5), 3: (-5, 0), 4: (5, 0)}, 5),      # ls20
    ({1: (0, -2), 4: (4, 0)}, 2),                              # gcd, not the mode
    ({1: (0, -3), 2: (0, 3)}, 3),
    ({}, None),
])
def test_step_is_the_gcd_of_every_displacement(dirs, expected):
    assert infer_step(dirs) == expected


# --- classify_colours --------------------------------------------------------------

def test_a_colour_walked_over_is_passable_even_if_also_seen_when_blocked():
    """Floor tiles appear in the destination of a blocked move too — the wall is what is
    different about that destination. Success is the stronger evidence."""
    samples = [(frozenset({7}), True)] * 2 + [(frozenset({7, 4}), False)] * 2
    passable, blocking = classify_colours(samples)
    assert passable == {7}
    assert blocking == {4}


def test_colour_only_ever_seen_on_blocked_moves_is_blocking():
    samples = [(frozenset({4}), False)] * 2 + [(frozenset({9}), False)] * 2
    passable, blocking = classify_colours(samples)
    assert passable == set()
    assert blocking == {4, 9}


def test_no_evidence_means_no_claim():
    assert classify_colours([]) == (set(), set())


# --- terrain_samples ---------------------------------------------------------------
# ls20 gives 21 actions per life and then respawns the piece at the start. That jump is a
# displacement, so counting "it moved" as "it walked there" taught the walker that the
# wall colour was floor. Only a displacement equal to the action's own direction is
# evidence about the terrain in front of the piece.

def _rec(action, delta, at=(0, 0, 1, 1)):
    p = ("hero", 9)
    return {"action": action, "shifts": {p: delta} if delta else {}, "boxes": {p: at},
            "after": {p}, "grid": np.array([[7, 4], [7, 4]])}


def test_a_move_matching_the_action_direction_is_walked_evidence():
    p = ("hero", 9)
    got = terrain_samples([_rec(1, (1, 0))], p, {p}, {1: (1, 0)})
    assert got == [(frozenset({4}), True)]


def test_no_movement_is_blocked_evidence():
    p = ("hero", 9)
    got = terrain_samples([_rec(1, None)], p, {p}, {1: (1, 0)})
    assert got == [(frozenset({4}), False)]


def test_losing_sight_of_the_piece_is_not_a_blocked_move():
    """Objects are matched across a step by colour *and* cell count, so a piece that
    changes size drops out of the match entirely. Reading that as "it did not move"
    invented 25 blocked moves on `sc25` whose destinations were plain floor."""
    p = ("hero", 9)
    rec = _rec(1, None)
    rec["after"] = set()                       # the piece is not in the next frame's index
    assert terrain_samples([rec], p, {p}, {1: (1, 0)}) == []


def test_a_displacement_that_is_not_the_action_direction_teaches_nothing():
    """A respawn, a knock-back or a conveyor. The piece is not where the move would
    have put it, so the destination it did not enter proves nothing either way."""
    p = ("hero", 9)
    assert terrain_samples([_rec(1, (0, 40))], p, {p}, {1: (1, 0)}) == []


# --- dest_colours ------------------------------------------------------------------

def test_dest_colours_excludes_the_players_own_colours():
    """When the step is smaller than the piece, the destination overlaps the piece itself.
    Seeing your own body is not evidence about the terrain."""
    grid = np.full((10, 10), 7, dtype=int)
    grid[2:4, 2:4] = 12          # the piece, 2x2 at (2,2)
    grid[2:4, 3] = 12
    got = dest_colours(grid, x=2, y=2, w=2, h=2, dx=1, dy=0)
    assert got == frozenset({7})


def test_dest_colours_subtracts_the_bodys_colours_not_the_whole_box():
    """A piece that does not fill its bounding box has background inside the box. Taking
    `own` from the box then subtracts the floor from every destination and the evidence
    comes back empty — 38 of 38 observations on `ar25`."""
    grid = np.full((10, 10), 7, dtype=int)
    grid[2, 2] = 5                       # a sparse piece: one cell of colour 5 ...
    grid[4, 4] = 5                       # ... and another, box (2,2)-(4,4) full of floor
    assert dest_colours(grid, 2, 2, 3, 3, 3, 0) == frozenset()
    assert dest_colours(grid, 2, 2, 3, 3, 3, 0, own={5}) == frozenset({7})


def test_dest_colours_is_none_off_the_board():
    grid = np.full((10, 10), 7, dtype=int)
    assert dest_colours(grid, x=8, y=0, w=2, h=2, dx=1, dy=0) is None


# --- walkable ----------------------------------------------------------------------

def _model(**kw):
    base = dict(player=1, body={1}, colour=9, box=(2, 2), dirs={1: (0, -2)}, step=2,
                passable={7}, blocking={4}, rows=10)
    return Model(**{**base, **kw})


def test_walkable_rejects_a_footprint_touching_a_blocking_colour():
    grid = np.full((10, 10), 7, dtype=int)
    grid[5, 5] = 4
    m = _model()
    assert walkable(grid, m, 4, 4) is False   # footprint (4,4)-(5,5) covers the wall
    assert walkable(grid, m, 0, 0) is True


def test_walkable_rejects_off_board_and_the_hud_strip():
    grid = np.full((10, 10), 7, dtype=int)
    m = _model(rows=8)
    assert walkable(grid, m, -1, 0) is False
    assert walkable(grid, m, 9, 0) is False   # 9+2 > 10
    assert walkable(grid, m, 0, 7) is False   # 7+2 > rows=8, into the HUD


# --- locate ------------------------------------------------------------------------
# A model is built from track ids, and those die with the board they were made on. To
# be usable on the next level — or in a scored run at all — the piece has to be
# recognisable from what it looks like.

def _frame(rows=60, cols=64, fill=7):
    return [np.full((rows + 4, cols), fill, dtype=int)]


def _paint(frame, colour, x, y, w, h):
    frame[0][y:y + h, x:x + w] = colour


def _model_with(parts, box):
    return Model(player=1, body={1}, colour=parts[0][0], parts=parts, box=box,
                 dirs={1: (0, -5)}, step=5, passable=set(), blocking=set(), rows=60)


def test_locate_finds_a_two_part_piece_and_returns_the_union_box():
    f = _frame()
    _paint(f, 12, 30, 40, 5, 2)
    _paint(f, 9, 30, 42, 5, 3)
    m = _model_with(((9, 5, 3), (12, 5, 2)), (5, 5))
    assert locate(f, m) == (30, 40, 5, 5)


def test_locate_returns_none_when_the_piece_is_not_on_screen():
    m = _model_with(((9, 5, 3), (12, 5, 2)), (5, 5))
    assert locate(_frame(), m) is None


def test_locate_ignores_a_matching_shape_on_the_far_side_of_the_board():
    """Another object of the same colour and size elsewhere must not stretch the box
    across half the board."""
    f = _frame()
    _paint(f, 12, 30, 40, 5, 2)
    _paint(f, 9, 30, 42, 5, 3)
    _paint(f, 12, 2, 2, 5, 2)          # decoy, top-left
    m = _model_with(((9, 5, 3), (12, 5, 2)), (5, 5))
    x, y, w, h = locate(f, m)
    assert (w, h) == (5, 5)
    assert (x, y) in {(2, 2), (30, 40)}   # one piece or the other, never a union of both


# --- explain-away ------------------------------------------------------------------
# A blocked destination usually shows several unfamiliar colours and only one is the
# wall. Taking all of them made dc22 treat colour 9 as solid because it sits beside the
# real wall, sealing the board down to 9 reachable cells.

def test_a_colour_that_never_blocks_alone_is_not_a_wall():
    """dc22 exactly: colour 4 is the only unexplained thing 109 times, colour 9 never."""
    samples = [(frozenset({4}), False)] * 3 + [(frozenset({4, 9}), False)] * 5
    passable, blocking = classify_colours(samples)
    assert blocking == {4}


def test_one_sighting_is_not_enough_to_call_something_a_wall():
    samples = [(frozenset({2}), False)] * 5 + [(frozenset({15}), False)]
    _, blocking = classify_colours(samples)
    assert blocking == {2}


def test_explaining_away_iterates():
    """Once 4 is known, {4,9} is explained; {9,11} then makes 11 the sole candidate."""
    samples = ([(frozenset({4}), False)] * 2 + [(frozenset({4, 9}), False)] * 2
               + [(frozenset({9, 11}), False)] * 2 + [(frozenset({9}), True)])
    passable, blocking = classify_colours(samples)
    assert passable == {9}
    assert blocking == {4, 11}


def test_locate_tolerates_a_part_redrawn_slightly_larger():
    """`ar25` and `sc25` could not find their own piece on the board they started from,
    because an exact size match loses a piece that is redrawn a cell wider."""
    f = _frame()
    _paint(f, 12, 30, 40, 6, 2)          # model says 5x2; this frame draws it 6 wide
    m = _model_with(((12, 5, 2),), (5, 2))
    assert locate(f, m) == (30, 40, 5, 2)


def test_locate_still_refuses_a_completely_different_shape():
    f = _frame()
    _paint(f, 12, 30, 40, 20, 20)
    m = _model_with(((12, 5, 2),), (5, 2))
    assert locate(f, m) is None
