"""Tests for the LLM goal proposer.

Only the pure parts: the scene it is shown, and the parsing of what comes back. A 7B model
answers with prose, fences, extra keys and out-of-range indices, and every one of those has
to become "no plan" rather than a crash or a plan that points at nothing.
"""

from goal_llm import describe, parse


class FakeModel:
    colour, box, step, dirs = 12, (5, 5), 5, {1: (0, -5), 2: (0, 5)}
    blocking, passable = {4}, {3}


def obj(colour, cells, x, y, w=1, h=1):
    return {"colour": colour, "cells": cells, "x": [x, x + w - 1], "y": [y, y + h - 1]}


def test_scene_lists_every_object_with_its_index():
    s = describe(FakeModel(), [obj(5, 43, 33, 9, 7, 7), obj(1, 1, 20, 32)], {11: 84}, 1)
    assert "[0] colour 5, 7x7, 43 cells, at x=33 y=9" in s
    assert "[1] colour 1, 1x1, 1 cells, at x=20 y=32" in s
    assert "Walls (impassable colours): [4]" in s
    assert "{11: 84}" in s


def test_scene_says_so_when_no_wall_was_found():
    class NoWalls(FakeModel):
        blocking = set()
    assert "none found" in describe(NoWalls(), [], {}, 1)


def test_parse_takes_plans_out_of_a_fenced_reply():
    text = 'Sure!\n```json\n{"plans": [[2], [0, 2]], "why": "the box is the exit"}\n```'
    assert parse(text, 3) == [[2], [0, 2]]


def test_parse_drops_indices_that_do_not_exist():
    """A model that invents object 9 on a three-object board must not become a plan."""
    assert parse('{"plans": [[9], [1]]}', 3) == [[1]]


def test_parse_drops_empty_and_overlong_plans():
    assert parse('{"plans": [[], [0,1,2,3,4], [1]]}', 5) == [[1]]


def test_parse_deduplicates():
    assert parse('{"plans": [[1], [1], [0]]}', 2) == [[1], [0]]


def test_parse_survives_junk():
    for junk in ["", "no idea", "{not json", '{"plans": "all of them"}', '{"plans": [[ "a" ]]}']:
        assert parse(junk, 3) == []


def test_parse_unwraps_a_plan_paired_with_its_reason():
    """Observed from qwen2.5:7b: [[6], "reach the small object"] instead of [6]."""
    text = '{"plans": [[[6], "reach small object"], [[7, 9], "combine then exit"]]}'
    assert parse(text, 10) == [[6], [7, 9]]


def test_parse_takes_indices_out_of_an_object_shaped_plan():
    assert parse('{"plans": [{"objects": [3, 1], "why": "x"}]}', 5) == [[3, 1]]


def test_parse_accepts_a_bare_integer_as_a_one_object_plan():
    assert parse('{"plans": [2, 0]}', 5) == [[2], [0]]
