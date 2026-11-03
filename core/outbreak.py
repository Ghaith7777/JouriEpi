"""Offline outbreak curves and Cori-style instantaneous reproduction numbers."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil, isfinite
from typing import Any

import pandas as pd
from scipy.stats import gamma


@dataclass(frozen=True)
class RtResult:
    estimates: pd.DataFrame
    serial_interval_weights: tuple[float, ...]
    window: int
    prior_shape: float
    prior_rate: float
    method: str = "Cori et al. (2013) instantaneous Rt; Poisson-Gamma conjugate posterior"

    def to_dict(self) -> dict[str, Any]:
        records = self.estimates.to_dict(orient="records")
        for record in records:
            for column in ("window_start", "date"):
                if column in record and hasattr(record[column], "isoformat"):
                    record[column] = record[column].isoformat()
        return {
            "estimates": records,
            "serial_interval_weights": list(self.serial_interval_weights),
            "window": self.window, "prior_shape": self.prior_shape,
            "prior_rate": self.prior_rate, "method": self.method,
        }


def _daily_incidence(df: pd.DataFrame, date_col: str) -> pd.Series:
    if not isinstance(df, pd.DataFrame) or date_col not in df.columns:
        raise ValueError("df must be a DataFrame containing date_col")
    dates = pd.to_datetime(df[date_col], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
    if dates.isna().any():
        raise ValueError("date_col contains missing or invalid dates")
    counts = dates.value_counts().sort_index().astype(int)
    full = pd.date_range(counts.index.min(), counts.index.max(), freq="D")
    return counts.reindex(full, fill_value=0).rename("cases").astype(int)


def epicurve(df: pd.DataFrame, date_col: str, interval: str = "day") -> pd.DataFrame:
    """Aggregate a case line list by calendar day or ISO epidemiological week."""
    if interval not in {"day", "iso_week"}:
        raise ValueError("interval must be 'day' or 'iso_week'")
    daily = _daily_incidence(df, date_col)
    frame = daily.rename_axis("date").reset_index()
    if interval == "day":
        return frame
    iso = frame["date"].dt.isocalendar()
    frame["iso_year"] = iso.year.astype(int)
    frame["iso_week"] = iso.week.astype(int)
    frame["week_start"] = frame["date"] - pd.to_timedelta(iso.day.astype(int) - 1, unit="D")
    return (frame.groupby(["iso_year", "iso_week"], as_index=False, sort=True)
            .agg(week_start=("week_start", "first"), cases=("cases", "sum")))


def estimate_rt(
    df: pd.DataFrame,
    date_col: str,
    window: int = 7,
    mean_si: float = 4.7,
    std_si: float = 2.9,
    *,
    prior_shape: float = 1.0,
    prior_rate: float = 0.2,
    credible_level: float = 0.95,
) -> RtResult:
    """Estimate instantaneous Rt using Cori's sliding-window Gamma posterior.

    A discretized Gamma serial-interval distribution assigns mass to day
    intervals (k-1, k]. For each complete window, posterior shape is the prior
    shape plus incident cases, and posterior rate is the prior rate plus total
    infectiousness. The default prior is Gamma(shape=1, rate=0.2).
    """
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ValueError("window must be a positive integer")
    numeric_parameters = {}
    for value, name in ((mean_si, "mean_si"), (std_si, "std_si"),
                        (prior_shape, "prior_shape"), (prior_rate, "prior_rate")):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)) or float(value) <= 0:
            raise ValueError(f"{name} must be finite and greater than zero")
        numeric_parameters[name] = float(value)
    mean_si = numeric_parameters["mean_si"]
    std_si = numeric_parameters["std_si"]
    prior_shape = numeric_parameters["prior_shape"]
    prior_rate = numeric_parameters["prior_rate"]
    if isinstance(credible_level, bool) or not isinstance(credible_level, (int, float)) or not isfinite(float(credible_level)) or not 0 < credible_level < 1:
        raise ValueError("credible_level must be between 0 and 1")
    incidence = _daily_incidence(df, date_col)
    n = len(incidence)
    if n < window:
        raise ValueError("the observed date range must contain at least 'window' calendar days")
    shape_si = (mean_si / std_si) ** 2
    scale_si = (std_si ** 2) / mean_si
    max_lag = max(1, int(ceil(mean_si + 6 * std_si)))
    weights = [float(gamma.cdf(day, a=shape_si, scale=scale_si) -
                     gamma.cdf(day - 1, a=shape_si, scale=scale_si))
               for day in range(1, max_lag + 1)]
    total_weight = sum(weights)
    if total_weight <= 0:
        raise ValueError("serial-interval distribution has no mass over the observed follow-up")
    weights = [weight / total_weight for weight in weights]
    cases = incidence.to_numpy(dtype=float)
    infectiousness = [0.0] * n
    for t in range(n):
        infectiousness[t] = sum(cases[t - lag] * weights[lag - 1]
                                for lag in range(1, min(t, len(weights)) + 1))
    alpha_tail = (1 - credible_level) / 2
    records: list[dict[str, Any]] = []
    for t in range(window - 1, n):
        start = t - window + 1
        observed = float(cases[start:t + 1].sum())
        lambda_sum = float(sum(infectiousness[start:t + 1]))
        posterior_shape = prior_shape + observed
        posterior_rate = prior_rate + lambda_sum
        records.append({
            "window_start": incidence.index[start], "date": incidence.index[t],
            "cases_in_window": int(observed),
            "infectiousness": lambda_sum,
            "rt_mean": posterior_shape / posterior_rate,
            "rt_median": float(gamma.ppf(0.5, a=posterior_shape, scale=1 / posterior_rate)),
            "rt_lower": float(gamma.ppf(alpha_tail, a=posterior_shape, scale=1 / posterior_rate)),
            "rt_upper": float(gamma.ppf(1 - alpha_tail, a=posterior_shape, scale=1 / posterior_rate)),
            "posterior_shape": posterior_shape, "posterior_rate": posterior_rate,
        })
    return RtResult(pd.DataFrame.from_records(records), tuple(weights), window,
                    float(prior_shape), float(prior_rate))
