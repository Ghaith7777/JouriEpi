import math

import pytest

from core.interaction import analyze_additive_interaction


def test_additive_interaction_matches_odds_ratio_scale_benchmark():
    result = analyze_additive_interaction([(20, 80), (40, 60), (30, 70), (60, 40)])
    or10 = (40 / 60) / (20 / 80)
    or01 = (30 / 70) / (20 / 80)
    or11 = (60 / 40) / (20 / 80)
    reri = or11 - or10 - or01 + 1
    assert result.odds_ratio_10 == pytest.approx(or10)
    assert result.odds_ratio_01 == pytest.approx(or01)
    assert result.odds_ratio_11 == pytest.approx(or11)
    assert result.reri == pytest.approx(reri)
    assert result.attributable_proportion == pytest.approx(reri / or11)
    assert result.synergy_index == pytest.approx((or11 - 1) / ((or10 - 1) + (or01 - 1)))
    for low, high in (result.reri_ci, result.ap_ci, result.si_ci):
        assert math.isfinite(low) and math.isfinite(high) and low < high
    assert len(result.covariance_beta) == 3


@pytest.mark.parametrize("counts", [
    [(0, 5), (2, 4), (3, 7), (4, 8)],
    [(1, 2), (2, 3)],
    [(1, 2), (2, -1), (3, 4), (4, 5)],
])
def test_interaction_rejects_zero_cells_invalid_shape_and_negative_counts(counts):
    with pytest.raises(ValueError):
        analyze_additive_interaction(counts)


def test_interaction_rejects_invalid_alpha():
    with pytest.raises(ValueError):
        analyze_additive_interaction([(20, 80), (40, 60), (30, 70), (60, 40)], alpha=1.0)
