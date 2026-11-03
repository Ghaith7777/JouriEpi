"""JouriEpi's stable public Python API.

All calculations execute locally. No API function performs network access.
"""
from .causal_sensitivity import EValueResult, e_value
from .decision_curve import DecisionCurvePoint, DecisionCurveResult
from .diagnostic_accuracy import DiagnosticResult, DeLongComparisonResult, DiagnosticTestAccuracy, compare_roc_curves, fagan_post_test_probability
from .engine_2x2 import Table2x2
from .interaction import AdditiveInteractionResult, analyze_additive_interaction
from .paired_analysis import McNemarResult, mcnemar_test
from .public_api import (
    AnalysisResult,
    additive_interaction,
    analyze_2x2,
    analyze_decision_curve,
    diagnostic_accuracy,
    paired_mcnemar,
    stratified_analysis,
    compare_roc_delong,
    decision_curve_analysis,
)
from .stratification import StratifiedResult, StratumResult, analyze_stratified_dataframe, analyze_stratified_line_list, analyze_stratified_tables
from .linelist import DataHealthSummary, clean_linelist
from .outbreak import RtResult, epicurve, estimate_rt

__version__ = "1.0.0"

__all__ = [
    "AnalysisResult", "Table2x2", "analyze_2x2", "stratified_analysis",
    "diagnostic_accuracy", "paired_mcnemar", "analyze_decision_curve",
    "additive_interaction", "AdditiveInteractionResult", "analyze_additive_interaction",
    "DiagnosticResult", "DeLongComparisonResult", "DiagnosticTestAccuracy",
    "compare_roc_curves", "fagan_post_test_probability", "McNemarResult",
    "mcnemar_test", "DecisionCurvePoint", "DecisionCurveResult",
    "EValueResult", "e_value", "StratumResult", "StratifiedResult",
    "analyze_stratified_tables", "analyze_stratified_line_list", "analyze_stratified_dataframe", "__version__",
    "DataHealthSummary", "clean_linelist", "RtResult", "epicurve", "estimate_rt",
    "compare_roc_delong", "decision_curve_analysis",
]
