import numpy as np

from sorter import signature


def board():
    g = np.zeros((64, 64), dtype=int)
    for x, colour in zip((3, 10, 17), (3, 4, 5)):
        g[5, x:x + 3] = colour
    for x, colour in zip((3, 10, 17), (5, 3, 4)):
        g[55, x:x + 3] = colour
    for x in (3, 10, 17):
        g[30, x:x + 2] = 2
    return g


def test_signature_claims_recipe_stock_and_slots():
    assert signature(board())


def test_signature_rejects_a_blank_board():
    assert not signature(np.zeros((64, 64), dtype=int))
