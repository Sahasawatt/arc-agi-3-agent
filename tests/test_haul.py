"""Offline checks for the carry rung. No engine, no network."""

import numpy as np

from haul import Haul, blob, crates, moved, signature

BG = 1
W = H = 64


def board(px=32, py=48, crate_at=((44, 24), (16, 28), (32, 36)), frame=(28, 28, 12, 4)):
    """A wa30-shaped board: a 4x4 piece with a colour-0 heading edge on top, 4x4
    crates with a colour-4 ring and colour-9 inner, and a wide colour-9 frame with
    a colour-2 interior."""
    g = np.full((H, W), BG, dtype=int)
    fx, fy, fw, fh = frame
    g[fy:fy + fh, fx:fx + fw] = 9
    g[fy + 1:fy + fh - 1, fx + 1:fx + fw - 1] = 2
    for cx, cy in crate_at:
        g[cy:cy + 4, cx:cx + 4] = 4
        g[cy + 1:cy + 3, cx + 1:cx + 3] = 9
    g[py:py + 4, px:px + 4] = 14
    g[py, px:px + 4] = 0
    g[H - 1, :] = 7
    return g


def learned(g=None):
    h = Haul([1, 2, 3, 4, 5])
    h.body = 14
    h.dirs = {1: (0, -4), 2: (0, 4), 3: (-4, 0), 4: (4, 0)}
    if g is not None:
        h.act(g, 0)          # latches mine / base / lattice
    return h


# -- signature ------------------------------------------------------------

def test_signature_true_on_the_family_board():
    assert signature(board())


def test_signature_needs_one_crate_bigger_than_the_rest():
    # four equal crates and no frame: re86's shape, which must NOT fire
    g = np.full((H, W), BG, dtype=int)
    for cx, cy in ((10, 10), (20, 10), (10, 20), (20, 20)):
        g[cy:cy + 4, cx:cx + 4] = 4
        g[cy + 1:cy + 3, cx + 1:cx + 3] = 9
    assert not signature(g)


def test_signature_needs_the_big_ones_inner_to_be_its_own():
    g = board(frame=(28, 28, 12, 4))
    g[29:31, 29:39] = 9          # frame interior same as the crates' inner
    assert not signature(g)


def test_signature_ignores_a_plain_board():
    assert not signature(np.full((H, W), BG, dtype=int))


def test_crates_reads_ring_inner_and_position():
    got = {(c[4], c[5]): (c[0], c[1], c[2], c[3]) for c in crates(board())}
    assert got[(44, 24)] == (4, 4, 4, 9)
    assert got[(28, 28)] == (12, 4, 9, 2)


# -- reading the piece ----------------------------------------------------

def test_moved_prefers_the_body_over_its_heading_edge():
    # the edge is a rigid translate too; the body outnumbers it
    assert moved(board(py=48), board(py=44)) == (14, (0, -4))


def test_blob_stops_at_the_pieces_own_colours():
    """A carried crate is repainted into the piece's edge colour, so a flood fill
    over everything non-background swallows the frame the moment they touch."""
    g = board(px=28, py=32)
    g[28:32, 28:32] = 0          # a carried crate sitting on the frame
    wide = blob(g, 14, set(g.ravel().tolist()) - {BG})
    own = blob(g, 14, {0, 14})
    assert max(c[0] for c in wide) > max(c[0] for c in own)
    assert max(c[0] for c in own) == 31


# -- planning -------------------------------------------------------------

def test_walk_goes_round_a_crate_instead_of_through_it():
    g = board()
    h = learned(g)
    blocked = [(32, 36, 4, 4)]
    path = h._walk((32, 32), (32, 44), (4, 4), blocked, g.shape)
    assert path is not None
    assert path != [2, 2, 2]                    # the straight line is blocked
    pos = (32, 32)
    for a in path:
        d = h.dirs[a]
        pos = (pos[0] + d[0], pos[1] + d[1])
        assert not (pos[0] < 36 and pos[0] + 4 > 32
                    and pos[1] < 40 and pos[1] + 4 > 36)
    assert pos == (32, 44)


def test_walk_treats_the_frame_as_passable():
    g = board()
    h = learned(g)
    assert h._walk((32, 32), (32, 24), (4, 4), [], g.shape) == [1, 1]


def test_approach_ends_with_a_step_toward_the_crate():
    g = board()
    h = learned(g)
    legs = h._approach((32, 44), (32, 40), 1, (4, 4), [(32, 36, 4, 4)], g.shape)
    assert legs is not None and legs[-1] == 1


def test_slots_are_latched_against_the_piece_standing_on_them():
    g = board()
    h = learned(g)
    frame = crates(g)[0]
    first = [t[:2] for t in h._slots(g, frame)]
    covered = g.copy()
    covered[28:32, 32:36] = 14                  # the piece parked on the frame
    assert [t[:2] for t in h._slots(covered, frame)] == first


def test_a_filled_slot_is_not_offered_again():
    g = board()
    h = learned(g)
    frame = crates(g)[0]
    first = h._slots(g, frame)[0][:2]
    h.filled.add(first)
    assert first not in [t[:2] for t in h._slots(g, frame)]


def test_plan_is_free_of_side_effects():
    """A debug trace that called it booked slots that were never used."""
    g = board()
    h = learned(g)
    box = h._piece(g, 1)
    h._plan(g, box)
    before = set(h.filled)
    h._plan(g, box)
    assert h.filled == before


# -- the contract ---------------------------------------------------------

def test_silent_without_the_actions_it_needs():
    assert Haul([1, 2, 3, 4]).act(board(), 0) is None
    assert Haul([1, 2, 3, 4, 5]).act(None, 0) is None


def test_a_new_level_forgets_the_old_board():
    g = board()
    h = learned(g)
    h.filled.add((28, 28))
    h.frame = crates(g)[0]
    h.act(g, 1)
    assert h.lvl == 1
    assert h.filled == set()          # the old board's slots are not this board's
    # and the frame is re-derived from THIS board rather than carried over
    assert h.frame == crates(g)[0]
