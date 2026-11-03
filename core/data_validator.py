"""Pre-flight quality checks for uploaded epidemiological line-list data."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _value_label(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def inspect_line_list(frame: pd.DataFrame, exposure_col: Any | None = None,
                      outcome_col: Any | None = None) -> dict[str, Any]:
    """Summarize dimensions, missingness, dtypes and binary-column cleanliness.

    No records are removed or changed. The function only diagnoses issues that
    can make an exposure/outcome mapping ambiguous or unsuitable for a 2x2 table.
    """
    rows, columns = frame.shape
    total_cells = rows * columns
    blank_strings = frame.apply(lambda column: column.map(lambda value: isinstance(value, str) and not value.strip()))
    missing_mask = frame.isna() | blank_strings
    missing_count = int(missing_mask.to_numpy().sum())
    missing_pct = (100.0 * missing_count / total_cells) if total_cells else 0.0
    types = [{"Column": str(name), "Data type": str(dtype),
              "Distinct non-missing": int(frame[name].nunique(dropna=True)),
              "Missing": int(missing_mask[name].sum())}
             for name, dtype in frame.dtypes.items()]

    binary_checks: dict[str, dict[str, Any]] = {}
    for role, name in (("exposure", exposure_col), ("outcome", outcome_col)):
        if name is None or name not in frame.columns:
            continue
        series = frame[name]
        nonmissing = series.dropna()
        raw_values = list(pd.unique(nonmissing))
        normalized = [_value_label(value).strip().casefold() for value in raw_values]
        has_blank = bool((series.map(lambda v: isinstance(v, str) and not v.strip())).any())
        duplicate_normalized = len(set(normalized)) != len(normalized)
        whitespace = any(_value_label(value) != _value_label(value).strip() for value in raw_values)
        valid_binary = len(raw_values) == 2 and not series.isna().any() and not has_blank and not duplicate_normalized and not whitespace
        issues: list[str] = []
        if series.isna().any() or has_blank:
            issues.append("missing or blank values")
        if len(raw_values) != 2:
            issues.append(f"expected 2 categories; found {len(raw_values)}")
        if duplicate_normalized:
            issues.append("categories differ only by case/spacing")
        elif whitespace:
            issues.append("leading/trailing whitespace in categories")
        binary_checks[role] = {
            "column": str(name), "valid_binary": valid_binary,
            "categories": [_value_label(value) for value in raw_values[:12]],
            "distinct_count": len(raw_values), "missing_count": int(missing_mask[name].sum()),
            "issues": issues,
        }

    return {
        "rows": rows, "columns": columns, "missing_count": missing_count,
        "missing_pct": missing_pct, "types": types,
        "binary_checks": binary_checks,
    }
