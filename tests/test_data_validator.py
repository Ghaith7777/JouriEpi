from __future__ import annotations

import pandas as pd

from core.data_validator import inspect_line_list


def test_health_summary_reports_dimensions_missingness_and_types():
    frame = pd.DataFrame({"exposure": ["yes", "no", None], "outcome": [1, 0, 1], "age": [22, 41, 50]})
    result = inspect_line_list(frame)
    assert (result["rows"], result["columns"]) == (3, 3)
    assert result["missing_count"] == 1
    assert result["missing_pct"] == 100 / 9
    assert {item["Column"]: item["Data type"] for item in result["types"]}["age"] == "int64"


def test_binary_health_accepts_two_complete_categories_without_mutating_data():
    frame = pd.DataFrame({"exposure": ["yes", "no"], "outcome": ["case", "control"]})
    before = frame.copy(deep=True)
    result = inspect_line_list(frame, "exposure", "outcome")
    assert result["binary_checks"]["exposure"]["valid_binary"]
    assert result["binary_checks"]["outcome"]["valid_binary"]
    pd.testing.assert_frame_equal(frame, before)


def test_binary_health_flags_missing_multicategory_and_unclean_labels():
    frame = pd.DataFrame({"exposure": ["yes", " yes ", "no"], "outcome": ["case", None, "other"]})
    result = inspect_line_list(frame, "exposure", "outcome")["binary_checks"]
    assert not result["exposure"]["valid_binary"]
    assert any("whitespace" in issue or "case/spacing" in issue for issue in result["exposure"]["issues"])
    assert not result["outcome"]["valid_binary"]
    assert any("missing" in issue for issue in result["outcome"]["issues"])
