"""Generate a reproducible Word clinical epidemiology dossier.

The document records software/method provenance and supplied analysis outputs.
It is a reporting aid, not a validation, regulatory certification, or substitute
for a study-specific protocol, quality system, or human review.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from importlib import metadata
from io import BytesIO
import json
import math
import platform
from typing import Any, Mapping, Sequence

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from core.i18n import translate, normalize_language


REFERENCES = [
    "Katz D, Baptista J, Azen SP, Pike MC. Obtaining confidence intervals for the risk ratio in cohort studies. Biometrics. 1978;34(3):469–474.",
    "Woolf B. On estimating the relation between blood group and disease. Ann Hum Genet. 1955;19:251–253.",
    "Wilson EB. Probable inference, the law of succession, and statistical inference. J Am Stat Assoc. 1927;22(158):209–212. doi:10.1080/01621459.1927.10502953.",
    "Boschloo RD. Raised conditional level of significance for the 2×2-table when testing the equality of two probabilities. Stat Neerl. 1970;24(1):1–9.",
    "DeLong ER, DeLong DM, Clarke-Pearson DL. Comparing the areas under two or more correlated receiver operating characteristic curves: a nonparametric approach. Biometrics. 1988;44(3):837–845. doi:10.2307/2531595.",
    "VanderWeele TJ, Ding P. Sensitivity Analysis in Observational Research: Introducing the E-Value. Ann Intern Med. 2017;167(4):268–274. doi:10.7326/M16-2607.",
]


def _safe(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _safe({key: getattr(value, key) for key in value.__dataclass_fields__})
    if isinstance(value, Mapping):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "Infinity" if value > 0 else "-Infinity" if value < 0 else None
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _version(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return "not installed"


def _fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "Not estimable"
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            return "Infinity" if value > 0 else "Not estimable"
        return f"{value:.{digits}f}"
    return str(value)


def _add_table(document, headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Light Shading Accent 1"
    for cell, value in zip(table.rows[0].cells, headers):
        cell.text = str(value)
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row):
            cell.text = str(value)


def _add_figure(document, content: bytes | None, caption: str) -> None:
    if not content:
        return
    document.add_picture(BytesIO(content), width=Inches(6.2))
    paragraph = document.add_paragraph(caption)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in paragraph.runs:
        run.italic = True
        run.font.size = Pt(9)


def generate_clinical_dossier(
    counts: Sequence[int], analysis_result: Mapping[str, Any], *,
    design: str = "Cohort / cross-sectional", title: str = "JouriEpi Clinical Epidemiological Analysis Dossier",
    metadata_fields: Mapping[str, Any] | None = None, stratified_result: Any = None,
    e_value_result: Any = None, dta_result: Any = None,
    forest_png: bytes | None = None, roc_png: bytes | None = None,
    fagan_png: bytes | None = None, dca_png: bytes | None = None, dual_roc_png: bytes | None = None,
    language: str = "en",
    logo_bytes: bytes | None = None,
) -> bytes:
    """Compile results and provenance into a styled .docx document in memory."""
    if len(counts) != 4 or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in counts):
        raise ValueError("counts must be four nonnegative integers in (a,b,c,d) order")
    if not isinstance(analysis_result, Mapping):
        raise TypeError("analysis_result must be a mapping of calculated results")
    a, b, c, d = counts
    if a + b == 0 or c + d == 0:
        raise ValueError("both exposed and unexposed row totals must be positive")
    language = normalize_language(language)
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    versions = {name: _version(name) for name in ("python-docx", "scipy", "statsmodels", "pandas", "streamlit", "Pillow")}
    provenance = {
        "title": title, "generated_at_utc": generated, "python": platform.python_version(),
        "software_versions": versions, "counts": list(counts), "design": design,
        "analysis_result": _safe(dict(analysis_result)), "metadata": _safe(dict(metadata_fields or {})),
        "stratified_result": _safe(stratified_result), "e_value_result": _safe(e_value_result),
        "dta_result": _safe(dta_result), "language": language,
    }
    session_hash = sha256(json.dumps(provenance, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.7); section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8); section.right_margin = Inches(0.8)
    if logo_bytes:
        # Keep branding in the document header so it repeats on every page.
        header_paragraph = section.header.paragraphs[0]
        header_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        header_paragraph.add_run().add_picture(BytesIO(logo_bytes), height=Inches(0.42))
    styles = doc.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"].font.size = Pt(10)
    styles["Title"].font.name = "Aptos Display"
    styles["Title"].font.color.rgb = RGBColor(15, 87, 100)
    styles["Heading 1"].font.color.rgb = RGBColor(15, 87, 100)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("JOURIEPI")
    run.bold = True; run.font.size = Pt(16); run.font.color.rgb = RGBColor(15, 87, 100)
    doc.add_paragraph(title, style="Title").alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph(translate("report_subtitle", language))
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in sub.runs:
        r.italic = True
    doc.add_paragraph("")
    _add_table(doc, ["Study metadata", "Value"], [
        (str(k), str(v)) for k, v in (metadata_fields or {}).items()
    ] or [("Study metadata", "Not supplied")])
    _add_table(doc, ["Analysis integrity", "Value"], [
        ("Analysis timestamp (UTC)", generated), ("Session integrity SHA-256", session_hash),
        ("Python", platform.python_version()), ("Sampling design", design),
    ])
    doc.add_page_break()

    doc.add_heading(translate("report_methods", language), level=1)
    doc.add_paragraph(translate("report_cells", language))
    doc.add_paragraph("Odds ratio confidence interval: Woolf log-Wald method. Risk ratio confidence interval: Katz log method. Diagnostic proportion intervals: Wald and Wilson score methods. Diagnostic likelihood-ratio and diagnostic-odds-ratio intervals: log-Wald approximations where estimable. Continuous-score AUC: Mann–Whitney estimator with placement-value variance; the interval is a normal approximation and is not a full paired-curve comparison. Boschloo's exact test is available in the application when the optional SciPy dependency is installed.")
    doc.add_paragraph("Software versions: " + "; ".join(f"{k} {v}" for k, v in versions.items()) + f"; Python {platform.python_version()}.")
    for reference in REFERENCES:
        doc.add_paragraph(reference, style="List Number")

    doc.add_heading(translate("report_tables", language), level=1)
    _add_table(doc, ["Exposure group", "Cases", "Non-cases", "Total"], [
        ("Exposed", a, b, a+b), ("Unexposed", c, d, c+d), ("Total", a+c, b+d, sum(counts))
    ])
    measure_rows = []
    for key, label, ci_key, method in (
        ("risk_ratio", "Risk ratio", "risk_ratio_katz_ci", "Katz log CI"),
        ("risk_difference", "Risk difference", "risk_difference_wald_ci", "Wald CI"),
        ("odds_ratio", "Odds ratio", "odds_ratio_woolf_ci", "Woolf log CI"),
        ("fisher_two_sided_p", "Fisher exact p-value (two-sided)", None, "Conditional exact"),
    ):
        ci = analysis_result.get(ci_key) if ci_key else None
        measure_rows.append((label, _fmt(analysis_result.get(key)), f"{_fmt(ci[0])}–{_fmt(ci[1])}" if ci else "Not applicable", method))
    _add_table(doc, ["Measure", "Estimate", "95% CI", "Method"], measure_rows)
    if stratified_result is not None:
        doc.add_heading("Stratum-specific estimates", level=2)
        _add_table(doc, ["Stratum", "a", "b", "c", "d", "OR", "OR 95% CI", "RR", "RR 95% CI"], [
            (s.label, *s.counts, _fmt(s.odds_ratio), str(s.odds_ratio_ci or "Not estimable"),
             _fmt(s.risk_ratio), str(s.risk_ratio_ci or "Not estimable")) for s in stratified_result.strata
        ])
        doc.add_paragraph(f"Mantel–Haenszel OR = {_fmt(stratified_result.mantel_haenszel_odds_ratio)}; RBG-based 95% CI = {str(stratified_result.mantel_haenszel_odds_ratio_ci or 'not estimable')}; Mantel–Haenszel RR = {_fmt(stratified_result.mantel_haenszel_risk_ratio)}.")

    doc.add_heading(translate("report_narrative", language), level=1)
    risk1, risk0 = a/(a+b), c/(c+d)
    if language == "fr":
        narrative = (f"L’analyse comprenait {sum(counts)} observations : {a+b} personnes exposées et {c+d} non exposées. "
                    f"La proportion observée était de {a}/{a+b} ({risk1:.1%}) chez les personnes exposées et de {c}/{c+d} ({risk0:.1%}) chez les personnes non exposées. "
                    f"L’odds ratio était de {_fmt(analysis_result.get('odds_ratio'))} (IC à 95 % de Woolf : {analysis_result.get('odds_ratio_woolf_ci') or 'non estimable'}) ; "
                    f"le risque relatif était de {_fmt(analysis_result.get('risk_ratio'))} (IC à 95 % de Katz : {analysis_result.get('risk_ratio_katz_ci') or 'non estimable'}). "
                    f"Le plan d’échantillonnage enregistré était : {design}. Ces résultats décrivent le tableau fourni et ne démontrent pas la causalité. "
                    "Les éléments STROBE propres à l’étude, notamment le contexte, les dates, l’éligibilité, les données manquantes, l’ajustement, l’éthique et le financement, doivent être complétés par les auteurs.")
    elif language == "de":
        narrative = (f"Die Analyse umfasste {sum(counts)} Datensätze: {a+b} exponierte und {c+d} nicht exponierte Personen. "
                     f"Der beobachtete Anteil betrug {a}/{a+b} ({risk1:.1%}) bei Exponierten und {c}/{c+d} ({risk0:.1%}) bei Nicht-Exponierten. "
                     f"Die Odds Ratio betrug {_fmt(analysis_result.get('odds_ratio'))} (Woolf-95%-KI: {analysis_result.get('odds_ratio_woolf_ci') or 'nicht schätzbar'}); "
                     f"das relative Risiko betrug {_fmt(analysis_result.get('risk_ratio'))} (Katz-95%-KI: {analysis_result.get('risk_ratio_katz_ci') or 'nicht schätzbar'}). "
                     f"Das dokumentierte Stichprobendesign war: {design}. Diese Ergebnisse beschreiben die bereitgestellte Tabelle und belegen keine Kausalität. "
                     "Studienbezogene STROBE-Angaben zu Setting, Zeiträumen, Eignung, fehlenden Daten, Adjustierung, Ethik und Finanzierung müssen anhand der Studienunterlagen ergänzt werden.")
    else:
        narrative = (f"The analysis included {sum(counts)} records: {a+b} exposed and {c+d} unexposed. "
                    f"The observed outcome proportion was {a}/{a+b} ({risk1:.1%}) among exposed participants and "
                    f"{c}/{c+d} ({risk0:.1%}) among unexposed participants. The odds ratio was {_fmt(analysis_result.get('odds_ratio'))} "
                    f"(Woolf 95% CI {analysis_result.get('odds_ratio_woolf_ci') or 'not estimable'}); the risk ratio was "
                    f"{_fmt(analysis_result.get('risk_ratio'))} (Katz 95% CI {analysis_result.get('risk_ratio_katz_ci') or 'not estimable'}). "
                    f"The sampling design was recorded as {design}. These results describe the supplied table and do not by themselves establish causality. "
                    "Complete study-specific STROBE items, including setting, dates, eligibility, missing-data handling, confounder adjustment, ethics and funding, from the source study record.")
    doc.add_paragraph(narrative)

    doc.add_heading(translate("report_sensitivity", language), level=1)
    if e_value_result is not None:
        doc.add_paragraph(f"E-value: {_fmt(e_value_result.e_value)}; confidence-limit E-value: {_fmt(e_value_result.confidence_limit_e_value)}. {e_value_result.interpretation}")
    else:
        doc.add_paragraph("No E-value result was supplied for this dossier. The E-value is a sensitivity summary and does not establish causality or rule out bias.")
    if stratified_result is not None:
        doc.add_paragraph(f"Simpson's paradox reversal flag: {bool(stratified_result.simpsons_paradox_detected)}. Crude-versus-MH OR percent change: {_fmt(stratified_result.percent_change)}. This is an automated diagnostic flag, not a causal determination.")
    if dta_result is not None:
        doc.add_paragraph(f"DTA result mode: {dta_result.mode}; AUC: {_fmt(dta_result.auc)}; AUC 95% CI: {str(dta_result.auc_ci or 'not estimable')}. AUC is not identified from a single 2×2 operating point.")

    doc.add_heading(translate("report_figures", language), level=1)
    _add_figure(doc, forest_png, translate("report_forest_caption", language))
    _add_figure(doc, roc_png, translate("report_roc_caption", language))
    _add_figure(doc, dual_roc_png, "Figure 3. Dual ROC curves with DeLong comparison; model curves and operating points are shown in contrasting colors.")
    _add_figure(doc, fagan_png, translate("report_fagan_caption", language))
    _add_figure(doc, dca_png, translate("report_dca_caption", language))
    doc.add_heading(translate("report_integrity", language), level=1)
    doc.add_paragraph("This dossier contains a SHA-256 integrity hash of its canonical analysis payload and reports methods and versions for traceability. It does not, by itself, satisfy FDA 21 CFR Part 11, GCP, electronic-signature, validation, access-control, or record-retention requirements. Regulated use requires a fit-for-purpose validated system, controlled procedures, access and change controls, and organizational review.")
    footer = section.footer.paragraphs[0]
    footer.text = f"JouriEpi · generated {generated} · session SHA-256 {session_hash[:16]}…"
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    out = BytesIO()
    doc.save(out)
    return out.getvalue()

