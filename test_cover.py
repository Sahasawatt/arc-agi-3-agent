"""Offline checks for the framed-box rung. No engine, no network."""

import numpy as np

from cover import at, boxes, candidates, group_plan, route, signature, swatch_zone, swatches

BG = 5


def board():
    """A 64x64 board with two 3x3-framed boxes and nothing else."""
    g = np.full((64, 64), BG, dtype=int)
    for cx, cy, ink in ((10, 10, 9), (40, 40, 11)):
        g[cy - 1:cy + 2, cx - 1:cx + 2] = 4
        g[cy, cx] = ink
    return g


def test_boxes_reads_inner_colour_not_the_frame():
    assert boxes(board()) == {(10, 10): 9, (40, 40): 11}


def test_signature_needs_four_boxes():
    g = board()
    assert not signature(g)          # two is not the family
    for cx, cy in ((20, 20), (30, 30)):
        g[cy - 1:cy + 2, cx - 1:cx + 2] = 4
        g[cy, cx] = 9
    assert signature(g)


def test_signature_ignores_a_plain_block():
    g = np.full((64, 64), BG, dtype=int)
    g[10:13, 10:13] = 7            # a solid 3x3 is not a ring round a different colour
    assert not signature(g)


def test_at_finds_the_single_marker():
    g = board()
    g[45, 36] = 0
    assert at(g) == (36, 45)
    assert at(board()) is None


def test_route_walks_the_3_lattice_and_refuses_frame_cells():
    lava = {(int(x), int(y)) for y, x in zip(*np.nonzero(board() == 4))}
    path = route((36, 45), (36, 30), lava)
    assert path == [1] * 5
    # a centre standing on a frame cell is GAME_OVER, so (9, 9) is not a place
    assert route((12, 40), (9, 9), lava) is None
    assert route((12, 40), (12, 10), lava) == [1] * 10   # alongside it is fine


def test_route_clamps_at_the_board_edge():
    assert len(route((0, 45), (0, 45), set())) == 0
    assert route((3, 45), (0, 45), set()) == [3]


PLUS = {(0, d) for d in range(-13, 14)} | {(d, 0) for d in range(-13, 14)}
DIAG = {(d, d) for d in range(-10, 11)} | {(d, -d) for d in range(-10, 11)}


def test_candidates_finds_the_intersection_of_a_plus_group():
    bxs = {(48, 16): 9, (40, 24): 9, (53, 24): 9, (48, 35): 9}
    cov, centre = candidates({"pos": (36, 45), "offs": PLUS}, bxs, set())[0]
    assert centre == (48, 24) and len(cov) == 4


def test_candidates_respects_the_shapes_own_lattice():
    bxs = {(48, 16): 9, (40, 24): 9, (53, 24): 9, (48, 35): 9}
    # a shape spawned one cell off the lattice can never reach (48, 24)
    cands = candidates({"pos": (37, 45), "offs": PLUS}, bxs, set())
    assert all(c != (48, 24) for _, c in cands)


def test_group_plan_partitions_boxes_between_two_shapes():
    gb = {(48, 16): 9, (40, 24): 9, (53, 24): 9, (48, 35): 9,
          (20, 20): 9, (40, 20): 9, (20, 40): 9, (40, 40): 9}
    shapes = [{"pos": (36, 45), "colour": 9, "offs": PLUS},
              {"pos": (21, 27), "colour": 9, "offs": DIAG}]
    got = group_plan(shapes, gb, set())
    assert got is not None
    centres = dict(got)
    assert centres[0] == (48, 24)             # the plus takes its own intersection
    assert centres[1] == (30, 30)             # the diagonal takes the diamond four


def test_group_plan_none_when_the_boxes_cannot_all_be_covered():
    gb = {(48, 16): 9, (40, 24): 9, (53, 24): 9, (48, 35): 9, (1, 1): 9}
    shapes = [{"pos": (36, 45), "colour": 9, "offs": PLUS}]
    assert group_plan(shapes, gb, set()) is None


def test_swatches_reads_inner_rect_and_skips_plain_blocks():
    g = np.full((64, 64), BG, dtype=int)
    g[4:10, 4:10] = 2                # ring
    g[5:9, 5:9] = 12                 # inner 4x4
    g[20:24, 20:24] = 7              # solid block on bare background: no station
    assert swatches(g, BG) == {12: (5, 5, 8, 8)}


def test_swatch_zone_is_the_block_dilated_by_the_shape():
    # a 1-cell "shape" keeps only the block and its ring out
    zone = swatch_zone({(0, 0)}, [(5, 5, 8, 8)])
    assert (4, 4) in zone and (9, 9) in zone and (10, 5) not in zone
    # an arm reaching +3 keeps centres 3 left of the block out too
    zone = swatch_zone({(0, 0), (3, 0)}, [(5, 5, 8, 8)])
    assert (1, 5) in zone
