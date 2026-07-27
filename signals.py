"""Find the game's own progress meter, wherever it is drawn.

`perception.hud` reads rows 60 and below, which is where `ls20` keeps its status bar and
nowhere else. The frame-by-frame capture showed `cn04` walking a marker along row 0,
`sc25` sliding one down the right-hand column, and `re86` running two counters at once —
all invisible to a reader that only looks at the bottom strip.

This looks at the whole frame and at counts rather than positions, so it does not matter
where the meter lives or which way it points. The distinction that matters is not
increasing versus decreasing; it is **how often it moves**. A quantity that changes on
every single action is the clock — the action budget ticking down — and hill-climbing on
it just rewards taking actions. A quantity that changes on *some* actions is a
consequence, and that is a reward signal: something to climb toward between levels, where
`levels_completed` is one bit that only flips at the very end.

Measured outcome, so nobody re-derives it: on these games there is no such quantity. Every
counter found — `ls20`'s budget, `cn04`'s row-0 marker, `sc25`'s right-hand column, `re86`'s
pair, `ka59`'s tally — is a straight line in the number of actions taken. They tick at
different speeds, which is what made the slower ones look like progress at first, and not
one of them waits for anything to happen. There is no gradient to climb here.
"""

import numpy as np

# Every counter these nine games expose measures between 0.955 and 1.000 — they are all
# clocks at different speeds, and none waits for an event. The threshold sits just under
# the least straight of them so that all of them are labelled honestly, and `progress`
# stays available for a counter that genuinely steps.
LINEAR = 0.95
MIN_CHANGES = 2       # fewer moves than this is noise, not a meter


def counts(frame):
    """{colour: cells} over the whole frame, HUD included."""
    grid = np.array(frame)[-1]
    colours, n = np.unique(grid, return_counts=True)
    return {int(c): int(k) for c, k in zip(colours, n)}


def series(frames):
    """{colour: [count per frame]}, zero-filled for colours absent from some frames."""
    per = [counts(f) for f in frames]
    keys = sorted({c for d in per for c in d})
    return {c: [d.get(c, 0) for d in per] for c in keys}


def classify(seq):
    """'clock', 'progress' or 'noise' for one colour's count over a run.

    Rate is not the test. `cn04` advances a counter on every SECOND action — 135, 135,
    136, 136, 137, 137 — which passes any "changes rarely" rule and is still just a clock
    running at half speed. What separates them is shape: a clock is a straight line in the
    number of actions taken, and a consequence is a step function that waits for something
    to happen. So measure how straight it is.
    """
    steps = [b - a for a, b in zip(seq, seq[1:])]
    moves = [d for d in steps if d]
    if len(moves) < MIN_CHANGES:
        return "noise"
    if not (all(d > 0 for d in moves) or all(d < 0 for d in moves)):
        return "noise"
    return "clock" if _straightness(seq) >= LINEAR else "progress"


def _straightness(seq):
    """|r| of the count against the action index. 1.0 is a perfect straight line."""
    n = len(seq)
    x = np.arange(n, dtype=float)
    y = np.asarray(seq, dtype=float)
    if y.std() == 0 or n < 3:
        return 1.0
    return abs(float(np.corrcoef(x, y)[0, 1]))


def meters(frames):
    """{colour: 'clock' | 'progress'} — the counters worth knowing about."""
    return {c: kind for c, seq in series(frames).items()
            for kind in [classify(seq)] if kind != "noise"}


def score(frame, progress_colours, direction):
    """How far along this frame is, as one number to hill-climb on.

    Signed by the direction each meter was observed to move, so 'more is better' holds
    whether the game counts up towards a target or down towards zero.
    """
    c = counts(frame)
    return sum(direction[k] * c.get(k, 0) for k in progress_colours)


def directions(frames, progress_colours):
    """{colour: +1 or -1} — which way each progress meter was seen to move."""
    s = series(frames)
    out = {}
    for c in progress_colours:
        moves = [b - a for a, b in zip(s[c], s[c][1:]) if b != a]
        out[c] = 1 if moves and moves[0] > 0 else -1
    return out


def refills(steps, clock_colours):
    """Object kinds whose disappearance coincided with a clock jumping the wrong way.

    A clock only falls, so a rise is an event, and the thing that vanished on that step is
    what caused it. This is the mechanic `ls20` level 2 needs and level 1 does not: the
    level's route is longer than one life's budget, so it cannot be walked without picking
    a refill up on the way. Returns {(colour, x, y)} of the objects seen to do it.
    """
    out = set()
    for s in steps:
        rose = any(int(k) in clock_colours and now > was
                   for k, (was, now) in s.get("hud", {}).items())
        # Losing a life also refills the clock, and teleports the piece to the start. Only
        # a step the piece actually WALKED can be a pickup; without this the detector marks
        # whatever happened to vanish around a death, which on ls20 is the level's marker.
        if rose and s.get("walked", True):
            out.update(tuple(g) for g in s.get("gone", []))
    return out


def clock_level(frame, clock_colours, direction):
    """How much of the falling clock is left, as one number. None if there is no clock."""
    if not clock_colours:
        return None
    c = counts(frame)
    return sum(direction.get(k, -1) * -1 * c.get(k, 0) for k in clock_colours)
