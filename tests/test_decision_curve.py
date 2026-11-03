"""Decision curve analysis formulas and edge cases."""

import pytest

from core.decision_curve import analyze_decision_curve


def test_net_benefit_matches_manual_model_treat_all_and_treat_none_calculation():
    result = analyze_decision_curve([0.9, 0.8, 0.2, 0.1], [1, 0, 1, 0], [0.5])
    point = result.points[0]
    # At threshold .5, two are classified positive: TP=1, FP=1.
    assert point.true_positives == 1
    assert point.false_positives == 1
    assert point.model_net_benefit == pytest.approx(0.0)
    assert point.treat_all_net_benefit == pytest.approx(0.0)
    assert point.treat_none_net_benefit == 0.0
    assert result.prevalence == pytest.approx(0.5)


def test_thresholds_are_sorted_deduplicated_and_high_threshold_treats_none_by_model():
    result = analyze_decision_curve([0.1, 0.2], [0, 1], [0.9, 0.1, 0.9])
    assert [point.threshold_probability for point in result.points] == [0.1, 0.9]
    assert result.points[1].model_net_benefit == 0.0


@pytest.mark.parametrize("scores,outcomes,thresholds", [
    ([], [], [0.5]), ([0.2], [0, 1], [0.5]), ([1.2], [1], [0.5]),
    ([float("nan")], [1], [0.5]), ([0.2], [2], [0.5]), ([0.2], [1], [0, 1]),
    ([0.2], [1], []),
])
def test_decision_curve_rejects_invalid_scores_outcomes_and_thresholds(scores, outcomes, thresholds):
    with pytest.raises(ValueError):
        analyze_decision_curve(scores, outcomes, thresholds)


def test_all_negative_and_all_positive_outcomes_remain_finite_and_explicit():
    negative = analyze_decision_curve([0.1, 0.2], [0, 0], [0.5]).points[0]
    positive = analyze_decision_curve([0.8, 0.9], [1, 1], [0.5]).points[0]
    assert negative.model_net_benefit == 0.0
    assert negative.treat_all_net_benefit == pytest.approx(-1.0)
    assert positive.treat_all_net_benefit == pytest.approx(1.0)
