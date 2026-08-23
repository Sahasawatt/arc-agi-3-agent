import numpy as np

from claw import signature


def board():
    g = np.ones((64, 64), dtype=int)
    g[2:13, 2:12] = 0
    g[20:31, 20:30] = 14
    for x, y in ((40, 5), (50, 5), (40, 15), (50, 15)):
        g[y:y + 3, x:x + 3] = 8
    return g


def test_signature_claims_the_claw_socket_and_four_pads():
    assert signature(board())


def test_signature_rejects_a_blank_board():
    assert not signature(np.zeros((64, 64), dtype=int))
