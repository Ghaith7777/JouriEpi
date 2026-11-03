"""Calculations for a 2x2 epidemiological table.

Table convention: rows are exposed/unexposed and columns are disease/no disease.
The input counts are a=exposed cases, b=exposed non-cases,
c=unexposed cases, d=unexposed non-cases.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import erfc, exp, isfinite, lgamma, log, sqrt

from statistics import NormalDist


@dataclass(frozen=True)
class Table2x2:
    """A validated 2x2 table using exposed-first row order."""

    a: int
    b: int
    c: int
    d: int

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.a + self.b == 0 or self.c + self.d == 0:
            raise ValueError("Each exposure row must have a positive total")

    @property
    def matrix(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """Return rows (exposed, unexposed), columns (case, non-case)."""
        return ((self.a, self.b), (self.c, self.d))

    @property
    def total(self) -> int:
        return self.a + self.b + self.c + self.d

    @property
    def expected(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """Expected cell counts under independence."""
        row1, row2 = self.a + self.b, self.c + self.d
        case_total, noncase_total = self.a + self.c, self.b + self.d
        n = self.total
        if n == 0:
            return ((0.0, 0.0), (0.0, 0.0))
        return ((row1 * case_total / n, row1 * noncase_total / n),
                (row2 * case_total / n, row2 * noncase_total / n))


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    value = numerator / denominator
    return value if isfinite(value) else None


def _chi_square_1df_p(value: float) -> float:
    """Survival probability for a chi-square statistic with one degree of freedom."""
    return erfc(sqrt(max(0.0, value) / 2))


def _chi_square(table: Table2x2, correction: bool = False) -> tuple[float | None, float | None]:
    """Pearson chi-square for a 2x2 table, optionally with Yates correction."""
    expected = table.expected
    if any(value == 0 for row in expected for value in row):
        return None, None
    observed = table.matrix
    statistic = 0.0
    for i in range(2):
        for j in range(2):
            delta = abs(observed[i][j] - expected[i][j])
            if correction:
                delta = max(0.0, delta - 0.5)
            statistic += delta * delta / expected[i][j]
    return statistic, _chi_square_1df_p(statistic)


def _fisher_p_values(table: Table2x2) -> dict[str, float]:
    """Fisher exact p-values conditional on margins, with explicit alternatives.

    ``less`` sums tables with exposed-case count <= observed; ``greater`` sums
    counts >= observed. ``two_sided`` uses probability ordering (all tables no
    more probable than the observed table, up to floating-point tolerance).
    """
    a, b, c, d = table.a, table.b, table.c, table.d
    row1, row2, col1 = a + b, c + d, a + c
    total = row1 + row2
    lo, hi = max(0, col1 - row2), min(row1, col1)

    def log_choose(n: int, k: int) -> float:
        if k < 0 or k > n:
            return float("-inf")
        return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)

    def log_probability(x: int) -> float:
        return (log_choose(row1, x) + log_choose(row2, col1 - x)
                - log_choose(total, col1))

    observed_log_probability = log_probability(a)
    tolerance = log(1 + 1e-12)
    log_probabilities = [log_probability(x) for x in range(lo, hi + 1)]

    def sum_logs(values: list[float]) -> float:
        if not values:
            return 0.0
        peak = max(values)
        # Log-sum-exp avoids losing the entire tail to individual underflow.
        return min(1.0, exp(peak) * sum(exp(value - peak) for value in values))

    less = sum_logs(log_probabilities[:a - lo + 1])
    greater = sum_logs(log_probabilities[a - lo:])
    two_sided = sum_logs([value for value in log_probabilities
                          if value <= observed_log_probability + tolerance])
    return {"less": less, "greater": greater, "two_sided": two_sided}


def analyze_2x2(table: Table2x2, alpha: float = 0.05, *,
                haldane_anscombe: bool = False) -> dict[str, object]:
    """Calculate common 2x2 association measures and tests.

    Confidence intervals are standard large-sample Woolf/Wald/Katz intervals.
    Fisher's exact p-value uses the common probability-ordering two-sided
    definition. These are modern reference calculations; historical parity is
    unverified. The core uses Python's standard library and stays offline.
    """
    if not isinstance(haldane_anscombe, bool):
        raise ValueError("haldane_anscombe must be a boolean")
    if (isinstance(alpha, bool) or not isinstance(alpha, (int, float))
            or not isfinite(alpha) or not 0 < alpha < 1):
        raise ValueError("alpha must be a finite number strictly between 0 and 1")
    if 1 - alpha / 2 >= 1.0:
        raise ValueError("alpha is too small to represent the requested tail probability in double precision")
    a, b, c, d = table.a, table.b, table.c, table.d
    n1, n0 = a + b, c + d
    risk1, risk0 = a / n1, c / n0
    rr = _ratio(risk1, risk0)
    rd = risk1 - risk0
    z = NormalDist().inv_cdf(1 - alpha / 2)
    odds_ratio = _ratio(a * d, b * c)
    odds_ratio_ha: float | None = None
    odds_ratio_ha_ci: tuple[float, float] | None = None
    if haldane_anscombe:
        # Explicitly requested Haldane–Anscombe sensitivity estimate. Apply
        # the specified +0.5 to every cell whenever enabled, including tables
        # without zero cells. The uncorrected OR/RR/RD remain unchanged.
        aa, bb, cc, dd = (value + 0.5 for value in (a, b, c, d))
        odds_ratio_ha = (aa * dd) / (bb * cc)
        se_ha = sqrt(1 / aa + 1 / bb + 1 / cc + 1 / dd)
        odds_ratio_ha_ci = (exp(log(odds_ratio_ha) - z * se_ha),
                             exp(log(odds_ratio_ha) + z * se_ha))
    expected = table.expected
    pearson_chi2, pearson_p = _chi_square(table)
    yates_chi2, yates_p = _chi_square(table, correction=True)
    fisher = _fisher_p_values(table)
    or_ci: tuple[float, float] | None = None
    if all(x > 0 for x in (a, b, c, d)) and odds_ratio is not None:
        se_log_or = sqrt(1 / a + 1 / b + 1 / c + 1 / d)
        or_ci = (exp(log(odds_ratio) - z * se_log_or), exp(log(odds_ratio) + z * se_log_or))

    rr_ci: tuple[float, float] | None = None
    if all(x > 0 for x in (a, c)) and risk1 > 0 and risk0 > 0:
        se_log_rr = sqrt(1 / a - 1 / n1 + 1 / c - 1 / n0)
        rr_ci = (exp(log(rr) - z * se_log_rr), exp(log(rr) + z * se_log_rr)) if rr is not None else None

    se_rd = sqrt(risk1 * (1 - risk1) / n1 + risk0 * (1 - risk0) / n0)
    rd_ci = (rd - z * se_rd, rd + z * se_rd)
    af_exposed = _ratio(rd, risk1)
    af_exposed_ci = ((1 - 1 / rr_ci[0], 1 - 1 / rr_ci[1])
                     if rr_ci is not None and rr_ci[0] > 0 else None)
    # Definition-based PAF: (population risk - unexposed risk) / population
    # risk. This is algebraically equivalent to Pe*(RR-1)/(1+Pe*(RR-1)),
    # where Pe is the population exposure prevalence, when RR is finite.
    # Computing from risks also handles RR=0 and the limit RR -> infinity.
    population_risk = (a + c) / table.total
    paf = _ratio(population_risk - risk0, population_risk)

    return {
        "counts": {"a_exposed_cases": a, "b_exposed_non_cases": b,
                   "c_unexposed_cases": c, "d_unexposed_non_cases": d},
        "risk_exposed": risk1, "risk_unexposed": risk0,
        "odds_ratio": odds_ratio, "odds_ratio_woolf_ci": or_ci,
        "odds_ratio_haldane_anscombe": odds_ratio_ha,
        "odds_ratio_haldane_anscombe_woolf_ci": odds_ratio_ha_ci,
        "risk_ratio": rr, "risk_ratio_katz_ci": rr_ci,
        "risk_difference": rd, "risk_difference_wald_ci": rd_ci,
        "attributable_fraction_exposed": af_exposed,
        "attributable_fraction_exposed_katz_ci": af_exposed_ci,
        "population_attributable_fraction": paf,
        "pearson_chi2": pearson_chi2, "pearson_p": pearson_p,
        "yates_chi2": yates_chi2, "yates_p": yates_p,
        "fisher_less_p": fisher["less"],
        "fisher_greater_p": fisher["greater"],
        "fisher_two_sided_p": fisher["two_sided"],
        "expected_counts": expected,
        "expected_any_below_5": any(v < 5 for row in expected for v in row),
        "alpha": alpha,
        "notes": ["Modern standard-library implementation; historical EpiTable output parity has not been established.",
                  "Population attributable fraction is (population risk - unexposed risk) / population risk; causal interpretation requires substantive assumptions.",
                  "For case-control sampled tables, interpret the odds ratio; risk, risk ratio, risk difference, and attributable fractions are not identified by case-control sampling alone.",
                  "Exact Cornfield/Fisher/mid-p odds-ratio confidence limits described by the legacy help are not implemented; the displayed odds-ratio interval is Woolf's large-sample interval.",
                  "Haldane–Anscombe corrected odds ratio is available only when explicitly requested; it does not replace uncorrected estimates."],
    }


def diagnostic_metrics(tp: int, fp: int, fn: int, tn: int) -> dict[str, float | None]:
    """Return screening metrics for true-positive, false-positive, false-negative, true-negative counts."""
    vals = (tp, fp, fn, tn)
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in vals):
        raise ValueError("diagnostic counts must be nonnegative integers")
    sens = _ratio(tp, tp + fn)
    spec = _ratio(tn, tn + fp)
    ppv = _ratio(tp, tp + fp)
    npv = _ratio(tn, tn + fn)
    lr_pos = _ratio(sens, 1 - spec) if sens is not None and spec is not None else None
    lr_neg = _ratio(1 - sens, spec) if sens is not None and spec is not None else None
    total = tp + fp + fn + tn
    accuracy = _ratio(tp + tn, total)
    balanced_accuracy = ((sens + spec) / 2
                         if sens is not None and spec is not None else None)
    f1 = _ratio(2 * tp, 2 * tp + fp + fn)
    return {"sensitivity": sens, "specificity": spec, "ppv": ppv, "npv": npv,
            "false_positive_rate": 1 - spec if spec is not None else None,
            "false_negative_rate": 1 - sens if sens is not None else None,
            "accuracy": accuracy, "balanced_accuracy": balanced_accuracy, "f1": f1,
            "lr_positive": lr_pos, "lr_negative": lr_neg}
