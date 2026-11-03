import pytest

from core.diagnostic_accuracy import compare_roc_curves
from ui.components import dual_roc_plot_svg


def test_paired_delong_identical_scores_have_zero_delta_and_p_one():
    scores = [0.1, 0.8, 0.3, 0.9, 0.4, 0.7]
    outcomes = [0, 1, 0, 1, 0, 1]
    result = compare_roc_curves(scores, scores, outcomes, paired=True)
    assert result.auc1 == pytest.approx(result.auc2)
    assert result.delta_auc == pytest.approx(0)
    assert result.p_value_two_sided == pytest.approx(1)
    assert result.paired


def test_paired_delong_computes_covariance_and_plot_has_two_curves_and_operating_points():
    y = [0, 1, 0, 1, 0, 1, 0, 1]
    s1 = [0.2, 0.8, 0.3, 0.9, 0.4, 0.7, 0.6, 0.65]
    s2 = [0.1, 0.75, 0.6, 0.85, 0.35, 0.8, 0.25, 0.55]
    result = compare_roc_curves(s1, s2, y)
    assert result.standard_error_difference >= 0
    assert -1 <= result.delta_auc <= 1
    svg = dual_roc_plot_svg(result)
    assert svg.count("<polyline") == 2
    assert svg.count("<circle") == 2
    assert "AUC" in svg


def test_independent_delong_requires_second_outcome_vector_and_uses_variance_sum():
    y1 = [0, 1, 0, 1, 0, 1]
    y2 = [0, 0, 1, 1, 0, 1]
    s1 = [0.1, 0.9, 0.3, 0.8, 0.2, 0.7]
    s2 = [0.2, 0.6, 0.7, 0.9, 0.1, 0.4]
    result = compare_roc_curves(s1, s2, y1, outcomes2=y2, paired=False)
    assert not result.paired
    assert result.standard_error_difference == pytest.approx((result.variance_auc1 + result.variance_auc2) ** 0.5)
    with pytest.raises(ValueError):
        compare_roc_curves(s1, s2, y1, paired=False)


def test_paired_delong_rejects_misaligned_outcomes():
    with pytest.raises(ValueError, match="subject-for-subject"):
        compare_roc_curves([0.1, 0.8, 0.3, 0.9], [0.2, 0.7, 0.4, 0.8], [0, 1, 0, 1], outcomes2=[0, 0, 1, 1])
