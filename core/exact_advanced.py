"""Optional Boschloo unconditional exact tests for 2x2 tables.

SciPy is an optional dependency. The core app remains offline and its base
installation stays dependency-free; install the ``advanced`` extra to enable
this module's calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from math import isfinite

from .engine_2x2 import Table2x2

MIN_SCIPY_VERSION = (1, 7, 0)


@dataclass(frozen=True)
class BoschlooResult:
    """Boschloo p-values for each directional alternative and two-sided test."""

    statistic: float
    p_value_greater: float
    p_value_less: float
    p_value_two_sided: float
    scipy_version: str
    method: str = "Boschloo unconditional exact test"


def _version_tuple(value: str) -> tuple[int, ...]:
    """Parse the numeric release prefix without requiring packaging at runtime."""
    parts: list[int] = []
    for piece in value.split("."):
        digits = "".join(char for char in piece if char.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def _boschloo_function():
    try:
        installed = version("scipy")
    except PackageNotFoundError as exc:
        raise RuntimeError(
            "Boschloo's test requires the optional SciPy dependency; install modern-epitable[advanced] in an approved environment."
        ) from exc
    if _version_tuple(installed) < MIN_SCIPY_VERSION:
        raise RuntimeError(
            f"Boschloo's test requires SciPy >= {'.'.join(map(str, MIN_SCIPY_VERSION))}; found {installed}."
        )
    try:
        function = import_module("scipy.stats").boschloo_exact
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(
            f"SciPy {installed} does not expose scipy.stats.boschloo_exact; upgrade SciPy to >= 1.7.0."
        ) from exc
    return installed, function


def analyze_boschloo(table: Table2x2) -> BoschlooResult:
    """Calculate Boschloo's greater, less and two-sided p-values.

    The input is ``[[a,b],[c,d]]``: exposed/unexposed rows and case/non-case
    columns. With this orientation, ``greater`` tests in the direction of an
    odds ratio above one. Boschloo's test is an unconditional exact test that
    uses Fisher's exact test as its ordering statistic. It can be more powerful
    than Fisher's conditional exact test for some tables while controlling
    type-I error under its stated model; that is not a guarantee for every
    dataset, and p-values should not be selected post hoc.

    Raises an actionable RuntimeError when the optional compatible SciPy is
    absent. No data is sent over a network and no continuity correction is used.
    """
    if not isinstance(table, Table2x2):
        raise ValueError("table must be a validated Table2x2 instance")
    installed, function = _boschloo_function()
    matrix = [[table.a, table.b], [table.c, table.d]]
    try:
        greater = function(matrix, alternative="greater")
        less = function(matrix, alternative="less")
        two_sided = function(matrix, alternative="two-sided")
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"SciPy {installed} Boschloo calculation failed for this table: {exc}") from exc
    values = (float(greater.pvalue), float(less.pvalue), float(two_sided.pvalue))
    if any(not isfinite(value) or not 0 <= value <= 1 for value in values):
        raise RuntimeError("SciPy returned an invalid Boschloo p-value outside [0, 1].")
    return BoschlooResult(float(two_sided.statistic), values[0], values[1], values[2], installed)
