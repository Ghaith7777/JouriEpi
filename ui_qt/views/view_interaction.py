from PySide6.QtWidgets import QFormLayout, QSpinBox, QDoubleSpinBox, QLabel
from core.public_api import additive_interaction
from .common import AnalysisView, add_run_button


class InteractionView(AnalysisView):
    def __init__(self, parent=None):
        super().__init__("Additive Interaction · RERI / AP / SI", parent)
        self.cells = []
        form = QFormLayout()
        for group, cases, noncases in (("00 · neither exposure", 10, 90), ("10 · exposure A", 18, 82),
                                       ("01 · exposure B", 16, 84), ("11 · both exposures", 35, 65)):
            a = QSpinBox(); a.setRange(0, 2_000_000_000); a.setValue(cases)
            b = QSpinBox(); b.setRange(0, 2_000_000_000); b.setValue(noncases)
            self.cells.append((a, b)); form.addRow(group + " · cases / non-cases", self._pair(a, b))
        self.root.insertLayout(1, form)
        self.alpha = QDoubleSpinBox(); self.alpha.setRange(.001, .2); self.alpha.setValue(.05)
        self.root.insertWidget(2, QLabel("Significance level α")); self.root.insertWidget(3, self.alpha)
        add_run_button(self.root, self.run_analysis)

    @staticmethod
    def _pair(a, b):
        from PySide6.QtWidgets import QWidget, QHBoxLayout
        holder = QWidget(); layout = QHBoxLayout(holder); layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(a); layout.addWidget(b); return holder

    def run_analysis(self):
        try:
            counts = [[a.value(), b.value()] for a, b in self.cells]
            self.show_result(additive_interaction(counts, alpha=self.alpha.value()))
        except Exception as exc:
            self.status.setText(str(exc))

    def reset_inputs(self):
        for (a, b), values in zip(self.cells, ((10, 90), (18, 82), (16, 84), (35, 65))):
            a.setValue(values[0]); b.setValue(values[1])
        self.alpha.setValue(0.05)
