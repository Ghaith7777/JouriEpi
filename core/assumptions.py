"""Assumption and data-quality checks for 2x2 tables."""

from .engine_2x2 import Table2x2


def audit_expected_counts(table: Table2x2) -> dict[str, object]:
    """Summarize expected counts without automatically changing the test."""
    values = [x for row in table.expected for x in row]
    return {"expected_counts": table.expected,
            "minimum_expected": min(values),
            "cells_below_5": sum(x < 5 for x in values),
            "any_expected_below_5": any(x < 5 for x in values),
            "zero_observed_cells": sum(x == 0 for x in (table.a, table.b, table.c, table.d))}
