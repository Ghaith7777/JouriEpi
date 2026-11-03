"""Clinical, human-readable Word exports for JouriEpi analysis results."""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
import math
from collections.abc import Mapping
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


def format_p_value(p: float | None) -> str:
    """Format inferential p-values without rounding small values to zero."""
    if p is None:
        return "—"
    try:
        value = float(p)
    except (TypeError, ValueError):
        return str(p)
    if not math.isfinite(value):
        return "Not estimable"
    if value < 0.001:
        return "< 0.001"
    return f"{value:.4f}"


_METRICS = (
    ("odds_ratio", "Odds Ratio", "odds_ratio_woolf_ci", None),
    ("risk_ratio", "Risk Ratio", "risk_ratio_katz_ci", None),
    ("risk_difference", "Risk Difference", "risk_difference_wald_ci", None),
    ("pearson_chi2", "Pearson Chi-Square", None, "pearson_p"),
    ("yates_chi2", "Yates-Corrected Chi-Square", None, "yates_p"),
    ("fisher_two_sided_p", "Fisher Exact Test (two-sided)", None, "fisher_two_sided_p"),
)

_ADDITIONAL_LABELS = {
    "risk_exposed": "Outcome Proportion (Exposed)",
    "risk_unexposed": "Outcome Proportion (Unexposed)",
    "attributable_fraction_exposed": "Attributable Fraction among Exposed",
    "population_attributable_fraction": "Population Attributable Fraction",
    "odds_ratio_haldane_anscombe": "Haldane–Anscombe Corrected Odds Ratio",
}
_ADDITIONAL_INTERVALS = {
    "attributable_fraction_exposed": "attributable_fraction_exposed_katz_ci",
}


def _number(value: Any, digits: int = 4) -> str:
    if value is None:
        return "Not estimable"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isnan(number):
            return "Not estimable"
        if math.isinf(number):
            return "Infinite" if number > 0 else "Not estimable"
        return f"{number:.{digits}f}"
    return str(value)


def _interval(value: Any) -> str:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        return "Not estimable"
    return f"{_number(value[0])} to {_number(value[1])}"


def _borders(table) -> None:
    """Apply explicit single-line borders so the table remains clear in Word."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "CBD5E1")


def _table(document, headers, rows):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = True
    _borders(table)
    for cell, value in zip(table.rows[0].cells, headers):
        cell.text = str(value)
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(15, 87, 100)
    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = str(value)
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
    return table


def _metric_rows(estimates: Mapping[str, Any]):
    rows = []
    for key, label, ci_key, p_key in _METRICS:
        if key not in estimates:
            continue
        estimate = estimates.get(key)
        # For a p-value-only test, keep the p-value in its dedicated column.
        p_value = estimates.get(p_key) if p_key else None
        if key.endswith("_p") or key == "fisher_two_sided_p":
            rows.append((label, "—", "Not applicable", format_p_value(estimate)))
        else:
            rows.append((label, _number(estimate), _interval(estimates.get(ci_key)) if ci_key else "Not applicable",
                         format_p_value(p_value) if p_key else "—"))
    # Include other supported scalar estimates without exposing implementation keys.
    known = {item[0] for item in _METRICS}
    for key, value in estimates.items():
        if key in known or key.endswith(("_ci", "_p", "_notes")) or key in {
            "counts", "expected_counts", "e_value", "notes", "alpha", "method",
            "expected_any_below_5", "haldane_anscombe",
        }:
            continue
        if value is None:
            continue
        if isinstance(value, (int, float)):
            label = _ADDITIONAL_LABELS.get(key, key.replace("_", " ").title())
            ci_key = _ADDITIONAL_INTERVALS.get(key)
            rows.append((label, _number(value), _interval(estimates.get(ci_key)) if ci_key else "Not reported", "—"))
    return rows or [("No reportable scalar estimates", "—", "—", "—")]


def result_to_docx(result: Any, *, title: str | None = None) -> bytes:
    """Create a polished clinical dossier from an AnalysisResult-like object."""
    if not hasattr(result, "analysis") or not isinstance(getattr(result, "estimates", None), Mapping):
        raise TypeError("result must expose an analysis name and an estimates mapping")

    estimates = result.estimates
    inputs = getattr(result, "inputs", {}) or {}
    counts = inputs.get("counts") if isinstance(inputs, Mapping) else None
    is_2x2 = result.analysis == "2x2" and isinstance(counts, (tuple, list)) and len(counts) == 4
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    styles = document.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"].font.size = Pt(9.5)
    styles["Title"].font.name = "Aptos Display"
    styles["Title"].font.color.rgb = RGBColor(15, 87, 100)
    for heading in ("Heading 1", "Heading 2"):
        styles[heading].font.color.rgb = RGBColor(15, 87, 100)

    heading = document.add_paragraph(style="Title")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.add_run(title or f"JouriEpi Clinical Report — {result.analysis.replace('_', ' ').title()}")
    stamp = document.add_paragraph(f"Generated: {generated}")
    stamp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    note = document.add_paragraph("Local execution: this report was generated on this device. Analysis data was not transmitted to a remote service.")
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER

    document.add_heading("Input 2×2 Contingency Table" if is_2x2 else "Analysis Inputs", level=1)
    if is_2x2:
        a, b, c, d = (int(value) for value in counts)
        _table(document, ["Exposure group", "Cases", "Non-cases", "Total"], [
            ("Exposed", a, b, a + b),
            ("Unexposed", c, d, c + d),
            ("Total", a + c, b + d, sum((a, b, c, d))),
        ])
    else:
        input_rows = []
        if isinstance(inputs, Mapping):
            for key, value in inputs.items():
                if key == "counts" and isinstance(value, (tuple, list)):
                    value = ", ".join(str(item) for item in value)
                elif isinstance(value, (tuple, list)):
                    value = f"{len(value)} values supplied"
                input_rows.append((key.replace("_", " ").title(), _number(value) if isinstance(value, (int, float)) else value))
        _table(document, ["Input", "Value"], input_rows or [("Inputs", "Not supplied")])

    document.add_heading("Main Association & Diagnostic Results", level=1)
    _table(document, ["Metric", "Estimate", "95% CI", "p-value"], _metric_rows(estimates))

    forest_png = _forest_plot_png(estimates)
    if forest_png is not None:
        document.add_heading("Association Forest Plot", level=2)
        document.add_picture(BytesIO(forest_png), width=Inches(6.2))

    document.add_heading("Sensitivity & E-value Interpretation", level=1)
    e_value = estimates.get("e_value") if isinstance(estimates, Mapping) else None
    if isinstance(e_value, Mapping):
        document.add_paragraph(
            f"E-value: {_number(e_value.get('e_value'))}. "
            f"Confidence-limit E-value: {_number(e_value.get('confidence_limit_e_value'))}. "
            f"{e_value.get('interpretation') or 'Interpretation was not supplied by the analysis.'}"
        )
    else:
        document.add_paragraph("No E-value sensitivity result was supplied. This analysis therefore makes no E-value-based statement about the strength of unmeasured confounding required to explain the observed association.")
    if estimates.get("odds_ratio_haldane_anscombe") is not None:
        document.add_paragraph(
            "A Haldane–Anscombe corrected odds ratio was additionally calculated because it was explicitly requested: "
            f"{_number(estimates.get('odds_ratio_haldane_anscombe'))} "
            f"(95% CI {_interval(estimates.get('odds_ratio_haldane_anscombe_woolf_ci'))}). "
            "It is supplementary and does not replace the uncorrected primary estimate."
        )

    document.add_heading("Statistical Notes & Assumptions", level=1)
    if is_2x2:
        document.add_paragraph("Table orientation: rows are exposed and unexposed; columns are cases and non-cases. The input order is (a, b, c, d) = exposed cases, exposed non-cases, unexposed cases, unexposed non-cases.")
        document.add_paragraph("Odds Ratio: Woolf log-Wald 95% confidence interval. Risk Ratio: Katz log 95% confidence interval. Risk Difference: Wald 95% confidence interval. Pearson and Yates-corrected chi-square tests use one degree of freedom. Fisher’s exact test is conditional on the observed margins.")
        expected = estimates.get("expected_counts")
        if expected is not None:
            low = estimates.get("expected_any_below_5")
            document.add_paragraph("At least one expected cell count is below 5; interpret the asymptotic chi-square approximation cautiously." if low else "All expected cell counts are at least 5; the usual expected-count guideline for the chi-square approximation is met.")
        alpha = inputs.get("alpha", estimates.get("alpha", 0.05))
        document.add_paragraph(f"Nominal significance level: α = {_number(alpha)}. Confidence intervals are descriptive large-sample intervals; sparse data and zero cells may make some estimates or intervals non-estimable.")
    else:
        document.add_paragraph(f"Analysis type: {result.analysis.replace('_', ' ').title()}. Interpret estimates in accordance with the sampling design, measurement process, and assumptions of the selected method.")
    notes = estimates.get("notes", ())
    if isinstance(notes, (tuple, list)):
        for item in notes:
            document.add_paragraph(str(item), style="List Bullet")
    method = estimates.get("method")
    if method:
        document.add_paragraph(f"Method: {method}")
    document.add_paragraph("This report is a statistical reporting aid, not a diagnosis or a substitute for clinical judgement, study-specific protocol review, or independent verification of source data.")

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("JouriEpi Clinical Workstation · Local report · Review before clinical or research use").font.size = Pt(8)
    stream = BytesIO()
    document.save(stream)
    return stream.getvalue()


def _forest_plot_png(estimates: Mapping[str, Any]) -> bytes | None:
    """Render available OR/RR estimates and confidence intervals at 300 DPI."""
    rows = []
    for label, estimate_key, ci_key in (
        ("Odds ratio", "odds_ratio", "odds_ratio_woolf_ci"),
        ("Risk ratio", "risk_ratio", "risk_ratio_katz_ci"),
    ):
        estimate, interval = estimates.get(estimate_key), estimates.get(ci_key)
        if (isinstance(estimate, (int, float)) and math.isfinite(float(estimate)) and estimate > 0
                and isinstance(interval, (tuple, list)) and len(interval) == 2
                and all(isinstance(v, (int, float)) and math.isfinite(float(v)) and v > 0 for v in interval)):
            rows.append((label, float(estimate), float(interval[0]), float(interval[1])))
    if not rows:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    width, height = 2400, 750 if len(rows) > 1 else 600
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 38)
        small = ImageFont.truetype("arial.ttf", 30)
    except OSError:
        font = small = ImageFont.load_default()
    values = [value for row in rows for value in row[1:]] + [1.0]
    low, high = min(values) / 1.8, max(values) * 1.8
    log_low, log_high = math.log(low), math.log(high)
    left, right = 650, 1900
    def xpos(value: float) -> float:
        return left + (math.log(value) - log_low) / (log_high - log_low) * (right - left)
    top, bottom = 170, height - 150
    null_x = xpos(1.0)
    draw.line((null_x, top - 40, null_x, bottom + 25), fill="#64748b", width=5)
    draw.text((null_x + 12, top - 85), "Null = 1", fill="#334155", font=small)
    for index, (label, estimate, lower, upper) in enumerate(rows):
        y = top + (index + 1) * (bottom - top) / (len(rows) + 1)
        x1, x2, xm = xpos(lower), xpos(upper), xpos(estimate)
        draw.text((70, y - 28), label, fill="#0f172a", font=font)
        draw.line((x1, y, x2, y), fill="#0f766e", width=9)
        draw.line((x1, y - 22, x1, y + 22), fill="#0f766e", width=7)
        draw.line((x2, y - 22, x2, y + 22), fill="#0f766e", width=7)
        draw.ellipse((xm - 16, y - 16, xm + 16, y + 16), fill="#0f766e")
        draw.text((right + 25, y - 25), f"{estimate:.3g} ({lower:.3g}–{upper:.3g})",
                  fill="#0f172a", font=small)
    draw.line((left, bottom + 55, right, bottom + 55), fill="#334155", width=4)
    draw.text((left, bottom + 75), "Ratio (log scale)", fill="#334155", font=small)
    output = BytesIO()
    image.save(output, format="PNG", dpi=(300, 300), optimize=True)
    return output.getvalue()
