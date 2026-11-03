import json
from pathlib import Path

import pytest

from core.engine_2x2 import Table2x2, analyze_2x2, diagnostic_metrics
from core.assumptions import audit_expected_counts


@pytest.mark.parametrize("counts,expected", [
    ((25, 15, 10, 30), (5.0, 2.5, 25 / 40 - 10 / 40)),
    ((3, 1, 2, 4), (6.0, 2.25, 3 / 4 - 2 / 6)),
    ((0, 12, 8, 15), (0.0, 0.0, -8 / 23)),
])
def test_reference_metrics(counts, expected):
    result = analyze_2x2(Table2x2(*counts))
    assert result["odds_ratio"] == pytest.approx(expected[0])
    assert result["risk_ratio"] == pytest.approx(expected[1])
    assert result["risk_difference"] == pytest.approx(expected[2])


def test_fixture_is_explicitly_not_legacy_golden():
    fixture = json.loads((Path(__file__).parent / "golden_benchmarks.json").read_text())
    assert fixture["status"] == "theoretical_reference_only_not_legacy_output"
    assert fixture["legacy_capture"] is None
    assert fixture["provenance"]["legacy_executable_run"] is False
    assert "not EpiTable" in fixture["provenance"]["warning"]
    for case in fixture["cases"]:
        assert case["provenance"]
        assert set(case["expected"]) == set(case["expected_provenance"])
        assert all(isinstance(source, str) and source.strip()
                   for source in case["expected_provenance"].values())
        result = analyze_2x2(Table2x2(*case["counts"]))
        for metric, expected in case["expected"].items():
            if expected is None:
                assert result[metric] is None
            else:
                assert result[metric] == pytest.approx(expected)


def test_fixture_schema_and_required_matrix_cases_are_consistent():
    base = Path(__file__).parent
    fixture = json.loads((base / "golden_benchmarks.json").read_text(encoding="utf-8"))
    schema = json.loads((base / "golden_benchmarks.schema.json").read_text(encoding="utf-8"))
    assert fixture["$schema"] == "golden_benchmarks.schema.json"
    assert schema["properties"]["status"]["const"] == fixture["status"]
    assert {tuple(case["counts"]) for case in fixture["cases"]} >= {
        (25, 15, 10, 30), (3, 1, 2, 4), (0, 12, 8, 15)
    }
    for case in fixture["cases"]:
        assert len(case["counts"]) == 4
        assert all(isinstance(value, int) and not isinstance(value, bool) and value >= 0
                   for value in case["counts"])
        required_metrics = {"odds_ratio", "risk_ratio", "risk_difference",
                            "attributable_fraction_exposed", "population_attributable_fraction"}
        assert set(case["expected"]) == required_metrics
        assert set(case["expected_provenance"]) == required_metrics


@pytest.mark.parametrize("counts", [(-1, 2, 3, 4), (1.5, 2, 3, 4), (True, 2, 3, 4)])
def test_invalid_counts_rejected(counts):
    with pytest.raises(ValueError):
        Table2x2(*counts)


def test_empty_exposure_row_rejected():
    with pytest.raises(ValueError):
        Table2x2(0, 0, 1, 2)


def test_expected_count_audit():
    audit = audit_expected_counts(Table2x2(3, 1, 2, 4))
    assert audit["any_expected_below_5"] is True


def test_diagnostic_metrics():
    metrics = diagnostic_metrics(90, 10, 20, 80)
    assert metrics["sensitivity"] == pytest.approx(90 / 110)
    assert metrics["specificity"] == pytest.approx(80 / 90)
    assert metrics["ppv"] == pytest.approx(0.9)
    assert metrics["accuracy"] == pytest.approx(170 / 200)
    assert metrics["false_positive_rate"] == pytest.approx(10 / 90)
    assert metrics["false_negative_rate"] == pytest.approx(20 / 110)
    assert metrics["f1"] == pytest.approx(6 / 7)


def test_diagnostic_zero_denominator_is_undefined():
    metrics = diagnostic_metrics(0, 0, 5, 10)
    assert metrics["ppv"] is None
    assert metrics["f1"] == 0
    assert metrics["false_positive_rate"] == 0


def test_diagnostic_metrics_with_no_reference_positive_cases_do_not_crash():
    metrics = diagnostic_metrics(0, 2, 0, 8)
    assert metrics["sensitivity"] is None
    assert metrics["false_negative_rate"] is None
    assert metrics["lr_positive"] is None
    assert metrics["lr_negative"] is None


def test_diagnostic_metrics_all_zero_counts_are_undefined_not_infinite():
    metrics = diagnostic_metrics(0, 0, 0, 0)
    assert metrics["accuracy"] is None
    assert metrics["f1"] is None
    assert metrics["sensitivity"] is None
    assert metrics["specificity"] is None


def test_diagnostic_rejects_boolean_and_negative_counts():
    with pytest.raises(ValueError):
        diagnostic_metrics(True, 1, 1, 1)
    with pytest.raises(ValueError):
        diagnostic_metrics(1, -1, 1, 1)


def test_alpha_must_be_valid_probability():
    table = Table2x2(2, 3, 4, 5)
    for alpha in (0, 1, -0.1, float("nan"), "0.05", True, 1e-300):
        with pytest.raises(ValueError):
            analyze_2x2(table, alpha)


def test_zero_risk_in_unexposed_group_has_undefined_risk_ratio():
    result = analyze_2x2(Table2x2(5, 5, 0, 10))
    assert result["risk_unexposed"] == 0
    assert result["risk_ratio"] is None
    assert result["risk_ratio_katz_ci"] is None


def test_zero_events_in_both_groups_yields_undefined_ratios_but_valid_fisher_result():
    result = analyze_2x2(Table2x2(0, 10, 0, 20))
    assert result["risk_exposed"] == 0
    assert result["risk_unexposed"] == 0
    assert result["odds_ratio"] is None
    assert result["risk_ratio"] is None
    assert result["risk_difference"] == 0
    assert result["population_attributable_fraction"] is None
    assert result["pearson_chi2"] is None
    assert result["fisher_two_sided_p"] == pytest.approx(1.0)


def test_zero_cell_does_not_apply_hidden_correction():
    result = analyze_2x2(Table2x2(0, 12, 8, 15))
    assert result["odds_ratio"] == 0
    assert result["odds_ratio_woolf_ci"] is None
    assert result["risk_ratio_katz_ci"] is None
    assert result["odds_ratio_haldane_anscombe"] is None


def test_haldane_anscombe_odds_ratio_is_opt_in_and_separately_named():
    table = Table2x2(0, 12, 8, 15)
    ordinary = analyze_2x2(table)
    corrected = analyze_2x2(table, haldane_anscombe=True)
    assert ordinary["odds_ratio"] == 0
    assert ordinary["odds_ratio_haldane_anscombe"] is None
    expected = (0.5 * 15.5) / (12.5 * 8.5)
    assert corrected["odds_ratio"] == 0
    assert corrected["odds_ratio_haldane_anscombe"] == pytest.approx(expected)
    assert corrected["odds_ratio_haldane_anscombe_woolf_ci"] is not None
    with pytest.raises(ValueError):
        analyze_2x2(table, haldane_anscombe=1)


def test_haldane_anscombe_adds_half_to_every_cell_when_enabled_without_zero_cells():
    table = Table2x2(12, 18, 5, 25)
    ordinary = analyze_2x2(table)
    corrected = analyze_2x2(table, haldane_anscombe=True)
    expected_or = (12.5 * 25.5) / (18.5 * 5.5)
    se = (1 / 12.5 + 1 / 18.5 + 1 / 5.5 + 1 / 25.5) ** 0.5
    from statistics import NormalDist
    z = NormalDist().inv_cdf(0.975)
    expected_ci = (expected_or * __import__("math").exp(-z * se),
                   expected_or * __import__("math").exp(z * se))
    assert ordinary["odds_ratio"] == pytest.approx(3.3333333333333335)
    assert corrected["odds_ratio"] == ordinary["odds_ratio"]
    assert corrected["odds_ratio_haldane_anscombe"] == pytest.approx(expected_or)
    assert corrected["odds_ratio_haldane_anscombe_woolf_ci"] == pytest.approx(expected_ci)


def test_population_attributable_fraction_uses_population_risk_definition():
    result = analyze_2x2(Table2x2(25, 15, 10, 30))
    assert result["population_attributable_fraction"] == pytest.approx(3 / 7)
    assert any("case-control sampled tables" in note for note in result["notes"])


def test_population_attributable_fraction_is_defined_when_rr_is_zero():
    result = analyze_2x2(Table2x2(0, 12, 8, 15))
    assert result["risk_ratio"] == 0
    assert result["population_attributable_fraction"] == pytest.approx(-12 / 23)


def test_population_attributable_fraction_is_one_when_unexposed_risk_is_zero():
    result = analyze_2x2(Table2x2(5, 5, 0, 10))
    assert result["risk_ratio"] is None
    assert result["population_attributable_fraction"] == pytest.approx(1.0)


def test_exposed_attributable_fraction_interval_is_monotone_transform_of_rr_ci():
    result = analyze_2x2(Table2x2(25, 15, 10, 30))
    rr_lower, rr_upper = result["risk_ratio_katz_ci"]
    af_lower, af_upper = result["attributable_fraction_exposed_katz_ci"]
    assert af_lower == pytest.approx(1 - 1 / rr_lower)
    assert af_upper == pytest.approx(1 - 1 / rr_upper)


def test_fisher_result_is_bounded_and_symmetric_under_row_swap():
    first = analyze_2x2(Table2x2(3, 1, 2, 4))["fisher_two_sided_p"]
    swapped = analyze_2x2(Table2x2(2, 4, 3, 1))["fisher_two_sided_p"]
    assert 0 <= first <= 1
    assert first == pytest.approx(swapped)


def test_fisher_probability_ordering_known_small_table():
    result = analyze_2x2(Table2x2(3, 1, 2, 4))
    # Fixed margins give probabilities (6, 60, 120, 60, 6)/252; probability
    # ordering includes x=0,1,3,4, yielding 132/252 = 11/21.
    assert result["fisher_two_sided_p"] == pytest.approx(11 / 21)
    assert result["fisher_less_p"] == pytest.approx(41 / 42)
    assert result["fisher_greater_p"] == pytest.approx(11 / 42)


def test_fisher_one_sided_probabilities_are_complement_consistent():
    result = analyze_2x2(Table2x2(3, 1, 2, 4))
    assert result["fisher_less_p"] + result["fisher_greater_p"] >= 1
    assert 0 <= result["fisher_less_p"] <= 1
    assert 0 <= result["fisher_greater_p"] <= 1
    # Probability-ordering two-sided p-values need not be <= either directional tail.
    assert result["fisher_two_sided_p"] == pytest.approx(11 / 21)


def test_pearson_and_yates_statistics_match_hand_calculation():
    result = analyze_2x2(Table2x2(25, 15, 10, 30))
    assert result["pearson_chi2"] == pytest.approx(80 / 7)
    assert result["yates_chi2"] == pytest.approx(9.955555555555556)
    assert result["expected_any_below_5"] is False


def test_fisher_large_counts_remain_finite():
    p = analyze_2x2(Table2x2(25000, 15000, 10000, 30000))["fisher_two_sided_p"]
    assert p is not None and 0 <= p <= 1


def test_expected_count_audit_reports_minimum_and_zero_cells():
    audit = audit_expected_counts(Table2x2(0, 12, 8, 15))
    assert audit["zero_observed_cells"] == 1
    assert audit["minimum_expected"] >= 0
