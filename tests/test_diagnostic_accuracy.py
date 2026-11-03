"""Diagnostic accuracy metrics, intervals and ROC regression tests."""

import math

import pytest

from core.diagnostic_accuracy import DiagnosticTestAccuracy, fagan_post_test_probability


def test_textbook_style_binary_table_metrics_and_intervals():
    result = DiagnosticTestAccuracy().from_counts(tp=45, fp=5, fn=15, tn=135)
    assert result.metrics["sensitivity"] == pytest.approx(0.75)
    assert result.metrics["specificity"] == pytest.approx(135 / 140)
    assert result.metrics["ppv"] == pytest.approx(0.90)
    assert result.metrics["npv"] == pytest.approx(0.90)
    assert result.metrics["lr_positive"] == pytest.approx(21.0)
    assert result.metrics["lr_negative"] == pytest.approx(0.25 / (135 / 140))
    assert result.metrics["dor"] == pytest.approx(81.0)
    for metric in ("sensitivity", "specificity", "ppv", "npv"):
        wald = result.intervals[metric]["wald"]
        wilson = result.intervals[metric]["wilson"]
        assert wald[0] <= result.metrics[metric] <= wald[1]
        assert wilson[0] <= result.metrics[metric] <= wilson[1]
    assert result.auc is None  # A single binary threshold cannot identify AUC.
    assert result.roc_points[-1][0] == pytest.approx(1 - result.metrics["specificity"])


def test_continuous_scores_calculate_mann_whitney_auc_delong_variance_and_roc():
    result = DiagnosticTestAccuracy().from_scores(
        scores=[0.9, 0.8, 0.4, 0.7, 0.3, 0.2],
        outcomes=[1, 1, 1, 0, 0, 0],
    )
    assert result.auc == pytest.approx(8 / 9)
    assert result.auc_variance is not None and result.auc_variance >= 0
    assert result.auc_ci[0] <= result.auc <= result.auc_ci[1]
    assert result.roc_points[0][:2] == (0.0, 0.0)
    assert result.roc_points[-1][:2] == (1.0, 1.0)
    assert all(0 <= x <= 1 and 0 <= y <= 1 for x, y, _ in result.roc_points)


def test_score_auc_handles_ties_as_half_credit():
    result = DiagnosticTestAccuracy().from_scores([1, 1, 0, 0], [1, 0, 1, 0])
    assert result.auc == pytest.approx(0.5)


@pytest.mark.parametrize("args", [(-1, 0, 1, 1), (1.5, 0, 1, 1), (True, 0, 1, 1), (0, 0, 0, 0)])
def test_invalid_diagnostic_counts_rejected(args):
    with pytest.raises(ValueError):
        DiagnosticTestAccuracy().from_counts(*args)


def test_undefined_metrics_are_explicit_for_zero_denominators():
    result = DiagnosticTestAccuracy().from_counts(10, 0, 0, 20)
    assert result.metrics["sensitivity"] == 1
    assert result.metrics["specificity"] == 1
    assert result.metrics["lr_positive"] is None
    assert result.metrics["lr_negative"] == 0
    assert result.intervals["lr_positive"]["wald"] is None


def test_score_input_rejects_nonbinary_outcome_nonfinite_scores_and_single_class():
    engine = DiagnosticTestAccuracy()
    with pytest.raises(ValueError, match="binary"):
        engine.from_scores([0.1, 0.9], [0, 2])
    with pytest.raises(ValueError, match="finite"):
        engine.from_scores([float("nan"), 0.9], [0, 1])
    with pytest.raises(ValueError, match="both positive and negative"):
        engine.from_scores([0.1, 0.9], [1, 1])


def test_confidence_level_is_validated():
    with pytest.raises(ValueError):
        DiagnosticTestAccuracy(alpha=1)


@pytest.mark.parametrize("pretest,lr,expected", [
    (0.20, 10.0, 0.7142857142857143),
    (0.20, 0.1, 0.02439024390243903),
    (0.50, 1.0, 0.50),
    (0.25, 0.0, 0.0),
    (0.25, math.inf, 1.0),
])
def test_fagan_post_test_probability_uses_bayes_odds_math(pretest, lr, expected):
    assert fagan_post_test_probability(pretest, lr) == pytest.approx(expected)


@pytest.mark.parametrize("pretest,lr", [(0, 1), (1, 1), (float("nan"), 1), (0.5, -1), (0.5, float("nan"))])
def test_fagan_rejects_invalid_probability_or_likelihood_ratio(pretest, lr):
    with pytest.raises(ValueError):
        fagan_post_test_probability(pretest, lr)

