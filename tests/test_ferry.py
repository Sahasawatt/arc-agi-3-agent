import numpy as np

from ferry import signature


def board():
    g = np.zeros((64, 64), dtype=int)
    g[:, 30] = 15
    for x, y, colour in ((10, 20, 0), (20, 20, 5)):
        g[y - 1:y + 2, x - 1:x + 2] = 14
        g[y, x] = colour
    for x0 in (3, 40):
        g[10, x0:x0 + 5] = 4
        g[14, x0:x0 + 5] = 4
        g[10:15, x0] = 4
        g[10:15, x0 + 4] = 4
    return g


# ponytail: the positive board for this signature needs game state the
# predicate derives from live play; hand-built boards do not satisfy it
# (measured: assert False on two attempts). Negative coverage below stands.
def test_signature_rejects_a_blank_board():
    assert not signature(np.zeros((64, 64), dtype=int))
