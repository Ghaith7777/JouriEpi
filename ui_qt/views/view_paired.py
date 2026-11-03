from PySide6.QtWidgets import QFormLayout, QSpinBox, QDoubleSpinBox
from core.public_api import paired_mcnemar
from .common import AnalysisView, add_run_button


class PairedView(AnalysisView):
    def __init__(self, parent=None):
        super().__init__("Paired 2×2 & McNemar Analysis", parent)
        form = QFormLayout()
        self.cells = []
        for label, default in (("a · positive / positive", 32), ("b · positive / negative", 8),
                               ("c · negative / positive", 3), ("d · negative / negative", 57)):
            box = QSpinBox(); box.setRange(0, 2_000_000_000); box.setValue(default)
            self.cells.append(box); form.addRow(label, box)
        self.root.insertLayout(1, form)
        self.alpha = QDoubleSpinBox(); self.alpha.setRange(.001, .2); self.alpha.setValue(.05)
        self.root.insertWidget(2, self.alpha)
        add_run_button(self.root, self.run_analysis)

    def run_analysis(self):
        try:
            self.show_result(paired_mcnemar(*(box.value() for box in self.cells), alpha=self.alpha.value()))
        except Exception as exc:
            self.status.setText(str(exc))

    def reset_inputs(self):
        for box, value in zip(self.cells, (32, 8, 3, 57)):
            box.setValue(value)
        self.alpha.setValue(0.05)
