"""Offline checks for the combination-lock rung. No engine, no network."""

import numpy as np

from dial import (DIAL, SLIDE, Dial, combination, read_board, shape_key,
                  signature, top_pairs, window)

TOPBG, LOWBG = 2, 3
HFRAME, RFRAME, INK, CLAMPC, BARC = 10, 7, 5, 0, 1
H, W = 44, 48
PITCH, WIN = 7, 5
# The lower region, laid out the way tr87's is: hint strip, clamp bracket, room
# strip, clamp bracket, budget bar -- every band separated by a background row,
# or two of them merge and neither reads as a 7-row strip.
HINT_Y, TOP_Y, ROOM_Y, BOT_Y, BAR_Y = 20, 28, 31, 41, 43
ROOM_X0 = 5                        # the strip's border column
STATIONS = [6, 13, 20]             # ROOM_X0 + 1, then every PITCH

GLYPHS = {
    "a": [(0, 0), (0, 4), (2, 2), (4, 0), (4, 4)],
    "b": [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2)],
    "c": [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],
    "d": [(2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],   # "b" turned a quarter
    "e": [(1, 3), (3, 1), (4, 4)],
}


def mask(name):
    m = np.zeros((WIN, WIN), dtype=bool)
    for y, x in GLYPHS[name]:
        m[y, x] = True
    return m


def paint(g, y0, x0, m, frame, ink):
    """A 7x7 tile: solid frame colour, ink where the mask is set."""
    g[y0:y0 + 7, x0:x0 + 7] = frame
    for y in range(WIN):
        for x in range(WIN):
            if m[y, x]:
                g[y0 + 1 + y, x0 + x + 1] = ink


def strip(g, y0, names, frame, ink):
    """A 7-row station strip: frame colour, one 5-wide glyph per station."""
    g[y0:y0 + 7, ROOM_X0:ROOM_X0 + 2 + len(STATIONS) * PITCH - 2] = frame
    for x, name in zip(STATIONS, names):
        if name is None:
            continue
        m = mask(name)
        for y in range(WIN):
            for xx in range(WIN):
                if m[y, xx]:
                    g[y0 + 1 + y, x + xx] = ink


def board(hints=("a", "b", "c"), room=("b", "b", "b"), pairs=(("a", "c"), ("b", "e")),
          clamp=STATIONS[0], bar=True):
    """A tr87-shaped board. `pairs` are (icon glyph, block glyph): the icon
    names a station through the hint strip, the block names that station's
    target. Two pairs per top band, one band per two pairs -- the real board's
    shape, and the one that catches a per-band scan."""
    g = np.full((H, W), TOPBG, dtype=int)
    g[HINT_Y:] = LOWBG
    for i, (icon, block) in enumerate(pairs):
        y0 = 2 + (i // 2) * 9
        x0 = 2 + (i % 2) * 19
        paint(g, y0, x0, mask(icon), HFRAME, INK)
        paint(g, y0, x0 + 10, mask(block), RFRAME, INK)
        # The connector the real board draws across the gap, which is why the
        # two tiles of a pair are ONE column run and the pairs of a row are two.
        g[y0 + 3, x0 + 7:x0 + 10] = LOWBG
    strip(g, HINT_Y, hints, HFRAME, INK)
    strip(g, ROOM_Y, room, RFRAME, INK)
    for y in (TOP_Y, TOP_Y + 1, BOT_Y - 1, BOT_Y):
        g[y, clamp:clamp + WIN] = CLAMPC
    if bar:
        g[BAR_Y, :] = BARC
    return g


def test_read_board_finds_both_strips_and_the_station_lattice():
    b = read_board(board())
    assert b is not None
    assert (b["hint"], b["room"]) == (HINT_Y, ROOM_Y)
    assert b["stations"] == STATIONS
    assert (b["hframe"], b["hink"]) == (HFRAME, INK)
    assert (b["rframe"], b["rink"]) == (RFRAME, INK)


def test_read_board_reads_the_clamp_as_the_station_it_is_parked_at():
    assert read_board(board(clamp=STATIONS[1]))["clamp"] == STATIONS[1]


def test_read_board_none_on_a_board_with_no_strips():
    g = np.full((H, W), LOWBG, dtype=int)
    g[BAR_Y, :] = BARC
    assert read_board(g) is None


def test_read_board_none_on_an_empty_frame():
    assert read_board(np.zeros((0, 0), dtype=int)) is None


def test_top_pairs_finds_every_pair_not_one_per_row_band():
    # Two pairs share a row band; a scan that iterates bands and keeps the last
    # tile of each kind silently returns one. This is the bug the live probe hit
    # (`results/tr87-probe20.txt`: 3 pairs found where the board has 6).
    assert len(top_pairs(board(), read_board(board()))) == 2


def test_combination_names_a_station_through_its_hint():
    g = board(hints=("a", "b", "c"), pairs=(("a", "c"), ("b", "d")))
    b = read_board(g)
    assert combination(g, b) == {STATIONS[0]: shape_key(mask("c")),
                                 STATIONS[1]: shape_key(mask("d"))}


def test_combination_matches_a_hint_up_to_rotation():
    # "d" is "b" turned a quarter: three of tr87's five icons only match their
    # hint under the dihedral canon (`results/tr87-probe16.txt`).
    g = board(hints=("a", "d", "c"), pairs=(("b", "c"),))
    assert list(combination(g, read_board(g))) == [STATIONS[1]]


def test_combination_drops_a_pair_whose_icon_names_no_station():
    # tr87's sixth pair is exactly this and is not part of the combination.
    g = board(hints=("a", "b", "c"), pairs=(("a", "c"), ("e", "d")))
    assert list(combination(g, read_board(g))) == [STATIONS[0]]


def test_combination_drops_an_icon_that_names_two_stations():
    g = board(hints=("a", "a", "c"), pairs=(("a", "c"),))
    assert combination(g, read_board(g)) == {}


def test_signature_true_on_the_family_board():
    assert signature(board()) is True


def test_signature_false_with_only_one_named_station():
    assert signature(board(pairs=(("a", "c"),))) is False


def test_signature_false_on_a_plain_board():
    assert signature(np.full((H, W), LOWBG, dtype=int)) is False


def test_signature_false_on_an_empty_frame():
    assert signature(np.zeros((0, 0), dtype=int)) is False


def driver():
    return Dial([1, 2, 3, 4])


def test_act_dials_the_station_the_clamp_is_parked_at():
    # station 0 wants "c" and shows "b" -> dial it.
    g = board(room=("b", "b", "b"), clamp=STATIONS[0])
    assert driver().act(g, 0) == DIAL


def test_act_slides_on_when_the_parked_station_already_matches():
    g = board(room=("c", "b", "b"), clamp=STATIONS[0])
    assert driver().act(g, 0) == SLIDE


def test_act_none_once_every_named_station_holds_its_target():
    g = board(room=("c", "e", "b"), clamp=STATIONS[0])
    assert driver().act(g, 0) is None


def test_act_off_without_the_two_actions_it_needs():
    assert Dial([3, 4]).act(board(), 0) is None


def test_act_none_on_an_empty_frame_without_giving_up():
    d = driver()
    assert d.act(np.zeros((0, 0), dtype=int), 0) is None
    assert d.done is False
    assert d.act(board(), 0) == DIAL


def test_act_gives_up_on_a_station_a_full_turn_never_answers():
    d, g = driver(), board(room=("b", "e", "b"), clamp=STATIONS[0])
    seen = [d.act(g, 0) for _ in range(9)]
    assert seen[0] == DIAL and seen[-1] is None
    # It stops dialing a station whose target never appears, and since the only
    # other named station already holds, there is nothing left to do.
    assert d.done is True


def test_act_retires_when_the_combination_is_unreadable():
    # hints ("a", "a", "c"): one icon names two stations, combination() drops
    # it and answers {} -- fewer than two targets is a misread board, and the
    # driver must RETIRE (done = True), not merely pass this frame: a driver
    # that answers None while staying live is re-consulted forever.
    d = driver()
    g = board(hints=("a", "a", "c"), pairs=(("a", "c"),))
    assert d.act(g, 0) is None
    assert d.done is True


def test_act_moves_on_rather_than_giving_up_while_another_station_is_live():
    d = driver()
    g = board(room=("b", "b", "b"), clamp=STATIONS[0])
    outs = [d.act(g, 0) for _ in range(9)]
    assert outs[-1] == SLIDE and d.done is False


def test_a_new_level_forgets_the_presses_spent_on_the_old_one():
    d, g = driver(), board(room=("b", "b", "b"), clamp=STATIONS[0])
    for _ in range(9):
        d.act(g, 0)
    assert d.act(g, 0) == SLIDE       # station 0 is spent at level 0
    assert d.act(g, 1) == DIAL        # ... and live again on a new board


def test_act_none_when_the_clamp_cannot_be_found():
    g = board()
    g[TOP_Y:TOP_Y + 2] = LOWBG
    g[BOT_Y - 1:BOT_Y + 1] = LOWBG
    assert driver().act(g, 0) is None


def test_window_reads_the_strips_interior():
    g = board(room=("c", "b", "b"))
    assert np.array_equal(window(g, ROOM_Y, STATIONS[0], INK), mask("c"))
