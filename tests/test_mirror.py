import numpy as np

from mirror import signature


def test_signature_claims_a_three_column_full_height_wall_and_sprite():
    g = np.ones((64, 64), dtype=int)
    g[:63, 20:23] = 10
    g[2:11, 40:45] = 4
    assert signature(g)


def test_signature_rejects_a_blank_board():
    assert not signature(np.zeros((64, 64), dtype=int))
