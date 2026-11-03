from __future__ import annotations

from datetime import datetime, timezone
import json
import pandas as pd
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QGuiApplication
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QComboBox, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QWidget)
from core.linelist import clean_linelist, outbreak_case_counts
from .common import AnalysisView


class CurveWidget(QWidget):
    """Small dependency-free epidemic curve rendered directly by Qt."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.counts: list[int] = []
        self.setMinimumHeight(220)

    def set_counts(self, counts):
        self.counts = list(counts)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(34, 16, -18, -28)
        dark = self.palette().window().color().lightness() < 128
        axis_color = QColor("#d4d4d8") if dark else QColor("#334155")
        painter.setPen(QPen(axis_color, 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.topLeft())
        if not self.counts:
            painter.setPen(QColor("#a1a1aa") if dark else QColor("#334155"))
            painter.drawText(rect, Qt.AlignCenter, "Import a line list to display the epidemic curve")
            return
        maximum = max(self.counts) or 1
        points = []
        for index, count in enumerate(self.counts):
            x = rect.left() + (rect.width() * index / max(1, len(self.counts) - 1))
            y = rect.bottom() - (rect.height() * count / maximum)
            points.append(QPointF(x, y))
        painter.setPen(QPen(self.palette().highlight().color(), 2.5))
        for first, second in zip(points, points[1:]):
            painter.drawLine(first, second)
        painter.setPen(axis_color)
        painter.drawText(4, rect.top() + 10, str(maximum))
        painter.drawText(10, rect.bottom(), "0")


class OutbreakView(AnalysisView):
    def __init__(self, parent=None):
        super().__init__("Line List & Outbreak Curve", parent)
        self.frame: pd.DataFrame | None = None
        self.date_column = QLineEdit("onset_date")
        self.case_column = QLineEdit("case")
        self.id_column = QLineEdit("case_id")
        self.case_value = QComboBox()
        self.case_value.setObjectName("OutbreakCaseValue")
        self.case_value.setToolTip("Select the category representing confirmed cases; controls are excluded.")
        self.load_button = QPushButton("Import CSV / Excel…")
        self.load_button.clicked.connect(self.load_file)
        self.root.insertWidget(1, self.load_button)
        row = QHBoxLayout()
        for label, field in (("Date column", self.date_column), ("Case/status column", self.case_column),
                             ("ID column (optional)", self.id_column)):
            row.addWidget(QLabel(label)); row.addWidget(field)
        row.addWidget(QLabel("Case Value / Category")); row.addWidget(self.case_value)
        self.root.insertLayout(2, row)
        self.date_column.textChanged.connect(self._process)
        self.case_column.textChanged.connect(self._refresh_case_values)
        self.id_column.textChanged.connect(self._process)
        self.case_value.currentTextChanged.connect(self._process)
        self.curve = CurveWidget()
        self.root.insertWidget(3, self.curve)
        self.summary = QLabel("No line list loaded.")
        self.summary.setWordWrap(True)
        self.root.insertWidget(4, self.summary)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open line list", "", "Data files (*.csv *.xlsx *.xls)")
        if not path:
            return
        try:
            self.frame = pd.read_csv(path) if path.lower().endswith(".csv") else pd.read_excel(path)
            self.source_path = path
            self.status.setText(f"Loaded {len(self.frame)} rows from {path}")
            self._refresh_case_values()
        except Exception as exc:
            self.status.setText(str(exc))

    def _process(self):
        if self.frame is None:
            return
        date_col = self.date_column.text().strip()
        case_col = self.case_column.text().strip()
        id_col = self.id_column.text().strip() or None
        try:
            cleaned, summary = clean_linelist(self.frame, [date_col], [case_col], id_col=id_col)
            selected = self.case_value.currentText()
            if not selected:
                raise ValueError("Select the case value/category to include in the outbreak curve.")
            ordered, daily_counts, case_rows = outbreak_case_counts(cleaned, date_col, case_col, selected)
            self.curve.set_counts(daily_counts)
            self.summary.setText(
                f"Selected case category: {selected} · case records with valid dates: {case_rows} · "
                f"Rows received: {summary.rows_received} · retained: {summary.rows_returned} · "
                f"exact duplicates removed: {summary.exact_duplicate_rows_removed} · "
                f"duplicate-ID rows flagged: {summary.duplicate_id_rows} · "
                f"missing values: {sum(summary.missing_values.values())}"
            )
            self.export_r_button.setEnabled(True)
            self.copy_r_button.setEnabled(True)
            self.status.setText("Outbreak curve includes only the selected case category. Flagged duplicates/outliers are retained per core policy.")
        except Exception as exc:
            self.curve.set_counts([])
            self.summary.setText("The outbreak curve could not be recalculated with the current column/category selection.")
            self.status.setText(str(exc))

    def _refresh_case_values(self, *_):
        if self.frame is None:
            return
        column = self.case_column.text().strip()
        previous = self.case_value.currentText()
        self.case_value.blockSignals(True)
        self.case_value.clear()
        if column in self.frame.columns:
            values = self.frame[column].dropna().map(lambda value: str(value).strip())
            self.case_value.addItems(sorted(value for value in values.unique() if value))
        if previous and self.case_value.findText(previous) >= 0:
            self.case_value.setCurrentText(previous)
        elif self.case_value.count():
            preferred = self.case_value.findText("case")
            self.case_value.setCurrentIndex(preferred if preferred >= 0 else 0)
        self.case_value.blockSignals(False)
        self._process()

    def _outbreak_r_script(self) -> str | None:
        if self.frame is None:
            self.status.setText("Import and process a line list before exporting an R script.")
            return None
        date_col = self.date_column.text().strip()
        case_col = self.case_column.text().strip()
        id_col = self.id_column.text().strip() or None
        if date_col not in self.frame.columns or case_col not in self.frame.columns:
            self.status.setText("The configured date and case/status columns must exist in the imported line list.")
            return None
        if not self.case_value.currentText():
            self.status.setText("Select a case value/category before exporting the reproducible R script.")
            return None
        csv_payload = self.frame.to_csv(index=False, lineterminator="\n")
        r_csv = json.dumps(csv_payload, ensure_ascii=False)
        r_dates = f"c({json.dumps(date_col)})"
        r_categories = f"c({json.dumps(case_col)})"
        r_case_value = json.dumps(self.case_value.currentText())
        r_id = "NULL" if id_col is None else json.dumps(id_col)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        return (
            "# ==============================================================================\n"
            "# JouriEpi Clinical Workstation - Line List & Outbreak Curve\n"
            "# Engine: jouriepi (CRAN-compliant R package v1.0.0)\n"
            f"# Generated: {timestamp}\n"
            "# Author & Architect: Ghaith Baccari\n"
            "# ==============================================================================\n\n"
            "if (!requireNamespace(\"jouriepi\", quietly = TRUE)) {\n"
            "  stop(\"Package 'jouriepi' is not installed. Please install 'jouriepi_1.0.0.tar.gz'.\")\n"
            "}\n"
            "library(jouriepi)\n\n"
            "# Embedded source line list: this export is self-contained.\n"
            f"csv_data <- {r_csv}\n"
            "df_raw <- read.csv(text = csv_data, stringsAsFactors = FALSE, check.names = FALSE)\n\n"
            "# Apply the same date, category and identifier configuration as the desktop view.\n"
            f"res <- epi_clean_linelist(df_raw, date_cols = {r_dates}, categorical_cols = {r_categories}, id_col = {r_id})\n"
            "cleaned <- res$data\n"
            f"case_rows <- cleaned[!is.na(cleaned[[{json.dumps(case_col)}]]) & trimws(as.character(cleaned[[{json.dumps(case_col)}]])) == {r_case_value}, , drop = FALSE]\n"
            f"curve <- epi_curve(case_rows[!is.na(case_rows[[{json.dumps(date_col)}]]), , drop = FALSE], {json.dumps(date_col)})\n\n"
            "print(res$health)\n"
            "summary(res$health)\n"
            "df_results <- as.data.frame(res$health)\n"
            "print(df_results)\n"
            "print(curve)\n"
        )

    def save_r_script(self):
        content = self._outbreak_r_script()
        if content is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export R Script", "JouriEpi_Outbreak_Analysis.R", "R Script (*.R);;All Files (*)"
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
        content = self._outbreak_r_script()
        if content is None:
            return
        QGuiApplication.clipboard().setText(content)
        self.status.setText("Reproducible R script copied to the system clipboard.")

    def reset_inputs(self):
        self.frame = None
        self.date_column.setText("onset_date")
        self.case_column.setText("case")
        self.id_column.setText("case_id")
        self.case_value.clear()
        self.curve.set_counts([])
        self.summary.setText("No line list loaded.")
        self.source_path = None
