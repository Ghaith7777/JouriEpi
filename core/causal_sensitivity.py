"""E-values for unmeasured-confounding sensitivity analysis.

Implements the risk-ratio E-value of VanderWeele and Ding (2017). Odds ratios
must be converted explicitly: either the square-root approximation for a
common outcome, or baseline-risk conversion. These are sensitivity summaries,
not evidence that an association is causal or that bias is absent.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

Scale = Literal["RR", "OR"]
ORMethod = Literal["sqrt_approximation", "baseline_risk"]


@dataclass(frozen=True)
class EValueResult:
    """Point and confidence-limit E-values plus transparent input metadata."""

    e_value: float
    confidence_limit_e_value: float | None
    estimate: float
    confidence_interval: tuple[float, float] | None
    input_scale: Scale
    risk_ratio_estimate: float
    risk_ratio_confidence_interval: tuple[float, float] | None
    conversion_method: str
    baseline_risk: float | None
    confidence_interval_includes_null: bool | None
    interpretation: str


def _positive_finite(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite positive number")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return value


def _e_value(rr: float) -> float:
    """Return the E-value for an RR on either side of the null."""
    rr = 1.0 / rr if rr < 1 else rr
    return rr + math.sqrt(rr * (rr - 1.0))


def _to_rr(value: float, scale: Scale, method: ORMethod | None,
           baseline_risk: float | None) -> float:
    if scale == "RR":
        if method is not None or baseline_risk is not None:
            raise ValueError("OR conversion options are only valid when scale='OR'")
        return value
    if scale != "OR":
        raise ValueError("scale must be 'RR' or 'OR'")
    if method == "sqrt_approximation":
        if baseline_risk is not None:
            raise ValueError("baseline_risk cannot be combined with sqrt_approximation")
        return math.sqrt(value)
    if method == "baseline_risk":
        if baseline_risk is None:
            raise ValueError("baseline_risk is required for baseline_risk conversion")
        if isinstance(baseline_risk, bool) or not isinstance(baseline_risk, (int, float)):
            raise TypeError("baseline_risk must be a number in (0, 1)")
        p0 = float(baseline_risk)
        if not math.isfinite(p0) or not 0 < p0 < 1:
            raise ValueError("baseline_risk must be finite and strictly between 0 and 1")
        return value / (1.0 - p0 + p0 * value)
    raise ValueError("OR scale requires method='sqrt_approximation' or 'baseline_risk'")


def e_value(
    estimate: float,
    confidence_interval: tuple[float, float] | None = None,
    *,
    scale: Scale = "RR",
    or_method: ORMethod | None = None,
    baseline_risk: float | None = None,
) -> EValueResult:
    """Calculate an E-value for an RR, or an explicitly converted OR.

    The confidence-limit E-value uses the limit nearest the null (lower bound
    for harmful estimates, upper bound for protective estimates). If the CI
    includes RR=1, its confidence-limit E-value is 1. CI inputs are specified
    on the original scale and must be finite, positive, and ordered.

    OR conversion methods: ``sqrt_approximation`` uses RR≈sqrt(OR), a rough
    approximation most defensible for common outcomes; ``baseline_risk`` uses
    RR≈OR/(1-p0+p0*OR), where p0 is the unexposed baseline risk. Neither method
    is silently selected. Reference: VanderWeele TJ, Ding P. Sensitivity
    Analysis in Observational Research: Introducing the E-Value. Ann Intern
    Med. 2017;167(4):268-274. doi:10.7326/M16-2607.
    """
    est = _positive_finite(estimate, "estimate")
    if confidence_interval is not None:
        if (not isinstance(confidence_interval, (tuple, list)) or len(confidence_interval) != 2):
            raise ValueError("confidence_interval must be a (lower, upper) pair")
        low = _positive_finite(confidence_interval[0], "confidence_interval lower bound")
        high = _positive_finite(confidence_interval[1], "confidence_interval upper bound")
        if low > high:
            raise ValueError("confidence_interval lower bound must not exceed upper bound")
        if not low <= est <= high:
            raise ValueError("estimate must lie within confidence_interval")
    else:
        low = high = None

    rr = _to_rr(est, scale, or_method, baseline_risk)
    rr_ci = None
    ci_includes_null = None
    if confidence_interval is not None:
        rr_low = _to_rr(low, scale, or_method, baseline_risk)
        rr_high = _to_rr(high, scale, or_method, baseline_risk)
        rr_ci = (rr_low, rr_high)
        ci_includes_null = rr_low <= 1.0 <= rr_high
        if ci_includes_null:
            ci_e = 1.0
        elif rr < 1.0:
            ci_e = _e_value(rr_high)
        else:
            ci_e = _e_value(rr_low)
    else:
        ci_e = None

    point_e = _e_value(rr)
    if rr > 1:
        direction = "harmful/higher-risk association"
    elif rr < 1:
        direction = "protective/lower-risk association"
    else:
        direction = "null association"
    if confidence_interval is None:
        ci_note = "No confidence interval was supplied, so no confidence-limit E-value or interval-based inference is available."
    elif ci_includes_null:
        ci_note = "The confidence interval includes the null; its confidence-limit E-value is 1."
    else:
        ci_note = "The confidence interval excludes the null; the confidence-limit E-value uses the bound nearest the null."
    narrative = (
        f"The converted estimate indicates a {direction}. The point E-value is {point_e:.3g}: "
        "under the E-value framework, an unmeasured confounder would need associations of at least "
        "this strength with both exposure and outcome, on the risk-ratio scale and conditional on "
        "measured covariates, to explain away the point estimate under the framework's assumptions. "
        f"{ci_note} This does not establish causality or rule out bias."
    )
    conversion = "none (risk ratio input)" if scale == "RR" else str(or_method)
    return EValueResult(point_e, ci_e, est, tuple(confidence_interval) if confidence_interval is not None else None,
                        scale, rr, rr_ci, conversion, baseline_risk, ci_includes_null, narrative)
