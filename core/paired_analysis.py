"""Paired 2×2 analysis, McNemar test and conditional exact paired odds ratio CI."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from statistics import NormalDist


@dataclass(frozen=True)
class McNemarResult:
    a: int
    b: int
    c: int
    d: int
    discordant_b: int
    discordant_c: int
    discordant_total: int
    asymptotic_chi_square: float | None
    asymptotic_p_value: float | None
    exact_p_value: float | None
    paired_odds_ratio: float | None
    exact_or_ci: tuple[float, float] | None
    alpha: float
    continuity_correction: str = "Edwards (subtract 1 from |b-c|, floored at 0)"

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_counts(a: int, b: int, c: int, d: int) -> tuple[int, int, int, int]:
    values = (a, b, c, d)
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in values):
        raise ValueError("paired 2×2 counts must be nonnegative integers")
    if sum(values) == 0:
        raise ValueError("at least one matched pair is required")
    return values


def _exact_binomial_pvalue(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    from scipy.stats import binomtest
    return float(binomtest(min(b, c), n=n, p=0.5, alternative="two-sided").pvalue)


def _clopper_pearson(k: int, n: int, alpha: float) -> tuple[float, float]:
    from scipy.stats import beta
    low = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    high = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return low, high


def mcnemar_test(a: int, b: int, c: int, d: int, *, alpha: float = 0.05) -> McNemarResult:
    """Calculate McNemar's test for a paired 2×2 table.

    Table convention: rows are reference/pre and columns are comparison/post;
    ``b`` and ``c`` are the two discordant cells. Exact p uses a two-sided
    binomial test conditional on the discordant total. Exact OR limits invert
    Clopper–Pearson limits for p=b/(b+c), transformed to OR=p/(1-p).
    """
    a, b, c, d = _validate_counts(a, b, c, d)
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not isfinite(float(alpha)) or not 0 < alpha < 1:
        raise ValueError("alpha must be finite and strictly between 0 and 1")
    n = b + c
    if n:
        from scipy.stats import chi2
        statistic = max(0, abs(b - c) - 1) ** 2 / n
        asymptotic_p = float(chi2.sf(statistic, 1))
        exact_p = _exact_binomial_pvalue(b, c)
        p_hat = b / n
        or_estimate = b / c if c else (float("inf") if b else None)
        p_low, p_high = _clopper_pearson(b, n, float(alpha))
        low = 0.0 if p_low == 0 else p_low / (1 - p_low)
        high = float("inf") if p_high == 1 else p_high / (1 - p_high)
        ci = (low, high)
    else:
        statistic = asymptotic_p = or_estimate = ci = None
        # With no discordant pairs the conditional sample is empty; the exact
        # two-sided test is conventionally reported as p=1, while OR/CI remain
        # undefined and the asymptotic statistic is not estimable.
        exact_p = 1.0
    return McNemarResult(a, b, c, d, b, c, n, statistic, asymptotic_p, exact_p,
                         or_estimate, ci, float(alpha))
