"""Tests for reading a frame: what a glyph looks like once it is comparable."""

import numpy as np

from perception import icon

# --- the glyph normal form ----------------------------------------------------------------
# The two plates draw the same glyph at different scales, so the bitmap has to be divided
# back down before it can be compared. Collapsing runs of identical adjacent rows and
# columns does that and is scale-invariant — but it is not injective, and a door that reads
# as open when it is shut is worse than one that cannot be read at all.

def framed(rows):
    """A frame with `rows` (strings of '#' and '.') drawn in ink 8 on a plate of 5."""
    g = np.full((64, 64), 5)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == "#":
                g[10 + y, 10 + x] = 8
    return [g.tolist()]


def at(rows, scale=1):
    big = ["".join(c * scale for c in row) for row in rows for _ in range(scale)]
    return icon(framed(big), 10, 10 + len(big[0]) - 1, 10, 10 + len(big) - 1, ink=8)


def test_the_same_glyph_at_two_scales_reads_the_same():
    zig = ["#.#", "##.", ".##"]
    assert at(zig, 1) == at(zig, 2) == at(zig, 3) == "#.#/##./.##"


def test_a_glyph_that_repeats_a_row_is_not_confused_with_a_shorter_one():
    """`#.#/#.#/###` collapses onto `#.#/###` under run-collapsing, and `ls20` level 5 draws
    both — the panel showed the first while the goal box asked for something else."""
    assert at(["#.#", "#.#", "###"]) == "#.#/#.#/###"
    assert at(["#.#", "###"]) == "#.#/###"
    assert at(["#.#", "#.#", "###"]) != at(["#.#", "###"])


def test_an_irregular_bitmap_is_left_alone():
    """Nothing to divide by: a glyph whose runs share no factor keeps every cell."""
    assert at(["##.", "#.#", "..#"]) == "##./#.#/..#"
