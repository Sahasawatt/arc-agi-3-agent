"""The competition's own scoring, reimplemented so results can be computed offline.

Mirrors arc_agi.scorecard.EnvironmentScoreCalculator (see scorecard.py:168-206 in the
installed package): a level scores on how few actions it took relative to the human
baseline, squared, and levels are averaged weighted by their level number.
"""

SDK_CAP = 115.0  # the SDK caps a level at 115; Kaggle's overview states scores cap at 100


def level_score(baseline_actions: int, actions_taken: int, cap: float = SDK_CAP) -> float:
    """Score for one level. 0 if it was never completed (actions_taken=0 means no attempt)."""
    if actions_taken <= 0:
        return 0.0
    return min((baseline_actions / actions_taken) ** 2 * 100, cap)


def environment_score(level_scores: dict[int, float], total_levels: int) -> float:
    """Weighted average over ALL levels of the game, weighting each by its level number.

    `level_scores` maps 1-based level number → that level's score; levels absent from it
    were not completed and contribute 0 to the numerator but still to the denominator,
    which is what makes deep levels dominate.
    """
    if total_levels <= 0:
        return 0.0
    weights = sum(range(1, total_levels + 1))
    return sum(level_scores.get(i, 0.0) * i for i in range(1, total_levels + 1)) / weights
