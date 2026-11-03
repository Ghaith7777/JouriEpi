"""Additive interaction measures on the odds-ratio scale.

Input rows are exposure groups 00, 10, 01, 11; each row is (cases, non-cases).
The reference group is 00. Delta-method intervals use the covariance matrix
of the three logistic-regression contrast coefficients. Zero cells are not
silently corrected: the log-odds model is not estimable and raises ValueError.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class AdditiveInteractionResult:
    odds_ratio_10: float
    odds_ratio_01: float
    odds_ratio_11: float
    reri: float
    reri_ci: tuple[float, float]
    attributable_proportion: float
    ap_ci: tuple[float, float]
    synergy_index: float
    si_ci: tuple[float, float]
    covariance_beta: tuple[tuple[float, ...], ...]
    alpha: float
    method: str = "Delta method on saturated logistic log-odds contrasts"

    def as_dict(self) -> dict:
        return asdict(self)


def _measures(beta: np.ndarray) -> np.ndarray:
    beta_a, beta_b, beta_ab = map(float, beta)
    or10 = math.exp(beta_a)
    or01 = math.exp(beta_b)
    or11 = math.exp(beta_a + beta_b + beta_ab)
    reri = or11 - or10 - or01 + 1.0
    ap = reri / or11
    denominator = (or10 - 1.0) + (or01 - 1.0)
    si = (or11 - 1.0) / denominator if abs(denominator) > 1e-12 else math.nan
    return np.array([reri, ap, si], dtype=float)


def _numeric_gradient(function, beta: np.ndarray) -> np.ndarray:
    gradient = np.empty((3, len(beta)), dtype=float)
    for index in range(len(beta)):
        step = 1e-5 * max(1.0, abs(float(beta[index])))
        upper, lower = beta.copy(), beta.copy()
        upper[index] += step
        lower[index] -= step
        gradient[:, index] = (function(upper) - function(lower)) / (2 * step)
    return gradient


def analyze_additive_interaction(
    counts: Sequence[Sequence[int]], *, alpha: float = 0.05
) -> AdditiveInteractionResult:
    """Estimate RERI, AP and SI from four independent exposure groups.

    ``counts`` must be ``[(cases, noncases)_00, ... _10, _01, _11]``. CIs are
    normal/Wald delta-method intervals and are not truncated to plausible
    ranges. AP and SI are undefined when their denominators are zero.
    """
    if len(counts) != 4 or any(len(row) != 2 for row in counts):
        raise ValueError("counts must contain four (cases, non-cases) pairs in 00,10,01,11 order")
    normalized: list[tuple[int, int]] = []
    for row in counts:
        pair = []
        for value in row:
            if isinstance(value, bool) or int(value) != value or int(value) < 0:
                raise ValueError("counts must be nonnegative integers")
            pair.append(int(value))
        cases, noncases = pair
        if cases == 0 or noncases == 0:
            raise ValueError("each exposure group needs positive case and non-case counts; no continuity correction is applied")
        normalized.append((cases, noncases))
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")

    # Independent binomial groups: Var(logit p_i) = 1/cases + 1/noncases.
    cell_var = np.array([1 / case + 1 / noncase for case, noncase in normalized], dtype=float)
    cell_log_odds = np.array([math.log(case / noncase) for case, noncase in normalized])
    # beta = (theta10-theta00, theta01-theta00, theta11-theta10-theta01+theta00)
    contrast = np.array([[-1, 1, 0, 0], [-1, 0, 1, 0], [1, -1, -1, 1]], dtype=float)
    beta = contrast @ cell_log_odds
    covariance = contrast @ np.diag(cell_var) @ contrast.T
    estimates = _measures(beta)
    if not np.all(np.isfinite(estimates)):
        raise ValueError("RERI/AP/SI not all estimable: synergy-index denominator or OR11 is zero/undefined")
    gradient = _numeric_gradient(_measures, beta)
    variances = np.einsum("ij,jk,ik->i", gradient, covariance, gradient)
    standard_errors = np.sqrt(np.maximum(variances, 0.0))
    z = float(norm.ppf(1 - alpha / 2))
    intervals = [(float(estimates[i] - z * standard_errors[i]), float(estimates[i] + z * standard_errors[i])) for i in range(3)]
    ors = np.exp([beta[0], beta[1], beta.sum()])
    return AdditiveInteractionResult(
        odds_ratio_10=float(ors[0]), odds_ratio_01=float(ors[1]), odds_ratio_11=float(ors[2]),
        reri=float(estimates[0]), reri_ci=intervals[0],
        attributable_proportion=float(estimates[1]), ap_ci=intervals[1],
        synergy_index=float(estimates[2]), si_ci=intervals[2],
        covariance_beta=tuple(tuple(float(v) for v in row) for row in covariance), alpha=float(alpha),
    )
