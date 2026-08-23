"""Offline checks for the skewer rung. No engine, no network."""

import numpy as np

from skewer import (Skewer, braid_cluster, read_static, signature,
                    solid_blocks, weave_rows)

BG, FLOOR = 5, 4
WEAVE_A, WEAVE_B = 1, 2
FRAME = 6
H, W = 64, 64
ARM_Y = 38            # the arm's two rows at reset, y38-39
MACHINE_X = 11        # machine box x11-16
ROOM = (11, 12, 47, 41)


def braid(n, first=WEAVE_A):
    """n cells of the 112112 weave, the phase sk48 draws on its upper row."""
    pat = [WEAVE_A, WEAVE_A, WEAVE_B] if first == WEAVE_A else \
          [WEAVE_B, WEAVE_B, WEAVE_A]
    return [pat[i % 3] for i in range(n)]


def board(arm_y=ARM_Y, arm_len=6, stock=((8, 42, 19), (9, 42, 25), (14, 42, 31)),
          recipe=(8, 14, 9), pierced=()):
    """An sk48-shaped board: room of FLOOR on BG, a machine box with a woven
    2-row arm, wall stock blocks, and a HUD picture below the room whose
    block colours read left-to-right as `recipe`."""
    g = np.full((H, W), BG, dtype=int)
    x0, y0, x1, y1 = ROOM
    g[y0:y1 + 1, x0:x1 + 1] = FLOOR
    # machine: a frame around the arm's start
    g[arm_y - 2:arm_y + 4, MACHINE_X:MACHINE_X + 6] = FRAME
    g[arm_y - 1:arm_y + 3, MACHINE_X + 1:MACHINE_X + 5] = 0
    # the family board's machine interior carries frame-coloured marks -- it
    # is never a solid 4x4, and stock detection leans on that. The marks sit
    # on the rows OUTSIDE the arm's own, so no {0, 6} row-pair can imitate a
    # second braid cluster.
    g[arm_y - 1, MACHINE_X + 2:MACHINE_X + 4] = FRAME
    g[arm_y + 2, MACHINE_X + 2:MACHINE_X + 4] = FRAME
    ax = MACHINE_X + 6
    for i, v in enumerate(braid(arm_len)):
        g[arm_y, ax + i] = v
    for i, v in enumerate(braid(arm_len, WEAVE_B)):
        g[arm_y + 1, ax + i] = v
    # A threaded block RIDES the arm: it sits on the arm's rows with braid
    # arriving at its left edge, never at its wall slot (`sk48-p5.txt`).
    ridden = [c for c, _, _ in stock if c in pierced]
    for i, c in enumerate(ridden):
        bx = 36 - 6 * i
        g[arm_y - 1:arm_y + 3, bx:bx + 4] = c
        g[arm_y, bx - 1] = WEAVE_A
        g[arm_y + 1, bx - 1] = WEAVE_B
    for c, bx, by in stock:
        if c in pierced:
            continue
        g[by:by + 4, bx:bx + 4] = c
    # HUD picture: blocks in recipe order below the room, braid bits between
    hx = 20
    for c in recipe:
        g[57:61, hx:hx + 4] = c
        hx += 6
    return g


def test_weave_rows_reads_the_period_three_braid():
    g = board()
    ys = [y for y, cols in weave_rows(g, BG) if cols == frozenset({1, 2})]
    assert ys == [ARM_Y, ARM_Y + 1]


def test_weave_rows_rejects_a_run_with_a_triple():
    # The scanner may keep a clean >=6 SUB-run of a longer corrupted run (it
    # restarts one cell later), so the rejection case is a run whose only
    # clean suffix is under the minimum.
    g = np.full((10, 20), BG, dtype=int)
    g[4, 3:9] = [1, 1, 1, 2, 1, 1]
    assert weave_rows(g, BG) == []


def test_weave_rows_rejects_a_single_colour_run():
    g = np.full((10, 20), BG, dtype=int)
    g[4, 3:11] = 1
    assert weave_rows(g, BG) == []


def test_braid_cluster_wants_exactly_one_adjacent_pair():
    assert braid_cluster(board()) == ([ARM_Y, ARM_Y + 1], frozenset({1, 2}))
    g = board()
    for i, v in enumerate(braid(8)):           # a second braid pair elsewhere
        g[5, 30 + i] = v
    for i, v in enumerate(braid(8, WEAVE_B)):
        g[6, 30 + i] = v
    assert braid_cluster(g) is None


def test_read_static_splits_stock_from_recipe_by_the_room():
    b = read_static(board())
    assert b is not None
    assert [c for c, _, _ in b["stock"]] == [8, 9, 14]
    assert b["recipe"] == [8, 14, 9]
    assert b["arm_rows"] == [ARM_Y, ARM_Y + 1]


def test_read_static_survives_a_wall_to_wall_arm():
    # Arm clear across the room: its rows hold no floor cell, and the floor
    # is SPLIT in two -- both halves' blocks must stay in stock.
    g = board(arm_y=26, arm_len=24, stock=((8, 42, 19), (14, 42, 31)))
    b = read_static(g, FLOOR)
    assert b is not None
    assert {c for c, _, _ in b["stock"]} == {8, 14}


def test_read_static_none_without_a_braid():
    g = np.full((H, W), BG, dtype=int)
    assert read_static(g) is None


def test_signature_true_on_the_family_board():
    assert signature(board()) is True


def test_signature_false_without_hud_blocks():
    assert signature(board(recipe=())) is False


def test_signature_false_without_stock():
    assert signature(board(stock=())) is False


def test_signature_false_on_an_empty_frame():
    assert signature(np.zeros((0, 0), dtype=int)) is False


def driver(known=True):
    sk = Skewer([1, 2, 3, 4, 7])
    if known:
        sk.up, sk.down, sk.ext, sk.ret = 1, 2, 4, 3
        # The floor is latched from the level's first clean read; tests that
        # start mid-level (arm at a pierced block) must carry it the same
        # way the live driver does -- deriving it fresh there reads the
        # block as the floor.
        sk.lvl, sk.floor = 0, FLOOR
    return sk


def test_act_moves_toward_the_first_recipe_block():
    # First recipe colour is 8 at rows 19-22; the arm sits at 38 -> up.
    sk = driver()
    assert sk.act(board(), 0) == 1


def test_act_extends_once_aligned():
    sk = driver()
    assert sk.act(board(arm_y=20), 0) == 4


def test_act_targets_in_recipe_order_not_row_order():
    # 8 pierced already: next is 14 (recipe 8, 14, 9), NOT 9 -- even though
    # 9's rows are nearer the arm.
    sk = driver()
    g = board(arm_y=20, pierced=(8,))
    assert sk.act(g, 0) == 2          # down toward 14 at y31, past 9 at y25
    sk2 = driver()
    assert sk2.act(board(arm_y=32, pierced=(8,)), 0) == 4   # aligned with 14


def test_act_retracts_when_a_vertical_press_is_refused():
    sk = driver()
    g = board(arm_y=20, pierced=(8,))
    assert sk.act(g, 0) == 2
    # Same frame handed back: the down press did nothing (threaded block
    # against the wall) -> one retract.
    assert sk.act(g, 0) == 3


def test_act_learns_a_control_by_pressing_an_untried_action():
    sk = driver(known=False)
    v = sk.act(board(), 0)
    assert v in (1, 2, 3, 4, 7)       # some untried press, not a crash


def test_act_labels_the_press_that_moved_the_arm_up():
    sk = driver(known=False)
    first = sk.act(board(), 0)
    sk.act(board(arm_y=ARM_Y - 6), 0)
    assert sk.up == first


def test_act_learns_retract_from_a_collapsed_arm():
    sk = driver(known=False)
    sk.act(board(), 0)                      # latch the level, store prev
    sk.last = 3                             # pretend the press was action 3
    g = np.full((H, W), BG, dtype=int)      # no braid anywhere
    x0, y0, x1, y1 = ROOM
    g[y0:y1 + 1, x0:x1 + 1] = FLOOR
    sk.act(g, 0)
    assert sk.ret == 3


def test_act_none_on_an_empty_frame_without_giving_up():
    sk = driver()
    assert sk.act(np.zeros((0, 0), dtype=int), 0) is None
    assert sk.done is False


def test_act_done_once_every_recipe_block_is_threaded():
    sk = driver()
    g = board(arm_y=20, pierced=(8, 9, 14))
    assert sk.act(g, 0) is None
    assert sk.done is True


def test_act_off_without_enough_actions():
    assert Skewer([1, 2]).act(board(), 0) is None


def test_a_new_level_resets_the_recipe():
    sk = driver()
    sk.act(board(), 0)
    assert sk.recipe == [8, 14, 9]
    sk.act(board(recipe=(9, 8, 14)), 1)
    assert sk.recipe == [9, 8, 14]
