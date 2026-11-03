"""Streamlit-level regression tests for the real UI workflows.

These tests deliberately exercise widget state, reruns, uploads and handoff rather
than testing only the ingestion helper functions.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "ui" / "app.py"
LINE_LIST_LABEL = "Line list \u2192 2\u00d72"
ANALYSIS_LABEL = "2\u00d72 Analysis"


def line_list_app() -> AppTest:
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    nav = next(value for value in app.radio[0].options if value.startswith("Line list"))
    app.radio[0].set_value(nav).run()
    assert any("Upload a CSV, Excel, or SPSS" in item.value for item in app.info)
    return app


def upload(app: AppTest, filename: str, content: bytes, mime: str = "text/csv") -> AppTest:
    uploader = next(item for item in app.get("file_uploader") if item.key in {"line_file", "dta_score_file"})
    uploader.set_value((filename, content, mime)).run()
    return app


def click_key(app: AppTest, key: str) -> AppTest:
    button = next(item for item in app.button if item.key == key)
    button.click().run()
    return app


def csv_bytes(exposure, outcome) -> bytes:
    frame = pd.DataFrame({"exposure": exposure, "outcome": outcome})
    return frame.to_csv(index=False).encode("utf-8")


def test_csv_upload_preview_mapping_aggregate_and_analysis_handoff():
    app = line_list_app()
    upload(app, "cohort.csv", csv_bytes(
        ["yes", "yes", "yes", "no", "no", "no", "yes", "no"],
        ["case", "case", "control", "case", "control", "control", "control", "case"],
    ))

    assert any("Step 1" in item.value for item in app.subheader)
    assert app.session_state["line_exposure_col"] == "exposure"
    assert app.session_state["line_outcome_col"] == "outcome"
    assert len(app.selectbox) == 6  # demo selector plus line-list mapping and optional stratification

    click_key(app, "aggregate_line_list")
    assert app.session_state["line_result"]["counts"] == (2, 2, 2, 2)
    assert not app.exception
    assert any("Step 4" in item.value for item in app.subheader)

    handoff = next(item for item in app.button if item.label == "Send to 2\u00d72 Analysis")
    handoff.click().run()
    assert app.session_state["nav_section"] == ANALYSIS_LABEL
    assert tuple(app.session_state[key] for key in ("a", "b", "c", "d")) == (2, 2, 2, 2)
    assert app.session_state["analysis_counts"] == (2, 2, 2, 2)
    assert app.session_state["analysis_result"]["odds_ratio"] == pytest.approx(1.0)
    assert any("Key estimates" in item.value for item in app.subheader)
    assert not app.exception


def test_calculated_analysis_exposes_report_text_and_all_three_downloads():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    next(item for item in app.button if item.label == "Calculate").click().run()

    assert not app.exception
    assert len(app.code) == 1
    report = app.code[0].value
    assert "Counts (a,b,c,d): 25, 15, 7, 30" in report
    assert "Risk ratio: 3.30; 95% CI 1.63" in report
    assert "Odds ratio: 7.14; 95% CI 2.52" in report
    assert "Risk difference: 0.436; 95% CI 0.240" in report
    assert "exact parity with historical software has not been verified" in report

    downloads = {item.label: item.proto.url for item in app.get("download_button")}
    assert set(downloads) >= {
        "Download results (.txt)", "Download CSV", "Download forest plot (PNG)",
        "Download forest plot (SVG)", "Download forest plot (300 DPI PNG)",
        "Download forest plot (vector PDF)"
    }
    assert downloads["Download results (.txt)"].endswith(".txt")
    assert downloads["Download CSV"].endswith(".csv")
    assert downloads["Download forest plot (PNG)"].endswith(".png")


def test_publication_section_renders_strobe_and_downloadable_comparison_after_calculation():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    next(item for item in app.button if item.label == "Calculate").click().run()
    publication = next(value for value in app.radio[0].options if value.startswith("Publication"))
    app.radio[0].set_value(publication).run()
    assert not app.exception
    assert any("STROBE-style results narrative" in item.value for item in app.subheader)
    assert any("77 records" in item.value for item in app.markdown)
    downloads = {item.label for item in app.get("download_button")}
    assert "Download Markdown table" in downloads
    assert "Download LaTeX table" in downloads
    assert "Download technical JSON" in downloads
    assert "Download Complete Clinical Dossier (.docx)" in downloads
    assert "Download Reproducibility Certificate (audit_certificate.json)" in downloads
    assert any(item.label == "Technical JSON Payload" for item in app.expander)


def test_publication_section_exposes_icmje_apa_docx_html_and_latex_exports():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    next(item for item in app.button if item.label == "Calculate").click().run()
    publication = next(value for value in app.radio[0].options if value.startswith("Publication"))
    app.radio[0].set_value(publication).run()
    assert not app.exception
    downloads = {item.label: item.proto.url for item in app.get("download_button")}
    assert "Publication table (.docx)" in downloads
    assert "Publication table (.html)" in downloads
    assert "LaTeX tabular (.tex)" in downloads


def test_help_whitepaper_exports_complete_statistical_citations_and_printable_privacy_notice():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    next(item for item in app.button if item.key == "menu_help").click().run()
    assert not app.exception
    assert any("Boschloo vs Fisher" in item.value for item in app.subheader)
    citation_text = "\n".join(item.value for item in app.text)
    assert "DeLong, E. R." in citation_text
    assert "Robins, J. M." in citation_text
    assert "Fisher, R. A." in citation_text
    download_keys = {item.key for item in app.get("download_button")}
    assert "download_method_citations" in download_keys
    assert "download_privacy_statement" in download_keys
    assert "download_privacy_statement_html" in download_keys


def test_advanced_section_integrates_evalue_stratification_simpson_and_boschloo():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    advanced = next(value for value in app.radio[0].options if value.startswith("Advanced"))
    app.radio[0].set_value(advanced).run()
    assert not app.exception
    assert any("E-value" in item.value for item in app.subheader)
    assert any("Stratification" in item.value for item in app.subheader)
    assert any("Boschloo" in item.value for item in app.subheader)

    click_key(app, "calculate_evalue")
    assert app.session_state["evalue_result"].e_value == pytest.approx(2 + (2 * 1) ** 0.5)
    assert not app.exception

    click_key(app, "analyze_strata")
    result = app.session_state["stratified_result"]
    assert len(result.strata) == 2
    assert result.mantel_haenszel_odds_ratio is not None
    assert not app.exception

    click_key(app, "calculate_boschloo")
    if app.session_state.get("boschloo_result") is not None:
        assert 0 <= app.session_state["boschloo_result"].p_value_two_sided <= 1
    else:
        assert any("Boschloo test unavailable" in item.value for item in app.error)
    assert not app.exception


def test_advanced_section_calculates_additive_interaction_with_delta_method_ci():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    advanced = next(value for value in app.radio[0].options if value.startswith("Advanced"))
    app.radio[0].set_value(advanced).run()
    assert any("RERI" in item.value and "synergy index" in item.value.lower() for item in app.subheader)
    next(item for item in app.button if item.key == "calculate_additive_interaction").click().run()
    assert not app.exception
    result = app.session_state["additive_interaction_result"]
    assert result is not None
    assert result.reri == pytest.approx(result.odds_ratio_11 - result.odds_ratio_10 - result.odds_ratio_01 + 1)
    assert result.reri_ci[0] < result.reri_ci[1]


def test_excel_upload_uses_actual_ui_workflow_and_hands_off_counts():
    app = line_list_app()
    buffer = BytesIO()
    pd.DataFrame({"group": ["treated", "treated", "usual", "usual", "treated"],
                  "status": ["ill", "well", "ill", "well", "well"]}).to_excel(buffer, index=False)
    upload(app, "cohort.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    app.selectbox(key="line_exposure_col").set_value("group").run()
    app.selectbox(key="line_outcome_col").set_value("status").run()
    app.selectbox(key="line_exposed_value").set_value("treated").run()
    app.selectbox(key="line_case_value").set_value("ill").run()
    click_key(app, "aggregate_line_list")
    assert app.session_state["line_result"]["counts"] == (1, 2, 1, 1)
    next(item for item in app.button if item.label == "Send to 2\u00d72 Analysis").click().run()
    assert tuple(app.session_state[key] for key in ("a", "b", "c", "d")) == (1, 2, 1, 1)
    assert app.session_state["nav_section"] == ANALYSIS_LABEL
    assert app.session_state["analysis_counts"] == (1, 2, 1, 1)
    assert app.session_state["analysis_result"]["odds_ratio"] == pytest.approx(0.5)
    assert not app.exception


def test_spss_sav_upload_uses_real_line_list_mapping_and_aggregation_workflow():
    import pyreadstat
    app = line_list_app()
    frame = pd.DataFrame({"exposure": [1, 1, 0, 0], "outcome": [1, 0, 1, 0]})
    with __import__("tempfile").TemporaryDirectory() as directory:
        path = Path(directory) / "line-list.sav"
        pyreadstat.write_sav(frame, str(path))
        payload = path.read_bytes()
    upload(app, "line-list.sav", payload, "application/octet-stream")
    click_key(app, "aggregate_line_list")
    assert app.session_state["line_result"]["counts"] == (1, 1, 1, 1)
    assert not app.exception


def test_missing_exposure_or_outcome_values_block_aggregation_actionably():
    app = line_list_app()
    upload(app, "missing.csv", b"exposure,outcome\nyes,case\n,control\nno,\n")
    assert any("Aggregation is blocked" in item.value for item in app.warning)
    assert not any(item.key == "aggregate_line_list" for item in app.button)
    assert app.session_state.get("line_result") is None
    assert not app.exception


def test_ambiguous_nonbinary_categories_are_not_silently_aggregated():
    app = line_list_app()
    upload(app, "ambiguous.csv", b"exposure,outcome\nyes,case\nno,control\nmaybe,case\n")
    assert any("Each must have exactly two categories" in item.value for item in app.warning)
    assert not any(item.key == "aggregate_line_list" for item in app.button)
    assert app.session_state.get("line_result") is None
    assert not app.exception


def test_duplicate_csv_headers_produce_actionable_error_without_raw_exception():
    app = line_list_app()
    upload(app, "duplicate.csv", b"status,status\nyes,case\nno,control\n")
    messages = " ".join(item.value for item in app.error)
    assert "Duplicate column names" in messages
    assert not any(item.label == "Details" for item in app.expander)
    assert not app.exception


def test_changed_contents_under_same_filename_invalidate_aggregate_and_reconcile_categories():
    app = line_list_app()
    first = csv_bytes(["yes", "yes", "no", "no"], ["case", "control", "case", "control"])
    upload(app, "same.csv", first)
    click_key(app, "aggregate_line_list")
    assert app.session_state["line_result"]["counts"] == (1, 1, 1, 1)
    old_fingerprint = app.session_state["line_fingerprint"]

    changed = csv_bytes(["treated", "treated", "treated", "usual"], ["ill", "well", "well", "well"])
    upload(app, "same.csv", changed)
    assert app.session_state["line_fingerprint"] != old_fingerprint
    assert app.session_state["line_result"] is None
    assert app.session_state["line_exposed_value"] in {"treated", "usual"}
    assert app.session_state["line_case_value"] in {"ill", "well"}
    assert {"treated", "usual"} == set(app.selectbox(key="line_exposed_value").options)
    assert {"ill", "well"} == set(app.selectbox(key="line_case_value").options)
    assert not any("Step 4" in item.value for item in app.subheader)
    assert not app.exception


def test_mapping_column_change_reconciles_outcome_selection_and_stale_result():
    app = line_list_app()
    content = (b"exposure,outcome,alternate\n"
               b"yes,case,positive\nyes,control,negative\nno,case,negative\nno,control,positive\n")
    upload(app, "mapping.csv", content)
    click_key(app, "aggregate_line_list")
    assert app.session_state["line_result"] is not None
    app.selectbox(key="line_outcome_col").set_value("alternate").run()
    assert app.session_state["line_result"] is None
    assert any("mapping or reference categories changed" in item.value for item in app.info)
    assert set(app.selectbox(key="line_case_value").options) == {"positive", "negative"}
    click_key(app, "aggregate_line_list")
    assert app.session_state["line_result"]["counts"] == (1, 1, 1, 1)
    assert not app.exception


def test_sampling_design_change_invalidates_aggregated_result_until_reaggregated():
    app = line_list_app()
    upload(app, "design.csv", csv_bytes(
        ["yes", "yes", "no", "no"], ["case", "control", "case", "control"]
    ))
    click_key(app, "aggregate_line_list")
    assert app.session_state["line_result"]["design"] == "Cohort / cross-sectional"
    assert any("Step 4" in item.value for item in app.subheader)

    app.get("segmented_control")[0].set_value("Case-control").run()
    assert app.session_state["line_result"] is None
    assert any("sampling design changed" in item.value for item in app.info)
    assert not any("Step 4" in item.value for item in app.subheader)
    assert not app.exception

    click_key(app, "aggregate_line_list")
    assert app.session_state["line_result"]["design"] == "Case-control"
    assert any("Step 4" in item.value for item in app.subheader)
    assert not app.exception


@pytest.mark.parametrize("section", [ANALYSIS_LABEL, "Sample size & power"])
def test_primary_sections_render_and_keep_state_across_navigation(section):
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    app.radio[0].set_value(section).run()
    assert not app.exception
    if section == ANALYSIS_LABEL:
        assert any("Contingency table" in item.value for item in app.subheader)
        app.number_input(key="a").set_value(26).run()
        app.radio[0].set_value(next(value for value in app.radio[0].options if value.startswith("Line list"))).run()
        app.radio[0].set_value(ANALYSIS_LABEL).run()
        assert app.session_state["a"] == 26
    else:
        assert any("Study design" in item.label for item in app.get("segmented_control"))
        assert any("Calculate sample size" == item.label for item in app.button)


@pytest.mark.parametrize("design", ["Cohort", "Cross-sectional", "Case-control"])
def test_power_design_calculates_and_retains_result_and_selection_after_navigation(design):
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    app.radio[0].set_value("Sample size & power").run()
    app.get("segmented_control")[0].set_value(design).run()
    click_key(app, "calculate_power")
    result = app.session_state["power_result"]
    assert result["design"] == design
    assert result["n_control"] > 0 and result["n_exposed"] > 0
    assert 0.5 <= result["achieved_power"] <= 1
    assert any("Power curve" in item.value for item in app.subheader)
    app.radio[0].set_value(ANALYSIS_LABEL).run()
    app.radio[0].set_value("Sample size & power").run()
    assert app.session_state["planning_design"] == design
    assert app.session_state["power_result"]["design"] == design
    assert not app.exception


def test_diagnostic_test_accuracy_navigation_renders_metrics_and_roc_operating_point():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    section = next(value for value in app.radio[0].options if value.startswith("Diagnostic Test Accuracy"))
    app.radio[0].set_value(section).run()
    assert any("Diagnostic Test Accuracy" in item.value for item in app.header)
    click_key(app, "calculate_dta_counts")
    assert not app.exception
    assert app.session_state["dta_result"].metrics["sensitivity"] == pytest.approx(0.75)
    assert any("For a 2×2 table" in item.value for item in app.caption)
    assert any("Fagan nomogram" in item.value for item in app.subheader)
    assert {item.label for item in app.get("download_button")} >= {
        "Fagan nomogram (SVG)", "Fagan nomogram (300 DPI PNG)", "Fagan nomogram (vector PDF)"
    }


def test_continuous_probability_upload_calculates_dca_and_exposes_vector_exports():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    section = next(value for value in app.radio[0].options if value.startswith("Diagnostic Test Accuracy"))
    app.radio[0].set_value(section).run()
    app.get("segmented_control")[0].set_value("Continuous score + gold standard").run()
    upload(app, "risk_scores.csv", b"risk,outcome\n0.9,1\n0.8,0\n0.7,1\n0.2,0\n0.1,0\n0.6,1\n")
    click_key(app, "calculate_dta_scores")
    assert app.session_state["dta_result"].mode == "scores"
    click_key(app, "calculate_dca")
    result = app.session_state["dca_result"]
    assert len(result.points) >= 2
    assert all(0 < point.threshold_probability < 1 for point in result.points)
    assert {item.label for item in app.get("download_button")} >= {
        "Decision curve (SVG)", "Decision curve (300 DPI PNG)", "Decision curve (vector PDF)"
    }
    assert not app.exception


def test_line_list_stratification_selector_renders_multi_strata_comparison_and_forest_plot():
    app = line_list_app()
    content = (b"exposure,outcome,site\n"
               b"yes,case,A\nyes,control,A\nno,case,A\nno,control,A\n"
               b"yes,case,B\nyes,case,B\nno,control,B\nno,control,B\n")
    upload(app, "stratified.csv", content)
    app.selectbox(key="line_stratum_col").set_value("site").run()
    click_key(app, "aggregate_line_list")
    assert app.session_state["line_result"]["stratum_col"] == "site"
    assert any("Multi-strata comparison" in item.value for item in app.subheader)
    assert any("Mantel–Haenszel pooled OR" in item.value for item in app.markdown)
    assert not app.exception
