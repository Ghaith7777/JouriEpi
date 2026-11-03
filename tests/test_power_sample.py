import pytest

from core.power_sample import (case_control_sample_size, cohort_sample_size,
                               cross_sectional_sample_size, two_proportion_power,
                               two_proportion_sample_size)


def test_two_proportion_sample_size_returns_positive_group_sizes():
    control, exposed = two_proportion_sample_size(0.10, 0.20, power=0.8)
    # Independent normal-approximation calculation gives 198.6, rounded up.
    assert control == 199
    assert exposed == control
    assert two_proportion_power(control, exposed, 0.10, 0.20) >= 0.8


def test_two_proportion_sample_size_rejects_equal_proportions():
    with pytest.raises(ValueError):
        two_proportion_sample_size(0.10, 0.10)


@pytest.mark.parametrize("kwargs", [
    {"p_control": 0, "p_exposed": 0.2},
    {"p_control": 0.1, "p_exposed": 1},
    {"p_control": 0.1, "p_exposed": 0.2, "alpha": 1},
    {"p_control": 0.1, "p_exposed": 0.2, "power": 0},
    {"p_control": 0.1, "p_exposed": 0.2, "allocation_ratio": 0},
    {"p_control": float("nan"), "p_exposed": 0.2},
    {"p_control": "0.1", "p_exposed": 0.2},
    {"p_control": 0.1, "p_exposed": 0.2, "allocation_ratio": 1e308},
    {"p_control": 0.1, "p_exposed": 0.2, "alpha": 1e-300},
    {"p_control": 0.1, "p_exposed": 0.2, "power": 0.4},
])
def test_two_proportion_sample_size_rejects_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        two_proportion_sample_size(**kwargs)


def test_two_proportion_sample_size_supports_unequal_allocation():
    control, exposed = two_proportion_sample_size(0.10, 0.20, allocation_ratio=2)
    assert control > 0
    assert exposed == 2 * control


def test_case_control_sample_size_returns_controls_then_cases():
    controls, cases = case_control_sample_size(1.5, 0.22, cases_per_control=2)
    assert controls > 0
    assert cases == 2 * controls


def test_case_control_sample_size_rejects_null_odds_ratio():
    with pytest.raises(ValueError):
        case_control_sample_size(1.0, 0.22)


def test_case_control_sample_size_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        case_control_sample_size(0, 0.22)
    with pytest.raises(ValueError):
        case_control_sample_size(1.5, 1)
    with pytest.raises(ValueError):
        case_control_sample_size("1.5", 0.2)


def test_cohort_and_cross_sectional_wrappers_use_consistent_allocation():
    control, exposed = cohort_sample_size(0.10, 0.20, exposed_per_unexposed=2)
    assert exposed == 2 * control
    control, exposed = cross_sectional_sample_size(0.20, 0.30)
    assert control == exposed
    assert control > 0


def test_two_proportion_power_is_bounded_and_increases_with_sample_size():
    small = two_proportion_power(40, 40, 0.10, 0.20)
    large = two_proportion_power(400, 400, 0.10, 0.20)
    assert 0 < small < 1
    assert small < large < 1


@pytest.mark.parametrize("args", [
    (0, 20, 0.1, 0.2), (20, 20, 0, 0.2), (20, 20, 0.1, 0.2, 1),
    (20.5, 20, 0.1, 0.2), (20, 20, float("nan"), 0.2),
    (20, 20, 0.1, 0.2, 1e-300),
])
def test_two_proportion_power_rejects_invalid_inputs(args):
    with pytest.raises(ValueError):
        two_proportion_power(*args)

