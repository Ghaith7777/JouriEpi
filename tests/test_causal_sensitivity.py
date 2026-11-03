import math

import pytest

from core.causal_sensitivity import EValueResult, e_value


def test_formula_benchmark_rr_2_5():
    # Independently checked formula benchmark; not claimed as a published numeric example.
    result = e_value(2.5, (1.5, 4.0))
    assert isinstance(result, EValueResult)
    assert result.e_value == pytest.approx(4.4364916731)
    assert result.confidence_limit_e_value == pytest.approx(2.3660254038)
    assert result.input_scale == "RR"


def test_protective_estimate_and_nearest_null_upper_bound():
    result = e_value(0.4, (0.25, 0.8))
    assert result.e_value == pytest.approx(4.4364916731)
    assert result.confidence_limit_e_value == pytest.approx(1.25 + math.sqrt(1.25 * 0.25))


def test_null_and_ci_crossing_null():
    assert e_value(1).e_value == 1
    assert e_value(1).confidence_limit_e_value is None
    result = e_value(1.4, (0.8, 2.0))
    assert result.confidence_interval_includes_null is True
    assert result.confidence_limit_e_value == 1


def test_ci_excludes_null_and_harmful_bound_nearest_null():
    result = e_value(2.0, (1.2, 3.1))
    assert result.confidence_interval_includes_null is False
    assert result.confidence_limit_e_value == pytest.approx(1.2 + math.sqrt(1.2 * 0.2))


def test_or_requires_explicit_conversion_method():
    with pytest.raises(ValueError, match="requires method"):
        e_value(4, scale="OR")
    approx = e_value(4, scale="OR", or_method="sqrt_approximation")
    assert approx.risk_ratio_estimate == pytest.approx(2)
    assert approx.conversion_method == "sqrt_approximation"


def test_or_baseline_risk_conversion():
    result = e_value(2, (1.5, 3), scale="OR", or_method="baseline_risk", baseline_risk=0.2)
    assert result.risk_ratio_estimate == pytest.approx(2 / 1.2)
    assert result.risk_ratio_confidence_interval == pytest.approx((1.5 / 1.1, 3 / 1.4))
    assert result.baseline_risk == 0.2


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), -float("inf")])
def test_rejects_nonpositive_or_nonfinite_estimates(value):
    with pytest.raises(ValueError):
        e_value(value)


@pytest.mark.parametrize("ci", [(2, 1), (0.5, 1.2), (1, float("inf")), (1,), (2, 3)])
def test_invalid_intervals(ci):
    with pytest.raises((ValueError, TypeError)):
        e_value(1.5, ci)


def test_rejects_conflicting_or_conversion_options():
    with pytest.raises(ValueError):
        e_value(2, or_method="baseline_risk")
    with pytest.raises(ValueError):
        e_value(2, scale="OR", or_method="sqrt_approximation", baseline_risk=0.2)
    with pytest.raises(ValueError):
        e_value(2, scale="OR", or_method="baseline_risk")
    with pytest.raises(ValueError):
        e_value(2, scale="OR", or_method="baseline_risk", baseline_risk=1)
    with pytest.raises(ValueError):
        e_value(2, scale="RR", baseline_risk=0.2)


def test_estimate_must_be_inside_ci_and_interpretation_is_cautious():
    with pytest.raises(ValueError, match="within"):
        e_value(3, (1.1, 2.9))
    assert "does not establish causality" in e_value(2).interpretation
