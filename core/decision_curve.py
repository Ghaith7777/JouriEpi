"""Decision curve analysis for binary outcomes and predicted risk scores.

Net benefit at threshold p_t is TP/N - FP/N * p_t/(1-p_t). Treat-all uses
prevalence - (1-prevalence)*p_t/(1-p_t); treat-none has net benefit zero.
Predicted scores must be calibrated or interpreted as predicted probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Sequence


@dataclass(frozen=True)
class DecisionCurvePoint:
    threshold_probability: float
    model_net_benefit: float
    treat_all_net_benefit: float
    treat_none_net_benefit: float = 0.0
    true_positives: int = 0
    false_positives: int = 0


@dataclass(frozen=True)
class DecisionCurveResult:
    n: int
    prevalence: float
    points: tuple[DecisionCurvePoint, ...]


def analyze_decision_curve(
    predicted_probabilities: Sequence[float],
    outcomes: Sequence[int],
    threshold_probabilities: Sequence[float] | None = None,
) -> DecisionCurveResult:
    """Calculate model, treat-all, and treat-none net benefit across thresholds.

    The model is classified positive when predicted probability >= threshold.
    Thresholds are strictly inside (0, 1), avoiding an undefined odds weight.
    """
    if len(predicted_probabilities) != len(outcomes) or not outcomes:
        raise ValueError("predicted probabilities and outcomes must have equal, nonzero length")
    scores: list[float] = []
    labels: list[int] = []
    for i, (score, outcome) in enumerate(zip(predicted_probabilities, outcomes)):
        if (isinstance(score, bool) or not isinstance(score, (int, float))
                or not isfinite(float(score)) or not 0 <= float(score) <= 1):
            raise ValueError(f"predicted probability at index {i} must be finite and between 0 and 1")
        if isinstance(outcome, bool) or outcome not in (0, 1):
            raise ValueError("outcomes must be binary 0/1")
        scores.append(float(score))
        labels.append(int(outcome))
    thresholds = threshold_probabilities if threshold_probabilities is not None else tuple(i / 100 for i in range(1, 100))
    clean_thresholds = sorted(set(float(t) for t in thresholds))
    if not clean_thresholds:
        raise ValueError("provide at least one threshold probability")
    if any(not isfinite(t) or not 0 < t < 1 for t in clean_thresholds):
        raise ValueError("threshold probabilities must be finite and strictly between 0 and 1")
    n = len(labels)
    prevalence = sum(labels) / n
    points = []
    for threshold in clean_thresholds:
        tp = sum(score >= threshold and y == 1 for score, y in zip(scores, labels))
        fp = sum(score >= threshold and y == 0 for score, y in zip(scores, labels))
        weight = threshold / (1 - threshold)
        points.append(DecisionCurvePoint(
            threshold, tp / n - fp / n * weight,
            prevalence - (1 - prevalence) * weight, 0.0, int(tp), int(fp)))
    return DecisionCurveResult(n, prevalence, tuple(points))
