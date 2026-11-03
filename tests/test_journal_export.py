from io import BytesIO

from docx import Document

from core.journal_export import export_journal_docx, export_journal_html, export_journal_latex


RESULT = {"risk_ratio": 2.0, "risk_ratio_katz_ci": (1.2, 3.1), "odds_ratio": 3.0,
          "odds_ratio_woolf_ci": (1.5, 6.0), "risk_difference": 0.2, "risk_difference_wald_ci": (0.1, 0.3)}


def test_journal_exporters_produce_docx_html_and_three_rule_latex():
    counts = (25, 15, 7, 30)
    html = export_journal_html(counts, RESULT)
    latex = export_journal_latex(counts, RESULT)
    docx = export_journal_docx(counts, RESULT)
    assert "border-top:2px solid" in html and "border-bottom:2px solid" in html
    assert "\\toprule" in latex and "\\midrule" in latex and "\\bottomrule" in latex
    assert "OR" not in latex  # labels are plain text; no fabricated result labels
    document = Document(BytesIO(docx))
    assert len(document.tables) == 1
    assert document.tables[0].rows[0].cells[0].text == "Measure"
    assert "2.000" in " ".join(cell.text for row in document.tables[0].rows for cell in row.cells)
