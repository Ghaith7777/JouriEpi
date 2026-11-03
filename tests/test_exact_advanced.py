"""Tests for the optional Boschloo unconditional exact test."""

import pytest

from core.engine_2x2 import Table2x2
from core import exact_advanced


def test_invalid_table_argument_is_rejected_before_loading_optional_scipy():
    with pytest.raises(ValueError, match="Table2x2"):
        exact_advanced.analyze_boschloo((1, 2, 3, 4))


def test_missing_scipy_has_actionable_offline_dependency_message(monkeypatch):
    from importlib.metadata import PackageNotFoundError

    def no_package(_name):
        raise PackageNotFoundError("scipy")

    monkeypatch.setattr(exact_advanced, "version", no_package)
    with pytest.raises(RuntimeError, match=r"modern-epitable\[advanced\]"):
        exact_advanced.analyze_boschloo(Table2x2(5, 10, 2, 13))


def test_scipy_version_gate_rejects_unsupported_version(monkeypatch):
    monkeypatch.setattr(exact_advanced, "version", lambda _name: "1.6.3")
    with pytest.raises(RuntimeError, match="requires SciPy >= 1.7.0"):
        exact_advanced.analyze_boschloo(Table2x2(5, 10, 2, 13))


def test_supported_version_calls_all_three_alternatives_and_returns_results(monkeypatch):
    from types import SimpleNamespace

    calls = []

    def fake_boschloo(matrix, *, alternative):
        calls.append((matrix, alternative))
        return SimpleNamespace(statistic=0.42, pvalue={"greater": 0.12, "less": 0.91, "two-sided": 0.24}[alternative])

    monkeypatch.setattr(exact_advanced, "version", lambda _name: "1.12.0")
    monkeypatch.setattr(exact_advanced, "import_module", lambda _name: SimpleNamespace(boschloo_exact=fake_boschloo))
    result = exact_advanced.analyze_boschloo(Table2x2(5, 10, 2, 13))
    assert result.statistic == pytest.approx(0.42)
    assert (result.p_value_greater, result.p_value_less, result.p_value_two_sided) == pytest.approx((0.12, 0.91, 0.24))
    assert [alternative for _, alternative in calls] == ["greater", "less", "two-sided"]
    assert all(matrix == [[5, 10], [2, 13]] for matrix, _ in calls)


def test_boschloo_p_values_match_scipy_when_optional_dependency_is_installed():
    scipy_stats = pytest.importorskip("scipy.stats")
    import scipy

    table = Table2x2(5, 10, 2, 13)
    result = exact_advanced.analyze_boschloo(table)
    matrix = [[5, 10], [2, 13]]
    assert result.scipy_version == scipy.__version__
    assert result.p_value_greater == pytest.approx(scipy_stats.boschloo_exact(matrix, alternative="greater").pvalue)
    assert result.p_value_less == pytest.approx(scipy_stats.boschloo_exact(matrix, alternative="less").pvalue)
    assert result.p_value_two_sided == pytest.approx(scipy_stats.boschloo_exact(matrix, alternative="two-sided").pvalue)
    assert all(0 <= value <= 1 for value in (result.p_value_greater, result.p_value_less, result.p_value_two_sided))


@pytest.mark.parametrize("counts", [(1, 20, 12, 2), (0, 8, 5, 0), (2, 1, 1, 2)])
def test_sparse_tables_are_supported_when_scipy_is_installed(counts):
    pytest.importorskip("scipy.stats")
    result = exact_advanced.analyze_boschloo(Table2x2(*counts))
    assert 0 <= result.p_value_two_sided <= 1
