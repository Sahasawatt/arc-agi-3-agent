"""Tests for reading a target's glyph against what the board is displaying.

The board under test is `ls20` level 2 in miniature: a goal box with a shape inside it, a
plate in the corner showing a different shape, and the rule that the box will not let the
piece in until the two agree. Every shape here is one measured off the real frame.
"""

import numpy as np

from discover import Model
from gate import Gate, cycle, plates

INDICATOR = "###/..#/#.#"   # what ls20 level 2 shows at the start
WANTED = "###/#../#.#"      # what its goal box asks for — the same glyph, a quarter turn on


def blank():
    return np.zeros((64, 64), dtype=int)


def plate(grid, x0, y0, w, h, colour, ink, cells):
    """A framed region of `colour` with `ink` cells drawn strictly inside it."""
    grid[y0:y0 + h, x0:x0 + w] = colour
    for dx, dy in cells:
        grid[y0 + dy, x0 + dx] = ink


def goal_box(grid, x0=13, y0=39, shape=((1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (3, 3))):
    plate(grid, x0, y0, 7, 7, 5, 9, shape)


def panel(grid, shape=((1, 1), (2, 1), (3, 1), (3, 2), (1, 3), (3, 3))):
    plate(grid, 1, 53, 10, 10, 5, 9, shape)


def frame(grid):
    return [grid]


def model(**kw):
    base = dict(player=1, body={1}, colour=12, box=(5, 5),
                dirs={1: (0, -5), 2: (0, 5), 3: (-5, 0), 4: (5, 0)}, step=5,
                passable={3}, blocking={4}, rows=60, parts=((12, 5, 5),))
    base.update(kw)
    return Model(**base)


def obj(x0, x1, y0, y1, colour=5):
    return {"colour": colour, "x": [x0, x1], "y": [y0, y1], "cells": 1}


# --- reading a shape off the board -------------------------------------------------

def test_a_framed_region_with_a_shape_inside_is_a_plate():
    g = blank()
    goal_box(g)
    got = plates(frame(g))
    assert got[(13, 19, 39, 45)] == (9, WANTED)


def test_the_bulk_of_the_board_is_not_a_plate():
    """Without the border test every large component is a plate, because the bounding box
    of anything ragged contains most of the board — the floor would be a plate displaying
    the walls."""
    g = blank()
    g[10:50, 10:50] = 3
    g[20, 20] = 4          # a hole in it, so the region's bbox is not all one colour
    g[10, 10] = 4
    assert plates(frame(g)) == {}


def test_a_plate_is_read_across_the_line_where_the_hud_begins():
    """`ls20` draws its indicator over rows 53 to 62 and the play area stops at row 60. A
    reader that stops there cuts the glyph in half — trap 3 of NOTES-ls20.md, in a new
    disguise."""
    g = blank()
    panel(g)
    assert plates(frame(g))[(1, 10, 53, 62)] == (9, INDICATOR)


def test_a_shape_drawn_at_twice_the_size_compares_equal():
    """The indicator is drawn at 2x the goal marker's scale, which is why comparing cell
    counts conflates different glyphs and comparing raw bitmaps never matches."""
    small, big = blank(), blank()
    plate(small, 20, 20, 5, 5, 5, 9, [(1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (3, 3)])
    plate(big, 20, 20, 9, 9, 5, 9,
          [(x, y) for x0, y0 in [(1, 1), (3, 1), (5, 1), (1, 3), (1, 5), (5, 5)]
           for x in (x0, x0 + 1) for y in (y0, y0 + 1)])
    assert plates(frame(small))[(20, 24, 20, 24)][1] == plates(frame(big))[(20, 28, 20, 28)][1]


# --- locked, matched, and the square that changes it --------------------------------

def test_nothing_is_locked_before_a_display_has_been_seen_to_change():
    """A plate that has never moved is not evidence of a gate; guessing one would refuse
    to walk to the only target on a board that has no gate at all."""
    g = blank()
    goal_box(g)
    panel(g)
    gate = Gate()
    gate.observe(frame(g), (29, 40), True)
    assert not gate.locked(obj(13, 19, 39, 45))
    assert not gate.matched(obj(13, 19, 39, 45))


def test_a_target_wearing_a_shape_the_display_does_not_show_is_locked():
    g = blank()
    goal_box(g)
    panel(g)
    gate = Gate()
    gate.observe(frame(g), (29, 40), True)
    g2 = blank()
    goal_box(g2)
    panel(g2, shape=((1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (3, 1)))  # a quarter turn on
    gate.observe(frame(g2), (49, 45), True)
    assert gate.displays == {(1, 10, 53, 62)}
    assert gate.changer == (49, 45)
    assert gate.locked(obj(13, 19, 39, 45))


def test_a_target_wearing_what_the_display_shows_is_a_door():
    g = blank()
    goal_box(g)
    panel(g)
    gate = Gate()
    gate.observe(frame(g), (29, 40), True)
    g2 = blank()
    goal_box(g2)
    panel(g2, shape=((1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (3, 3)))  # now the box's own
    gate.observe(frame(g2), (49, 45), True)
    assert gate.matched(obj(13, 19, 39, 45))
    assert not gate.locked(obj(13, 19, 39, 45))


def test_a_display_that_changes_while_the_piece_was_teleported_names_no_changer():
    """Running out of budget also rewrites the display and puts the piece back at the
    start. Reading that as a discovery names the starting square as the thing that turns
    the glyph, and the agent then stands there pressing off and on for the rest of the
    level."""
    g = blank()
    panel(g)
    gate = Gate()
    gate.observe(frame(g), (29, 40), True)
    g2 = blank()
    panel(g2, shape=((1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (3, 1)))
    gate.observe(frame(g2), (29, 40), False)
    assert gate.displays and gate.changer is None


def test_a_door_that_refuses_settles_the_state_it_refused_under():
    """Collapsing runs of identical rows and columns is what makes a glyph comparable across
    the two scales it is drawn at, and it throws detail away — so equal is a hypothesis and
    the engine is the oracle. Measured on `ls20` level 3: the box refuses the piece under the
    state its own marker matches exactly."""
    g = blank()
    goal_box(g)
    panel(g, shape=((1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (3, 3)))   # same as the box
    gate = Gate()
    gate.observe(frame(g), (29, 40), True)
    g2 = blank()
    goal_box(g2)
    panel(g2, shape=((1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (3, 1)))  # a turn, so it moved
    gate.observe(frame(g2), (49, 45), True)
    gate.observe(frame(g), (49, 45), True)                             # and back to matching
    door = obj(13, 19, 39, 45)
    assert gate.matched(door)
    gate.reject(door)
    assert not gate.matched(door)


def test_a_refused_state_does_not_un_reject_every_glyph_it_resembles():
    """The door wants one glyph and no other.

    This used to be the opposite assertion. Collapsing runs of identical rows and columns
    made the two drawing scales comparable but not injectively — `#.#/#.#/###` collapsed
    onto `#.#/###` — so an equality was only a hypothesis, and once the engine refused the
    state the bitmaps had agreed on, every glyph that comparison might have confused was
    worth a try. Dividing by the scale the glyph is actually drawn at is exact, so equal
    means equal, and the escape hatch only walks the piece into a shut door wearing a glyph
    that plainly does not match — which is what `ls20` level 5 spends its lives doing.
    """
    g = blank()
    goal_box(g)
    panel(g, shape=((1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (3, 3)))
    gate = Gate()
    gate.observe(frame(g), (29, 40), True)
    g2 = blank()
    goal_box(g2)
    panel(g2, shape=((1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (3, 1)))
    gate.observe(frame(g2), (49, 45), True)
    gate.observe(frame(g), (49, 45), True)
    door = obj(13, 19, 39, 45)
    gate.reject(door)                        # refused under the state the bitmaps agreed on
    gate.observe(frame(g2), (49, 45), True)  # a different glyph, and not the one it wants
    assert not gate.matched(door), "a different glyph is a different glyph"


def test_the_ink_is_part_of_what_a_plate_says():
    """`ls20` level 3 has two things that move the indicator: a cross that turns the shape
    and a multi-coloured square that recolours the ink, 12 then 9 then 14. Its goal box is
    drawn in 9, so a gate comparing shapes alone walks to a door wearing the right shape in
    the wrong colour, and is refused."""
    g, g2 = blank(), blank()
    goal_box(g)
    panel(g, shape=((1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (3, 3)))       # right shape...
    plate(g2, 13, 39, 7, 7, 5, 9, ((1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (3, 3)))
    plate(g2, 1, 53, 10, 10, 5, 12, ((1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (3, 3)))
    gate = Gate()
    gate.observe(frame(g), (29, 40), True)
    gate.observe(frame(g2), (29, 45), True)                                # ...wrong ink
    door = obj(13, 19, 39, 45)
    assert not gate.matched(door)
    assert gate.locked(door)
    assert gate.changers == {(29, 45): {0}}      # it moved the ink, not the shape


def test_the_changer_chosen_is_the_one_that_moves_the_half_that_is_wrong():
    gate = Gate()
    gate.icons = {(13, 19, 39, 45): (9, WANTED), (1, 10, 53, 62): (9, INDICATOR)}
    gate.displays = {(1, 10, 53, 62)}
    gate.changers = {(29, 45): {0}, (49, 10): {1}}   # ink square, shape cross
    gate.changer = (29, 45)
    # ink already agrees, the shape does not: the cross is the square to go and stand on
    assert gate.changer_for(obj(13, 19, 39, 45)) == (49, 10)


def test_no_known_changer_for_the_wrong_half_means_no_answer():
    """Re-entering the square that moves the other half is the cheapest way never to finish;
    saying nothing lets ordinary exploration go and find the one that helps."""
    gate = Gate()
    gate.icons = {(13, 19, 39, 45): (9, WANTED), (1, 10, 53, 62): (9, INDICATOR)}
    gate.displays = {(1, 10, 53, 62)}
    gate.changers = {(29, 45): {0}}
    gate.changer = (29, 45)
    assert gate.changer_for(obj(13, 19, 39, 45)) is None


def test_a_changer_that_stops_paying_out_is_forgotten():
    gate = Gate()
    gate.changer = (49, 45)
    gate.cycled()
    gate.cycled()
    assert gate.changer == (49, 45)
    gate.cycled()
    assert gate.changer is None


def test_a_marked_place_is_known_even_before_a_display_has_moved():
    """Rarity ranks by colour, and a goal box painted in the colour that also draws the
    border and the status strip sorts tenth — past the cut, so the gate never sees it. A
    plate is a place the board has drawn a shape on, and there are one or two per board."""
    g = blank()
    goal_box(g)
    panel(g)
    gate = Gate()
    gate.observe(frame(g), (29, 40), True)
    assert gate.marked(obj(13, 19, 39, 45))
    assert not gate.marked(obj(50, 52, 46, 48, colour=0))


def test_a_display_is_not_a_marked_place():
    """It reports state; walking to it is walking to a readout."""
    g = blank()
    panel(g)
    gate = Gate()
    gate.observe(frame(g), (29, 40), True)
    g2 = blank()
    panel(g2, shape=((1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (3, 1)))
    gate.observe(frame(g2), (49, 45), True)
    assert not gate.marked(obj(1, 10, 53, 62))


def test_a_target_on_the_changer_is_known_to_turn_the_display():
    gate = Gate()
    gate.changer = (49, 45)
    assert gate.changing(obj(51, 52, 46, 47, colour=0), (5, 5))
    assert not gate.changing(obj(13, 19, 39, 45), (5, 5))


# --- re-entering the square ---------------------------------------------------------

def test_cycling_steps_off_the_square_and_back_on():
    """Standing on the changer does nothing — it is entering that counts — so one more
    turn of the display costs two actions, not one."""
    g = blank()
    g[:60, :] = 3
    out, back = cycle(g, model(), (25, 25))
    assert model().dirs[out] == tuple(-d for d in model().dirs[back])


def test_cycling_walled_in_gives_no_actions_rather_than_a_wrong_one():
    g = blank()
    g[:60, :] = 4
    g[25:30, 25:30] = 3
    assert cycle(g, model(), (25, 25)) == []


# --- planning the order ---------------------------------------------------------------
# `compete.stage` is the piece the rungs cannot be: which changer to turn first, and which
# refill to spend before which leg. `ls20` level 3 is decided by that order.

def board():
    """An open floor with walls round the edge, on the 5-cell grid the piece steps on."""
    g = np.full((64, 64), 4)
    g[1:59, 1:59] = 3
    return g


def test_a_plan_refuels_when_the_changer_is_out_of_reach():
    from compete import stage
    g = board()
    m = model(box=(5, 5), passable={3, 5, 9, 11}, blocking={4})
    gate = Gate()
    gate.icons = {(30, 36, 5, 11): (9, WANTED)}     # the door wears a shape
    gate.displays = set()
    gate.changers = {(5, 30): {1}}
    gate.icons[(1, 10, 53, 62)] = (9, INDICATOR)    # ...the display shows another
    gate.displays = {(1, 10, 53, 62)}
    door = obj(30, 36, 5, 11)
    fuel = [{"colour": 11, "x": [10, 12], "y": [10, 12], "cells": 8}]
    assert gate.locked(door)
    # Six actions of clock: the changer is five steps away and the door is far past it, so
    # the only order that finishes tops up at the refill on the way.
    got = stage(g, m, gate, (5, 5), 6, 21, door, fuel)
    assert got, "a plan exists through the refill"
    # ...and with a clock that cannot even reach the refill, there is no plan at all.
    assert stage(g, m, gate, (5, 5), 1, 21, door, fuel) is None


def test_no_plan_when_no_changer_is_known_for_the_wrong_half():
    from compete import stage
    g = board()
    m = model(box=(5, 5), passable={3, 5, 9, 11}, blocking={4})
    gate = Gate()
    gate.icons = {(30, 36, 5, 11): (9, WANTED), (1, 10, 53, 62): (12, WANTED)}
    gate.displays = {(1, 10, 53, 62)}
    gate.changers = {(5, 30): {1}}                  # moves the shape; the ink is what is wrong
    assert stage(g, m, gate, (5, 5), 21, 21, obj(30, 36, 5, 11), []) is None


# --- counting the turns ----------------------------------------------------------------
# A changer walks its half round a cycle. Knowing the cycle is the difference between "go
# and press it" and knowing the press costs two actions or six.

def cycling_gate():
    """A gate that has watched one square turn the shape A -> B -> C -> A."""
    g = Gate()
    g.icons = {(13, 19, 39, 45): (9, "C"), (1, 10, 53, 62): (9, "A")}
    g.displays = {(1, 10, 53, 62)}
    g.changers = {(49, 45): {1}}
    g.cycles = {((49, 45), 1): {"A": "B", "B": "C", "C": "A"}}
    return g


def test_the_presses_are_counted_along_the_cycle_that_was_observed():
    g = cycling_gate()
    door = obj(13, 19, 39, 45)
    assert g.presses_for(door, 1, (49, 45)) == 2      # A -> B -> C
    g.icons[(1, 10, 53, 62)] = (9, "B")
    assert g.presses_for(door, 1, (49, 45)) == 1      # B -> C
    g.icons[(1, 10, 53, 62)] = (9, "C")
    assert g.presses_for(door, 1, (49, 45)) == 0      # already showing it


def test_a_value_the_changer_has_never_produced_answers_nothing():
    """Better no answer than a confident one: the planner falls back to the old assumption
    of a single turn, which is exactly what it did everywhere before this existed."""
    g = cycling_gate()
    g.icons[(1, 10, 53, 62)] = (9, "Z")               # a state off the observed cycle
    assert g.presses_for(obj(13, 19, 39, 45), 1, (49, 45)) is None


def test_a_cycle_that_closes_without_passing_the_wanted_value_answers_nothing():
    """A square that demonstrably cannot produce what the door wants must say so, not
    return a number one larger than the loop it just walked."""
    g = cycling_gate()
    g.cycles = {((49, 45), 1): {"A": "B", "B": "A"}}   # a two-state loop that misses C
    assert g.presses_for(obj(13, 19, 39, 45), 1, (49, 45)) is None


# --- two changers writing the same half ---------------------------------------------------
# `ls20` level 5 has two squares that write the shape: six states round one, four round the
# other, and the glyph its goal box asks for is in NEITHER. It exists only in the states the
# two reach by being interleaved, and a plan that walks one changer's own cycle can only
# press the same square forever.

def two_changer_gate():
    """Two squares. Alone each returns to where it started; together they reach `D`."""
    g = Gate()
    g.icons = {(13, 19, 39, 45): (9, "D"), (1, 10, 53, 62): (9, "A")}
    g.displays = {(1, 10, 53, 62)}
    g.changers = {(49, 45): {1}, (9, 45): {1}}
    # Alone, the first square only ever swaps A and B — D is not on its cycle at all. The
    # second swaps A with C and B with D. Only A -> B (first) -> D (second) gets there.
    g.cycles = {((49, 45), 1): {"A": "B", "B": "A"},
                ((9, 45), 1): {"A": "C", "C": "A", "B": "D", "D": "B"}}
    return g


def test_a_value_off_both_cycles_is_still_planned_for():
    """A -> C on the second square, C -> D on the first. Neither square gets there alone."""
    g = two_changer_gate()
    door = obj(13, 19, 39, 45)
    assert g.presses_for(door, 1, (49, 45)) is None      # the single-changer reading
    assert g.presses_for(door, 1, (9, 45)) is None
    assert g.leg_for(door, 1) == ((49, 45), 1)           # go here first, once


def test_the_first_leg_counts_the_entries_that_stay_on_one_square():
    """Only the first leg is committed, so consecutive entries of the same square are one
    trip with a press count — the rest is re-planned from what actually happened."""
    g = two_changer_gate()
    g.cycles[((49, 45), 1)] = {"A": "E", "E": "B", "B": "A"}
    assert g.leg_for(obj(13, 19, 39, 45), 1) == ((49, 45), 2)  # A -> E -> B, then swap


def test_a_half_already_showing_what_is_wanted_needs_no_leg():
    g = two_changer_gate()
    g.icons[(1, 10, 53, 62)] = (9, "D")
    assert g.leg_for(obj(13, 19, 39, 45), 1) is None


def test_turns_for_names_the_square_the_combined_search_wants_first():
    """`turns_for` drives the order search, so it has to agree with `leg_for` — naming the
    square that merely moves the half sends the planner round an orbit past the state."""
    g = two_changer_gate()
    assert g.turns_for(obj(13, 19, 39, 45)) == {1: (49, 45)}


# --- a plate that stops being reported ----------------------------------------------------
# The piece is 5x5 and `ls20` level 5's goal box is 7x7, so walking in hides what the box is
# asking for: `plates` reports it right up until the moment it matters and then stops. Read
# fresh at that moment, the agent concludes the panel it spent ninety actions setting is
# wrong and walks away one press from the door — measured three times over, by hand.
#
# The opposite case looks identical from here and wants the opposite answer: a refill that
# has been picked up is gone for good, and remembering it leaves the planner routing to fuel
# that is not there. Keeping every vanished plate, or every one never seen to change, costs
# `ls20` levels 3 and 4. What separates them is whether the piece is standing on it.

def two_plates():
    g = blank()
    goal_box(g)                    # a 7x7 box at x13-19, y39-45
    panel(g)                       # the indicator at x1-10, y53-62
    return g


OFF = (40, 10, 5, 5)      # nowhere near either plate
ON_BOX = (14, 40, 5, 5)   # standing on the goal box at x13-19, y39-45


def test_a_plate_the_piece_is_standing_on_keeps_its_last_reading():
    g = Gate()
    g.observe(frame(two_plates()), OFF, True)
    was = dict(g.icons)
    gone = blank()
    panel(gone)                    # the goal box is no longer drawn: the piece is on it
    g.observe(frame(gone), ON_BOX, True)
    assert g.icons.get((13, 19, 39, 45)) == was[(13, 19, 39, 45)]


def test_a_plate_read_through_the_piece_is_not_a_display_changing():
    """The piece covers part of the box before it covers all of it, so the glyph reads
    garbled — and a plate whose value changes under the square the piece is on is exactly
    how a changer is recognised. `ls20` level 5 recorded the square that touches its goal
    box as one and stood there turning nothing for 549 planning rounds."""
    g = Gate()
    g.observe(frame(two_plates()), OFF, True)
    garbled = blank()
    goal_box(garbled, shape=((1, 1), (2, 1)))   # most of the glyph hidden by the piece
    panel(garbled)
    g.observe(frame(garbled), ON_BOX, True)
    assert (13, 19, 39, 45) not in g.displays, "not a display, just an obscured one"
    assert g.changer != (14, 40), "and the square standing on it is not a changer"


def test_a_plate_that_vanishes_out_of_reach_is_forgotten():
    """A refill that has been taken. Remembering it is routing to fuel that is not there."""
    g = Gate()
    g.observe(frame(two_plates()), OFF, True)
    gone = blank()
    panel(gone)
    g.observe(frame(gone), OFF, True)
    assert (13, 19, 39, 45) not in g.icons


def test_a_plate_the_piece_is_off_is_read_fresh_not_remembered():
    """Remembering must not outrank looking: from off the plate, what it says now is the
    answer."""
    g = Gate()
    g.observe(frame(two_plates()), OFF, True)
    before = g.icons[(13, 19, 39, 45)]
    moved = blank()
    goal_box(moved, shape=((1, 1), (2, 1), (3, 1), (1, 2), (1, 3), (2, 3)))
    panel(moved)
    g.observe(frame(moved), OFF, True)
    assert g.icons[(13, 19, 39, 45)] != before, "the new drawing wins while it is drawn"
    assert len([k for k in g.icons if k[0] == 13]) == 1, "no phantom copy alongside it"


# --- changers that MOVE ---------------------------------------------------------------
# `ls20` level 6's changers are not squares: they are small objects PATROLLING the
# corridors on short cycles, advancing one lattice step per piece move — a refused press
# freezes them — and a press is the piece's footprint overlapping one after the move.
# Everything below is that mechanism in miniature (measured in results/l6-model.md).

def ticked(gate, positions, key="cross"):
    for p in positions:
        gate.track({key: (p[0], p[1], 3, 3)}, set(), True)


def test_a_patrolling_object_earns_its_period_after_two_cycles():
    g = Gate()
    lap = [(15, 11), (20, 11), (25, 11), (30, 11), (35, 11), (30, 11), (25, 11), (20, 11)]
    ticked(g, lap + lap)
    assert g.mover_period("cross") == 8


def test_a_parked_object_has_no_period():
    """A static object repeats with every period; only real movement is a patrol. Door
    glyphs, carry markers and refills all sit still, and none of them may enter the set."""
    g = Gate()
    ticked(g, [(15, 11)] * 32)
    assert g.mover_period("cross") is None


def test_a_frozen_tick_is_not_recorded():
    """The patrol clock is the piece MOVING. A refused press freezes every patroller —
    measured three times in one probe — so feeding the frozen frame in would smear the
    period across everything downstream."""
    g = Gate()
    lap = [(15, 11), (20, 11), (25, 11), (30, 11)]
    for p in lap:
        g.track({"cross": (p[0], p[1], 3, 3)}, set(), True)
        g.track({"cross": (p[0], p[1], 3, 3)}, set(), False)   # the piece was refused
    ticked(g, lap)
    assert g.mover_period("cross") == 4


def test_the_future_position_is_read_off_the_cycle():
    g = Gate()
    lap = [(15, 11), (20, 11), (25, 11), (30, 11)]
    ticked(g, lap + lap)
    assert g.mover_at("cross", 1)[:2] == (15, 11)   # after 30 the lap wraps
    assert g.mover_at("cross", 2)[:2] == (20, 11)
    assert g.mover_at("cross", 4)[:2] == (30, 11)


def test_the_piece_itself_is_never_a_mover():
    g = Gate()
    for p in [(15, 11), (20, 11), (25, 11), (30, 11)] * 4:
        g.track({"me": (p[0], p[1], 5, 5)}, {"me"}, True)
    assert g.mover_period("me") is None


# --- routing through a patroller ------------------------------------------------------
# The plan has to arrive at the door wearing its ask, pressing the patroller on the way —
# matching first and walking after is how `ls20` level 6 wasted its matched panels.

def moving_board():
    """Open floor, a door at (13,39) asking (9, WANTED), the panel showing (9, INDICATOR),
    and one patroller shuttling between (24,25) and (29,25) that turns INDICATOR<->WANTED."""
    g = np.full((64, 64), 3)
    gate = Gate()
    gate.icons = {(13, 19, 39, 45): (9, WANTED), (1, 10, 53, 62): (9, INDICATOR)}
    gate.displays = {(1, 10, 53, 62)}
    # The lap sits OFF the piece's own lattice (real patrollers do), because a mover
    # aligned to it can only ever share a square's parity, never its tick — a footprint
    # five apart from a box five apart arrives on the wrong beat every time.
    lap = [(20, 25, 3, 3), (25, 25, 3, 3)]
    gate.ticks = 8
    gate.movers = {"m": {"hist": [(i, lap[i % 2]) for i in range(1, 9)], "halves": {1}}}
    gate.mover_edges = {("m", 1): {INDICATOR: WANTED, WANTED: INDICATOR}}
    return g, gate


def test_a_route_presses_the_patroller_and_arrives_wearing_the_ask():
    g, gate = moving_board()
    m = model(box=(5, 5), passable={3, 5, 9}, blocking={4})
    got = gate.route_moving(g, m, (44, 40), obj(13, 19, 39, 45), [], 42, 42)
    assert got is not None
    acts, marks, opened = got
    assert opened == 1, "the goal door itself is the one gate this plan opens"
    assert sum(marks) % 2 == 1, "an odd number of presses flips INDICATOR to WANTED"
    # walk the plan forward: it must end inside the door box
    pos = (44, 40)
    for a in acts:
        d = m.dirs[a]
        pos = (pos[0] + d[0], pos[1] + d[1])
    assert 13 <= pos[0] and pos[0] + 5 <= 20 and 39 <= pos[1] and pos[1] + 5 <= 46


def test_no_route_when_the_press_cannot_be_simulated():
    """A patroller with no usable edge for the panel's value is unplannable ground —
    better no plan than a walk that scrambles the panel."""
    g, gate = moving_board()
    gate.mover_edges = {("m", 1): {"###/###/###": WANTED}}   # nothing about INDICATOR
    m = model(box=(5, 5), passable={3, 5, 9}, blocking={4})
    assert gate.route_moving(g, m, (44, 40), obj(13, 19, 39, 45), [], 42, 42) is None


def test_learn_mode_walks_to_the_press_it_has_no_edge_for():
    """The planner can only press values it has watched. Aiming only at the edge out of
    the CURRENT value leaves a door whose ask is several unwatched presses away
    unreachable — level 6's ask is exactly that, and the gap cost it 483 actions of
    square-changer trips. In learn mode the unplannable press IS the goal."""
    g, gate = moving_board()
    gate.icons[(13, 19, 39, 45)] = (9, "###/###/###")   # an ask no known edge reaches
    gate.mover_edges = {("m", 1): {INDICATOR: "##./##./##."}}   # one edge, elsewhere
    m = model(box=(5, 5), passable={3, 5, 9}, blocking={4})
    door = obj(13, 19, 39, 45)
    assert gate.route_moving(g, m, (44, 40), door, [], 42, 42) is None, "no honest plan"
    got = gate.route_moving(g, m, (44, 40), door, [], 42, 42, learn=True)
    assert got is not None and got[1][-1] is True, "it ends on a press"


def test_learn_mode_will_not_spend_the_last_of_the_tank():
    """A press the piece starves on teaches nothing that survives: a death resets the
    panel and every door it had opened."""
    g, gate = moving_board()
    gate.icons[(13, 19, 39, 45)] = (9, "###/###/###")
    gate.mover_edges = {("m", 1): {}}
    m = model(box=(5, 5), passable={3, 5, 9}, blocking={4})
    door = obj(13, 19, 39, 45)
    assert gate.route_moving(g, m, (44, 40), door, [], 42, 6, learn=True) is None


def test_a_patroller_that_moves_nothing_is_no_planner():
    """A mover that has never been seen to move a half of the display is scenery; a board
    with only those is a static board, and this planner has no business on it."""
    g, gate = moving_board()
    gate.movers["m"]["halves"] = set()
    m = model(box=(5, 5), passable={3, 5, 9}, blocking={4})
    assert gate.route_moving(g, m, (44, 40), obj(13, 19, 39, 45), [], 42, 42) is None
