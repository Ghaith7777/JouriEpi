from PySide6.QtWidgets import QLabel, QPlainTextEdit
from core.public_api import stratified_analysis
from .common import AnalysisView, add_run_button


class StratifiedView(AnalysisView):
    def __init__(self, parent=None):
        super().__init__("Stratified Analysis & Simpson's Paradox", parent)
        self.root.insertWidget(1, QLabel("One stratum per line: name, a, b, c, d (nonnegative integer counts)."))
        self.input = QPlainTextEdit("Age < 50, 12, 18, 5, 25\nAge ≥ 50, 8, 12, 10, 20")
        self.input.setMinimumHeight(110)
        self.root.insertWidget(2, self.input)
        add_run_button(self.root, self.run_analysis)

    def run_analysis(self):
        try:
            strata = {}
            for line in self.input.toPlainText().splitlines():
                if not line.strip():
                    continue
                parts = [part.strip() for part in line.split(",")]
                if len(parts) != 5:
                    raise ValueError("Each line must contain a stratum name and four counts separated by commas.")
                name = parts[0]
                if name in strata:
                    raise ValueError(f"Duplicate stratum name: {name}")
                strata[name] = tuple(int(value) for value in parts[1:])
            if not strata:
                raise ValueError("Enter at least one stratum.")
            self.show_result(stratified_analysis(strata))
        except Exception as exc:
            self.status.setText(str(exc))

    def reset_inputs(self):
        self.input.setPlainText("Age < 50, 12, 18, 5, 25\nAge ≥ 50, 8, 12, 10, 20")
