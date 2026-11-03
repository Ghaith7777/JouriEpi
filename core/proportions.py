"""Offline confidence intervals for a single binomial proportion.

The Wilson score interval is a modern score-based approximation. The
Clopper-Pearson interval is an exact equal-tailed binomial interval. Neither is
claimed to reproduce the Fleiss or mid-p options in historical EpiTable.
Only the Python standard library is required.
"""

from __future__ import annotations

from math import exp, isfinite, lgamma, log, log1p
from statistics import NormalDist


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    """Evaluate the incomplete-beta continued fraction (Numerical Recipes)."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    tiny = 1e-300
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 10001):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-14:
            return h
    raise ArithmeticError("Incomplete-beta continued fraction did not converge")


def _regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    log_front = (lgamma(a + b) - lgamma(a) - lgamma(b)
                 + a * log(x) + b * log1p(-x))
    front = exp(log_front)
    if x < (a + 1) / (a + b + 2):
        return min(1.0, max(0.0, front * _beta_continued_fraction(a, b, x) / a))
    return min(1.0, max(0.0, 1.0 - front * _beta_continued_fraction(b, a, 1 - x) / b))


def _beta_quantile(probability: float, a: float, b: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if _regularized_beta(mid, a, b) < probability:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def proportion_confidence_intervals(successes: int, trials: int,
                                    alpha: float = 0.05) -> dict[str, tuple[float, float]]:
    """Return Wilson score and exact Clopper-Pearson intervals.

    Args:
        successes: Integer count of successes, between zero and trials.
        trials: Positive integer binomial denominator.
        alpha: Two-sided tail probability, strictly between zero and one.

    Returns:
        Mapping with ``wilson_score`` (score-based approximation) and
        ``clopper_pearson_exact`` (equal-tailed exact binomial interval).
    """
    if (isinstance(successes, bool) or not isinstance(successes, int)
            or isinstance(trials, bool) or not isinstance(trials, int)
            or trials <= 0 or not 0 <= successes <= trials):
        raise ValueError("Require integer counts with 0 <= successes <= trials and trials > 0")
    if (isinstance(alpha, bool) or not isinstance(alpha, (int, float))
            or not isfinite(alpha) or not 0 < alpha < 1):
        raise ValueError("alpha must be a finite number strictly between 0 and 1")
    if 1 - alpha / 2 >= 1.0:
        raise ValueError("alpha is too small to represent the requested tail probability in double precision")
    p = successes / trials
    z = NormalDist().inv_cdf(1 - alpha / 2)
    z2 = z * z
    denom = 1 + z2 / trials
    center = (p + z2 / (2 * trials)) / denom
    half = z * ((p * (1 - p) / trials + z2 / (4 * trials * trials)) ** 0.5) / denom
    wilson = (max(0.0, center - half), min(1.0, center + half))
    lower = 0.0 if successes == 0 else _beta_quantile(alpha / 2, successes, trials - successes + 1)
    upper = 1.0 if successes == trials else _beta_quantile(1 - alpha / 2, successes + 1, trials - successes)
    return {"wilson_score": wilson, "clopper_pearson_exact": (lower, upper)}
