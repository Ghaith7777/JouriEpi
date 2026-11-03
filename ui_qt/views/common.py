from __future__ import annotations

import math
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
                               QScrollArea, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget, QFrame as QtFrame)
from PySide6.QtGui import QGuiApplication
from core.public_api import AnalysisResult
from ui_qt.components.metric_card import MetricCard


def format_value(value) -> str:
    if value is None:
        return "Not estimable"
    if isinstance(value, float):
        if math.isnan(value):
            return "Not estimable"
        if math.isinf(value):
            return "∞" if value > 0 else "−∞"
        return f"{value:.4g}"
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return f"{format_value(value[0])} to {format_value(value[1])}"
    return str(value)


class AnalysisView(QWidget):
    result_ready = Signal(object)

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.result: AnalysisResult | None = None
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setObjectName("AnalysisScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtFrame.NoFrame)
        content = QWidget()
        self.root = QVBoxLayout(content)
        self.root.setContentsMargins(24, 22, 24, 22)
        self.root.setSpacing(16)
        heading = QLabel(title)
        heading.setObjectName("PageTitle")
        self.root.addWidget(heading)
        self.metrics_host = QWidget()
        self.metrics_layout = QGridLayout(self.metrics_host)
        self.metrics_layout.setContentsMargins(0, 0, 0, 0)
        self.metrics_layout.setSpacing(10)
        self.root.addWidget(self.metrics_host)
        self.results_table = QTableWidget(0, 2)
        self.results_table.setHorizontalHeaderLabels(["Measure", "Estimate"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setMaximumHeight(270)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.root.addWidget(self.results_table)
        self.status = QLabel("Enter data and run the analysis. All calculations are performed locally.")
        self.status.setObjectName("StatusText")
        self.status.setWordWrap(True)
        self.root.addWidget(self.status)
        export_row = QHBoxLayout()
        self.export_r_button = QPushButton("Export R Script…")
        self.export_r_button.setObjectName("SecondaryButton")
        self.export_r_button.setEnabled(False)
        self.export_r_button.clicked.connect(self.save_r_script)
        self.copy_r_button = QPushButton("Copy R Script")
        self.copy_r_button.setObjectName("SecondaryButton")
        self.copy_r_button.setEnabled(False)
        self.copy_r_button.clicked.connect(self.copy_r_script)
        export_row.addWidget(self.export_r_button)
        export_row.addWidget(self.copy_r_button)
        export_row.addStretch(1)
        self.root.addLayout(export_row)
        self.root.addStretch(1)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

    def show_result(self, result: AnalysisResult):
        self.result = result
        payload = result.to_dict()["estimates"]
        rows = []
        for key, value in payload.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    rows.append((f"{key} · {subkey}", format_value(subvalue)))
            else:
                rows.append((key.replace("_", " ").title(), format_value(value)))
        self.results_table.setRowCount(len(rows))
        for row, (label, value) in enumerate(rows):
            self.results_table.setItem(row, 0, QTableWidgetItem(label))
            self.results_table.setItem(row, 1, QTableWidgetItem(value))
        self.status.setText(f"{result.analysis.replace('_', ' ').title()} completed. Core result is available for export.")
        self._show_metrics(payload)
        self.export_r_button.setEnabled(True)
        self.copy_r_button.setEnabled(True)
        self.result_ready.emit(result)

    def clear_result(self):
        """Clear displayed calculations while retaining the current input values."""
        self.result = None
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        while self.metrics_layout.count():
            item = self.metrics_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.export_r_button.setEnabled(False)
        self.copy_r_button.setEnabled(False)
        self.status.setText("Enter data and run the analysis. All calculations are performed locally.")

    def _r_script(self) -> str | None:
        if self.result is None:
            self.status.setText("Run the analysis before exporting an R script.")
            return None
        try:
            return self.result.to_r_script()
        except Exception as exc:
            self.status.setText(f"R script export unavailable: {exc}")
            return None

    def save_r_script(self):
        content = self._r_script()
        if content is None:
            return
        default_name = f"JouriEpi_{self.result.analysis}_Analysis.R"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export R Script", default_name, "R Script (*.R);;All Files (*)"
        )
        if not path:
            return
        if not path.lower().endswith(".r"):
            path += ".R"
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            self.status.setText(f"R script saved: {path}")
        except OSError as exc:
            self.status.setText(f"Could not save R script: {exc}")

    def copy_r_script(self):
        content = self._r_script()
        if content is None:
            return
        QGuiApplication.clipboard().setText(content)
        self.status.setText("Reproducible R script copied to the system clipboard.")

    def _show_metrics(self, payload: dict):
        while self.metrics_layout.count():
            item = self.metrics_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        candidates = []
        for key, value in payload.items():
            if isinstance(value, (int, float)) or value is None:
                if any(token in key for token in ("risk_ratio", "odds_ratio", "risk_difference", "auc", "p_value", "reri", "attributable", "synergy")):
                    candidates.append((key.replace("_", " ").title(), value))
        for index, (label, value) in enumerate(candidates[:4]):
            self.metrics_layout.addWidget(MetricCard(label, format_value(value)), index // 4, index % 4)


def add_run_button(layout, callback, text="Run analysis"):
    row = QHBoxLayout()
    button = QPushButton(text)
    button.setObjectName("PrimaryButton")
    button.clicked.connect(callback)
    row.addWidget(button)
    row.addStretch(1)
    layout.addLayout(row)
    return button


def add_label(layout, text):
    label = QLabel(text)
    label.setObjectName("FieldLabel")
    layout.addWidget(label)
    return label
