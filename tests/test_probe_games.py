"""verdict() is the only part of the probe that is pure — and it is the part that decides
the go/no-go answer, so it gets the tests."""

from probe_games import _shifts, verdict


def obj(colour, cells, x, y):
    return {"colour": colour, "cells": cells, "x": [x, x + 1], "y": [y, y + 1]}


def base(**over):
    r = {"moved": True, "terrain_separable": True, "constant_step": True,
         "step_size": 5, "distinct_directions": 4, "complex_actions": [],
         "bulk_fill_colours": [3, 4]}
    r.update(over)
    return r


def test_ls20_shaped_game_is_maze_like():
    assert verdict(base())[0] == "MAZE_LIKE"


def test_nothing_moves_with_click_actions_is_pointer_game():
    assert verdict(base(moved=False, complex_actions=[6]))[0] == "NEEDS_POINTER"


def test_nothing_moves_at_all_is_a_perception_failure():
    assert verdict(base(moved=False))[0] == "NO_PLAYER_FOUND"


def test_no_bulk_terrain_means_no_map():
    assert verdict(base(terrain_separable=False, bulk_fill_colours=[]))[0] == "NO_MAP"


def test_irregular_movement_is_not_grid_stepped():
    assert verdict(base(constant_step=False))[0] == "NOT_GRID_STEPPED"


def test_one_direction_is_partial():
    assert verdict(base(distinct_directions=1))[0] == "PARTIAL"


def test_error_short_circuits_every_other_check():
    """An unmakeable game must not be classified on its (absent) measurements."""
    assert verdict({"error": "make() returned None"})[0] == "ERROR"


def test_movement_check_precedes_terrain_check():
    """A game where nothing moves is NOT_PLAYER/POINTER even if terrain is also broken —
    reporting 'no map' there would send someone fixing the wrong thing."""
    assert verdict(base(moved=False, terrain_separable=False))[0] == "NO_PLAYER_FOUND"


def test_shifts_matches_objects_by_colour_and_size():
    before = [obj(12, 25, 10, 10), obj(9, 4, 50, 50)]
    after = [obj(12, 25, 15, 10), obj(9, 4, 50, 50)]  # only the first moved
    assert _shifts(before, after) == [(5, 0)]


def test_shifts_ignores_objects_that_only_appear():
    before = [obj(12, 25, 10, 10)]
    after = [obj(12, 25, 10, 10), obj(7, 3, 0, 0)]
    assert _shifts(before, after) == []
