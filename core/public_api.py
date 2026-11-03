"""Stable, serializable high-level API for programmatic JouriEpi analyses."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
import math
from numbers import Integral
from typing import Any, Mapping, Sequence

import pandas as pd

from .decision_curve import analyze_decision_curve as _decision_curve
from .diagnostic_accuracy import DiagnosticTestAccuracy
from .engine_2x2 import Table2x2, analyze_2x2 as _analyze_2x2
from .interaction import analyze_additive_interaction
from .paired_analysis import mcnemar_test
from .stratification import analyze_stratified_tables, analyze_stratified_dataframe
from .causal_sensitivity import e_value
from .exporters import result_to_docx


def _integer_counts(values: Sequence[int], *, name: str = "counts") -> tuple[int, ...]:
    """Normalize Python/NumPy integer scalars without accepting float counts."""
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence of nonnegative integers") from exc
    if any(isinstance(value, bool) or not isinstance(value, Integral) or value < 0 for value in normalized):
        raise ValueError(f"{name} must contain nonnegative integers")
    return tuple(int(value) for value in normalized)


def _native_scalars(values: Sequence[Any]) -> list[Any]:
    """Convert NumPy scalar objects to Python scalars without coercing strings."""
    return [value.item() if hasattr(value, "item") else value for value in values]


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if hasattr(value, "item"):
        try:
            return _plain(value.item())
        except (ValueError, TypeError):
            pass
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def _r_value(value: Any) -> str:
    """Serialize a scalar as valid, locale-independent R source."""
    value = value.item() if hasattr(value, "item") else value
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
        return f'"{escaped}"'
    if isinstance(value, Integral):
        return str(int(value))
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("R script export requires finite numeric inputs")
        return repr(value)
    raise TypeError(f"Unsupported R script scalar: {type(value).__name__}")


@dataclass(frozen=True)
class AnalysisResult:
    """Consistent wrapper for analysis outputs and publication-friendly views."""
    analysis: str
    estimates: Mapping[str, Any]
    inputs: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"analysis": self.analysis, "estimates": _plain(self.estimates)}

    def to_dataframe(self) -> pd.DataFrame:
        payload = _plain(self.estimates)
        if not isinstance(payload, Mapping):
            return pd.DataFrame({"value": [payload]})
        rows = []
        for key, value in payload.items():
            if isinstance(value, Mapping):
                for subkey, subvalue in value.items():
                    rows.append({"measure": f"{key}.{subkey}", "estimate": str(subvalue)})
            else:
                rows.append({"measure": key, "estimate": str(value) if value is None else value})
        return pd.DataFrame(rows, columns=["measure", "estimate"])

    def to_latex(self, standalone: bool = False, *, caption: str | None = None,
                 label: str = "tab:jouriepi-results") -> str:
        """Render a booktabs table fragment or a complete standalone LaTeX document."""
        if not isinstance(standalone, bool):
            raise TypeError("standalone must be a bool")
        def tex(value: Any) -> str:
            return (str(value).replace("\\", r"\textbackslash{}").replace("&", r"\&")
                    .replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
                    .replace("{", r"\{").replace("}", r"\}"))

        def number(value: Any) -> str:
            if value is None:
                return "Not estimable"
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if not math.isfinite(float(value)):
                    return "Not estimable"
                return f"{float(value):.4f}"
            return tex(value)

        def format_p(value: Any) -> str:
            if value is None:
                return "—"
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return tex(value)
            if not math.isfinite(numeric):
                return "Not estimable"
            return "< 0.001" if numeric < 0.001 else f"{numeric:.4f}"

        estimates = _plain(self.estimates)
        if not isinstance(estimates, Mapping):
            estimates = {"estimate": estimates}
        ci_suffixes = ("haldane_anscombe_woolf_ci", "woolf_ci", "katz_ci", "wald_ci", "ci")
        excluded = {"counts", "expected_counts", "roc_points", "roc_points1", "roc_points2",
                    "confusion_matrix", "raw_matrix", "matrix", "notes", "thresholds",
                    "threshold_probabilities", "predicted_probabilities", "outcomes"}
        scalar_values: dict[str, Any] = {}
        intervals: dict[str, Any] = {}
        p_values: dict[str, Any] = {}

        def collect(mapping: Mapping[str, Any], prefix: str = "") -> None:
            for raw_key, value in mapping.items():
                key = str(raw_key)
                full_key = f"{prefix}_{key}" if prefix else key
                if key in excluded or any(token in key.lower() for token in ("roc_points", "matrix", "raw_array")):
                    continue
                if isinstance(value, Mapping):
                    collect(value, full_key)
                elif isinstance(value, (tuple, list)):
                    if len(value) == 2 and all(isinstance(x, (int, float)) or x is None for x in value):
                        base = full_key
                        for suffix in ci_suffixes:
                            if base.endswith(suffix):
                                base = base[:-len(suffix)].rstrip("_")
                                break
                        intervals[base] = value
                elif isinstance(value, (int, float)) or value is None:
                    if full_key.endswith("_p") or "p_value" in full_key:
                        p_values[full_key] = value
                    elif not full_key.endswith("_alpha"):
                        scalar_values[full_key] = value

        collect(estimates)
        table_rows = []
        consumed = set()
        for key, value in scalar_values.items():
            display = key.replace("_", " ").title()
            ci = intervals.get(key)
            p_key = next((candidate for candidate in p_values if candidate in {f"{key}_p", f"{key}_p_value"}), None)
            p_value = p_values.get(p_key) if p_key else None
            if p_key:
                consumed.add(p_key)
            table_rows.append((display, number(value),
                               f"{number(ci[0])} to {number(ci[1])}" if ci else "—",
                               format_p(p_value) if p_key else "—"))
        for key, value in p_values.items():
            if key not in consumed:
                table_rows.append((key.replace("_", " ").title(), "—", "—", format_p(value)))

        rows = []
        for metric, estimate, ci, p_value in table_rows:
            rows.append(f"{tex(metric)} & {tex(estimate)} & {tex(ci)} & {tex(p_value)} " + r"\\")
        cap = caption or self.analysis.replace("_", " ").title()
        fragment = ("% Requires \\usepackage{booktabs}\n\\begin{table}[htbp]\n\\centering\n"
                f"\\caption{{{tex(cap)}}}\n\\label{{{tex(label)}}}\n"
                r"\begin{tabular}{lrrr}" + "\n\\toprule\nMetric & Estimate & 95\\% CI & p-value " + r"\\" +
                "\n\\midrule\n" + "\n".join(rows) +
                "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n")
        if not standalone:
            return fragment
        return ("\\documentclass{article}\n\\usepackage{booktabs}\n\\begin{document}\n\n" +
                fragment.replace("% Requires \\usepackage{booktabs}\n", "") +
                "\n\\end{document}\n")

    def __str__(self) -> str:
        return f"{self.analysis}: {self.to_dataframe().to_string(index=False)}"

    def to_docx(self, *, title: str | None = None) -> bytes:
        """Return a Word dossier containing the complete result table."""
        return result_to_docx(self, title=title)

    def to_python_script(self) -> str:
        """Return a standalone script that reruns this analysis with JouriEpi."""
        import json
        payload = json.dumps(_plain(self.inputs), ensure_ascii=False, allow_nan=False, indent=2)
        dispatch = {
            "2x2": "result = analyze_2x2(**INPUTS)",
            "stratified": "result = stratified_analysis(**INPUTS)",
            "diagnostic_accuracy": "result = diagnostic_accuracy(**INPUTS)",
            "paired_mcnemar": "result = paired_mcnemar(**INPUTS)",
            "decision_curve": "result = analyze_decision_curve(**INPUTS)",
            "additive_interaction": "result = additive_interaction(**INPUTS)",
            "delong_comparison": "result = compare_roc_delong(**INPUTS)",
        }
        if self.analysis not in dispatch:
            raise NotImplementedError(f"Python reproduction export is not yet available for {self.analysis!r}")
        imports = "analyze_2x2, stratified_analysis, diagnostic_accuracy, paired_mcnemar, analyze_decision_curve, additive_interaction, compare_roc_delong"
        return ("\"\"\"Offline JouriEpi reproducibility script; install jouriepi locally.\"\"\"\n"
                f"import json\nfrom jouriepi import {imports}\nINPUTS = json.loads(r'''{payload}''')\n"
                f"{dispatch[self.analysis]}\nprint(result)\nprint(result.to_dict())\n")

    def to_r_script(self) -> str:
        """Return a reproducible script using the canonical jouriepi R API."""
        from datetime import datetime, timezone
        import json

        def r_vector(values):
            return "c(" + ", ".join(_r_value(value) for value in values) + ")"

        def r_list(mapping):
            return "list(\n" + ",\n".join(
                f"  {json.dumps(str(name), ensure_ascii=False)} = {r_vector(values)}"
                for name, values in mapping.items()
            ) + "\n)"

        def script(call: str, analysis_label: str) -> str:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            return (
                "# ==============================================================================\n"
                f"# JouriEpi Clinical Workstation - {analysis_label}\n"
                "# Engine: jouriepi (CRAN-compliant R package v1.0.0)\n"
                f"# Generated: {timestamp}\n"
                "# Author & Architect: Ghaith Baccari\n"
                "# ==============================================================================\n\n"
                "# 1. Load the standalone JouriEpi package\n"
                "if (!requireNamespace(\"jouriepi\", quietly = TRUE)) {\n"
                "  stop(\"Package 'jouriepi' is not installed. Please install 'jouriepi_1.0.0.tar.gz'.\")\n"
                "}\n"
                "library(jouriepi)\n\n"
                "# 2. Execute deterministic analysis\n"
                f"{call}\n\n"
                "# 3. Formatted clinical output\n"
                "print(res)\n"
                "summary(res)\n\n"
                "# 4. Tidy data-frame conversion\n"
                "df_results <- as.data.frame(res)\n"
                "print(df_results)\n\n"
                "# 5. LaTeX booktabs table export\n"
                "cat(to_latex(res))\n"
            )

        if self.analysis == "2x2":
            if self.inputs.get("haldane_anscombe") or self.inputs.get("include_boschloo"):
                raise NotImplementedError("The native R package does not yet reproduce Haldane-Anscombe or Boschloo sensitivity analyses")
            counts = self.inputs["counts"]
            conf_level = 1 - self.inputs.get("alpha", 0.05)
            call = f"res <- epi_2x2(a = {counts[0]}, b = {counts[1]}, c = {counts[2]}, d = {counts[3]}, conf_level = {conf_level!r})"
            return script(call, "2x2 Contingency Analysis")
        if self.analysis == "diagnostic_accuracy" and "tp" in self.inputs:
            values = ", ".join(f"{key} = {self.inputs[key]}" for key in ("tp", "fp", "fn", "tn"))
            return script(f"res <- epi_diagnostic({values}, alpha = {self.inputs.get('alpha', 0.05)!r})", "Diagnostic Test Accuracy")
        if self.analysis == "diagnostic_accuracy":
            raise NotImplementedError("The R package currently exports count-based diagnostic accuracy; score-based single-test analysis is not yet implemented in R.")
        if self.analysis == "stratified":
            strata = r_list(self.inputs["strata"])
            return script(f"strata <- {strata}\nres <- epi_stratified(strata, conf_level = 0.95)", "Stratified Analysis (Mantel-Haenszel)")
        if self.analysis == "additive_interaction":
            counts = self.inputs["counts"]
            flat = ", ".join(_r_value(value) for row in counts for value in row)
            call = (f"interaction_counts <- matrix(c({flat}), nrow = 4, byrow = TRUE)\n"
                    f"res <- epi_interaction(counts = interaction_counts, alpha = {self.inputs.get('alpha', 0.05)!r})")
            return script(call, "Additive Interaction (RERI / AP / SI)")
        if self.analysis == "paired_mcnemar":
            values = ", ".join(f"{key}={self.inputs[key]}" for key in ("a", "b", "c", "d"))
            return script(f"res <- epi_mcnemar({values}, alpha = {self.inputs.get('alpha', 0.05)!r})", "Paired 2x2 McNemar Analysis")
        if self.analysis == "decision_curve":
            probabilities = r_vector(self.inputs["predicted_probabilities"])
            outcomes = r_vector(self.inputs["outcomes"])
            thresholds = self.inputs.get("threshold_probabilities")
            threshold_arg = f", threshold_probabilities = {r_vector(thresholds)}" if thresholds is not None else ""
            return script(f"res <- epi_dca({probabilities}, {outcomes}{threshold_arg})", "Decision Curve Analysis")
        if self.analysis == "delong_comparison":
            values = self.inputs
            vectors = ", ".join(f"{key} = {r_vector(values[key])}"
                                 for key in ("scores1", "scores2", "outcomes"))
            if not values.get("paired", True) and values.get("outcomes2") is not None:
                vectors += f", outcomes2 = {r_vector(values['outcomes2'])}"
            call = (f"res <- epi_roc_compare({vectors}, paired = {str(values.get('paired', True)).upper()}, "
                    f"alpha = {values.get('alpha', 0.05)!r})")
            return script(call, "Diagnostic ROC Comparison (DeLong)")
        raise NotImplementedError(f"R reproduction export is not yet available for {self.analysis!r}")


def analyze_2x2(counts: Sequence[int] | Table2x2, *, alpha: float = 0.05,
                haldane_anscombe: bool = False, include_boschloo: bool = False) -> AnalysisResult:
    """Analyze counts in exposed-case, exposed-noncase, unexposed-case, unexposed-noncase order."""
    table = counts if isinstance(counts, Table2x2) else Table2x2(*_integer_counts(counts))
    estimates = _analyze_2x2(table, alpha, haldane_anscombe=haldane_anscombe)
    estimates["haldane_anscombe_status"] = (
        "Active" if haldane_anscombe else "Off (enable via checkbox)"
    )
    rr, rr_ci = estimates.get("risk_ratio"), estimates.get("risk_ratio_katz_ci")
    estimates["e_value"] = asdict(e_value(rr, rr_ci)) if rr is not None and rr > 0 else None
    if include_boschloo:
        from .exact_advanced import analyze_boschloo
        estimates["boschloo"] = asdict(analyze_boschloo(table))
    flat_counts = [table.a, table.b, table.c, table.d]
    return AnalysisResult("2x2", estimates, {"counts": flat_counts, "alpha": alpha,
                                               "haldane_anscombe": haldane_anscombe,
                                               "include_boschloo": include_boschloo})


def stratified_analysis(
    strata: Mapping[str, Sequence[int] | Table2x2] | pd.DataFrame,
    *, exposure_col: str | None = None, outcome_col: str | None = None,
    stratum_col: str | None = None, exposed_value: Any = 1, case_value: Any = 1,
) -> AnalysisResult:
    """Analyze named 2x2 strata or aggregate a pandas line-list DataFrame."""
    if isinstance(strata, pd.DataFrame):
        if not all((exposure_col, outcome_col, stratum_col)):
            raise ValueError("DataFrame stratification requires exposure_col, outcome_col, and stratum_col")
        result = analyze_stratified_dataframe(
            strata, exposure_col=exposure_col, outcome_col=outcome_col,
            stratum_col=stratum_col, exposed_value=exposed_value, case_value=case_value,
        )
        normalized = {item.label: list(item.counts) for item in result.strata}
    else:
        normalized = {name: ([value.a, value.b, value.c, value.d] if isinstance(value, Table2x2)
                             else list(_integer_counts(value, name=f"stratum {name!r}")))
                      for name, value in strata.items()}
        result = analyze_stratified_tables(normalized)
    return AnalysisResult("stratified", asdict(result), {"strata": normalized})


def diagnostic_accuracy(*, scores: Sequence[float] | None = None,
                        outcomes: Sequence[int] | None = None,
                        tp: int | None = None, fp: int | None = None,
                        fn: int | None = None, tn: int | None = None,
                        alpha: float = 0.05) -> AnalysisResult:
    """Calculate diagnostic metrics from continuous scores or TP/FP/FN/TN counts."""
    calculator = DiagnosticTestAccuracy(alpha=alpha)
    if scores is not None or outcomes is not None:
        if scores is None or outcomes is None:
            raise ValueError("scores and outcomes must be provided together")
        scores, outcomes = _native_scalars(scores), _native_scalars(outcomes)
        result = calculator.from_scores(scores, outcomes)
    else:
        if any(value is None for value in (tp, fp, fn, tn)):
            raise ValueError("provide scores/outcomes or all of tp, fp, fn, tn")
        tp, fp, fn, tn = _integer_counts((tp, fp, fn, tn), name="TP, FP, FN and TN")
        result = calculator.from_counts(tp, fp, fn, tn)
    inputs = ({"scores": list(scores), "outcomes": list(outcomes), "alpha": alpha}
              if scores is not None and outcomes is not None else
              {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "alpha": alpha})
    return AnalysisResult("diagnostic_accuracy", asdict(result), inputs)


def paired_mcnemar(a: int, b: int, c: int, d: int, *, alpha: float = 0.05) -> AnalysisResult:
    """Paired 2x2 McNemar analysis (reference/pre rows by comparison/post columns)."""
    a, b, c, d = _integer_counts((a, b, c, d), name="paired 2x2 counts")
    return AnalysisResult("paired_mcnemar", asdict(mcnemar_test(a, b, c, d, alpha=alpha)),
                          {"a": a, "b": b, "c": c, "d": d, "alpha": alpha})


def analyze_decision_curve(predicted_probabilities: Sequence[float], outcomes: Sequence[int],
                           threshold_probabilities: Sequence[float] | None = None) -> AnalysisResult:
    """Decision-curve net benefit at explicitly supplied or default thresholds."""
    predicted_probabilities = _native_scalars(predicted_probabilities)
    outcomes = _native_scalars(outcomes)
    threshold_probabilities = _native_scalars(threshold_probabilities) if threshold_probabilities is not None else None
    return AnalysisResult("decision_curve", asdict(_decision_curve(predicted_probabilities, outcomes, threshold_probabilities)),
                          {"predicted_probabilities": list(predicted_probabilities), "outcomes": list(outcomes),
                           "threshold_probabilities": list(threshold_probabilities) if threshold_probabilities is not None else None})


def additive_interaction(counts: Sequence[Sequence[int]], *, alpha: float = 0.05) -> AnalysisResult:
    """RERI, AP and SI from rows in exposure-group order 00, 10, 01, 11."""
    return AnalysisResult("additive_interaction", asdict(analyze_additive_interaction(counts, alpha=alpha)),
                          {"counts": [list(row) for row in counts], "alpha": alpha})


decision_curve_analysis = analyze_decision_curve


def compare_roc_delong(scores1: Sequence[float], scores2: Sequence[float], outcomes: Sequence[int],
                       *, outcomes2: Sequence[int] | None = None, paired: bool = True,
                       alpha: float = 0.05) -> AnalysisResult:
    """Compare ROC curves and return a serializable DeLong result wrapper."""
    from .diagnostic_accuracy import compare_roc_curves
    scores1, scores2, outcomes = _native_scalars(scores1), _native_scalars(scores2), _native_scalars(outcomes)
    outcomes2 = _native_scalars(outcomes2) if outcomes2 is not None else None
    result = compare_roc_curves(scores1, scores2, outcomes, outcomes2=outcomes2,
                                paired=paired, alpha=alpha)
    return AnalysisResult("delong_comparison", asdict(result), {
        "scores1": list(scores1), "scores2": list(scores2), "outcomes": list(outcomes),
        "outcomes2": list(outcomes2) if outcomes2 is not None else None,
        "paired": paired, "alpha": alpha,
    })

