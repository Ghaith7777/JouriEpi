"""Publication-oriented narrative and comparison-table exports.

Outputs are descriptive templates populated only with supplied counts and
calculated values. They do not certify STROBE compliance or infer missing study
design, setting, dates, eligibility, ethics, or funding information.
"""

from __future__ import annotations

import json
import math
from typing import Any, Mapping, Sequence
from core.i18n import normalize_language


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "Not estimable"
    if isinstance(value, float):
        if value == float("inf"):
            return "Infinity"
        if value == float("-inf"):
            return "-Infinity"
        if value != value:
            return "Not estimable"
        return f"{value:.{digits}g}"
    return str(value)


def strobe_narrative(counts: Sequence[int], result: Mapping[str, Any], *, design: str,
                     exposure_label: str = "exposure", outcome_label: str = "case outcome",
                     language: str = "en") -> str:
    """Build a cautious STROBE-style results paragraph without inventing context."""
    if len(counts) != 4 or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in counts):
        raise ValueError("counts must be four nonnegative integers in (a,b,c,d) order")
    a, b, c, d = counts
    total = sum(counts)
    if total == 0 or a + b == 0 or c + d == 0:
        raise ValueError("counts must include participants in both exposure groups and a positive total")
    if not design.strip() or not exposure_label.strip() or not outcome_label.strip():
        raise ValueError("design and variable labels must be non-empty")
    language = normalize_language(language)
    if language == "fr":
        return (f"L’analyse comprenait {total} observations : {a+b} exposées et {c+d} non exposées. Pour {exposure_label}, "
                f"{a}/{a+b} personnes présentaient le résultat {outcome_label} ({a/(a+b):.1%}) ; chez les non-exposées, "
                f"{c}/{c+d} présentaient le résultat ({c/(c+d):.1%}). L’odds ratio était de {_fmt(result.get('odds_ratio'))} "
                f"(IC à 95 % de Woolf : {_fmt_ci(result.get('odds_ratio_woolf_ci'))}) ; la valeur p bilatérale exacte de Fisher était "
                f"{_fmt(result.get('fisher_two_sided_p'))}. Le plan d’échantillonnage était : {design}. Ces estimations décrivent les données observées sans établir la causalité. "
                "Les éléments STROBE relatifs au contexte, aux dates, à l’éligibilité, aux données manquantes, à l’ajustement, à l’éthique et au financement doivent être complétés par les auteurs.")
    if language == "de":
        return (f"Die Analyse umfasste {total} Datensätze: {a+b} exponierte und {c+d} nicht exponierte Personen. Bei {exposure_label} "
                f"hatten {a}/{a+b} Personen das Ergebnis {outcome_label} ({a/(a+b):.1%}); bei Nicht-Exponierten waren es "
                f"{c}/{c+d} ({c/(c+d):.1%}). Die Odds Ratio betrug {_fmt(result.get('odds_ratio'))} (Woolf-95%-KI: {_fmt_ci(result.get('odds_ratio_woolf_ci'))}); "
                f"der zweiseitige exakte Fisher-p-Wert betrug {_fmt(result.get('fisher_two_sided_p'))}. Das Stichprobendesign war: {design}. Diese Schätzungen beschreiben die Beobachtungen und belegen keine Kausalität. "
                "STROBE-Angaben zu Setting, Zeiträumen, Eignung, fehlenden Daten, Adjustierung, Ethik und Finanzierung müssen ergänzt werden.")
    return (
        f"The analysis included {total} records: {a + b} exposed and {c + d} unexposed. "
        f"For {exposure_label}, {a}/{a + b} participants had the {outcome_label} "
        f"({a / (a + b):.1%}); among unexposed participants, {c}/{c + d} had the outcome "
        f"({c / (c + d):.1%}). The odds ratio was {_fmt(result.get('odds_ratio'))} "
        f"(Woolf 95% CI {_fmt_ci(result.get('odds_ratio_woolf_ci'))}); the two-sided "
        f"Fisher exact p-value was {_fmt(result.get('fisher_two_sided_p'))}. "
        f"The sampling design was recorded as {design}. These estimates describe the observed "
        "table and do not establish causality. Study setting, participant eligibility, dates, "
        "missing-data handling, adjustment strategy, ethics, funding, and other STROBE items "
        "must be completed by the authors from the study record; this template does not infer them."
    )


def _fmt_ci(value: Any) -> str:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        return "not estimable"
    return f"{_fmt(value[0])} to {_fmt(value[1])}"


def comparison_markdown(counts: Sequence[int], result: Mapping[str, Any], *, language: str = "en") -> str:
    """Return a Markdown table of selected estimates and explicit methods."""
    if len(counts) != 4:
        raise ValueError("counts must contain exactly four values")
    rows = [
        ("Risk ratio", result.get("risk_ratio"), result.get("risk_ratio_katz_ci"), "Katz log interval"),
        ("Risk difference", result.get("risk_difference"), result.get("risk_difference_wald_ci"), "Wald interval"),
        ("Odds ratio", result.get("odds_ratio"), result.get("odds_ratio_woolf_ci"), "Woolf log interval"),
        ("Fisher exact p-value (two-sided)", result.get("fisher_two_sided_p"), None, "Conditional exact; probability ordering"),
    ]
    language = normalize_language(language)
    headers = {"en": ("Measure", "Estimate", "95% confidence interval", "Method"),
               "fr": ("Mesure", "Estimation", "Intervalle de confiance à 95 %", "Méthode"),
               "de": ("Maß", "Schätzung", "95%-Konfidenzintervall", "Methode")}[language]
    lines = ["| " + " | ".join(headers) + " |", "|---|---:|---:|---|"]
    for label, value, ci, method in rows:
        interval = _fmt_ci(ci) if ci is not None else "Not applicable"
        lines.append(f"| {label} | {_fmt(value)} | {interval} | {method} |")
    lines.extend(["", f"Counts (a,b,c,d): {', '.join(str(v) for v in counts)}.",
                  "Intervals are modern reference methods; exact EpiTable 6.04 parity is unverified."])
    return "\n".join(lines)


def comparison_latex(counts: Sequence[int], result: Mapping[str, Any], *, language: str = "en") -> str:
    """Return a self-contained LaTeX tabular environment (not a full document)."""
    md_rows = [
        ("Risk ratio", result.get("risk_ratio"), result.get("risk_ratio_katz_ci"), "Katz log interval"),
        ("Risk difference", result.get("risk_difference"), result.get("risk_difference_wald_ci"), "Wald interval"),
        ("Odds ratio", result.get("odds_ratio"), result.get("odds_ratio_woolf_ci"), "Woolf log interval"),
        ("Fisher exact p-value (two-sided)", result.get("fisher_two_sided_p"), None, "Conditional exact"),
    ]
    def escape(text: str) -> str:
        return text.replace("\\", r"\textbackslash{}").replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
    language = normalize_language(language)
    headers = {"en": ("Measure", "Estimate", "95\\% CI", "Method"),
               "fr": ("Mesure", "Estimation", "IC à 95\\%", "Méthode"),
               "de": ("Maß", "Schätzung", "95\\%-KI", "Methode")}[language]
    lines = [r"\begin{tabular}{lrrl}", r"\hline", " & ".join(escape(x) for x in headers) + r" \\", r"\hline"]
    for label, value, ci, method in md_rows:
        interval = _fmt_ci(ci) if ci is not None else "Not applicable"
        lines.append(f"{escape(label)} & {escape(_fmt(value))} & {escape(interval)} & {escape(method)} \\")
    lines.extend([r"\hline", r"\end{tabular}", "% Counts (a,b,c,d): " + ", ".join(str(v) for v in counts),
                  "% Modern methods; exact legacy EpiTable parity is unverified."])
    return "\n".join(lines)


def technical_payload(counts: Sequence[int], result: Mapping[str, Any], *, design: str, language: str = "en") -> str:
    """Serialize analysis provenance and results as stable, readable JSON."""
    if len(counts) != 4:
        raise ValueError("counts must contain exactly four values")
    def json_safe(value: Any) -> Any:
        if isinstance(value, float) and not math.isfinite(value):
            return "Infinity" if value > 0 else ("-Infinity" if value < 0 else None)
        if isinstance(value, Mapping):
            return {str(key): json_safe(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            return [json_safe(item) for item in value]
        return value

    payload = {
        "software": "JouriEpi: Clinical Epidemiological & Causal Inference Suite",
        "method_status": "modern_reference_calculations_legacy_parity_unverified",
        "offline_processing": True,
        "table_orientation": "exposed_cases, exposed_non_cases, unexposed_cases, unexposed_non_cases",
        "sampling_design": design,
        "language": normalize_language(language),
        "counts": list(counts),
        "results": json_safe(dict(result)),
    }
    return json.dumps(payload, indent=2, sort_keys=True, default=str, allow_nan=False)
