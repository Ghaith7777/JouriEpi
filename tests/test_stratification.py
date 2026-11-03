"""Tests for modern stratified estimates and confounder auditing."""

import math

import numpy as np
import pytest
from statsmodels.stats.contingency_tables import StratifiedTable
import pandas as pd

from core.engine_2x2 import Table2x2
from core.stratification import (analyze_stratified_line_list, analyze_stratified_tables,
                                 analyze_stratified_dataframe)


def test_mantel_haenszel_estimates_match_hand_calculation():
    result = analyze_stratified_tables({
        "young": (12, 8, 6, 14),
        "older": (20, 10, 10, 20),
    })
    expected_or = (12 * 14 / 40 + 20 * 20 / 60) / (8 * 6 / 40 + 10 * 10 / 60)
    expected_rr = (12 * 20 / 40 + 20 * 30 / 60) / (6 * 20 / 40 + 10 * 30 / 60)
    assert result.mantel_haenszel_odds_ratio == pytest.approx(expected_or)
    assert result.mantel_haenszel_risk_ratio == pytest.approx(expected_rr)
    assert result.crude_odds_ratio is not None
    assert len(result.strata) == 2


def test_accepts_existing_table_objects_and_reports_stratum_specific_estimates():
    result = analyze_stratified_tables({"A": Table2x2(25, 15, 10, 30), "B": Table2x2(5, 15, 10, 20)})
    assert result.strata[0].odds_ratio == pytest.approx(5.0)
    assert result.strata[1].risk_ratio == pytest.approx((5 / 20) / (10 / 30))


def test_simpsons_paradox_is_flagged_when_every_stratum_reverses_crude_direction():
    result = analyze_stratified_tables({
        "high baseline risk": (80, 20, 9, 1),
        "low baseline risk": (1, 9, 20, 80),
    })
    assert result.crude_odds_ratio > 1
    assert all(s.odds_ratio < 1 for s in result.strata)
    assert result.simpsons_paradox_detected is True
    assert any("Simpson's Paradox Detected" in warning for warning in result.warnings)


def test_meaningful_confounding_threshold_is_ten_percent():
    result = analyze_stratified_tables({"A": (20, 30, 10, 40), "B": (5, 45, 20, 80)})
    assert result.percent_change == pytest.approx(1 / 9)
    assert result.meaningful_confounding is True


def test_breslow_day_and_tarone_statistics_are_nonnegative_and_have_df():
    result = analyze_stratified_tables({
        "A": (12, 8, 6, 14),
        "B": (5, 15, 15, 5),
        "C": (18, 12, 10, 20),
    })
    assert result.breslow_day_df == 2
    assert result.breslow_day_statistic is not None and result.breslow_day_statistic >= 0
    assert result.breslow_day_tarone_statistic is not None and result.breslow_day_tarone_statistic >= 0
    assert result.breslow_day_p_value is not None and 0 <= result.breslow_day_p_value <= 1
    assert result.tarone_corrected_p_value is not None and 0 <= result.tarone_corrected_p_value <= 1
    assert result.breslow_day_tarone_statistic <= result.breslow_day_statistic + 1e-12
    assert result.effect_measure_modification is True


def test_one_degree_breslow_day_p_value_uses_exact_erfc_survival_function():
    result = analyze_stratified_tables({
        "A": (12, 8, 6, 14),
        "B": (5, 15, 15, 5),
    })
    assert result.breslow_day_df == 1
    assert result.breslow_day_statistic is not None
    assert result.breslow_day_p_value == pytest.approx(
        math.erfc(math.sqrt(result.breslow_day_statistic / 2)), rel=1e-13, abs=1e-15
    )


def test_zero_cells_are_not_silently_corrected_and_infinite_or_is_explicit():
    result = analyze_stratified_tables({"A": (4, 6, 0, 10), "B": (3, 7, 2, 8)})
    assert math.isinf(result.strata[0].odds_ratio)
    assert result.strata[0].counts == (4, 6, 0, 10)


def test_mantel_haenszel_ratios_report_infinite_limit_when_weighted_denominator_is_zero():
    result = analyze_stratified_tables({"A": (4, 0, 0, 5), "B": (3, 0, 0, 7)})
    assert math.isinf(result.mantel_haenszel_odds_ratio)
    assert math.isinf(result.mantel_haenszel_risk_ratio)


@pytest.mark.parametrize("strata", [{}, {"": (1, 1, 1, 1)}, {"A": (1, 1, 1)}, {"A": (-1, 2, 3, 4)}, {"A": (True, 1, 1, 1)}])
def test_invalid_strata_rejected(strata):
    with pytest.raises(ValueError):
        analyze_stratified_tables(strata)


def test_line_list_selected_columns_build_correct_strata():
    rows = [
        {"exposed": 1, "case": 1, "age_group": "young"},
        {"exposed": 1, "case": 0, "age_group": "young"},
        {"exposed": 0, "case": 1, "age_group": "young"},
        {"exposed": 0, "case": 0, "age_group": "young"},
        {"exposed": 1, "case": 1, "age_group": "older"},
        {"exposed": 1, "case": 1, "age_group": "older"},
        {"exposed": 1, "case": 0, "age_group": "older"},
        {"exposed": 0, "case": 0, "age_group": "older"},
    ]
    result = analyze_stratified_line_list(rows, exposure_column="exposed", outcome_column="case",
                                          stratification_column="age_group")
    assert result.strata[0].label == "young"
    assert result.strata[0].counts == (1, 1, 1, 1)
    assert result.strata[1].counts == (2, 1, 0, 1)


def test_line_list_rejects_missing_values_and_strata_without_both_exposure_groups():
    with pytest.raises(ValueError, match="missing"):
        analyze_stratified_line_list([{"e": 1, "y": 1}], exposure_column="e", outcome_column="y",
                                     stratification_column="s")
    with pytest.raises(ValueError, match="exactly two distinct"):
        analyze_stratified_line_list([{"e": 1, "y": 1, "s": "A"}], exposure_column="e",
                                     outcome_column="y", stratification_column="s")


def test_line_list_requires_binary_categories_and_valid_selected_reference_values():
    rows = [
        {"e": 1, "y": 1, "s": "A"},
        {"e": 1, "y": 0, "s": "A"},
        {"e": 0, "y": 1, "s": "A"},
        {"e": 0, "y": 0, "s": "A"},
    ]
    with pytest.raises(ValueError, match="exactly two distinct"):
        analyze_stratified_line_list(rows + [{"e": 2, "y": 1, "s": "A"}], exposure_column="e",
                                     outcome_column="y", stratification_column="s")
    with pytest.raises(ValueError, match="not present"):
        analyze_stratified_line_list(rows, exposure_column="e", outcome_column="y",
                                     stratification_column="s", exposed_value=3)


def test_line_list_treats_float_nan_as_missing():
    with pytest.raises(ValueError, match="missing"):
        analyze_stratified_line_list(
            [{"e": 1, "y": 1, "s": float("nan")}],
            exposure_column="e", outcome_column="y", stratification_column="s",
        )


def test_homogeneity_test_is_undefined_for_one_stratum():
    result = analyze_stratified_tables({"A": (5, 5, 2, 8)})
    assert result.breslow_day_statistic is None
    assert result.breslow_day_p_value is None


def test_dataframe_input_groups_directly_and_returns_stratum_and_pooled_intervals():
    frame = pd.DataFrame({
        "exposure": [1, 1, 0, 0, 1, 1, 0, 0],
        "outcome":  [1, 0, 1, 0, 1, 1, 0, 0],
        "site":     ["A", "A", "A", "A", "B", "B", "B", "B"],
    })
    result = analyze_stratified_dataframe(frame, exposure_col="exposure",
                                          outcome_col="outcome", stratum_col="site")
    assert [s.label for s in result.strata] == ["A", "B"]
    assert result.strata[0].counts == (1, 1, 1, 1)
    assert result.strata[1].counts == (2, 0, 0, 2)
    assert result.strata[0].odds_ratio_ci is not None
    assert result.mantel_haenszel_odds_ratio == pytest.approx(5.0)
    assert result.mantel_haenszel_odds_ratio_ci is not None
    assert result.mantel_haenszel_odds_ratio_log_variance > 0


def test_dataframe_ignores_empty_categorical_levels_and_exposes_explicit_ha_sensitivity():
    frame = pd.DataFrame({
        "e": pd.Categorical([1, 1, 0, 0], categories=[0, 1]),
        "y": [1, 0, 1, 0],
        "s": pd.Categorical(["observed"] * 4, categories=["observed", "empty"]),
    })
    result = analyze_stratified_dataframe(frame, exposure_col="e", outcome_col="y", stratum_col="s")
    assert len(result.strata) == 1
    assert result.strata[0].counts == (1, 1, 1, 1)
    zero_frame = pd.DataFrame({"e": [1, 1, 0, 0], "y": [1, 1, 0, 0], "s": ["A"] * 4})
    zero_result = analyze_stratified_dataframe(zero_frame, exposure_col="e", outcome_col="y", stratum_col="s")
    assert math.isinf(zero_result.strata[0].odds_ratio)
    assert zero_result.strata[0].odds_ratio_haldane_anscombe == pytest.approx(25.0)


@pytest.mark.parametrize("frame", [
    pd.DataFrame(columns=["e", "y", "s"]),
    pd.DataFrame({"e": [1, None, 0, 0], "y": [1, 0, 1, 0], "s": ["A"] * 4}),
])
def test_dataframe_rejects_empty_or_missing_mapped_data(frame):
    with pytest.raises(ValueError):
        analyze_stratified_dataframe(frame, exposure_col="e", outcome_col="y", stratum_col="s")


def test_rbg_variance_matches_explicit_formula_for_published_style_two_strata_benchmark():
    strata = {"1": (12, 8, 6, 14), "2": (20, 10, 10, 20)}
    result = analyze_stratified_tables(strata)
    numerator = sum(a*d/(a+b+c+d) for a,b,c,d in strata.values())
    denominator = sum(b*c/(a+b+c+d) for a,b,c,d in strata.values())
    aa = sum((a+d)*a*d/(a+b+c+d)**2 for a,b,c,d in strata.values())
    bb = sum((b+c)*b*c/(a+b+c+d)**2 for a,b,c,d in strata.values())
    cross = sum(((a+d)*b*c+(b+c)*a*d)/(a+b+c+d)**2 for a,b,c,d in strata.values())
    expected = 0.5*aa/numerator**2 + 0.5*bb/denominator**2 + 0.5*cross/(numerator*denominator)
    assert result.mantel_haenszel_odds_ratio_log_variance == pytest.approx(expected)
    assert result.mantel_haenszel_odds_ratio_ci[0] < result.mantel_haenszel_odds_ratio < result.mantel_haenszel_odds_ratio_ci[1]


def test_mh_or_and_rbg_interval_match_independent_statsmodels_stratified_table_reference():
    strata = {"young": (12, 8, 6, 14), "older": (20, 10, 10, 20)}
    matrices = np.stack([np.asarray([[a, b], [c, d]]) for a, b, c, d in strata.values()], axis=2)
    reference = StratifiedTable(matrices)
    result = analyze_stratified_tables(strata)
    reference_ci = reference.oddsratio_pooled_confint()
    assert result.mantel_haenszel_odds_ratio == pytest.approx(reference.oddsratio_pooled, rel=1e-12)
    assert result.mantel_haenszel_odds_ratio_ci[0] == pytest.approx(reference_ci[0], rel=1e-12)
    assert result.mantel_haenszel_odds_ratio_ci[1] == pytest.approx(reference_ci[1], rel=1e-12)


def test_breslow_day_and_tarone_adjustment_match_independent_statsmodels_reference():
    strata = {"A": (12, 8, 6, 14), "B": (5, 15, 15, 5)}
    matrices = np.stack([np.asarray([[a, b], [c, d]]) for a, b, c, d in strata.values()], axis=2)
    reference = StratifiedTable(matrices)
    expected_bd = reference.test_equal_odds(adjust=False)
    expected_tarone = reference.test_equal_odds(adjust=True)
    result = analyze_stratified_tables(strata)
    assert result.breslow_day_statistic == pytest.approx(expected_bd.statistic, rel=1e-12)
    assert result.breslow_day_p_value == pytest.approx(expected_bd.pvalue, rel=1e-12)
    assert result.breslow_day_tarone_statistic == pytest.approx(expected_tarone.statistic, rel=1e-12)
    assert result.tarone_corrected_p_value == pytest.approx(expected_tarone.pvalue, rel=1e-12)
    assert result.effect_measure_modification is True


def test_homogeneous_strata_do_not_trigger_effect_measure_modification_flag():
    result = analyze_stratified_tables({"A": (10, 10, 10, 10), "B": (20, 20, 20, 20)})
    assert result.breslow_day_p_value == pytest.approx(1.0)
    assert result.effect_measure_modification is False
