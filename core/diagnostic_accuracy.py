"""Diagnostic test accuracy measures and ROC analysis.

All calculations are local. Proportion intervals include both Wald and Wilson
score intervals; likelihood-ratio and diagnostic-odds-ratio intervals use log
Wald approximations. Continuous-score AUC uses the Mann–Whitney estimator and
DeLong's placement-value variance estimate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, log, log1p, sqrt
from statistics import NormalDist
from typing import Any, Sequence


@dataclass(frozen=True)
class DiagnosticResult:
    mode: str
    counts: tuple[int, int, int, int] | None
    metrics: dict[str, float | None]
    intervals: dict[str, dict[str, tuple[float, float] | None]]
    roc_points: tuple[tuple[float, float, float], ...]
    auc: float | None
    auc_variance: float | None
    auc_ci: tuple[float, float] | None
    alpha: float


@dataclass(frozen=True)
class DeLongComparisonResult:
    """Comparison of two AUCs; covariance is paired when subjects overlap."""
    auc1: float
    auc2: float
    delta_auc: float
    standard_error_difference: float
    z_statistic: float | None
    p_value_two_sided: float | None
    covariance: float
    variance_auc1: float
    variance_auc2: float
    paired: bool
    alpha: float
    roc_points1: tuple[tuple[float, float, float], ...]
    roc_points2: tuple[tuple[float, float, float], ...]
    operating_point1: tuple[float, float] | None = None
    operating_point2: tuple[float, float] | None = None


def _placement_values(scores: Sequence[float], outcomes: Sequence[int]):
    positives = [float(s) for s, y in zip(scores, outcomes) if y == 1]
    negatives = [float(s) for s, y in zip(scores, outcomes) if y == 0]
    if not positives or not negatives:
        raise ValueError("each ROC curve must include positive and negative reference outcomes")
    v10 = [sum(1.0 if p > n else 0.5 if p == n else 0.0 for n in negatives) / len(negatives) for p in positives]
    v01 = [sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives) / len(positives) for n in negatives]
    auc = sum(v10) / len(v10)
    def sample_variance(values):
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    variance = sample_variance(v10) / len(v10) + sample_variance(v01) / len(v01)
    return auc, variance, v10, v01


def compare_roc_curves(
    scores1: Sequence[float], scores2: Sequence[float], outcomes: Sequence[int], *,
    outcomes2: Sequence[int] | None = None, paired: bool = True, alpha: float = 0.05,
) -> DeLongComparisonResult:
    """Compare two ROC AUCs with DeLong's placement-value covariance method.

    For paired comparison, both scores must belong to the same subjects and share
    the same outcome vector. For independent comparison, supply outcomes2 for the
    second sample; the variance of the difference is the sum of the AUC variances.
    Scores must be finite numeric values and outcomes must be binary 0/1.
    """
    from statistics import NormalDist
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not isfinite(float(alpha)) or not 0 < alpha < 1:
        raise ValueError("alpha must be finite and strictly between 0 and 1")
    if len(scores1) != len(outcomes) or len(scores1) < 2:
        raise ValueError("scores1 and outcomes must have equal length of at least two")
    if paired:
        if len(scores2) != len(scores1):
            raise ValueError("paired comparison requires equal-length score vectors")
        if outcomes2 is not None and len(outcomes2) != len(scores2):
            raise ValueError("paired outcomes2 must match the second score vector length")
        clean_outcomes2 = list(outcomes if outcomes2 is None else outcomes2)
    else:
        if outcomes2 is None or len(scores2) != len(outcomes2) or len(scores2) < 2:
            raise ValueError("independent comparison requires scores2 and a matching outcomes2 vector")
        clean_outcomes2 = list(outcomes2)
    def clean(scores, ys, name):
        result = []
        for i, (score, outcome) in enumerate(zip(scores, ys)):
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not isfinite(float(score)):
                raise ValueError(f"{name} score at index {i} must be finite and numeric")
            if isinstance(outcome, bool) or outcome not in (0, 1):
                raise ValueError(f"{name} outcomes must be binary 0/1")
            result.append((float(score), int(outcome)))
        if not any(y == 1 for _, y in result) or not any(y == 0 for _, y in result):
            raise ValueError(f"{name} outcomes must include both positive and negative cases")
        return [s for s, _ in result], [y for _, y in result]
    s1, y1 = clean(scores1, outcomes, "first")
    s2, y2 = clean(scores2, clean_outcomes2, "second")
    if paired and y1 != y2:
        raise ValueError("paired comparison outcomes must match subject-for-subject")
    auc1, var1, p10_1, p01_1 = _placement_values(s1, y1)
    auc2, var2, p10_2, p01_2 = _placement_values(s2, y2)
    covariance = 0.0
    if paired:
        pos1 = [v for v, y in zip(p10_1, [y for y in y1 if y == 1])]
        pos2 = [v for v, y in zip(p10_2, [y for y in y2 if y == 1])]
        neg1 = [v for v, y in zip(p01_1, [y for y in y1 if y == 0])]
        neg2 = [v for v, y in zip(p01_2, [y for y in y2 if y == 0])]
        def sample_cov(x, y):
            if len(x) < 2:
                return 0.0
            mx, my = sum(x)/len(x), sum(y)/len(y)
            return sum((a-mx)*(b-my) for a,b in zip(x,y))/(len(x)-1)
        covariance = sample_cov(pos1, pos2)/len(pos1) + sample_cov(neg1, neg2)/len(neg1)
    variance_difference = max(0.0, var1 + var2 - 2 * covariance) if paired else var1 + var2
    se = sqrt(variance_difference)
    delta = auc1 - auc2
    z = delta / se if se > 0 else (0.0 if delta == 0 else None)
    p = (2 * (1 - NormalDist().cdf(abs(z))) if z is not None else (0.0 if delta else 1.0))
    def roc(scores, ys):
        positives = sum(y == 1 for y in ys); negatives = sum(y == 0 for y in ys)
        pts = [(0.0, 0.0, float("inf"))]
        for threshold in sorted(set(scores), reverse=True):
            tp = sum(s >= threshold and y == 1 for s, y in zip(scores, ys))
            fp = sum(s >= threshold and y == 0 for s, y in zip(scores, ys))
            pts.append((fp / negatives, tp / positives, threshold))
        if pts[-1][:2] != (1.0, 1.0):
            pts.append((1.0, 1.0, float("-inf")))
        return tuple(pts)
    def operating(scores, ys):
        threshold = sorted(set(scores), reverse=True)[len(set(scores)) // 2]
        pos = sum(y == 1 for y in ys); neg = sum(y == 0 for y in ys)
        return (sum(s >= threshold and y == 0 for s,y in zip(scores,ys))/neg,
                sum(s >= threshold and y == 1 for s,y in zip(scores,ys))/pos)
    return DeLongComparisonResult(auc1, auc2, delta, se, z, p, covariance, var1, var2,
                                  paired, float(alpha), roc(s1,y1), roc(s2,y2),
                                  operating(s1,y1), operating(s2,y2))


def fagan_post_test_probability(pretest_probability: float, likelihood_ratio: float) -> float:
    """Return Bayes post-test probability from pre-test probability and an LR.

    A pre-test probability strictly between zero and one is required. Likelihood
    ratios may be zero or positive infinity to represent limiting evidence; NaN
    and negative values are rejected. Calculations use odds, not probability × LR.
    """
    if (isinstance(pretest_probability, bool) or not isinstance(pretest_probability, (int, float))
            or not isfinite(float(pretest_probability)) or not 0 < float(pretest_probability) < 1):
        raise ValueError("pretest_probability must be finite and strictly between 0 and 1")
    if (isinstance(likelihood_ratio, bool) or not isinstance(likelihood_ratio, (int, float))
            or likelihood_ratio < 0 or likelihood_ratio != likelihood_ratio):
        raise ValueError("likelihood_ratio must be nonnegative and not NaN")
    lr = float(likelihood_ratio)
    if lr == float("inf"):
        return 1.0
    if lr == 0:
        return 0.0
    log_posttest_odds = (log(float(pretest_probability)) -
                         log1p(-float(pretest_probability)) + log(lr))
    # Logistic transform on the log-odds scale avoids overflow for very large LRs.
    if log_posttest_odds >= 0:
        return 1.0 / (1.0 + exp(-log_posttest_odds))
    odds = exp(log_posttest_odds)
    return odds / (1.0 + odds)


def _proportion_interval(x: int, n: int, z: float) -> tuple[tuple[float, float] | None, tuple[float, float] | None]:
    if n <= 0:
        return None, None
    p = x / n
    se = sqrt(p * (1 - p) / n)
    wald = (max(0.0, p - z * se), min(1.0, p + z * se))
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denom
    wilson = (max(0.0, center - half), min(1.0, center + half))
    return wald, wilson


def _log_interval(value: float | None, variance: float | None, z: float):
    if value is None or variance is None or value <= 0 or variance < 0 or not isfinite(value + variance):
        return None
    se = sqrt(variance)
    return exp(log(value) - z * se), exp(log(value) + z * se)


class DiagnosticTestAccuracy:
    """Calculate DTA metrics from a 2×2 table or continuous diagnostic scores."""

    def __init__(self, alpha: float = 0.05):
        if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must be finite and strictly between 0 and 1")
        self.alpha = float(alpha)
        self.z = NormalDist().inv_cdf(1 - self.alpha / 2)

    def from_counts(self, tp: int, fp: int, fn: int, tn: int) -> DiagnosticResult:
        values = (tp, fp, fn, tn)
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in values):
            raise ValueError("TP, FP, FN and TN must be nonnegative integers")
        if sum(values) <= 0:
            raise ValueError("at least one diagnostic observation is required")
        sens, sens_w = _proportion_interval(tp, tp + fn, self.z)
        spec, spec_w = _proportion_interval(tn, tn + fp, self.z)
        ppv, ppv_w = _proportion_interval(tp, tp + fp, self.z)
        npv, npv_w = _proportion_interval(tn, tn + fn, self.z)
        sensitivity = tp / (tp + fn) if tp + fn else None
        specificity = tn / (tn + fp) if tn + fp else None
        positive_predictive = tp / (tp + fp) if tp + fp else None
        negative_predictive = tn / (tn + fn) if tn + fn else None
        lr_pos = sensitivity / (1 - specificity) if sensitivity is not None and specificity is not None and specificity < 1 else None
        lr_neg = (1 - sensitivity) / specificity if sensitivity is not None and specificity is not None and specificity > 0 else None
        dor = (tp * tn) / (fp * fn) if fp > 0 and fn > 0 else (float("inf") if tp * tn > 0 else None)
        lr_pos_var = (1 / tp - 1 / (tp + fn) + 1 / fp - 1 / (fp + tn)) if tp > 0 and fp > 0 and tp + fn > 0 and fp + tn > 0 else None
        lr_neg_var = (1 / fn - 1 / (tp + fn) + 1 / tn - 1 / (fp + tn)) if fn > 0 and tn > 0 and tp + fn > 0 and fp + tn > 0 else None
        dor_var = sum(1 / x for x in values) if all(x > 0 for x in values) else None
        metrics = {
            "sensitivity": sensitivity, "specificity": specificity,
            "ppv": positive_predictive, "npv": negative_predictive,
            "lr_positive": lr_pos, "lr_negative": lr_neg, "dor": dor,
            "prevalence": (tp + fn) / sum(values),
        }
        intervals = {
            "sensitivity": {"wald": sens, "wilson": sens_w},
            "specificity": {"wald": spec, "wilson": spec_w},
            "ppv": {"wald": ppv, "wilson": ppv_w},
            "npv": {"wald": npv, "wilson": npv_w},
            "lr_positive": {"wald": _log_interval(lr_pos, lr_pos_var, self.z), "wilson": None},
            "lr_negative": {"wald": _log_interval(lr_neg, lr_neg_var, self.z), "wilson": None},
            "dor": {"wald": _log_interval(dor, dor_var, self.z), "wilson": None},
        }
        fpr = 1 - specificity if specificity is not None else None
        roc = ((0.0, 0.0, float("inf")), (fpr, sensitivity, 0.5)) if fpr is not None and sensitivity is not None else ()
        # A single operating point cannot identify AUC; do not fabricate an ROC area.
        return DiagnosticResult("counts", values, metrics, intervals, roc, None, None, None, self.alpha)

    def from_scores(self, scores: Sequence[float], outcomes: Sequence[int]) -> DiagnosticResult:
        if len(scores) != len(outcomes) or len(scores) < 2:
            raise ValueError("scores and outcomes must have equal length of at least two")
        clean_scores: list[float] = []
        clean_outcomes: list[int] = []
        for i, (score, outcome) in enumerate(zip(scores, outcomes)):
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not isfinite(float(score)):
                raise ValueError(f"score at index {i} must be finite and numeric")
            if isinstance(outcome, bool) or outcome not in (0, 1):
                raise ValueError("gold-standard outcomes must be binary 0/1")
            clean_scores.append(float(score)); clean_outcomes.append(int(outcome))
        positives = [s for s, y in zip(clean_scores, clean_outcomes) if y == 1]
        negatives = [s for s, y in zip(clean_scores, clean_outcomes) if y == 0]
        if not positives or not negatives:
            raise ValueError("gold-standard outcome must include both positive and negative cases")
        v10 = [sum(1.0 if p > n else 0.5 if p == n else 0.0 for n in negatives) / len(negatives) for p in positives]
        v01 = [sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives) / len(positives) for n in negatives]
        auc = sum(v10) / len(v10)
        def sample_variance(vals):
            if len(vals) < 2:
                return 0.0
            mean = sum(vals) / len(vals)
            return sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
        variance = sample_variance(v10) / len(v10) + sample_variance(v01) / len(v01)
        se = sqrt(max(0.0, variance))
        auc_ci = (max(0.0, auc - self.z * se), min(1.0, auc + self.z * se))
        thresholds = sorted(set(clean_scores), reverse=True)
        roc_points: list[tuple[float, float, float]] = [(0.0, 0.0, float("inf"))]
        for threshold in thresholds:
            tp = sum(1 for s, y in zip(clean_scores, clean_outcomes) if s >= threshold and y == 1)
            fp = sum(1 for s, y in zip(clean_scores, clean_outcomes) if s >= threshold and y == 0)
            roc_points.append((fp / len(negatives), tp / len(positives), threshold))
        if roc_points[-1][:2] != (1.0, 1.0):
            roc_points.append((1.0, 1.0, float("-inf")))
        intervals: dict[str, dict[str, tuple[float, float] | None]] = {"auc": {"wald": auc_ci, "wilson": None}}
        metrics = {"sensitivity": None, "specificity": None, "ppv": None, "npv": None,
                   "lr_positive": None, "lr_negative": None, "dor": None,
                   "prevalence": len(positives) / len(clean_scores)}
        return DiagnosticResult("scores", None, metrics, intervals, tuple(roc_points), auc, variance, auc_ci, self.alpha)

