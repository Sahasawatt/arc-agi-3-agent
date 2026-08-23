"""Offline checks for the fixed-pitch maze rung. No engine, no network."""

import numpy as np

from maze import (Maze, bands, blocks, find_goal, lattice_bfs, notched_all,
                   signature, _gap, _gap_colours, _passable)

BG, OPEN, WALL, BUDGET = 5, 2, 0, 6
BODY, NOTCH, GOAL_C = 9, 4, 14
H, W = 22, 21
RESTS = [(x, y) for x in (3, 9, 15) for y in (3, 9, 15)]


def board(walls=(), piece=(3, 3), notch="right", goal=(15, 15), extra=(),
          bar=W, no_piece=False):
    """A tu93-shaped maze on a small 3x3 lattice of rest positions (step 6,
    piece 3x3): a budget row on the bottom edge, an open/wall lattice built
    from the same `_gap` math the driver itself reads, a notched piece and a
    solid goal block."""
    g = np.full((H, W), BG, dtype=int)
    for (x, y) in RESTS:
        g[y:y + 3, x:x + 3] = OPEN
    closed = {frozenset(w) for w in walls}
    for (x, y) in RESTS:
        for d in ((6, 0), (0, 6), (-6, 0), (0, -6)):
            nx, ny = x + d[0], y + d[1]
            if (nx, ny) not in RESTS:
                continue
            r = _gap((x, y, 3, 3), d, (3, 3))
            if r is None:
                continue
            gx, gy, gw, gh = r
            c = WALL if frozenset({(x, y), (nx, ny)}) in closed else OPEN
            g[gy:gy + gh, gx:gx + gw] = c
    if not no_piece:
        px, py = piece
        g[py:py + 3, px:px + 3] = BODY
        nx, ny = {"right": (px + 2, py + 1), "left": (px, py + 1),
                  "up": (px + 1, py), "down": (px + 1, py + 2)}[notch]
        g[ny, nx] = NOTCH
    if goal is not None:
        gx, gy = goal
        g[gy:gy + 3, gx:gx + 3] = GOAL_C
    for (ex, ey, ec) in extra:
        g[ey, ex] = ec
    g[H - 1, :bar] = BUDGET
    return g


DIRS = {1: (0, -6), 2: (0, 6), 3: (-6, 0), 4: (6, 0)}


def learned():
    """A driver that already knows the game facts -- piece colours, size,
    arrow mapping, open colour -- but has not read a single frame yet this
    level (goal unknown, budget-watch unlatched)."""
    mz = Maze([1, 2, 3, 4])
    mz.lvl = 0
    mz.body, mz.notch, mz.size = BODY, NOTCH, (3, 3)
    mz.dirs = dict(DIRS)
    mz.open_colours = {OPEN}
    return mz


def ready(goal=(15, 15), piece=(3, 3), bar=W, **state):
    """`learned()`, plus the level's first round -- which is where the
    driver latches the budget-watch colours and finds the goal. Setting
    counters BEFORE that call sets them on a driver about to derive its
    own, a fixture agreeing with itself rather than with the code (the
    same trap `swap.py`'s own `ready()` guards against)."""
    mz = learned()
    mz.act(board(piece=piece, goal=goal, bar=bar), 0)
    for k, v in state.items():
        setattr(mz, k, v)
    return mz


# -- signature --------------------------------------------------------

def test_signature_true_on_the_family_board():
    assert signature(board())


def test_signature_false_without_a_piece():
    assert not signature(board(no_piece=True))


def test_signature_false_with_more_than_one_notched_window():
    # a second notch-shaped decoy elsewhere on the board -- tu93's own
    # signature is EXACTLY one hit, not "at least one"
    extra = [(10, 10, 7), (10, 11, 7), (11, 10, 7), (11, 11, 7),
             (12, 10, 7), (10, 12, 7), (11, 12, 7), (12, 12, 7), (12, 11, 3)]
    assert not signature(board(extra=extra))


def test_signature_ignores_a_plain_board():
    assert not signature(np.full((H, W), BG, dtype=int))


# -- notched_all --------------------------------------------------------

def test_notched_all_finds_body_and_notch_at_the_pieces_corner():
    got = notched_all(board(piece=(3, 3), notch="right"), {BG})
    assert got == [(3, 3, BODY, NOTCH)]


def test_notched_all_excludes_a_named_colour():
    assert notched_all(board(), {BG, BODY}) == []


# -- bands --------------------------------------------------------------

def test_bands_finds_only_the_budget_row():
    got = bands(board())
    assert got == [(H - 1, H - 1, BUDGET)]


def test_bands_empty_once_the_bar_has_burnt():
    # a bar that is not full width is not a band -- swap.py's exact lesson
    assert bands(board(bar=W - 3)) == []


# -- goal detection -------------------------------------------------------

def test_find_goal_ignores_a_smaller_decoy():
    # a 1-cell speck and the real 3x3 goal both pass the "lone region"
    # filter; only the goal matches the piece's own size
    g = board(extra=[(1, 1, 7)])
    excl = {BG, BODY, NOTCH, OPEN}
    assert find_goal(g, excl, (3, 3)) == (15, 15, 3, 3)


def test_find_goal_ignores_a_colour_that_tiles_the_board():
    # WALL(0) in two SEPARATE segments -- never a lone region, unlike a
    # single wall cell which would (wrongly) look just like the goal
    g = board(walls={frozenset({(3, 3), (9, 3)}), frozenset({(3, 15), (9, 15)})})
    excl = {BG, BODY, NOTCH, OPEN}
    found = find_goal(g, excl, (3, 3))
    assert found == (15, 15, 3, 3)


def test_blocks_requires_the_exact_piece_size():
    g = board()
    excl = {BG, BODY, NOTCH, OPEN}
    assert blocks(g, excl, (4, 4)) == []


# -- gap / passable ---------------------------------------------------------

def test_gap_reads_the_strip_between_two_rest_cells():
    r = _gap((3, 3, 3, 3), (6, 0), (3, 3))
    assert r == (6, 3, 3, 3)


def test_gap_is_none_when_the_step_equals_the_piece_extent():
    assert _gap((3, 3, 3, 3), (3, 0), (3, 3)) is None


def test_passable_true_through_an_open_connector():
    g = board()
    assert _passable(g, (3, 3, 3, 3), (6, 0), (3, 3), {OPEN})


def test_passable_false_through_a_wall():
    g = board(walls={frozenset({(3, 3), (9, 3)})})
    assert not _passable(g, (3, 3, 3, 3), (6, 0), (3, 3), {OPEN})


def test_passable_false_for_an_unproven_colour():
    # the connector really is open, but the colour has never been PROVEN
    # open -- unproven is treated as blocked, never guessed passable
    g = board()
    assert not _passable(g, (3, 3, 3, 3), (6, 0), (3, 3), set())


def test_gap_colours_reads_from_the_frame_handed_to_it():
    g = board()
    assert _gap_colours(g, (3, 3, 3, 3), (6, 0), (3, 3)) == {OPEN}


# -- lattice_bfs ------------------------------------------------------------

def test_bfs_finds_the_direct_route():
    g = board()
    path = lattice_bfs((3, 3), (9, 3), DIRS, (3, 3), {OPEN}, g)
    assert path == [4]


def test_bfs_routes_around_a_wall():
    g = board(walls={frozenset({(3, 3), (9, 3)})})
    path = lattice_bfs((3, 3), (9, 3), DIRS, (3, 3), {OPEN}, g)
    assert path is not None and path != [4]
    pos = (3, 3)
    for a in path:
        pos = (pos[0] + DIRS[a][0], pos[1] + DIRS[a][1])
    assert pos == (9, 3)


def test_bfs_returns_none_when_unreachable():
    g = board(walls={frozenset({(3, 3), (9, 3)}), frozenset({(3, 3), (3, 9)})})
    assert lattice_bfs((3, 3), (15, 15), DIRS, (3, 3), {OPEN}, g) is None


def test_bfs_honours_the_avoid_set():
    # (3, 3) is a corner whose only OTHER neighbour is walled off, so (9, 3)
    # is the sole way out -- avoiding it must strand the start entirely
    g = board(walls={frozenset({(3, 3), (3, 9)})})
    assert lattice_bfs((3, 3), (15, 3), DIRS, (3, 3), {OPEN}, g) is not None
    assert lattice_bfs((3, 3), (15, 3), DIRS, (3, 3), {OPEN}, g, {(9, 3)}) is None


# -- the contract -----------------------------------------------------------

def test_silent_without_the_actions_it_needs():
    assert Maze([1, 2, 3]).act(board(), 0) is None
    assert Maze([1, 2, 3, 4]).act(None, 0) is None


def test_reaching_the_goal_returns_none():
    # `self.goal` preset directly (not via find_goal): the piece standing
    # ON the goal occludes the goal's own colour in the frame, so this is
    # the short-circuit branch, not a goal-detection round.
    mz = learned()
    mz.goal = (3, 3)
    assert mz.act(board(piece=(3, 3), goal=(15, 15)), 0) is None


def test_a_new_level_forgets_the_goal_but_keeps_the_learned_game_facts():
    mz = ready(goal=(15, 15))
    assert mz.goal == (15, 15)
    mz.act(board(piece=(3, 3), goal=(9, 9), bar=W), 1)
    assert mz.lvl == 1
    assert mz.goal == (9, 9)           # re-derived from the new board, not stale
    assert mz.dirs == DIRS              # arrows are a game fact
    assert mz.open_colours == {OPEN}    # so is the open colour


def test_routes_toward_the_goal_when_everything_is_known():
    mz = learned()
    mz.goal = (9, 3)
    a = mz.act(board(piece=(3, 3), goal=(9, 3)), 0)
    assert a == 4


# -- bootstrap: learning the four directions by acting -----------------

def test_bootstrap_learns_all_four_directions_from_a_boxed_corner():
    """From (3, 3) -- the grid's own corner -- up and left run off the
    board; only right and down work at first. The Haul-style retry loop
    must still learn all four by walking to a position where the rest can
    be tried (Trap 1: a refusal is not retried in place forever)."""
    mz = Maze([1, 2, 3, 4])
    g = board(piece=(3, 3), notch="right")
    pos = (3, 3)
    for _ in range(40):
        a = mz.act(g, 0)
        if a is None:
            break
        if len(mz.dirs) == 4:
            break
        d = DIRS[a]
        nxt = (pos[0] + d[0], pos[1] + d[1])
        moved = nxt in RESTS and 0 <= nxt[0] and 0 <= nxt[1]
        if moved:
            pos = nxt
        notch = {(0, -6): "up", (0, 6): "down", (-6, 0): "left", (6, 0): "right"}[d] \
            if moved else "right"
        g = board(piece=pos, notch=notch)
    assert mz.dirs == DIRS


def test_a_heading_change_still_teaches_a_direction():
    """The notch moves to a different side of the 3x3 on a heading change,
    so the BODY colour alone is not a pure translation between the two
    frames -- only the union (body | notch) reads as rigid. Drive one
    press whose heading differs from the piece's current facing and check
    the direction still gets learned."""
    mz = Maze([1, 2, 3, 4])
    mz.body, mz.notch, mz.size = BODY, NOTCH, (3, 3)
    mz.lvl, mz.latched = 0, True
    g1 = board(piece=(9, 3), notch="right")   # facing right
    mz.act(g1, 0)                              # latches self.prev = g1
    mz.prev, mz.last = g1, 2                   # about to press DOWN
    g2 = board(piece=(9, 9), notch="down")     # moved down, notch flipped
    mz.act(g2, 0)
    assert mz.dirs.get(2) == (0, 6)


# -- the life-reset guard ------------------------------------------------

def test_a_life_reset_teaches_the_arrows_nothing():
    """A GAME_OVER puts the piece back at the level's start -- that IS a
    rigid translation, so a frame pair straddling one must not be read as
    a real press (`swap.py`'s exact lesson)."""
    mz = ready(piece=(15, 15), goal=(9, 15), bar=W)   # latches the watch, full bar
    mz.act(board(piece=(15, 15), goal=(9, 15), bar=W - 1), 0)   # watch -> W-1
    mz.prev = board(piece=(15, 15), goal=(9, 15), bar=W - 1)
    mz.last = 4
    before = dict(mz.dirs)
    g = board(piece=(3, 3), goal=(9, 15), bar=W)  # reset: back at the start, refilled
    mz.act(g, 0)
    assert dict(mz.dirs) == before


def test_a_life_reset_adds_the_would_be_target_to_avoid():
    mz = ready(piece=(3, 3), goal=(9, 3), bar=W)  # latches the watch, full bar
    out = mz.act(board(piece=(3, 3), goal=(9, 3), bar=W - 1), 0)   # watch -> W-1
    assert out == 4                                # the one-step route to the goal
    g = board(piece=(3, 3), goal=(9, 3), bar=W)    # reset: back at start, refilled
    mz.act(g, 0)
    assert (9, 3) in mz.avoid


def test_an_honest_move_does_not_pollute_avoid():
    mz = ready(piece=(3, 3), goal=(9, 3), bar=W)
    out = mz.act(board(piece=(3, 3), goal=(9, 3), bar=W - 1), 0)
    assert out == 4
    g = board(piece=(9, 3), goal=(9, 3), bar=W - 2)   # a normal successful step
    mz.act(g, 0)
    assert mz.avoid == set()
