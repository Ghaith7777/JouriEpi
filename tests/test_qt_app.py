from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from ui_qt.main import JouriEpiWindow
from ui_qt.components.contingency_table import ContingencyTable
from ui_qt.components.metric_card import MetricCard


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


@pytest.fixture
def window(app):
    instance = JouriEpiWindow()
    yield instance
    instance.close()


def test_native_window_has_expected_title_and_all_workspaces(window):
    assert "JouriEpi" in window.windowTitle()
    assert set(window.views) == {"association", "stratified", "diagnostics", "paired", "interaction", "outbreak", "reports"}
    assert window.stack.count() == 7


def test_cold_boot_defaults_to_light_and_dark_menu_action_still_switches(window):
    assert window.theme_name == "light"
    assert window.menus.theme_actions["light"].isChecked()
    window.menus.theme_actions["dark"].trigger()
    assert window.theme_name == "dark"
    assert window.menus.theme_actions["dark"].isChecked()
    window.menus.theme_actions["light"].trigger()
    assert window.theme_name == "light"


def test_sidebar_can_collapse_and_restore_without_losing_toggle(window):
    sidebar = window.sidebar
    sidebar.set_collapsed(True)
    QTest.qWait(220)
    assert sidebar.is_collapsed
    assert 76 <= sidebar.width() <= 78
    assert not sidebar.toggle_button.isHidden()
    assert sidebar.toggle_button.text() == "▶"
    sidebar.toggle_button.click()
    QTest.qWait(220)
    assert not sidebar.is_collapsed
    assert 258 <= sidebar.width() <= 260
    assert sidebar.toggle_button.text() == "◀"


def test_language_switch_updates_layout_direction_and_menu(window):
    window.set_language("ar")
    assert window.layoutDirection() == Qt.RightToLeft
    assert window.menus.language_actions["ar"].isChecked()
    window.set_language("fr")
    assert window.layoutDirection() == Qt.LeftToRight
    assert window.menus.language_actions["fr"].isChecked()
    heading = window.views["association"].findChild(QLabel, "PageTitle")
    assert heading.text() == "Analyse d’association 2×2"


def test_all_eight_languages_are_available_and_arabic_text_is_localized(window):
    assert set(window.menus.language_actions) == {"en", "fr", "de", "ar", "es", "ru", "zh", "ja"}
    window.set_language("ar")
    heading = window.views["association"].findChild(QLabel, "PageTitle")
    assert heading.text() == "تحليل الارتباط 2×2"


def test_dark_and_light_theme_stylesheets_have_tooltip_contrast(window):
    window.set_theme("dark")
    assert "QToolTip" in window.styleSheet() and "#e4e4e7" in window.styleSheet()
    window.set_theme("light")
    assert "QToolTip" in window.styleSheet() and "#0f172a" in window.styleSheet()


def test_theme_uses_embedded_styles_when_qss_files_are_not_packaged(window, monkeypatch, tmp_path):
    monkeypatch.setattr("ui_qt.main.ROOT", tmp_path)
    window.set_theme("dark")
    assert "#121214" in window.styleSheet() and "QToolTip" in window.styleSheet()
    window.set_theme("light")
    assert "#f8fafc" in window.styleSheet() and "QToolTip" in window.styleSheet()


def test_metric_card_surface_belongs_to_frame_and_child_labels_remain_transparent(window):
    window.set_theme("dark")
    card = MetricCard("Odds Ratio", "2.40", "95% CI: 1.2–4.8")
    assert card.objectName() == "MetricCard"
    assert card.styleSheet() == ""
    for label in card.findChildren(QLabel):
        assert label.styleSheet() == ""
    stylesheet = window.styleSheet()
    assert "QFrame#MetricCard { background: #1a1a1e;" in stylesheet
    assert "QLabel { background: transparent; background-color: transparent; }" in stylesheet


def test_scrollbars_and_dropdown_menus_have_ergonomic_spacing(window):
    from PySide6.QtWidgets import QMenu, QScrollBar

    labels = [
        "About JouriEpi",
        "Stratified Simpson's check",
        "Diagnostic accuracy ROC",
        "Generate & refresh preview",
    ]
    for theme in ("light", "dark"):
        window.set_theme(theme)
        stylesheet = window.styleSheet()
        assert "width: 12px" in stylesheet
        assert "height: 12px" in stylesheet
        assert "QScrollBar::handle:vertical:hover" in stylesheet
        assert "QScrollBar::handle:vertical:pressed" in stylesheet
        assert "border-radius: 6px" in stylesheet
        assert "min-width: 230px" in stylesheet
        assert "padding: 8px 32px 8px 14px" in stylesheet
        assert "QMenu::separator" in stylesheet

        menu = QMenu()
        menu.setStyleSheet(stylesheet)
        for label in labels:
            menu.addAction(label)
        vertical = QScrollBar(Qt.Vertical)
        vertical.setStyleSheet(stylesheet)
        horizontal = QScrollBar(Qt.Horizontal)
        horizontal.setStyleSheet(stylesheet)
        assert menu.sizeHint().width() >= 230
        assert vertical.sizeHint().width() >= 12
        assert horizontal.sizeHint().height() >= 12
        menu.deleteLater()
        vertical.deleteLater()
        horizontal.deleteLater()


def test_contingency_table_uses_core_a_b_c_d_order():
    table = ContingencyTable()
    table.set_values((11, 22, 33, 44))
    assert table.values() == (11, 22, 33, 44)
    assert all(table.cellWidget(row, col).__class__.__name__ == "QSpinBox"
               for row in range(2) for col in range(2))


def test_association_view_calls_headless_core_and_propagates_result(window):
    view = window.views["association"]
    received = []
    view.result_ready.connect(received.append)
    view.table.set_values((12, 18, 5, 25))
    view.run_analysis()
    assert received and received[0].analysis == "2x2"
    assert "risk_ratio" in received[0].estimates
    assert window.views["reports"].result is received[0]


def test_stratified_view_reports_simpsons_paradox_flag(window):
    view = window.views["stratified"]
    view.input.setPlainText("young, 12, 18, 5, 25\nolder, 8, 12, 10, 20")
    view.run_analysis()
    assert view.result is not None and view.result.analysis == "stratified"
    assert "simpsons_paradox_detected" in view.result.estimates


def test_reports_view_can_copy_latex_without_file_or_network_access(window):
    view = window.views["association"]
    view.run_analysis()
    reports = window.views["reports"]
    reports.copy_latex()
    assert "\\begin{table}" in QApplication.clipboard().text()
    assert r"\documentclass{article}" not in QApplication.clipboard().text()


def test_publication_standalone_checkbox_refreshes_preview_and_copy_buffer(window):
    view = window.views["association"]
    view.run_analysis()
    reports = window.views["reports"]
    checkbox = reports.standalone_checkbox
    assert checkbox.text() == "Standalone document (ready to compile)"
    assert r"\documentclass{article}" not in reports.preview.toPlainText()
    checkbox.setChecked(True)
    assert reports.preview.toPlainText().startswith(r"\documentclass{article}")
    reports.copy_latex()
    assert QApplication.clipboard().text().startswith(r"\documentclass{article}")
    checkbox.setChecked(False)
    assert r"\documentclass{article}" not in reports.preview.toPlainText()


def test_save_word_dossier_export_has_clinical_tables_and_no_machine_dump(window, monkeypatch, tmp_path):
    from docx import Document

    view = window.views["association"]
    view.table.set_values((25, 15, 7, 30))
    view.run_analysis()
    output = tmp_path / "clinical_dossier.docx"
    monkeypatch.setattr(
        "ui_qt.views.view_reports.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(output), "Word document (*.docx)"),
    )
    window.views["reports"].save_docx()
    assert output.is_file()
    document = Document(output)
    paragraphs = "\n".join(paragraph.text for paragraph in document.paragraphs)
    cells = "\n".join(cell.text for table in document.tables for row in table.rows for cell in row.cells)
    full_text = paragraphs + "\n" + cells

    assert "Generated:" in paragraphs and "Local execution:" in paragraphs
    assert "Input 2×2 Contingency Table" in paragraphs
    assert "Main Association & Diagnostic Results" in paragraphs
    assert "Sensitivity & E-value Interpretation" in paragraphs
    assert "Statistical Notes & Assumptions" in paragraphs
    assert "Odds Ratio" in cells and "Risk Ratio" in cells
    assert "Pearson Chi-Square" in cells and "p-value" in cells
    assert "0.16666666666666666" not in full_text
    assert "Machine-readable result" not in full_text
    assert "counts.a_exposed_cases" not in full_text
    assert "[" not in full_text and "]" not in full_text
    assert len(document.tables) >= 2
    assert "tblBorders" in document.tables[0]._tbl.xml


def test_qt_package_does_not_import_streamlit_or_web_engine_in_source():
    root = Path(__file__).resolve().parents[1] / "ui_qt"
    sources = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.py"))
    assert "streamlit" not in sources.lower()
    assert "QtWebEngine" not in sources
    assert "subprocess" not in sources


def test_dark_table_palette_and_light_table_palette_are_theme_specific(window):
    window.set_theme("dark")
    dark = window.styleSheet()
    assert "background: #18181b" in dark
    assert "alternate-background-color: #222227" in dark
    assert "gridline-color: #27272a" in dark
    assert "color: #f4f4f5" in dark
    assert "QTableWidget::item { color: #0f172a; background: #ffffff; }" not in dark
    assert "QTableWidget { alternate-background-color: #f8fafc; }" not in dark
    assert "QScrollBar::handle:vertical:hover { background: #38bdf8; }" in dark
    assert "QScrollBar::handle:vertical:pressed { background: #0284c7; }" in dark
    window.set_theme("light")
    light = window.styleSheet()
    assert "background: #ffffff" in light and "alternate-background-color: #f8fafc" in light


def test_haldane_anscombe_checkbox_recalculates_and_updates_status_immediately(window):
    view = window.views["association"]
    view.table.set_values((0, 18, 5, 25))
    view.run_analysis()
    assert view.result.estimates["haldane_anscombe_status"] == "Off (enable via checkbox)"
    assert view.result.estimates["odds_ratio_haldane_anscombe"] is None
    view.haldane.setChecked(True)
    assert view.result.estimates["haldane_anscombe_status"] == "Active"
    corrected = view.result.estimates["odds_ratio_haldane_anscombe"]
    corrected_ci = view.result.estimates["odds_ratio_haldane_anscombe_woolf_ci"]
    assert corrected is not None and corrected_ci is not None
    view.haldane.setChecked(False)
    assert view.result.estimates["haldane_anscombe_status"] == "Off (enable via checkbox)"
    assert view.result.estimates["odds_ratio_haldane_anscombe"] is None


def test_association_metric_cards_keep_fixed_identity_and_correct_haldane_binding(window):
    view = window.views["association"]
    view.table.set_values((12, 18, 5, 25))
    view.haldane.setChecked(False)
    view.run_analysis()
    cards = view.metric_cards
    assert [card.title_label.text() for card in cards] == [
        "Odds Ratio", "Odds Ratio (Haldane)", "Haldane Woolf CI", "Risk Ratio"
    ]
    assert cards[0].value_label.text() == "3.333"
    assert cards[1].value_label.text() == "—"
    assert cards[1].detail_label.text() == "Off (enable via checkbox)"
    assert cards[2].value_label.text() == "—"
    assert cards[2].detail_label.text() == "Off (enable via checkbox)"
    assert cards[3].value_label.text() == "2.4"

    view.haldane.setChecked(True)
    assert view.metric_cards == cards
    assert [card.title_label.text() for card in view.metric_cards] == [
        "Odds Ratio", "Odds Ratio (Haldane)", "Haldane Woolf CI", "Risk Ratio"
    ]
    assert cards[0].value_label.text() == "3.333"
    assert cards[1].value_label.text() == "3.133"
    # Woolf SE is sqrt(1/12.5 + 1/18.5 + 1/5.5 + 1/25.5),
    # giving this interval for the stated +0.5-to-every-cell estimate.
    assert cards[2].value_label.text() == "[0.9743, 10.07]"
    assert cards[3].value_label.text() == "2.4"
    assert view.result.estimates["odds_ratio_haldane_anscombe"] == pytest.approx(3.1326781326781328)
    view.clear_result()
    assert view.metric_cards == cards
    assert view.metrics_layout.count() == 4
