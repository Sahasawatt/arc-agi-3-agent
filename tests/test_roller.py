import numpy as np

from roller import signature


def test_signature_claims_the_roller_and_two_large_regions():
    g = np.full((64, 64), 7, dtype=int)
    g[2:12, 2:12] = 0
    g[20:30, 20:30] = 15
    g[40:46, 40:45] = 2
    assert signature(g)


def test_signature_rejects_a_blank_board():
    assert not signature(np.zeros((64, 64), dtype=int))
