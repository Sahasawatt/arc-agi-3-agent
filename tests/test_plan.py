import numpy as np

from discover import Model
from plan import bfs, bfs_all, route_to


def model(rows=5):
    # evidence=(1, 1) is load-bearing: discover.Model treats `blocking` as
    # meaningless while evidence[1] == 0 (discover.py:52), so a fixture without
    # it has no walls at all. And `rows` must MATCH the test grid: rows=5 over a
    # 3x3 grid lets bfs step below the board, where numpy's negative indexing
    # wraps to the top row and routes around every wall (measured: [2,2,2,4,4,1]
    # on a sealed goal).
    return Model(1, {1}, 9, (1, 1), {1: (0, -1), 2: (0, 1),
                                    3: (-1, 0), 4: (1, 0)}, 1,
                 {1}, {0}, rows, parts=((9, 1, 1),), evidence=(1, 1))


def test_bfs_finds_a_shortest_route_and_bfs_all_reaches_the_board():
    m = model()
    grid = np.ones((5, 5), dtype=int)
    assert bfs(grid, m, (0, 0), {(2, 0)}) == [4, 4]
    assert (4, 4) in bfs_all(grid, m, (0, 0))


def test_bfs_returns_none_when_walls_make_the_goal_unreachable():
    m = model(rows=3)
    grid = np.ones((3, 3), dtype=int)
    grid[0, 1:] = 0
    grid[1:, 1] = 0
    assert bfs(grid, m, (0, 0), {(2, 2)}) is None


def test_bfs_and_route_to_are_empty_when_already_there():
    m = model(rows=3)
    grid = np.ones((3, 3), dtype=int)
    assert bfs(grid, m, (1, 1), {(1, 1)}) == []
    frame = [grid.copy()]
    frame[0][1, 1] = 9
    assert route_to(frame, m, {"colour": 5, "x": [1, 1], "y": [1, 1],
                               "cells": 1}) == []
