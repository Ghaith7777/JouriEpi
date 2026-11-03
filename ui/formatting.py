"""Presentation-only formatting helpers for Modern EpiTable."""

from __future__ import annotations

from math import isfinite


def fmt_num(value: object, digits: int | None = None) -> str:
    """Format an estimate to 2 decimals (or 3 below one); allow explicit precision."""
    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    if not isfinite(number):
        return "—"
    if number == 0:
        return "0"
    if abs(number) >= 10000 or abs(number) < 0.001:
        return f"{number:.3g}"
    if digits is None:
        digits = 3 if abs(number) < 1 else 2
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{value:,}"
    return f"{number:.{digits}f}"


def fmt_p(value: object) -> str:
    """Format p-values without false precision or unreadable long decimals."""
    if value is None:
        return "—"
    try:
        p = float(value)
    except (TypeError, ValueError):
        return "—"
    if not isfinite(p) or not 0 <= p <= 1:
        return "—"
    if p < 0.001:
        return "p < 0.001"
    return f"{p:.3g}"


def fmt_ci(interval: object, digits: int = 2) -> str:
    """Format a two-sided confidence interval as ``lower – upper``."""
    if interval is None:
        return "Not estimable"
    try:
        lower, upper = interval  # type: ignore[misc]
        lower, upper = float(lower), float(upper)
    except (TypeError, ValueError):
        return "Not estimable"
    if not isfinite(lower) or not isfinite(upper):
        return "Not estimable"
    return f"{lower:.{digits}f} – {upper:.{digits}f}"


def fmt_pct(value: object, digits: int = 1) -> str:
    """Format a proportion as a percentage, preserving undefined values."""
    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    if not isfinite(number):
        return "—"
    return f"{number * 100:.{digits}f}%"

