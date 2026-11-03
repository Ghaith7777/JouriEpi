"""Small, deterministic synthetic datasets for offline clinical demonstrations.

These are invented teaching examples, not patient data and not evidence about
real clinical performance. All values are generated locally and reproducibly.
"""
from __future__ import annotations

import pandas as pd


DEMO_DATASETS = {
    "cardiovascular": "Cardiovascular Risk Study (Cohort 2x2)",
    "roc": "Diagnostic Biomarker vs. Gold Standard (Continuous ROC/AUC)",
    "stratified": "Multicenter Trial Stratification (Simpson's / Breslow-Day)",
}


def cardiovascular_risk_study() -> pd.DataFrame:
    """Synthetic patient-level cohort with exposure and binary outcome."""
    # Counts: exposed (18 cases, 82 non-cases); unexposed (8 cases, 92 non-cases).
    return pd.DataFrame({
        "participant_id": [f"CV-{i:03d}" for i in range(1, 201)],
        "risk_exposure": [1] * 100 + [0] * 100,
        "cardiovascular_event": [1] * 18 + [0] * 82 + [1] * 8 + [0] * 92,
    })


def diagnostic_biomarker_study() -> pd.DataFrame:
    """Synthetic continuous biomarker and reference-standard outcome scores."""
    negative = [0.08, 0.12, 0.15, 0.18, 0.21, 0.24, 0.27, 0.31, 0.34, 0.37,
                0.40, 0.43, 0.46, 0.49, 0.52, 0.55, 0.58, 0.61, 0.64, 0.68]
    positive = [0.29, 0.38, 0.45, 0.51, 0.57, 0.62, 0.66, 0.70, 0.73, 0.76,
                0.79, 0.82, 0.85, 0.87, 0.89, 0.91, 0.93, 0.95, 0.97, 0.99]
    scores = negative + positive
    return pd.DataFrame({
        "participant_id": [f"BM-{i:03d}" for i in range(1, len(scores) + 1)],
        "biomarker_score": scores,
        "gold_standard": [0] * len(negative) + [1] * len(positive),
    })


def multicenter_trial_strata() -> dict[str, tuple[int, int, int, int]]:
    """Synthetic two-centre 2×2 tables for stratified and homogeneity analyses."""
    return {
        "Center A": (18, 42, 12, 48),
        "Center B": (35, 25, 28, 32),
    }


def get_demo_dataset(key: str):
    """Return a fresh synthetic demo object for a supported dataset key."""
    if key == "cardiovascular":
        return cardiovascular_risk_study()
    if key == "roc":
        return diagnostic_biomarker_study()
    if key == "stratified":
        return multicenter_trial_strata()
    raise ValueError(f"Unknown clinical demo dataset: {key}")
