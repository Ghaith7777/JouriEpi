import math
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QImage, QPdfWriter
from PySide6.QtWidgets import (QCheckBox, QDoubleSpinBox, QFormLayout, QHBoxLayout,
                               QLabel, QWidget, QFileDialog, QPushButton)
from core.public_api import analyze_2x2
from ui_qt.components.contingency_table import ContingencyTable
from ui_qt.components.metric_card import MetricCard
from .common import AnalysisView, add_run_button


class RatioForestPlot(QWidget):
    """Dependency-free forest plot for the OR and RR calculated from 2×2 counts."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.setObjectName("RatioForestPlot")
        self.setMinimumHeight(190)

    def set_estimates(self, estimates):
        self.rows = []
        for label, estimate_key, ci_key in (
            ("Odds ratio", "odds_ratio", "odds_ratio_woolf_ci"),
            ("Risk ratio", "risk_ratio", "risk_ratio_katz_ci"),
        ):
            estimate, interval = estimates.get(estimate_key), estimates.get(ci_key)
            if estimate is not None and interval and estimate > 0 and all(v is not None and v > 0 for v in interval):
                self.rows.append((label, float(estimate), float(interval[0]), float(interval[1])))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        palette = self.palette()
        text_color = palette.text().color()
        dark = self.palette().window().color().lightness() < 128
        muted = QColor("#a1a1aa") if dark else QColor("#334155")
        accent = palette.highlight().color()
        rect = self.rect().adjusted(116, 24, -170, -38)
        painter.setPen(text_color)
        painter.drawText(12, 20, "Odds Ratio & Risk Ratio · 95% CI")
        if not self.rows:
            painter.setPen(muted)
            painter.drawText(rect, Qt.AlignCenter, "Confidence intervals are not estimable for these cell counts")
            return
        values = [v for row in self.rows for v in row[1:]]
        low = max(0.01, min(values + [1.0]) / 2)
        high = max(values + [1.0]) * 2
        if high <= low:
            high = low * 10
        log_low, log_high = math.log(low), math.log(high)
        def xpos(value):
            return rect.left() + (math.log(value) - log_low) / (log_high - log_low) * rect.width()
        null_x = xpos(1.0)
        painter.setPen(QPen(QColor("#f87171") if dark else QColor("#334155"), 1.4, Qt.DashLine))
        painter.drawLine(QPointF(null_x, rect.top()), QPointF(null_x, rect.bottom()))
        painter.setPen(muted)
        painter.drawText(int(null_x - 22), rect.bottom() + 22, "Null = 1")
        for index, (label, estimate, lower, upper) in enumerate(self.rows):
            y = rect.top() + (index + 1) * rect.height() / (len(self.rows) + 1)
            x1, x2, xm = xpos(lower), xpos(upper), xpos(estimate)
            painter.setPen(text_color)
            painter.drawText(8, int(y + 5), label)
            painter.setPen(QPen(accent, 2.2))
            painter.drawLine(QPointF(x1, y), QPointF(x2, y))
            painter.drawLine(QPointF(x1, y - 5), QPointF(x1, y + 5))
            painter.drawLine(QPointF(x2, y - 5), QPointF(x2, y + 5))
            painter.setBrush(accent)
            painter.drawEllipse(QPointF(xm, y), 4.5, 4.5)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(text_color)
            painter.drawText(int(rect.right() + 12), int(y + 5), f"{estimate:.3g} ({lower:.3g}–{upper:.3g})")


class AssociationView(AnalysisView):
    def __init__(self, parent=None):
        super().__init__("2×2 Association Analysis", parent)
        # These four cards are created once and retain their identity/order
        # across checkbox toggles and recalculations.
        self.metric_cards = (
            MetricCard("Odds Ratio", "—"),
            MetricCard("Odds Ratio (Haldane)", "—", "Off (enable via checkbox)"),
            MetricCard("Haldane Woolf CI", "—", "Off (enable via checkbox)"),
            MetricCard("Risk Ratio", "—"),
        )
        for index, card in enumerate(self.metric_cards):
            self.metrics_layout.addWidget(card, 0, index)
        self.table = ContingencyTable()
        self.table.setObjectName("AssociationInputTable")
        self.root.insertWidget(1, QLabel("Enter exposed/unexposed rows and case/non-case columns. Cell order: a, b, c, d."))
        self.root.insertWidget(2, self.table)
        self.forest_plot = RatioForestPlot()
        self.root.insertWidget(3, self.forest_plot)
        self.export_plot_button = QPushButton("Export Plot…")
        self.export_plot_button.setEnabled(False)
        self.export_plot_button.clicked.connect(self.export_plot)
        self.root.insertWidget(4, self.export_plot_button)
        options = QHBoxLayout()
        self.alpha = QDoubleSpinBox()
        self.alpha.setRange(0.001, 0.2)
        self.alpha.setSingleStep(0.01)
        self.alpha.setValue(0.05)
        self.haldane = QCheckBox("Explicit Haldane–Anscombe sensitivity correction")
        self.boschloo = QCheckBox("Include Boschloo exact test")
        options.addWidget(QLabel("Alpha")); options.addWidget(self.alpha)
        options.addWidget(self.haldane); options.addWidget(self.boschloo)
        self.root.insertLayout(5, options)
        self.calculate_button = add_run_button(self.root, self.run_analysis, text="Calculate")
        self.haldane.toggled.connect(self.run_analysis)

    def _show_metrics(self, payload: dict):
        """Update the fixed four-card association summary without rebuilding it."""
        def display(value):
            if value is None:
                return "—"
            return f"{float(value):.4g}"

        self.metric_cards[0].set_metric(
            "Odds Ratio", display(payload.get("odds_ratio")), "Unadjusted estimate"
        )
        if payload.get("haldane_anscombe_status") == "Active":
            self.metric_cards[1].set_metric(
                "Odds Ratio (Haldane)",
                display(payload.get("odds_ratio_haldane_anscombe")),
                "+0.5 applied to all four cells",
            )
            interval = payload.get("odds_ratio_haldane_anscombe_woolf_ci")
            interval_text = (
                f"[{display(interval[0])}, {display(interval[1])}]"
                if interval is not None else "—"
            )
            self.metric_cards[2].set_metric(
                "Haldane Woolf CI", interval_text, "95% Woolf confidence interval"
            )
        else:
            self.metric_cards[1].set_metric(
                "Odds Ratio (Haldane)", "—", "Off (enable via checkbox)"
            )
            self.metric_cards[2].set_metric(
                "Haldane Woolf CI", "—", "Off (enable via checkbox)"
            )
        self.metric_cards[3].set_metric(
            "Risk Ratio", display(payload.get("risk_ratio")), "Unadjusted estimate"
        )

    def clear_result(self):
        """Clear result details while retaining the four permanent metric cards."""
        self.result = None
        self.results_table.clearContents()
        self.results_table.setRowCount(0)
        self.export_r_button.setEnabled(False)
        self.copy_r_button.setEnabled(False)
        self.status.setText("Enter data and run the analysis. All calculations are performed locally.")
        self.metric_cards[0].set_metric("Odds Ratio", "—")
        self.metric_cards[1].set_metric(
            "Odds Ratio (Haldane)", "—", "Off (enable via checkbox)"
        )
        self.metric_cards[2].set_metric(
            "Haldane Woolf CI", "—", "Off (enable via checkbox)"
        )
        self.metric_cards[3].set_metric("Risk Ratio", "—")

    def run_analysis(self):
        try:
            result = analyze_2x2(self.table.values(), alpha=self.alpha.value(),
                                 haldane_anscombe=self.haldane.isChecked(),
                                 include_boschloo=self.boschloo.isChecked())
            self.show_result(result)
            self.forest_plot.set_estimates(result.to_dict()["estimates"])
            self.export_plot_button.setEnabled(bool(self.forest_plot.rows))
        except Exception as exc:
            self.status.setText(str(exc))

    def export_plot(self):
        if not self.forest_plot.rows:
            self.status.setText("Run an analysis with estimable ratio intervals before exporting the plot.")
            return
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export forest plot", "JouriEpi_forest_plot.png",
            "PNG image (*.png);;PDF document (*.pdf)"
        )
        if not path:
            return
        is_pdf = selected_filter.startswith("PDF") or path.lower().endswith(".pdf")
        extension = ".pdf" if is_pdf else ".png"
        if not path.lower().endswith(extension):
            path += extension
        try:
            if is_pdf:
                writer = QPdfWriter(path)
                writer.setResolution(300)
                painter = QPainter(writer)
                target = writer.pageLayout().paintRectPixels(writer.resolution())
                scale = min(target.width() / max(1, self.forest_plot.width()),
                            target.height() / max(1, self.forest_plot.height()))
                painter.translate(target.x(), target.y())
                painter.scale(scale, scale)
                self.forest_plot.render(painter)
                painter.end()
            else:
                scale = 3
                image = QImage(self.forest_plot.size() * scale, QImage.Format_ARGB32)
                image.setDotsPerMeterX(round(300 / 0.0254))
                image.setDotsPerMeterY(round(300 / 0.0254))
                image.fill(Qt.transparent)
                painter = QPainter(image)
                painter.scale(scale, scale)
                self.forest_plot.render(painter)
                painter.end()
                if not image.save(path, "PNG"):
                    raise OSError("Qt could not write the PNG image.")
            self.status.setText(f"Forest plot exported: {path}")
        except Exception as exc:
            self.status.setText(f"Could not export forest plot: {exc}")

    def reset_inputs(self):
        self.table.set_values((12, 18, 5, 25))
        self.alpha.setValue(0.05)
        self.haldane.setChecked(False)
        self.boschloo.setChecked(False)
        self.forest_plot.set_estimates({})
        self.export_plot_button.setEnabled(False)
