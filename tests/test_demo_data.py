"""Regression coverage for built-in synthetic demos and the clinical help drawer."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.demo_data import (
    DEMO_DATASETS,
    cardiovascular_risk_study,
    diagnostic_biomarker_study,
    multicenter_trial_strata,
)
from core.i18n import translate


APP_PATH = Path(__file__).resolve().parents[1] / "ui" / "app.py"


def test_demo_datasets_are_deterministic_and_have_expected_schema():
    cardiovascular = cardiovascular_risk_study()
    biomarker = diagnostic_biomarker_study()
    assert len(cardiovascular) == 200
    assert cardiovascular[["risk_exposure", "cardiovascular_event"]].sum().to_dict() == {
        "risk_exposure": 100, "cardiovascular_event": 26,
    }
    assert len(biomarker) == 40
    assert set(biomarker["gold_standard"]) == {0, 1}
    assert biomarker["biomarker_score"].between(0, 1).all()
    assert set(multicenter_trial_strata()) == {"Center A", "Center B"}
    assert set(DEMO_DATASETS) == {"cardiovascular", "roc", "stratified"}


@pytest.mark.parametrize(("language", "demo", "section", "state_key"), [
    ("en", "cardiovascular", "2×2 Analysis", "analysis_result"),
    ("fr", "roc", "Diagnostic Test Accuracy (DTA)", "dta_result"),
    ("de", "stratified", "Advanced analyses", "stratified_result"),
])
def test_demo_selection_loads_and_calculates_in_each_locale(language, demo, section, state_key):
    app = AppTest.from_file(APP_PATH, default_timeout=30)
    app.session_state["language"] = language
    app.run()
    selector = app.selectbox(key="clinical_demo_selector")
    assert selector.label == translate("demo_dataset", language)
    demo_label = translate({"cardiovascular": "demo_cardiovascular", "roc": "demo_roc", "stratified": "demo_stratified"}[demo], language)
    assert demo_label in selector.options
    selector.set_value(demo).run()
    assert not app.exception
    assert app.session_state["nav_section"] == section
    assert app.session_state[state_key] is not None
    assert any(translate("demo_loaded", language) in item.value for item in app.success)


def test_help_drawer_explains_methods_and_exposes_downloadable_citations():
    app = AppTest.from_file(APP_PATH, default_timeout=30).run()
    next(button for button in app.button if button.key == "menu_help").click().run()
    assert not app.exception
    text = " ".join(item.value for item in app.markdown) + " " + " ".join(item.value for item in app.text)
    assert "unconditional exact" in text or "Boschloo" in text
    assert "E-value" in text and "Fagan" in text and "Woolf" in text and "Katz" in text
    assert any(item.label == "Download citation block (.txt)" for item in app.get("download_button"))
