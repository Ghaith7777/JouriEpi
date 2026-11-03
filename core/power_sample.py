"""Basic normal-approximation sample-size helpers.

These helpers are transparent modern approximations and are not asserted to
match the proprietary EpiTable sample-size routines.
"""

from math import ceil, isfinite
from statistics import NormalDist


def two_proportion_sample_size(p_control: float, p_exposed: float,
                               alpha: float = 0.05, power: float = 0.8,
                               allocation_ratio: float = 1.0) -> tuple[int, int]:
    """Approximate independent group sizes for a two-sided two-proportion test.

    Returns (control_n, exposed_n); allocation_ratio is exposed/control.
    """
    values = (p_control, p_exposed, alpha, power, allocation_ratio)
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value)
           for value in values):
        raise ValueError("All inputs must be finite numbers")
    if not (0 < p_control < 1 and 0 < p_exposed < 1):
        raise ValueError("Both proportions must be strictly between 0 and 1")
    if p_control == p_exposed:
        raise ValueError("A finite sample size cannot be calculated for equal proportions")
    if not 0 < alpha < 1 or not 0 < power < 1 or allocation_ratio <= 0:
        raise ValueError("alpha, power, and allocation_ratio are outside valid ranges")
    if 1 - alpha / 2 >= 1.0:
        raise ValueError("alpha is too small to represent the requested tail probability in double precision")
    if power < 0.5:
        raise ValueError("power must be at least 0.5 for this normal-approximation sample-size formula")
    p_bar = (p_control + allocation_ratio * p_exposed) / (1 + allocation_ratio)
    normal = NormalDist()
    z_alpha = normal.inv_cdf(1 - alpha / 2)
    z_power = normal.inv_cdf(power)
    # Under H0, Var(p1-p0) = p_bar*(1-p_bar)*(1/n_control + 1/n_exposed).
    # Since n_exposed = allocation_ratio*n_control, the factor is (1 + 1/r),
    # with no additional factor of two (for r=1 this already equals two).
    numerator = (z_alpha * (p_bar * (1 - p_bar) * (1 + 1 / allocation_ratio)) ** 0.5 +
                 z_power * (p_control * (1 - p_control) +
                            p_exposed * (1 - p_exposed) / allocation_ratio) ** 0.5) ** 2
    raw_control_n = numerator / (p_exposed - p_control) ** 2
    if not isfinite(raw_control_n):
        raise ValueError("Required sample size exceeds the supported numeric range")
    n_control = ceil(raw_control_n)
    raw_exposed_n = n_control * allocation_ratio
    if not isfinite(raw_exposed_n):
        raise ValueError("Required exposed-group size exceeds the supported numeric range")
    return n_control, ceil(raw_exposed_n)


def case_control_sample_size(odds_ratio: float, exposure_prevalence_controls: float,
                             alpha: float = 0.05, power: float = 0.8,
                             cases_per_control: float = 1.0) -> tuple[int, int]:
    """Approximate case/control sample sizes for a target odds ratio.

    Uses the standard odds-ratio relationship to derive exposure prevalence in
    cases from the prevalence among controls, then applies the independent
    two-proportion normal approximation. Returns (controls_n, cases_n).
    This is a modern planning approximation, not an EpiTable reproduction.
    """
    values = (odds_ratio, exposure_prevalence_controls, alpha, power, cases_per_control)
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value)
           for value in values):
        raise ValueError("All inputs must be finite numbers")
    if odds_ratio <= 0:
        raise ValueError("odds_ratio must be positive")
    if not 0 < exposure_prevalence_controls < 1:
        raise ValueError("Control exposure prevalence must be strictly between 0 and 1")
    if isinstance(cases_per_control, bool) or not 0 < cases_per_control:
        raise ValueError("cases_per_control must be positive")
    p0 = exposure_prevalence_controls
    p1 = odds_ratio * p0 / (1 - p0 + odds_ratio * p0)
    if p1 == p0:
        raise ValueError("An odds ratio of 1 cannot be detected with finite sample size")
    controls, cases = two_proportion_sample_size(
        p0, p1, alpha=alpha, power=power, allocation_ratio=cases_per_control
    )
    return controls, cases


def cohort_sample_size(risk_unexposed: float, risk_exposed: float,
                       alpha: float = 0.05, power: float = 0.8,
                       exposed_per_unexposed: float = 1.0) -> tuple[int, int]:
    """Approximate cohort group sizes; returns (unexposed, exposed).

    This is the independent two-proportion normal approximation. It does not
    implement survival analysis, loss-to-follow-up inflation, or legacy parity.
    """
    return two_proportion_sample_size(risk_unexposed, risk_exposed, alpha, power,
                                      exposed_per_unexposed)


def cross_sectional_sample_size(prevalence_unexposed: float, prevalence_exposed: float,
                                alpha: float = 0.05, power: float = 0.8,
                                exposed_per_unexposed: float = 1.0) -> tuple[int, int]:
    """Approximate cross-sectional group sizes; returns (unexposed, exposed).

    Assumes independent groups and compares two prevalences; complex survey
    design effects and clustering are not included.
    """
    return two_proportion_sample_size(prevalence_unexposed, prevalence_exposed,
                                      alpha, power, exposed_per_unexposed)


def two_proportion_power(n_control: int, n_exposed: int, p_control: float,
                         p_exposed: float, alpha: float = 0.05) -> float:
    """Approximate two-sided power for an independent two-proportion z test.

    Uses the pooled null variance for the rejection threshold and unpooled
    alternative variance for power. This is a normal approximation, not an
    exact or continuity-corrected calculation.
    """
    numeric = (p_control, p_exposed, alpha)
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not isfinite(v)
           for v in numeric):
        raise ValueError("Proportions and alpha must be finite numbers")
    if (isinstance(n_control, bool) or not isinstance(n_control, int) or n_control <= 0
            or isinstance(n_exposed, bool) or not isinstance(n_exposed, int) or n_exposed <= 0):
        raise ValueError("Group sizes must be positive integers")
    if not (0 < p_control < 1 and 0 < p_exposed < 1):
        raise ValueError("Both proportions must be strictly between 0 and 1")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if 1 - alpha / 2 >= 1.0:
        raise ValueError("alpha is too small to represent the requested tail probability in double precision")
    pooled = (n_control * p_control + n_exposed * p_exposed) / (n_control + n_exposed)
    se_null = (pooled * (1 - pooled) * (1 / n_control + 1 / n_exposed)) ** 0.5
    se_alt = (p_control * (1 - p_control) / n_control
              + p_exposed * (1 - p_exposed) / n_exposed) ** 0.5
    z_critical = NormalDist().inv_cdf(1 - alpha / 2)
    delta = p_exposed - p_control
    cutoff = z_critical * se_null
    normal = NormalDist()
    return normal.cdf((-cutoff - delta) / se_alt) + 1 - normal.cdf((cutoff - delta) / se_alt)
