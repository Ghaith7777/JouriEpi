import math

import pytest

from core.paired_analysis import mcnemar_test


def test_mcnemar_exact_and_edwards_corrected_results():
    result = mcnemar_test(30, 2, 10, 40)
    assert result.discordant_total == 12
    assert result.asymptotic_chi_square == pytest.approx((abs(2 - 10) - 1) ** 2 / 12)
    assert result.exact_p_value == pytest.approx(0.03857421875)
    assert result.paired_odds_ratio == pytest.approx(0.2)
    assert result.exact_or_ci[0] < 0.2 < result.exact_or_ci[1]


def test_mcnemar_zero_discordants_are_explicitly_not_estimable():
    result = mcnemar_test(10, 0, 0, 12)
    assert result.exact_p_value == 1.0
    assert result.asymptotic_chi_square is None
    assert result.paired_odds_ratio is None
    assert result.exact_or_ci is None


@pytest.mark.parametrize("counts", [(-1, 0, 0, 1), (1.2, 0, 0, 1), (True, 0, 0, 1), (0, 0, 0, 0)])
def test_mcnemar_rejects_invalid_counts(counts):
    with pytest.raises(ValueError):
        mcnemar_test(*counts)


def test_mcnemar_exact_ci_can_have_infinite_endpoint():
    result = mcnemar_test(1, 5, 0, 2)
    assert math.isinf(result.exact_or_ci[1])
