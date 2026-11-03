"""Stratified 2x2 analysis and confounder auditing.

Tables use the project convention: exposed/unexposed rows and case/non-case
columns. This is a modern, pure-Python implementation; it does not claim parity
with legacy EpiTable output. No continuity correction is applied to zero cells.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import erfc, exp, isfinite, lgamma, log, sqrt
from statistics import NormalDist
from typing import Any, Iterable, Mapping, Sequence

from .engine_2x2 import Table2x2


@dataclass(frozen=True)
class StratumResult:
    """Counts and association estimates for one named stratum."""

    label: str
    counts: tuple[int, int, int, int]
    odds_ratio: float | None
    risk_ratio: float | None
    odds_ratio_ci: tuple[float, float] | None = None
    risk_ratio_ci: tuple[float, float] | None = None
    odds_ratio_haldane_anscombe: float | None = None


@dataclass(frozen=True)
class StratifiedResult:
    """Common estimates, homogeneity test, and automated confounding flags."""

    strata: tuple[StratumResult, ...]
    crude_odds_ratio: float | None
    mantel_haenszel_odds_ratio: float | None
    mantel_haenszel_risk_ratio: float | None
    breslow_day_statistic: float | None
    breslow_day_tarone_statistic: float | None
    breslow_day_df: int
    breslow_day_p_value: float | None
    tarone_corrected_p_value: float | None
    percent_change: float | None
    meaningful_confounding: bool
    simpsons_paradox_detected: bool
    warnings: tuple[str, ...]
    mantel_haenszel_odds_ratio_ci: tuple[float, float] | None = None
    mantel_haenszel_odds_ratio_log_variance: float | None = None
    effect_measure_modification: bool = False


def _valid_count(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def _is_missing(value: Any) -> bool:
    """Recognize ordinary nulls and floating-point NaN without pandas."""
    if value is None:
        return True
    return isinstance(value, float) and value != value


def _ratio(num: float, den: float) -> float | None:
    if den == 0:
        return None
    value = num / den
    return value if isfinite(value) else None


def _weighted_ratio(num: float, den: float) -> float | None:
    """Ratio of nonnegative weighted sums with explicit divergent limits."""
    if den == 0:
        return float("inf") if num > 0 else None
    return num / den


def _or(table: Table2x2) -> float | None:
    numerator, denominator = table.a * table.d, table.b * table.c
    if denominator == 0:
        return float("inf") if numerator > 0 else None
    return numerator / denominator


def _rr(table: Table2x2) -> float | None:
    risk_exposed = table.a / (table.a + table.b)
    risk_unexposed = table.c / (table.c + table.d)
    if risk_unexposed == 0:
        return float("inf") if risk_exposed > 0 else None
    return risk_exposed / risk_unexposed


def _chi_square_1df_p(statistic: float) -> float:
    """Chi-square(1) survival function, equivalent to erfc(sqrt(x/2))."""
    from math import erfc, sqrt
    return erfc(sqrt(max(0.0, statistic) / 2.0))


def _log_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)


def _conditional_moments(table: Table2x2, common_or: float) -> tuple[float, float]:
    """Conditional mean and variance of the exposed-case cell at common OR.

    Enumerating the fixed-margin noncentral hypergeometric support avoids
    requiring SciPy and remains stable by normalizing log probabilities.
    """
    a, b, c, d = table.a, table.b, table.c, table.d
    row1, row2, case_total = a + b, c + d, a + c
    low, high = max(0, case_total - row2), min(row1, case_total)
    log_theta = log(common_or) if common_or > 0 and isfinite(common_or) else 0.0
    logs = [_log_choose(row1, x) + _log_choose(row2, case_total - x) + x * log_theta
            for x in range(low, high + 1)]
    peak = max(logs)
    weights = [exp(v - peak) for v in logs]
    total = sum(weights)
    probabilities = [w / total for w in weights]
    mean = sum((low + i) * p for i, p in enumerate(probabilities))
    variance = sum(((low + i) - mean) ** 2 * p for i, p in enumerate(probabilities))
    return mean, variance


def _solve_common_or(tables: Sequence[Table2x2]) -> float:
    """Estimate common OR by solving the conditional score equation."""
    observed = sum(t.a for t in tables)
    minimum = sum(max(0, t.a + t.c - (t.c + t.d)) for t in tables)
    maximum = sum(min(t.a + t.b, t.a + t.c) for t in tables)
    if observed <= minimum:
        return 1e-12
    if observed >= maximum:
        return 1e12
    lo, hi = -30.0, 30.0  # log(OR), safely spans practical finite estimates
    for _ in range(100):
        mid = (lo + hi) / 2
        theta = exp(mid)
        expected = sum(_conditional_moments(t, theta)[0] for t in tables)
        if expected < observed:
            lo = mid
        else:
            hi = mid
    return exp((lo + hi) / 2)


def _breslow_day(tables: Sequence[Table2x2], common_or: float) -> tuple[float | None, float | None, float | None, float | None]:
    """Return standard Breslow–Day and Tarone-adjusted statistics and p-values.

    Expected exposed-case cells and their variances use the conventional
    fixed-margin quadratic solution under the Mantel–Haenszel common OR.
    This matches the published Breslow–Day formulation and common references.
    """
    if len(tables) < 2 or not isfinite(common_or) or common_or <= 0:
        return None, None, None, None
    expected_cells: list[float] = []
    variances: list[float] = []
    for t in tables:
        apb, apc, dma = t.a + t.b, t.a + t.c, t.d - t.a
        qa = 1.0 - common_or
        qb = common_or * (apb + apc) + dma
        qc = -common_or * apb * apc
        discriminant = qb * qb - 4.0 * qa * qc
        if discriminant < 0:
            return None, None, None, None
        if abs(qa) < 1e-12:
            if qb == 0:
                return None, None, None, None
            expected = -qc / qb
        else:
            expected = (-qb + sqrt(discriminant)) / (2.0 * qa)
        cells = (expected, apc - expected, apb - expected, dma + expected)
        if any(v <= 0 or not isfinite(v) for v in cells):
            return None, None, None, None
        variance = 1.0 / sum(1.0 / v for v in cells)
        if variance <= 0 or not isfinite(variance):
            return None, None, None, None
        expected_cells.append(expected)
        variances.append(variance)
    residuals = [t.a - mean for t, mean in zip(tables, expected_cells)]
    statistic = sum(r * r / v for r, v in zip(residuals, variances))
    tarone = max(0.0, statistic - (sum(residuals) ** 2 / sum(variances)))
    df = len(tables) - 1
    # Chi-square survival function for integer df using regularized gamma Q.
    # For df=1 use exact erfc; for higher df use a stable series/continued fraction.
    def gamma_q(a: float, x: float) -> float:
        if x <= 0:
            return 1.0
        # Q(1/2, x) has the exact erfc representation. Using it avoids
        # subtracting a nearly-one lower-tail probability from 1.
        if a == 0.5:
            return erfc(sqrt(x))
        if x < a + 1:
            term = total = 1.0 / a
            ap = a
            for _ in range(10000):
                ap += 1
                term *= x / ap
                total += term
                if abs(term) < abs(total) * 1e-14:
                    break
            p = total * exp(-x + a * log(x) - lgamma(a))
            return min(1.0, max(0.0, 1.0 - p))
        b = x + 1.0 - a
        c = 1e300
        d = 1.0 / b
        h = d
        for i in range(1, 10000):
            an = -i * (i - a)
            b += 2.0
            d = an * d + b
            if abs(d) < 1e-300:
                d = 1e-300
            c = b + an / c
            if abs(c) < 1e-300:
                c = 1e-300
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1.0) < 1e-14:
                break
        return min(1.0, max(0.0, exp(-x + a * log(x) - lgamma(a)) * h))

    return statistic, tarone, gamma_q(df / 2, statistic / 2), gamma_q(df / 2, tarone / 2)


def analyze_stratified_tables(strata: Mapping[str, Table2x2 | Sequence[int]]) -> StratifiedResult:
    """Analyze named 2x2 strata and audit confounding and Simpson's paradox.

    ``strata`` maps each stratum label to a :class:`Table2x2` or a four-count
    sequence ``(a,b,c,d)``. Empty mappings and fewer than two strata are allowed;
    the homogeneity test is undefined with fewer than two informative strata.
    """
    if not isinstance(strata, Mapping) or not strata:
        raise ValueError("strata must be a non-empty mapping of labels to 2x2 counts")
    labels: list[str] = []
    tables: list[Table2x2] = []
    for label, values in strata.items():
        if not isinstance(label, str) or not label.strip():
            raise ValueError("stratum labels must be non-empty strings")
        if isinstance(values, Table2x2):
            table = values
        else:
            if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or len(values) != 4:
                raise ValueError(f"stratum {label!r} must contain four counts (a,b,c,d)")
            table = Table2x2(*(_valid_count(v, f"{label} count") for v in values))
        labels.append(label)
        tables.append(table)

    z = NormalDist().inv_cdf(0.975)
    def estimate_ci(table: Table2x2, estimate: float | None, kind: str):
        a, b, c, d = table.a, table.b, table.c, table.d
        if kind == "OR" and estimate is not None and estimate > 0 and all(v > 0 for v in (a, b, c, d)):
            se = sqrt(1/a + 1/b + 1/c + 1/d)
        elif kind == "RR" and estimate is not None and estimate > 0 and a > 0 and c > 0:
            se2 = 1/a - 1/(a+b) + 1/c - 1/(c+d)
            se = sqrt(max(0.0, se2))
        else:
            return None
        return (exp(log(estimate) - z * se), exp(log(estimate) + z * se))
    stratum_results = tuple(StratumResult(
        label, (t.a, t.b, t.c, t.d), _or(t), _rr(t),
        estimate_ci(t, _or(t), "OR"), estimate_ci(t, _rr(t), "RR"),
        (((t.a + 0.5) * (t.d + 0.5)) / ((t.b + 0.5) * (t.c + 0.5))
         if any(v == 0 for v in (t.a, t.b, t.c, t.d)) else _or(t)))
                            for label, t in zip(labels, tables))
    a = sum(t.a for t in tables); b = sum(t.b for t in tables)
    c = sum(t.c for t in tables); d = sum(t.d for t in tables)
    crude_table = Table2x2(a, b, c, d)
    crude_or = _or(crude_table)
    mh_or_num = sum(t.a * t.d / t.total for t in tables if t.total)
    mh_or_den = sum(t.b * t.c / t.total for t in tables if t.total)
    mh_or = _weighted_ratio(mh_or_num, mh_or_den)
    mh_rr_num = sum(t.a * (t.c + t.d) / t.total for t in tables if t.total)
    mh_rr_den = sum(t.c * (t.a + t.b) / t.total for t in tables if t.total)
    mh_rr = _weighted_ratio(mh_rr_num, mh_rr_den)

    # Robins–Breslow–Greenland (RBG) variance estimator for log(MH OR).
    # Undefined when either MH cross-product sum is zero or a contributing
    # stratum has a zero total; do not silently continuity-correct the counts.
    rbg_variance = None
    mh_or_ci = None
    if mh_or is not None and isfinite(mh_or) and mh_or > 0 and mh_or_num > 0 and mh_or_den > 0:
        rbg_a = sum((t.a + t.d) * t.a * t.d / (t.total * t.total)
                    for t in tables if t.total)
        rbg_b = sum((t.b + t.c) * t.b * t.c / (t.total * t.total)
                    for t in tables if t.total)
        rbg_cross = sum(((t.a + t.d) * t.b * t.c + (t.b + t.c) * t.a * t.d) /
                        (t.total * t.total) for t in tables if t.total)
        # RBG's large-sample variance uses the weighted diagonal/off-diagonal
        # cell contributions and remains explicitly unavailable for sparse
        # boundary cases where a component cannot be estimated.
        if rbg_a > 0 and rbg_b > 0:
            rbg_variance = (0.5 * rbg_a / (mh_or_num * mh_or_num) +
                            0.5 * rbg_b / (mh_or_den * mh_or_den) +
                            0.5 * rbg_cross / (mh_or_num * mh_or_den))
            if rbg_variance >= 0 and isfinite(rbg_variance):
                mh_or_ci = (exp(log(mh_or) - z * sqrt(rbg_variance)),
                            exp(log(mh_or) + z * sqrt(rbg_variance)))

    percent_change = None
    if crude_or not in (None, 0, float("inf")) and mh_or is not None and isfinite(mh_or):
        percent_change = abs(crude_or - mh_or) / abs(crude_or)
    meaningful = percent_change is not None and percent_change >= 0.10
    crude_side = -1 if crude_or is not None and crude_or < 1 else (1 if crude_or is not None and crude_or > 1 else 0)
    stratum_sides = [(-1 if r.odds_ratio is not None and r.odds_ratio < 1 else
                      1 if r.odds_ratio is not None and r.odds_ratio > 1 else 0)
                     for r in stratum_results]
    simpson = crude_side != 0 and len(stratum_sides) > 0 and all(side == -crude_side for side in stratum_sides)

    bd_stat = bd_tarone = bd_p = bd_tarone_p = None
    informative = [t for t in tables if t.total > 0]
    if len(informative) >= 2:
        bd_stat, bd_tarone, bd_p, bd_tarone_p = _breslow_day(informative, mh_or)
    warnings: list[str] = []
    if meaningful:
        warnings.append("Meaningful confounding: crude and Mantel–Haenszel odds ratios differ by at least 10%.")
    if simpson:
        warnings.append("Simpson's Paradox Detected: every stratum-specific odds ratio is on the opposite side of 1 from the crude odds ratio.")
    if bd_p is not None and bd_p < 0.05:
        warnings.append("Evidence of odds-ratio heterogeneity across strata (Breslow–Day test, p < 0.05).")
    return StratifiedResult(stratum_results, crude_or, mh_or, mh_rr, bd_stat, bd_tarone,
                            len(informative) - 1, bd_p, bd_tarone_p, percent_change,
                            meaningful, simpson, tuple(warnings), mh_or_ci, rbg_variance,
                            bd_p is not None and bd_p < 0.05)


def analyze_stratified_dataframe(
    frame: Any, *, exposure_col: str, outcome_col: str, stratum_col: str,
    exposed_value: Any = 1, case_value: Any = 1,
) -> StratifiedResult:
    """Analyze a pandas DataFrame directly, preserving explicit column mapping.

    Empty categorical levels are ignored (they contain no observations); rows
    with missing mapped values are rejected rather than silently discarded.
    The table convention is exposed cases, exposed non-cases, unexposed cases,
    unexposed non-cases. Haldane–Anscombe correction is not applied implicitly.
    """
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - app/test installs pandas
        raise RuntimeError("pandas is required for DataFrame stratification") from exc
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame")
    columns = (exposure_col, outcome_col, stratum_col)
    if any(not isinstance(c, str) or not c.strip() for c in columns):
        raise ValueError("exposure_col, outcome_col, and stratum_col must be non-empty column names")
    if len(set(columns)) != 3:
        raise ValueError("exposure, outcome, and stratum columns must be different")
    missing_cols = [c for c in columns if c not in frame.columns]
    if missing_cols:
        raise ValueError(f"missing required column(s): {', '.join(missing_cols)}")
    if frame.empty:
        raise ValueError("DataFrame must contain at least one observation")
    selected = frame.loc[:, list(columns)]
    if selected.isna().any().any():
        raise ValueError("missing values in exposure, outcome, or stratum columns must be resolved first")
    for col, positive, name in ((exposure_col, exposed_value, "exposure"), (outcome_col, case_value, "outcome")):
        categories = list(selected[col].unique())
        if len(categories) != 2:
            raise ValueError(f"{name} column must contain exactly two distinct categories")
        if not any(v == positive for v in categories):
            raise ValueError(f"selected {name} value {positive!r} is not present in the data")
    counts: dict[str, tuple[int, int, int, int]] = {}
    # observed=True avoids fabricated zero-row categorical levels. Empty
    # strata are therefore handled as absent groups, not as invented records.
    for label, group in selected.groupby(stratum_col, sort=False, observed=True, dropna=False):
        if not len(group):
            continue
        exposed = group[exposure_col] == exposed_value
        cases = group[outcome_col] == case_value
        counts[str(label)] = (
            int((exposed & cases).sum()), int((exposed & ~cases).sum()),
            int((~exposed & cases).sum()), int((~exposed & ~cases).sum()),
        )
    if not counts:
        raise ValueError("no non-empty strata were found")
    return analyze_stratified_tables(counts)


def analyze_stratified_line_list(
    records: Iterable[Mapping[str, Any]], *, exposure_column: str,
    outcome_column: str, stratification_column: str,
    exposed_value: Any = 1, case_value: Any = 1,
) -> StratifiedResult:
    """Build 2x2xK counts from line-list records and analyze the strata.

    Values equal to ``exposed_value`` and ``case_value`` indicate exposed and
    case observations. Each mapped variable must contain exactly two distinct,
    non-missing categories and the selected positive category must be present;
    the other category is its reference. Missing values are rejected rather
    than silently discarded.
    """
    columns = (exposure_column, outcome_column, stratification_column)
    if any(not isinstance(col, str) or not col.strip() for col in columns):
        raise ValueError("column names must be non-empty strings")
    counts: dict[str, list[int]] = {}
    exposure_categories: list[Any] = []
    outcome_categories: list[Any] = []

    def add_category(categories: list[Any], value: Any, name: str) -> None:
        try:
            known = any(value == category for category in categories)
        except Exception as exc:
            raise ValueError(f"{name} values must be scalar categories") from exc
        if not known:
            categories.append(value)

    seen = 0
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError(f"record {index} must be a mapping")
        missing = [col for col in columns if col not in record or _is_missing(record[col])]
        if missing:
            raise ValueError(f"record {index} has missing required value(s): {', '.join(missing)}")
        add_category(exposure_categories, record[exposure_column], "exposure")
        add_category(outcome_categories, record[outcome_column], "outcome")
        label = str(record[stratification_column])
        if not label.strip():
            raise ValueError(f"record {index} has an empty stratum label")
        cell = (0 if record[exposure_column] == exposed_value else 2) + (0 if record[outcome_column] == case_value else 1)
        if label not in counts:
            counts[label] = [0, 0, 0, 0]
        counts[label][cell] += 1
        seen += 1
    if seen == 0:
        raise ValueError("records must contain at least one observation")
    for name, categories, selected in (
        ("exposure", exposure_categories, exposed_value),
        ("outcome", outcome_categories, case_value),
    ):
        try:
            selected_present = any(selected == category for category in categories)
        except Exception as exc:
            raise ValueError(f"selected {name} value must be a scalar category") from exc
        if len(categories) != 2:
            raise ValueError(f"{name} column must contain exactly two distinct non-missing categories")
        if not selected_present:
            raise ValueError(f"selected {name} value {selected!r} is not present in the data")
    # A stratum with no observations in one exposure row cannot form a valid
    # Table2x2; reject it explicitly instead of silently altering the data.
    for label, values in counts.items():
        if values[0] + values[1] == 0 or values[2] + values[3] == 0:
            raise ValueError(f"stratum {label!r} must contain both exposure groups")
    return analyze_stratified_tables(counts)
