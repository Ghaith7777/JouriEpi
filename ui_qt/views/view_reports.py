from PySide6.QtWidgets import QFileDialog, QCheckBox, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit
from PySide6.QtGui import QGuiApplication
from .common import AnalysisView


class ReportsView(AnalysisView):
    def __init__(self, parent=None):
        super().__init__("Publication & Reproducibility Exports", parent)
        self.result = None
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Run an analysis, then select an export format.")
        self.root.insertWidget(1, QLabel("Exports are generated from the exact serialized core result; calculations are not repeated in the UI."))
        self.root.insertWidget(2, self.preview)
        buttons = QHBoxLayout()
        self.standalone_checkbox = QCheckBox("Standalone document (ready to compile)")
        self.standalone_checkbox.setObjectName("StandaloneLatexCheckbox")
        self.standalone_checkbox.toggled.connect(self.refresh_preview)
        for label, callback in (("Copy LaTeX", self.copy_latex), ("Save Word dossier…", self.save_docx),
                                ("Save Python script…", self.save_python)):
            button = QPushButton(label); button.clicked.connect(callback); buttons.addWidget(button)
        buttons.insertWidget(1, self.standalone_checkbox)
        self.root.insertLayout(3, buttons)

    def set_analysis_result(self, result):
        self.result = result
        self.preview.setPlainText(result.to_latex(standalone=self.standalone_checkbox.isChecked()))
        self.export_r_button.setEnabled(True)
        self.copy_r_button.setEnabled(True)
        self.status.setText(f"Ready to export {result.analysis} results.")

    def refresh_preview(self):
        if self.result is None:
            self.status.setText("Run an analysis before generating a report preview.")
            return
        self.preview.setPlainText(self.result.to_latex(standalone=self.standalone_checkbox.isChecked()))
        mode = "standalone LaTeX document" if self.standalone_checkbox.isChecked() else "LaTeX table fragment"
        self.status.setText(f"Publication {mode} refreshed for {self.result.analysis}.")

    def reset_inputs(self):
        self.preview.clear()
        self.result = None

    def _require(self):
        if self.result is None:
            self.status.setText("Run an analysis before exporting.")
            return False
        return True

    def copy_latex(self):
        if self._require():
            QGuiApplication.clipboard().setText(self.result.to_latex(standalone=self.standalone_checkbox.isChecked()))
            self.status.setText("Standalone LaTeX document copied to the system clipboard." if
                                 self.standalone_checkbox.isChecked() else
                                 "LaTeX table fragment copied to the system clipboard.")

    def save_docx(self):
        if self._require():
            path, _ = QFileDialog.getSaveFileName(self, "Save Word dossier", "JouriEpi_results.docx", "Word document (*.docx)")
            if path:
                if not path.lower().endswith(".docx"): path += ".docx"
                with open(path, "wb") as stream: stream.write(self.result.to_docx())
                self.status.setText(f"Saved Word dossier: {path}")

    def save_python(self):
        if self._require():
            try:
                content = self.result.to_python_script()
                path, _ = QFileDialog.getSaveFileName(self, "Save Python script", "jouriepi_reproduce.py", "Python script (*.py)")
                if path:
                    with open(path, "w", encoding="utf-8") as stream: stream.write(content)
                    self.status.setText(f"Saved Python reproduction script: {path}")
            except Exception as exc: self.status.setText(str(exc))

    def save_r(self):
        if self._require():
            try:
                content = self.result.to_r_script()
                path, _ = QFileDialog.getSaveFileName(self, "Save R script", "jouriepi_reproduce.R", "R script (*.R)")
                if path:
                    with open(path, "w", encoding="utf-8") as stream: stream.write(content)
                    self.status.setText(f"Saved R reproduction script: {path}")
            except Exception as exc: self.status.setText(str(exc))
