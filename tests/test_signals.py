"""Tests for finding the game's progress meter.

The distinction under test is clock versus consequence. `ls20`'s budget bar falls by two
on every single press; hill-climbing on that rewards pressing buttons. `cn04`'s marker
advances one cell on some presses and not others, and that is the thing worth climbing.
"""

import numpy as np
import pytest

from signals import (actions_left, classify, counts, directions, drain, meters, refills,
                     score, series)


def frame(**colour_counts):
    """A 64x64 frame containing the requested number of cells of each colour."""
    grid = np.zeros((64, 64), dtype=int)
    flat = grid.reshape(-1)
    at = 0
    for colour, n in colour_counts.items():
        flat[at:at + n] = int(colour.lstrip("c"))
        at += n
    return [grid]


def test_counts_reads_the_whole_frame_not_just_the_bottom_strip():
    got = counts(frame(c5=10, c7=20))
    assert got[5] == 10 and got[7] == 20
    assert got[0] == 64 * 64 - 30


@pytest.mark.parametrize("seq, kind", [
    # every sequence below is measured off a real game, not invented
    ([84, 82, 80, 78, 76, 74, 72, 70], "clock"),                    # ls20 budget, 1.000
    ([135, 135, 136, 136, 137, 137, 138, 138], "clock"),            # cn04 row-0 marker, 0.976
    ([36, 36, 36, 40, 40, 44, 48, 48], "clock"),                    # sc25 right column, 0.956
    ([0, 1, 1, 2, 3, 3, 4, 4], "clock"),                            # re86 tally, 0.980
    ([5, 5, 5, 5, 5], "noise"),             # nothing happens
    ([5, 6, 5, 6, 5], "noise"),             # oscillates, so it is not a meter
    ([5, 5, 5, 5, 6], "noise"),             # one move is not evidence
])
def test_classify_separates_the_clock_from_real_progress(seq, kind):
    assert classify(seq) == kind


def test_a_counter_that_waits_for_events_is_progress():
    """Flat, flat, flat, then a jump, then flat again — that shape cannot be a clock, and
    direction is irrelevant: counting down to zero is still making progress."""
    assert classify([9, 9, 9, 9, 8, 8, 8, 8, 8, 7]) == "progress"


def test_no_real_counter_in_these_games_survives_as_progress():
    """The measurement that killed the idea: every counter found across the nine games is
    a straight line in the number of actions, from 0.955 to 1.000. They differ in speed,
    not in kind, and there is no gradient to climb."""
    real = [[84, 82, 80, 78, 76, 74, 72, 70], [892, 894, 896, 898, 900, 902, 904, 906],
            [135, 135, 136, 136, 137, 137, 138, 138], [32, 32, 31, 31, 30, 30, 29, 29],
            [36, 36, 36, 40, 40, 44, 48, 48], [128, 128, 128, 124, 124, 120, 116, 116],
            [0, 1, 1, 2, 3, 3, 4, 4], [64, 63, 63, 62, 61, 61, 60, 60],
            [1, 2, 2, 3, 4, 4, 5, 5]]
    assert {classify(seq) for seq in real} == {"clock"}


def test_meters_labels_each_colour_and_drops_the_noise():
    jumpy = [10, 10, 10, 10, 11, 11, 11, 11, 11, 12]
    frames = [frame(c1=84 - 2 * i, c2=jumpy[i], c3=7) for i in range(10)]
    got = meters(frames)
    assert got[1] == "clock"
    assert got[2] == "progress"
    assert 3 not in got


def test_score_is_signed_so_more_is_always_better():
    d = directions([frame(c9=10), frame(c9=8), frame(c9=6)], [9])
    assert d[9] == -1
    assert score(frame(c9=6), [9], d) > score(frame(c9=10), [9], d)


def test_score_of_no_meters_is_flat():
    assert score(frame(c9=10), [], {}) == 0


# --- refills -----------------------------------------------------------------------
# A clock only falls. A rise is an event, and whatever vanished on that step caused it.

def test_a_clock_jumping_up_marks_what_vanished_as_a_refill():
    steps = [{"hud": {"11": [80, 78]}, "gone": [[5, 10, 10]]},
             {"hud": {"11": [78, 84]}, "gone": [[11, 20, 20]]}]
    assert refills(steps, {11}) == {(11, 20, 20)}


def test_a_rise_in_something_that_is_not_the_clock_is_ignored():
    steps = [{"hud": {"9": [1, 2]}, "gone": [[5, 10, 10]]}]
    assert refills(steps, {11}) == set()


def test_no_refill_when_the_clock_only_falls():
    steps = [{"hud": {"11": [84, 82]}, "gone": [[5, 1, 1]]},
             {"hud": {"11": [82, 80]}, "gone": []}]
    assert refills(steps, {11}) == set()


# --- how much of the clock is left --------------------------------------------------
# The numbers below are ls20 level 2 as measured: an 84-cell yellow bar spending 4 cells
# an action, with the grey it leaves behind growing by the same 4.

def bar(was, now, spent_was, spent_now):
    return {"hud": {"11": [was, now], "3": [spent_was, spent_now]}}


def test_the_clock_is_the_falling_half_of_the_pair():
    """`ls20` runs two counters that move on every action and sum to a constant 84. An
    agent that adds them up reads a full tank on the step before it starves."""
    steps = [bar(84 - 4 * i, 80 - 4 * i, 4 * i, 4 * i + 4) for i in range(5)]
    assert drain(steps) == {11: 4}


def test_a_refill_does_not_change_the_rate():
    """The bar jumps back to full when a refill is picked up and when a life is lost.
    Neither is what it spends per action."""
    steps = [bar(84, 80, 0, 4), bar(80, 76, 4, 8), bar(76, 84, 8, 0), bar(84, 80, 0, 4)]
    assert drain(steps)[11] == 4


def test_a_counter_that_only_moves_sometimes_is_not_the_clock():
    steps = [{"hud": {"11": [84, 80]}}, {"hud": {}}, {"hud": {}}, {"hud": {}}]
    assert drain(steps) == {}


def test_actions_left_is_the_bar_over_its_rate():
    """21 actions to a life on ls20 level 2 — 84 cells at 4 a press."""
    steps = [bar(84 - 4 * i, 80 - 4 * i, 4 * i, 4 * i + 4) for i in range(5)]
    grid = np.zeros((64, 64), dtype=int)
    grid[60:, :64] = 3
    grid[60, :40] = 11                      # 40 cells of bar left, below the play area
    assert actions_left([grid], steps) == 10


def test_no_clock_reads_as_no_limit_rather_than_as_zero():
    """A game with no visible budget must not look like one about to starve, or every
    plan is rejected as unaffordable."""
    assert actions_left([np.zeros((64, 64), dtype=int)], []) is None


def test_the_rate_is_measured_from_recent_history_not_the_whole_run():
    """The same bar spends 2 cells an action on ls20 level 1 and 4 on level 2. Averaged
    over the run it reads a level-2 life as twice as long as it is."""
    old = [bar(84 - 2 * i, 82 - 2 * i, 2 * i, 2 * i + 2) for i in range(30)]
    new = [bar(84 - 4 * i, 80 - 4 * i, 4 * i, 4 * i + 4) for i in range(5)]
    grid = np.zeros((64, 64), dtype=int)
    grid[60, :40] = 11
    assert actions_left([grid], old + new, window=5) == 10
    assert actions_left([grid], old + new, window=40) == 20   # what the whole run says


def test_a_death_that_refills_the_clock_is_not_a_pickup():
    """Losing a life restores the budget and teleports the piece; whatever vanished near
    that moment did not cause it. On ls20 this marked the level's own marker as a refill."""
    steps = [{"hud": {"11": [12, 84]}, "gone": [[0, 21, 31]], "walked": False},
             {"hud": {"11": [40, 84]}, "gone": [[11, 5, 5]], "walked": True}]
    assert refills(steps, {11}) == {(11, 5, 5)}
