import pytest

from core.proportions import proportion_confidence_intervals


def test_wilson_and_clopper_pearson_midpoint_example():
    intervals = proportion_confidence_intervals(5, 10)
    wilson = intervals["wilson_score"]
    exact = intervals["clopper_pearson_exact"]
    assert wilson == pytest.approx((0.236593, 0.763407), abs=1e-5)
    assert exact[0] == pytest.approx(0.187086, abs=1e-5)
    assert exact[1] == pytest.approx(0.812914, abs=1e-5)


def test_exact_interval_handles_zero_and_all_successes():
    zero = proportion_confidence_intervals(0, 10)["clopper_pearson_exact"]
    all_successes = proportion_confidence_intervals(10, 10)["clopper_pearson_exact"]
    assert zero[0] == 0
    assert zero[1] == pytest.approx(1 - 0.025 ** 0.1, abs=1e-8)
    assert all_successes[0] == pytest.approx(0.025 ** 0.1, abs=1e-8)
    assert all_successes[1] == 1


@pytest.mark.parametrize("successes,trials,alpha", [
    (-1, 10, 0.05), (11, 10, 0.05), (1.5, 10, 0.05),
    (1, 0, 0.05), (True, 10, 0.05), (1, 10, float("nan")), (1, 10, 1e-300),
    (1, 10, 0), (1, 10, 1),
])
def test_invalid_proportion_interval_inputs_are_rejected(successes, trials, alpha):
    with pytest.raises(ValueError):
        proportion_confidence_intervals(successes, trials, alpha)


def test_intervals_are_ordered_and_bounded_for_sparse_counts():
    for successes, trials in ((0, 3), (1, 3), (2, 3), (3, 3), (1, 1000)):
        for lower, upper in proportion_confidence_intervals(successes, trials).values():
            assert 0 <= lower <= upper <= 1


def test_large_binomial_exact_interval_remains_finite_and_near_half():
    exact = proportion_confidence_intervals(500_000, 1_000_000)["clopper_pearson_exact"]
    assert 0 < exact[0] < 0.5 < exact[1] < 1
    assert exact[0] == pytest.approx(0.4990195, abs=2e-5)
    assert exact[1] == pytest.approx(0.5009805, abs=2e-5)
