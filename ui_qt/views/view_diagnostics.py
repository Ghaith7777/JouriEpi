from PySide6.QtWidgets import (QComboBox, QDoubleSpinBox, QFormLayout, QLabel,
                               QLineEdit, QSpinBox)
from core.public_api import diagnostic_accuracy, compare_roc_delong
from .common import AnalysisView, add_run_button


def _numbers(text: str, cast=float):
    values = [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]
    return [cast(value) for value in values]


class DiagnosticsView(AnalysisView):
    def __init__(self, parent=None):
        super().__init__("Diagnostic Accuracy & ROC", parent)
        self.mode = QComboBox()
        self.mode.addItem("2×2 diagnostic counts (TP, FP, FN, TN)", "counts")
        self.mode.addItem("Continuous scores and binary reference outcomes", "scores")
        self.mode.addItem("Compare two ROC curves (DeLong)", "delong")
        self.root.insertWidget(1, self.mode)
        self.tp = QSpinBox(); self.fp = QSpinBox()
        self.fn = QSpinBox(); self.tn = QSpinBox()
        for widget, value in ((self.tp, 42), (self.fp, 8), (self.fn, 6), (self.tn, 44)):
            widget.setRange(0, 10_000_000)
            widget.setValue(value)
        self.scores = QLineEdit("0.91, 0.82, 0.77, 0.31, 0.22, 0.15")
        self.outcomes = QLineEdit("1, 1, 1, 0, 0, 0")
        self.scores2 = QLineEdit("0.88, 0.79, 0.68, 0.35, 0.27, 0.12")
        form = QFormLayout()
        self.form_labels = {}
        for label, widget in (("True positives", self.tp), ("False positives", self.fp),
                              ("False negatives", self.fn), ("True negatives", self.tn),
                              ("Scores", self.scores), ("Reference outcomes (0/1)", self.outcomes),
                              ("Second test scores (DeLong)", self.scores2)):
            form.addRow(label, widget)
            self.form_labels[widget] = form.labelForField(widget)
        self.root.insertLayout(2, form)
        self.alpha = QDoubleSpinBox(); self.alpha.setRange(.001, .2); self.alpha.setValue(.05)
        self.root.insertWidget(3, QLabel("Significance level α")); self.root.insertWidget(4, self.alpha)
        self.mode.currentIndexChanged.connect(self._update_fields)
        self._update_fields()
        add_run_button(self.root, self.run_analysis)

    def _update_fields(self):
        mode = self.mode.currentData()
        for widget in (self.tp, self.fp, self.fn, self.tn):
            widget.setVisible(mode == "counts")
            self.form_labels[widget].setVisible(mode == "counts")
        for widget in (self.scores, self.outcomes):
            widget.setVisible(mode in {"scores", "delong"})
            self.form_labels[widget].setVisible(mode in {"scores", "delong"})
        self.scores2.setVisible(mode == "delong")
        self.form_labels[self.scores2].setVisible(mode == "delong")

    def run_analysis(self):
        try:
            mode = self.mode.currentData()
            if mode == "counts":
                result = diagnostic_accuracy(tp=self.tp.value(), fp=self.fp.value(),
                                              fn=self.fn.value(), tn=self.tn.value(), alpha=self.alpha.value())
            else:
                scores, outcomes = _numbers(self.scores.text()), _numbers(self.outcomes.text(), int)
                if mode == "scores":
                    result = diagnostic_accuracy(scores=scores, outcomes=outcomes, alpha=self.alpha.value())
                else:
                    result = compare_roc_delong(scores, _numbers(self.scores2.text()), outcomes, alpha=self.alpha.value())
            self.show_result(result)
        except Exception as exc:
            self.status.setText(str(exc))

    def reset_inputs(self):
        self.mode.setCurrentIndex(0)
        for widget, value in ((self.tp, 42), (self.fp, 8), (self.fn, 6), (self.tn, 44)):
            widget.setValue(value)
        self.scores.setText("0.91, 0.82, 0.77, 0.31, 0.22, 0.15")
        self.outcomes.setText("1, 1, 1, 0, 0, 0")
        self.scores2.setText("0.88, 0.79, 0.68, 0.35, 0.27, 0.12")
        self.alpha.setValue(0.05)
