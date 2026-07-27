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

    Then the completion cap. A level may score up to 1.15x the human baseline, but the
    GAME cannot: it is capped at the weight of the levels actually finished —
    "The maximum game score is also determined by this weighted average structure — it is
    capped based on how many levels the AI actually completed", worked through in the docs
    as (1+2+3+4)/(1+2+3+4+5) = 10/15 = 66.7%. Without this, clearing one level of seven at
    the 1.15x cap reported 4.107% where the real ceiling is 1/28 = 3.571%.
    https://docs.arcprize.org/methodology.md
    """
    if total_levels <= 0:
        return 0.0
    weights = sum(range(1, total_levels + 1))
    raw = sum(level_scores.get(i, 0.0) * i for i in range(1, total_levels + 1)) / weights

    done = [i for i in range(1, total_levels + 1) if level_scores.get(i, 0.0) > 0]
    cap = 100.0 * sum(done) / weights
    return min(raw, cap)
