"""Keep app-level tests from reading or mutating a real user's preferences."""
import pytest


@pytest.fixture(autouse=True)
def isolate_jouriepi_preferences(tmp_path, monkeypatch):
    monkeypatch.setenv("JOURIEPI_WORKSPACE", str(tmp_path / "jouriepi-test-workspace"))
