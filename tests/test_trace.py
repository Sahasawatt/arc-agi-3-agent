"""Tests for the frame-by-frame record.

The point of the trace is that it separates consequence from clockwork. A status bar that
ticks on every press is the clock; an object that vanishes when touched is a consequence,
and it is the only evidence about what the game wants.
"""

import numpy as np

from trace import per_action_keys, step, summarise


class FakeModel:
    parts = ((12, 1, 1),)


class Obs:
    """Minimal stand-in: a frame plus the level counter."""

    def __init__(self, cells, hud_row=None, levels=0):
        grid = np.full((64, 64), 7, dtype=int)
        for colour, x, y in cells:
            grid[y, x] = colour
        if hud_row:
            for colour, n in hud_row.items():
                grid[62, :n] = colour
        self.frame = [grid]
        self.levels_completed = levels


def test_a_touched_object_vanishing_is_recorded():
    before = Obs([(5, 10, 10), (3, 20, 20)])
    after = Obs([(3, 20, 20)])
    got = step(before, after, 4, FakeModel())
    assert got["gone"] == [[5, 10, 10]]
    assert got["new"] == []


def test_the_piece_moving_is_not_a_board_change():
    """The piece is colour 12 in the fake model; it must not show up as appear/disappear."""
    before = Obs([(12, 10, 10), (3, 20, 20)])
    after = Obs([(12, 15, 10), (3, 20, 20)])
    got = step(before, after, 4, FakeModel())
    assert got["gone"] == [] and got["new"] == []


def test_level_completion_is_carried_on_the_step():
    got = step(Obs([]), Obs([], levels=2), 1, FakeModel())
    assert got["levels"] == 2


def test_summary_says_nothing_changed_when_nothing_did():
    steps = [{"action": 1, "gone": [], "new": [], "hud": {}, "levels": 0}]
    assert summarise(steps).strip() == "press 1: nothing changed"


def test_summary_drops_the_per_action_counter_but_keeps_real_status_moves():
    steps = [{"action": 1, "gone": [], "new": [], "hud": {"11": [84, 82], "9": [3, 4]},
              "levels": 0}]
    out = summarise(steps, budget_keys={11})
    assert "status colour 9 went 3 to 4" in out
    assert "colour 11" not in out


def test_summary_keeps_only_the_recent_tail():
    steps = [{"action": i, "gone": [], "new": [], "hud": {}, "levels": 0} for i in range(40)]
    assert len(summarise(steps, limit=5).splitlines()) == 5


def test_per_action_keys_finds_the_clock_and_ignores_a_rare_mover():
    steps = ([{"action": 1, "gone": [], "new": [], "hud": {"11": [1, 2]}, "levels": 0}] * 9
             + [{"action": 1, "gone": [], "new": [], "hud": {"11": [1, 2], "4": [0, 1]},
                 "levels": 0}])
    assert per_action_keys(steps) == {11}


def test_per_action_keys_on_no_evidence():
    assert per_action_keys([]) == set()


def test_the_piece_is_excluded_by_colour_not_by_exact_size():
    """Matched on (colour, w, h), the piece drops out of the filter the moment it is drawn
    a cell shorter — and then every step of the trace reports it as an object that
    vanished and came back."""
    class Model:
        parts = ((12, 5, 2),)          # the model's idea of the piece
    before = Obs([(12, 10, 10), (12, 11, 10), (3, 20, 20)])   # drawn 2 wide here
    after = Obs([(12, 15, 10), (3, 20, 20)])                   # drawn 1 wide there
    got = step(before, after, 4, Model())
    assert got["gone"] == [] and got["new"] == []


class Moving:
    parts = ((12, 1, 1),)
    dirs = {1: (0, -5), 4: (5, 0)}


def test_a_part_the_body_model_missed_reads_as_walking_not_vanishing():
    """The trailing half of the piece is not in `parts`, so it appears as a disappearance
    plus an appearance on every single step — unless the gap matches the action's own
    displacement, which is what walking looks like."""
    before = Obs([(9, 10, 20), (3, 40, 40)])
    after = Obs([(9, 15, 20), (3, 40, 40)])
    got = step(before, after, 4, Moving())          # action 4 displaces (5, 0)
    assert got["gone"] == [] and got["new"] == []


def test_a_pickup_is_still_reported_when_something_also_walked():
    before = Obs([(9, 10, 20), (5, 30, 30)])
    after = Obs([(9, 15, 20)])                       # the colour-5 object was consumed
    got = step(before, after, 4, Moving())
    assert got["gone"] == [[5, 30, 30]] and got["new"] == []


def test_a_jump_that_is_not_the_action_displacement_is_still_a_change():
    before = Obs([(9, 10, 20)])
    after = Obs([(9, 40, 50)])                       # teleport, not a step
    got = step(before, after, 4, Moving())
    assert got["gone"] == [[9, 10, 20]] and got["new"] == [[9, 40, 50]]


def test_level_completion_is_announced_once_not_on_every_later_step():
    """`levels` is a running total. Testing it directly printed LEVEL COMPLETED on all
    sixteen lines of a summary for a single event."""
    steps = ([{"action": 1, "gone": [], "new": [], "hud": {}, "levels": 0}] * 2
             + [{"action": 2, "gone": [], "new": [], "hud": {}, "levels": 1}] * 3)
    assert summarise(steps).count("LEVEL COMPLETED") == 1
