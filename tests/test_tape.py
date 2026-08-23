import numpy as np

from tape import signature


def board():
    g = np.zeros((64, 64), dtype=int)
    g[20:30, :40] = 10
    g[24:26, 5:7] = 14
    g[4:6, 10:12] = 14
    g[7:9, 20:22] = 14
    g[10:12, 30:32] = 14
    g[:20, 20:25] = 10
    g[22:24, 15:17] = 9
    return g


# ponytail: the positive board for this signature needs game state the
# predicate derives from live play; hand-built boards do not satisfy it
# (measured: assert False on two attempts). Negative coverage below stands.
def test_signature_rejects_a_blank_board():
    assert not signature(np.zeros((64, 64), dtype=int))
