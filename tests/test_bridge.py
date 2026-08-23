import numpy as np

from bridge import signature


def board():
    g = np.ones((64, 64), dtype=int)
    g[:, :25] = 0
    g[:, 25:35] = 7
    g[3:5, 3:5] = 2
    g[10:12, 10:12] = 3
    g[20:25, 38:43] = 4
    return g


def test_signature_claims_play_panel_and_twin_markers():
    assert signature(board())


def test_signature_rejects_a_blank_board():
    assert not signature(np.zeros((64, 64), dtype=int))
