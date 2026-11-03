"""Publication export formatting and provenance regression tests."""

import json

import pytest

from core.engine_2x2 import Table2x2, analyze_2x2
from core.strobe_export import comparison_latex, comparison_markdown, strobe_narrative, technical_payload


@pytest.fixture
def analysis():
    counts = (25, 15, 7, 30)
    return counts, analyze_2x2(Table2x2(*counts))


def test_strobe_narrative_uses_only_counts_and_supplied_design(analysis):
    counts, result = analysis
    narrative = strobe_narrative(counts, result, design="Cohort / cross-sectional")
    assert "77 records" in narrative
    assert "40 exposed and 37 unexposed" in narrative
    assert "Cohort / cross-sectional" in narrative
    assert "do not establish causality" in narrative
    assert "Study setting" in narrative


def test_comparison_exports_include_estimates_ci_methods_and_provenance(analysis):
    counts, result = analysis
    markdown = comparison_markdown(counts, result)
    latex = comparison_latex(counts, result)
    assert "Odds ratio" in markdown and "Woolf log interval" in markdown
    assert r"\begin{tabular}" in latex and r"\end{tabular}" in latex
    assert "exact EpiTable 6.04 parity is unverified" in markdown


def test_technical_payload_is_valid_json_and_preserves_infinity_as_text():
    payload = json.loads(technical_payload((4, 0, 0, 8), {"odds_ratio": float("inf")}, design="cohort"))
    assert payload["offline_processing"] is True
    assert payload["counts"] == [4, 0, 0, 8]
    assert payload["results"]["odds_ratio"] == "Infinity"
    assert payload["table_orientation"].startswith("exposed_cases")


@pytest.mark.parametrize("counts", [(1, 2, 3), (True, 1, 2, 3), (-1, 1, 1, 1), (0, 0, 0, 0)])
def test_narrative_rejects_invalid_counts(counts):
    with pytest.raises(ValueError):
        strobe_narrative(counts, {}, design="cohort")
