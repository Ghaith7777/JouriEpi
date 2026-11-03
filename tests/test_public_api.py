from __future__ import annotations

import tomllib
from pathlib import Path

import pandas as pd
import pytest

import core
from core import (
    additive_interaction,
    analyze_2x2,
    analyze_decision_curve,
    diagnostic_accuracy,
    paired_mcnemar,
    stratified_analysis,
)


ROOT = Path(__file__).resolve().parents[1]


def test_distribution_metadata_declares_jouriepi_package_and_desktop_entrypoint():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["name"] == "jouriepi"
    assert metadata["project"]["version"] == "1.0.0"
    assert metadata["project"]["scripts"]["jouriepi-app"] == "ui_qt.main:main"
    assert "ui_qt*" in metadata["tool"]["setuptools"]["packages"]["find"]["include"]
    assert {"scipy>=1.10.0", "statsmodels>=0.14.0", "pandas>=2.0.0",
            "python-docx>=1.0.0", "pyreadstat>=1.3.7"} <= set(metadata["project"]["dependencies"])


def test_2x2_public_result_has_dict_dataframe_latex_and_string_views():
    result = analyze_2x2((20, 80, 10, 90))
    assert result.analysis == "2x2"
    assert result.to_dict()["estimates"]["risk_ratio"] == pytest.approx(2.0)
    frame = result.to_dataframe()
    assert isinstance(frame, pd.DataFrame)
    assert {"measure", "estimate"} == set(frame.columns)
    latex = result.to_latex()
    assert r"\toprule" in latex and r"\midrule" in latex and r"\bottomrule" in latex
    assert r"\begin{table}" in latex
    assert r"\documentclass" not in latex
    standalone = result.to_latex(standalone=True)
    assert standalone.startswith(r"\documentclass{article}")
    assert r"\usepackage{booktabs}" in standalone
    assert r"\begin{document}" in standalone and r"\end{document}" in standalone
    assert r"\begin{table}" in standalone
    with pytest.raises(TypeError, match="standalone must be a bool"):
        result.to_latex(standalone="yes")
    assert "2X2" in str(result).upper()


def test_public_api_wrappers_return_consistent_serializable_results():
    stratified = stratified_analysis({"Site 1": (20, 30, 10, 40), "Site 2": (15, 25, 8, 32)})
    dta = diagnostic_accuracy(tp=40, fp=10, fn=5, tn=45)
    paired = paired_mcnemar(40, 4, 10, 46)
    dca = analyze_decision_curve([0.1, 0.8, 0.7, 0.3], [0, 1, 1, 0], [0.2, 0.5])
    interaction = additive_interaction([(10, 90), (20, 80), (25, 75), (50, 50)])
    for result in (stratified, dta, paired, dca, interaction):
        payload = result.to_dict()
        assert payload["analysis"]
        assert isinstance(payload["estimates"], dict)
        assert not result.to_dataframe().empty
        assert r"\begin{table}" in result.to_latex()
        assert r"\documentclass{article}" in result.to_latex(standalone=True)
    assert dta.to_dict()["estimates"]["metrics"]["sensitivity"] == pytest.approx(40 / 45)
    assert "reri" in interaction.to_dict()["estimates"]


def test_public_api_rejects_incomplete_diagnostic_input():
    with pytest.raises(ValueError, match="provided together"):
        diagnostic_accuracy(scores=[0.1, 0.9])
    with pytest.raises(ValueError, match="all of tp"):
        diagnostic_accuracy(tp=1, fp=2)


def test_core_exports_the_requested_api():
    for name in ("analyze_2x2", "stratified_analysis", "diagnostic_accuracy",
                 "paired_mcnemar", "analyze_decision_curve", "additive_interaction"):
        assert callable(getattr(core, name))
