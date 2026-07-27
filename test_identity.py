"""Tests for cross-frame object identity.

Objects used to be keyed by `(colour, cell_count)`. Two objects sharing that key in one
frame collided in the dict and one was silently discarded — 55 objects across the 9
MAZE_LIKE games at reset alone, 19 of `dc22`'s 31. Everything downstream was reasoning
about a partial board.
"""

import pytest

from identity import Track, match, update


def obj(colour, cells, x, y, w=1, h=1):
    return {"colour": colour, "cells": cells, "x": [x, x + w - 1], "y": [y, y + h - 1]}


def track(tid, colour, area, x, y, w=1, h=1, velocity=(0, 0)):
    return Track(id=tid, colour=colour, area=area, box=(x, y, w, h), velocity=velocity)


# --- the bug that started this -----------------------------------------------------

def test_two_objects_with_the_same_colour_and_area_both_survive():
    """The dict-key version kept one and dropped the other with no error."""
    tracks, assign, _ = update([], [obj(3, 4, 10, 10), obj(3, 4, 30, 10)], 0)
    assert len(tracks) == 2
    assert len(set(assign.values())) == 2


def test_same_colour_and_area_objects_keep_their_own_identities_across_a_step():
    """The left one moves, the right one does not. Neither may inherit the other's id."""
    tracks, assign, nid = update([], [obj(3, 4, 10, 10), obj(3, 4, 30, 10)], 0)
    left = assign[0]
    tracks, assign, _ = update(tracks, [obj(3, 4, 13, 10), obj(3, 4, 30, 10)], nid)
    assert assign[0] == left               # the moved object is still the same object
    assert len(set(assign.values())) == 2


# --- matching --------------------------------------------------------------------

def test_an_object_that_changes_size_keeps_its_identity():
    """A piece redrawn mid-animation changes cell count. Exact-key matching lost it and
    the loss was misread as a blocked move."""
    tracks = [track(7, colour=3, area=4, x=10, y=10, w=2, h=2)]
    assert match(tracks, [obj(3, 6, 11, 10, w=2, h=3)]) == {0: 7}


def test_an_object_that_changes_colour_keeps_its_identity_when_nothing_else_fits():
    tracks = [track(7, colour=3, area=4, x=10, y=10)]
    assert match(tracks, [obj(9, 4, 10, 10)]) == {0: 7}


def test_colour_beats_proximity_when_both_are_plausible():
    """A same-colour candidate one cell further away is still the better match than a
    different-colour one right next to the prediction."""
    tracks = [track(7, colour=3, area=4, x=10, y=10)]
    got = match(tracks, [obj(9, 4, 11, 10), obj(3, 4, 12, 10)])
    assert got == {1: 7}


def test_velocity_prediction_breaks_a_tie_the_wrong_way_round_otherwise():
    """A piece moving right at 3 cells/step should match the object where it is *going*,
    not a stationary decoy behind it. This is the sc25 failure: raw distance picked the
    coincidental neighbour and produced a diagonal displacement."""
    tracks = [track(7, colour=3, area=4, x=10, y=10, velocity=(3, 0))]
    got = match(tracks, [obj(3, 4, 9, 10), obj(3, 4, 13, 10)])
    assert got == {1: 7}


def test_nothing_matches_beyond_the_gate():
    """An object on the far side of the board is a different object, not a teleport."""
    tracks = [track(7, colour=3, area=4, x=1, y=1)]
    assert match(tracks, [obj(3, 4, 60, 55)], gate=16) == {}


def test_each_track_takes_at_most_one_object_and_vice_versa():
    tracks = [track(7, colour=3, area=4, x=10, y=10)]
    got = match(tracks, [obj(3, 4, 10, 10), obj(3, 4, 11, 10)])
    assert got == {0: 7}


# --- update bookkeeping ------------------------------------------------------------

def test_a_new_object_gets_a_fresh_id():
    tracks, assign, nid = update([], [obj(3, 4, 10, 10)], 0)
    tracks, assign, nid = update(tracks, [obj(3, 4, 10, 10), obj(5, 9, 40, 40)], nid)
    assert len(tracks) == 2
    assert assign[1] == nid - 1


def test_an_unmatched_track_is_kept_and_counted_as_missed():
    """Losing sight of something for one frame is not proof it is gone; the caller needs
    to tell 'absent' from 'stationary'."""
    tracks, _, nid = update([], [obj(3, 4, 10, 10)], 0)
    tracks, assign, _ = update(tracks, [], nid)
    assert assign == {}
    assert [t.missed for t in tracks] == [1]


def test_a_track_missing_too_long_is_dropped():
    tracks, _, nid = update([], [obj(3, 4, 10, 10)], 0)
    for _ in range(3):
        tracks, _, nid = update(tracks, [], nid, max_missed=2)
    assert tracks == []


def test_velocity_is_the_last_observed_displacement():
    tracks, _, nid = update([], [obj(3, 4, 10, 10)], 0)
    tracks, _, _ = update(tracks, [obj(3, 4, 14, 10)], nid)
    assert tracks[0].velocity == (4, 0)
    assert tracks[0].hits == 2


@pytest.mark.parametrize("n", [0, 1, 40])
def test_update_handles_empty_and_many(n):
    objs = [obj(c % 6, 4, (c * 3) % 60, (c * 7) % 55) for c in range(n)]
    tracks, assign, nid = update([], objs, 0)
    assert len(tracks) == n and nid == n
