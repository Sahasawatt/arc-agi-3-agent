"""Ground truth here is computed by hand from published numbers, not from scoring.py."""

import pytest

from scoring import environment_score, level_score

# ls20's human baselines, as served by the API in EnvironmentInfo.baseline_actions
LS20_BASELINE = [22, 123, 73, 84, 96, 192, 186]
LS20_LEVELS = len(LS20_BASELINE)


def test_beating_the_baseline_is_capped():
    """Our hand-played ls20 run: 14 actions vs a baseline of 22 -> (22/14)^2*100 = 246.9."""
    assert level_score(22, 14, cap=1e9) == pytest.approx(246.94, abs=0.01)
    assert level_score(22, 14) == 115.0  # SDK cap
    assert level_score(22, 14, cap=100.0) == 100.0  # Kaggle-stated cap


def test_being_slower_than_baseline_costs_quadratically():
    """Twice the human's actions is a QUARTER of the score, not half."""
    assert level_score(100, 200) == pytest.approx(25.0)
    assert level_score(100, 100) == pytest.approx(100.0)
    assert level_score(100, 50) == 115.0  # would be 400, capped


def test_published_graph_explorer_scores_on_ls20():
    """arXiv 2512.24156 Table 1: 124 steps on L1, 3200 on L2, nothing after."""
    assert level_score(22, 124) == pytest.approx(3.1477, abs=0.001)
    assert level_score(123, 3200) == pytest.approx(0.1477, abs=0.001)


def test_uncompleted_level_scores_zero():
    assert level_score(22, 0) == 0.0
    assert level_score(22, -5) == 0.0


def test_environment_score_weights_by_level_number():
    """Weights are 1..7, summing to 28. Clearing L1 and L2 at the cap is 300/28."""
    scores = {1: 100.0, 2: 100.0}
    assert environment_score(scores, LS20_LEVELS) == pytest.approx(300 / 28, abs=1e-6)


def test_deep_levels_dominate():
    """Level 7 alone outscores levels 1+2 together, at identical per-level scores."""
    shallow = environment_score({1: 100.0, 2: 100.0}, 7)
    deep = environment_score({7: 100.0}, 7)
    assert deep > shallow


def test_graph_explorer_environment_score_on_ls20():
    """The published agent's whole-game score: ~0.12%, vs our 10.7% for the same two levels."""
    published = {1: level_score(22, 124), 2: level_score(123, 3200)}
    assert environment_score(published, LS20_LEVELS) == pytest.approx(0.123, abs=0.002)

    ours = {1: level_score(22, 14, cap=100.0), 2: level_score(123, 45, cap=100.0)}
    assert environment_score(ours, LS20_LEVELS) == pytest.approx(10.71, abs=0.01)


def test_no_levels_is_not_a_division_by_zero():
    assert environment_score({}, 0) == 0.0
    assert environment_score({1: 100.0}, 0) == 0.0
