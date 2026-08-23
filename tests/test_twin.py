import numpy as np

from twin import signature


def test_signature_claims_two_piece_colours_over_two_wall_colours():
    g = np.full((64, 64), 11, dtype=int)
    g[40:, :] = 12
    g[5:10, 5:10] = 10
    g[20:25, 20:25] = 10
    assert signature(g)


def test_signature_rejects_a_blank_board():
    assert not signature(np.zeros((64, 64), dtype=int))
