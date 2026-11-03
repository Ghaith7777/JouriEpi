from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_jouriepi_import_is_headless_and_exposes_native_apis():
    check = (
        "import sys, jouriepi; "
        "assert callable(jouriepi.analyze_2x2); "
        "assert callable(jouriepi.clean_linelist); "
        "assert callable(jouriepi.epicurve); "
        "assert callable(jouriepi.estimate_rt); "
        "assert 'streamlit' not in sys.modules; "
        "assert 'webview' not in sys.modules"
    )
    completed = subprocess.run([sys.executable, "-c", check], cwd=ROOT,
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr


def test_linelist_cleaning_standardizes_dates_trims_categories_and_audits_quality():
    frame = pd.DataFrame({
        "id": ["A", "B", "B", "C", "C", "D", "E"],
        "onset": ["2026-01-01", "2026-01-02", "2026-01-02", "2026-01-03", "2026-01-03", "not-a-date", "2026-01-05"],
        "site": [" North ", "South", "South ", "West", "West", "East", "North"],
        "age": [20, 21, 22, 23, 23, 24, 100],
    })
    cleaned, health = importlib.import_module("jouriepi").clean_linelist(
        frame, date_cols=["onset"], categorical_cols=["site"], id_col="id"
    )
    assert len(cleaned) == 6
    assert cleaned.loc[0, "site"] == "North"
    assert pd.isna(cleaned.loc[4, "onset"])
    assert health.exact_duplicate_rows_removed == 1
    assert health.duplicate_id_rows == 2
    assert health.duplicate_ids == ("B",)
    assert health.invalid_dates["onset"] == 1
    assert "age" in health.numeric_outliers
    assert health.rows_received == 7 and health.rows_returned == 6
    json.dumps(health.to_dict())


def test_linelist_cleaning_rejects_missing_columns_and_non_dataframe():
    clean_linelist = importlib.import_module("jouriepi").clean_linelist
    with pytest.raises(TypeError):
        clean_linelist([], [], [])
    with pytest.raises(ValueError, match="not found"):
        clean_linelist(pd.DataFrame({"x": [1]}), ["date"], [])


def test_epicurve_daily_and_iso_week_aggregate_case_records():
    epi = importlib.import_module("jouriepi")
    frame = pd.DataFrame({"onset": ["2026-01-01", "2026-01-01", "2026-01-03", "2026-01-08"]})
    daily = epi.epicurve(frame, "onset")
    assert daily["cases"].tolist() == [2, 0, 1, 0, 0, 0, 0, 1]
    weekly = epi.epicurve(frame, "onset", interval="iso_week")
    assert weekly["cases"].tolist() == [3, 1]
    with pytest.raises(ValueError, match="interval"):
        epi.epicurve(frame, "onset", interval="month")


def test_cori_rt_returns_gamma_posterior_and_validates_inputs():
    epi = importlib.import_module("jouriepi")
    frame = pd.DataFrame({"onset": pd.date_range("2026-01-01", periods=20).repeat(2)})
    result = epi.estimate_rt(frame, "onset", window=7, mean_si=4.7, std_si=2.9)
    assert len(result.estimates) == 14
    assert (result.estimates["rt_lower"] <= result.estimates["rt_mean"]).all()
    assert (result.estimates["rt_mean"] <= result.estimates["rt_upper"]).all()
    assert abs(sum(result.serial_interval_weights) - 1) < 1e-10
    assert "Cori" in result.method
    json.dumps(result.to_dict())
    with pytest.raises(ValueError, match="window"):
        epi.estimate_rt(frame, "onset", window=0)
    with pytest.raises(ValueError, match="at least"):
        epi.estimate_rt(frame.iloc[:3], "onset", window=7)


def test_public_result_exports_docx_and_reproducible_python_and_r_scripts():
    from jouriepi import analyze_2x2
    result = analyze_2x2((20, 80, 10, 90))
    assert result.to_docx().startswith(b"PK")
    python_script = result.to_python_script()
    assert "from jouriepi import" in python_script
    assert "analyze_2x2" in python_script
    r_script = result.to_r_script()
    assert "library(jouriepi)" in r_script
    assert "epi_2x2" in r_script
    assert "requireNamespace(\"jouriepi\"" in r_script
    assert "res <- epi_2x2(a = 20, b = 80, c = 10, d = 90" in r_script
    assert "summary(res)" in r_script
    assert "as.data.frame(res)" in r_script
    assert "cat(to_latex(res))" in r_script
    assert result.to_dict()["estimates"]["e_value"]["e_value"] >= 1


def test_public_api_accepts_numpy_integer_and_probability_arrays():
    import numpy as np
    from jouriepi import analyze_2x2, analyze_decision_curve, diagnostic_accuracy, paired_mcnemar
    assert analyze_2x2(np.array([20, 80, 10, 90], dtype=np.int64)).to_dict()["estimates"]["risk_ratio"] == pytest.approx(2)
    assert diagnostic_accuracy(tp=np.int64(40), fp=np.int64(10), fn=np.int64(5), tn=np.int64(45)).to_dict()["estimates"]["metrics"]["sensitivity"] == pytest.approx(40/45)
    assert paired_mcnemar(*(np.array([40, 4, 10, 46], dtype=np.int64))).analysis == "paired_mcnemar"
    dca = analyze_decision_curve(np.array([.1, .8, .7, .3]), np.array([0, 1, 1, 0]), np.array([.2, .5]))
    assert dca.analysis == "decision_curve"


def test_public_stratified_api_accepts_pandas_line_list_directly():
    from jouriepi import stratified_analysis
    frame = pd.DataFrame({
        "exposure": [1, 1, 0, 0, 1, 1, 0, 0],
        "outcome":  [1, 0, 1, 0, 1, 0, 1, 0],
        "site":     ["A", "A", "A", "A", "B", "B", "B", "B"],
    })
    result = stratified_analysis(frame, exposure_col="exposure", outcome_col="outcome", stratum_col="site")
    assert result.analysis == "stratified"
    assert len(result.to_dict()["estimates"]["strata"]) == 2
    assert "strata" in result.to_python_script()


def test_public_analysis_results_generate_reproducible_scripts_for_supported_methods():
    from jouriepi import (
        additive_interaction, analyze_decision_curve, compare_roc_delong,
        paired_mcnemar, stratified_analysis,
    )
    results = [
        stratified_analysis({"A": (20, 30, 10, 40), "B": (15, 25, 8, 32)}),
        additive_interaction([(10, 90), (20, 80), (25, 75), (50, 50)]),
        paired_mcnemar(40, 4, 10, 46),
        analyze_decision_curve([.1, .8, .7, .3], [0, 1, 1, 0], [.2, .5]),
        compare_roc_delong([.1, .8, .7, .2], [.2, .7, .8, .1], [0, 1, 1, 0]),
    ]
    for result in results:
        python_script = result.to_python_script()
        compile(python_script, f"{result.analysis}.py", "exec")
        script = result.to_r_script()
        assert "library(jouriepi)" in script
        assert "requireNamespace(\"jouriepi\"" in script
        assert "res <- epi_" in script
        assert "cat(to_latex(res))" in script


def test_native_windows_build_and_tooltip_theme_assets_are_declared():
    assert (ROOT / "build_windows.ps1").is_file()
    dark = (ROOT / "ui_qt" / "styles" / "dark.qss").read_text(encoding="utf-8")
    assert "QToolTip" in dark
    assert "background-color: #18181b" in dark


def test_packaged_desktop_entrypoint_is_native_qt_not_streamlit():
    source = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    launcher = (ROOT / "run_desktop.py").read_text(encoding="utf-8")
    assert 'jouriepi-app = "ui_qt.main:main"' in source
    assert "from ui_qt.main import main" in launcher
    assert "JouriEpiServer" not in launcher
