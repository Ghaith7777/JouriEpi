"""Offline line-list cleaning and data-health auditing.

Dates are parsed to pandas datetimes, categorical whitespace is trimmed, and
exact duplicate rows are removed. Duplicate identifiers and statistical
outliers are reported but retained: repeated IDs may represent legitimate
follow-up records, and outliers require epidemiological review rather than
automatic deletion.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import pandas as pd


def outbreak_case_counts(
    cleaned: pd.DataFrame, date_col: str, case_col: str, selected_case_value: Any
) -> tuple[list[Any], list[int], int]:
    """Count dates for one explicitly selected case category only.

    Returns sorted calendar dates, daily counts (including zero-count days),
    and the number of selected rows with valid dates.
    """
    missing = {date_col, case_col} - set(cleaned.columns)
    if missing:
        raise ValueError(f"columns not found: {', '.join(sorted(missing))}")
    case_mask = cleaned[case_col].astype("string").str.strip() == str(selected_case_value).strip()
    valid_cases = cleaned.loc[case_mask].copy()
    dates = pd.to_datetime(valid_cases[date_col], errors="coerce").dropna().dt.date
    if dates.empty:
        return [], [], 0
    counts = dates.value_counts().sort_index()
    calendar = pd.date_range(min(counts.index), max(counts.index), freq="D").date
    return list(calendar), [int(counts.get(day, 0)) for day in calendar], int(len(dates))


@dataclass(frozen=True)
class DataHealthSummary:
    rows_received: int
    rows_returned: int
    exact_duplicate_rows_removed: int
    duplicate_id_rows: int
    duplicate_ids: tuple[str, ...]
    invalid_dates: dict[str, int]
    numeric_outliers: dict[str, tuple[dict[str, Any], ...]]
    missing_values: dict[str, int]
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def clean_linelist(
    df: pd.DataFrame,
    date_cols: Sequence[str],
    categorical_cols: Sequence[str],
    id_col: str | None = None,
) -> tuple[pd.DataFrame, DataHealthSummary]:
    """Clean a line list and return ``(cleaned_dataframe, health_summary)``.

    Date columns become timezone-naive pandas datetimes (ISO-8601-compatible
    values); categorical strings are stripped without changing case. Exact
    duplicate rows are removed, while duplicate IDs and IQR outliers are only
    flagged. Numeric outliers use Tukey's 1.5-IQR fences and are not removed.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    if not df.columns.is_unique:
        raise ValueError("DataFrame column names must be unique")
    if df.empty:
        raise ValueError("df must contain at least one row")
    date_cols, categorical_cols = tuple(date_cols), tuple(categorical_cols)
    if len(set(date_cols)) != len(date_cols) or len(set(categorical_cols)) != len(categorical_cols):
        raise ValueError("date_cols and categorical_cols must not contain duplicates")
    if set(date_cols) & set(categorical_cols):
        raise ValueError("a column cannot be both a date and categorical column")
    requested = set(date_cols) | set(categorical_cols) | ({id_col} if id_col else set())
    missing = sorted(requested - set(df.columns))
    if missing:
        raise ValueError(f"columns not found: {', '.join(missing)}")

    cleaned = df.copy(deep=True)
    invalid_dates: dict[str, int] = {}
    for column in date_cols:
        original_nonmissing = cleaned[column].notna()
        parsed = pd.to_datetime(cleaned[column], errors="coerce", format="mixed", utc=True)
        invalid_dates[column] = int((original_nonmissing & parsed.isna()).sum())
        # UTC normalization makes mixed-offset inputs comparable and stable.
        cleaned[column] = parsed.dt.tz_convert(None)
    for column in categorical_cols:
        values = cleaned[column]
        cleaned[column] = values.map(lambda value: value.strip() if isinstance(value, str) else value)
        cleaned[column] = cleaned[column].replace("", pd.NA)

    rows_received = len(cleaned)
    duplicate_mask = cleaned.duplicated(keep="first")
    duplicate_rows = int(duplicate_mask.sum())
    cleaned = cleaned.loc[~duplicate_mask].copy().reset_index(drop=True)

    duplicate_ids: tuple[str, ...] = ()
    duplicate_id_rows = 0
    if id_col is not None:
        id_values = cleaned[id_col]
        duplicated_ids = id_values.notna() & id_values.duplicated(keep=False)
        duplicate_id_rows = int(duplicated_ids.sum())
        duplicate_ids = tuple(sorted(map(str, id_values[duplicated_ids].unique())))

    numeric_outliers: dict[str, tuple[dict[str, Any], ...]] = {}
    for column in cleaned.select_dtypes(include="number").columns:
        series = cleaned[column].dropna()
        if len(series) < 4 or series.nunique() < 2:
            continue
        q1, q3 = series.quantile([0.25, 0.75])
        spread = float(q3 - q1)
        if spread <= 0:
            continue
        lower, upper = float(q1 - 1.5 * spread), float(q3 + 1.5 * spread)
        mask = cleaned[column].notna() & ((cleaned[column] < lower) | (cleaned[column] > upper))
        if mask.any():
            flagged = []
            for index in cleaned.index[mask]:
                value = cleaned.at[index, column]
                if hasattr(value, "item"):
                    value = value.item()
                flagged.append({"row": int(index), "value": value,
                                "lower_fence": lower, "upper_fence": upper})
            numeric_outliers[column] = tuple(flagged)

    missing_values = {str(column): int(count) for column, count in cleaned.isna().sum().items() if count}
    warnings: list[str] = []
    if duplicate_id_rows:
        warnings.append("Duplicate identifiers were retained for review; they may represent repeated follow-up records.")
    if any(invalid_dates.values()):
        warnings.append("Unparseable dates were set to missing values.")
    if numeric_outliers:
        warnings.append("IQR outliers were flagged, not removed; assess clinical plausibility before exclusion.")
    summary = DataHealthSummary(
        rows_received=rows_received, rows_returned=len(cleaned),
        exact_duplicate_rows_removed=duplicate_rows, duplicate_id_rows=duplicate_id_rows,
        duplicate_ids=duplicate_ids, invalid_dates=invalid_dates,
        numeric_outliers=numeric_outliers, missing_values=missing_values,
        warnings=tuple(warnings),
    )
    return cleaned, summary
