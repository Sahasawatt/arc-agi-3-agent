"""Offline checks for the control-transfer rung. No engine, no network."""

import numpy as np

from swap import Swap, bands, blocks, moved, shifted, signature

BG, MINE, CLOCK, FLOOR = 12, 9, 14, 1
W = H = 64


def board(x=12, y=16, bar=64, w=20, h=4, mine=MINE, floor=True, clock=True):
    """An sp80-shaped board: a clock band on the top edge that BURNS from the
    right, a solid band on the bottom edge, and one driven block."""
    g = np.full((H, W), BG, dtype=int)
    if clock:
        g[0, :bar] = CLOCK
        g[0, bar:] = 0
    if floor:
        g[H - 4:H, :] = FLOOR
    if mine is not None:
        g[y:y + h, x:x + w] = mine
    return g


def drive(sw, frames, lvl=0):
    """Feed frames in order, collect the actions asked for."""
    return [sw.act(g, lvl) for g in frames]


def learned():
    """A driver that has already read the board and the arrows."""
    sw = Swap([1, 2, 3, 4, 5])
    sw.mine = MINE
    sw.dirs = {1: (0, -4), 2: (0, 4), 3: (-4, 0), 4: (4, 0)}
    return sw


def ready(**state):
    """`learned()`, plus the first round -- which is where the driver latches the
    clock colours and clears the level's state. Setting counters BEFORE that call
    sets them on a driver that is about to wipe them, which is a fixture agreeing
    with itself rather than with the code."""
    sw = learned()
    sw.act(board(bar=64), 0)
    for k, v in state.items():
        setattr(sw, k, v)
    return sw


# -- signature ------------------------------------------------------------

def test_signature_true_on_the_family_board():
    assert signature(board())


def test_signature_needs_a_band_on_both_edges():
    assert not signature(board(floor=False))     # top band only: re86's shape
    assert not signature(board(clock=False))     # bottom band only: most of the roster


def test_signature_needs_a_block_narrower_than_the_board():
    # both bands, but the only large solid thing spans the width -- dc22's shape,
    # measured as the one other game with two edge bands (`results/sp80-sig.txt`)
    g = board(mine=None)
    g[10:20, :] = 3
    assert not signature(g)


def test_signature_ignores_a_plain_board():
    assert not signature(np.full((H, W), BG, dtype=int))


def test_bands_merges_contiguous_rows_and_keeps_only_the_edges():
    g = board()
    g[30, :] = 7                                  # a full-width row in mid-board
    assert bands(g) == [(0, 0, CLOCK), (H - 4, H - 1, FLOOR)]


def test_blocks_skips_full_width_rectangles():
    got = blocks(board())
    assert (80, MINE, 12, 16, 20, 4) in got
    assert all(b[4] < W for b in got)


# -- reading motion -------------------------------------------------------

def test_moved_reads_the_colour_and_its_vector():
    assert moved(board(x=12), board(x=16)) == (MINE, (4, 0))


def test_shifted_refuses_a_body_that_was_partly_covered():
    a = board(x=12)
    b = board(x=12)
    b[16:18, 12:14] = BG                          # two cells hidden, not a move
    assert shifted(a, b, MINE) is None


def test_shifted_refuses_a_body_that_did_not_move():
    assert shifted(board(x=12), board(x=12), MINE) is None


# -- the magazine ---------------------------------------------------------

def test_a_life_reset_is_seen_after_the_clock_has_burnt():
    """The clock is a full-width BAND only while it is full, so a tracker that
    re-reads `bands()` every round loses the colour on the first action and never
    sees the refill -- measured, `mag` stayed None for a whole run
    (`results/sp80-swap1.txt`)."""
    sw = learned()
    sw.act(board(bar=64), 0)                      # latches the watched colours
    for bar in (62, 40, 10):
        assert not sw._fresh_life(board(bar=bar))
    assert sw._fresh_life(board(bar=64))


def test_the_killing_shot_is_not_recorded_as_tested():
    """The fifth press of the fire action is a GAME_OVER and it MASKS a win: the
    same position that levels up with a fresh magazine dies silently as shot five
    (`results/sp80-p18.txt` A vs B). Marking it tested is a false negative the
    sweep can never recover from."""
    sw = learned()
    frames, bar, x = [], 64, 12
    # four tested fires at four positions, then the fifth, then the refill
    for step in range(9):
        frames.append(board(x=x, bar=bar))
        bar -= 2
        if step % 2:
            x += 4
    got = drive(sw, frames)
    assert got.count(5) == 5                      # it kept firing: no cap known yet
    assert sw.shots == 5 and sw.mag is None
    killed = sw.pending
    assert killed == (28, 16)

    sw.act(board(x=12, bar=64), 0)                # the engine's post-death reset
    assert sw.mag == 4                            # learned, not assumed
    assert killed not in sw.fired                 # put back: it was never answered
    assert {(12, 16), (16, 16), (20, 16), (24, 16)} <= sw.fired


EVERYWHERE = {(x, y) for x in range(0, 45, 4) for y in range(0, 61, 4)}


def test_a_death_teaches_the_arrows_nothing():
    """A death puts the block back at the level's start, and that IS a rigid
    translation of the driven colour -- so a frame pair straddling one teaches a
    bogus vector. Measured before the guard existed: the arrow that had just been
    pressed flipped sign, (0, 4) -> (0, -4), with the honest-answer control clean
    (`results/sp80-d1.txt`)."""
    sw = ready(fired=EVERYWHERE - {(44, 44)}, shots=0, mag=4)
    out = sw.act(board(x=12, y=20, bar=40), 0)
    # positive control: the question is only about a pair whose first half ended on
    # a DIRECTION. If this round fired, the test is measuring nothing.
    assert out in (1, 2, 3, 4)
    before = dict(sw.dirs)
    sw.act(board(x=12, y=16, bar=64), 0)          # the engine's post-death reset
    assert dict(sw.dirs) == before


def test_an_honest_answer_still_teaches_the_arrows():
    """The other half of the pair: the guard must not deafen the learner."""
    sw = ready(fired=EVERYWHERE - {(44, 44)}, shots=0, mag=4)
    out = sw.act(board(x=12, y=20, bar=40), 0)
    assert out in (1, 2, 3, 4)
    sw.dirs[out] = (99, 99)                       # a wrong entry the walk must fix
    dx, dy = {1: (0, -4), 2: (0, 4), 3: (-4, 0), 4: (4, 0)}[out]
    sw.act(board(x=12 + dx, y=20 + dy, bar=38), 0)
    assert tuple(int(v) for v in sw.dirs[out]) == (dx, dy)


def test_the_magazine_caps_tested_fires_once_it_is_known():
    sw = ready(mag=4, shots=4, fired={(12, 16)})
    # standing somewhere untested with an empty magazine: it must not test it
    out = sw.act(board(x=16, bar=60), 0)
    assert (16, 16) not in sw.fired
    assert out == 5 and sw.shots == 5             # spent as a reset, not as a test
    assert sw.pending is None                     # and never claimed as an answer


def test_a_fire_is_offered_while_the_magazine_holds():
    sw = ready(mag=4, shots=2, fired=set())
    assert sw.act(board(x=16, bar=60), 0) == 5
    assert (16, 16) in sw.fired


# -- aiming ---------------------------------------------------------------

def test_toward_reads_the_mapping_and_never_assumes_it():
    sw = Swap([1, 2, 3, 4, 5])
    sw.dirs = {3: (4, 0), 4: (-4, 0)}             # ar25's reversed arrows
    assert sw._toward((12, 16), (24, 16)) == 3
    assert sw._toward((24, 16), (12, 16)) == 4
    assert sw._toward((12, 16), (12, 16)) is None


def test_pick_sweeps_its_own_row_toward_the_longer_side():
    sw = learned()
    row = {(x, 16) for x in range(0, 45, 4)} - {(12, 16)}
    other = {(x, 20) for x in range(0, 45, 4)}
    assert sw._pick((12, 16), row | other) == (16, 16)
    # with the long side to the left, it turns around
    left = {(x, 16) for x in range(0, 12, 4)} | {(16, 16)}
    assert sw._pick((12, 16), left)[0] == 8


def test_pick_leaves_the_row_only_when_it_is_finished():
    sw = learned()
    assert sw._pick((12, 16), {(40, 20), (44, 24)}) == (40, 20)


# -- the contract ---------------------------------------------------------

def test_silent_without_the_actions_it_needs():
    assert Swap([1, 2, 3, 4]).act(board(), 0) is None
    assert Swap([1, 2, 3, 4, 5]).act(None, 0) is None


def test_none_once_every_position_has_been_tested():
    sw = ready(mag=4, shots=0,
               fired={(x, y) for x in range(0, 45, 4) for y in range(0, 61, 4)})
    assert sw.act(board(x=12, bar=60), 0) is None
    assert sw.act(board(x=12, bar=58), 0) is None   # and it stays silent


def test_a_new_level_forgets_the_old_boards_answers():
    sw = ready(fired={(40, 44), (44, 44)}, mag=4, shots=3)
    sw.act(board(x=12, bar=64), 1)
    assert (40, 44) not in sw.fired                 # the old board's answers are gone
    assert sw.fired == {(12, 16)}                   # and this board starts again
    assert sw.lvl == 1 and sw.shots == 1
    assert sw.mag == 4                              # the magazine is a GAME fact
