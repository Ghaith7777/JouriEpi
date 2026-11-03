"""Generate self-contained Python and R reproducibility scripts offline."""
from __future__ import annotations

import json
from typing import Mapping, Sequence


def export_python_script(counts: Sequence[int], *, alpha: float = 0.05, analysis_name: str = "2x2 analysis") -> str:
    """Export a standalone script using SciPy and statsmodels (no JouriEpi imports)."""
    if len(counts) != 4 or any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in counts):
        raise ValueError("counts must contain four nonnegative integers in (a,b,c,d) order")
    if not 0 < float(alpha) < 1:
        raise ValueError("alpha must be between 0 and 1")
    payload = json.dumps(list(counts))
    return f'''"""Reproducibility export: {analysis_name.replace(chr(34), chr(39))}.
Generated locally by JouriEpi. Counts use exposed/case, exposed/non-case,
unexposed/case, unexposed/non-case order. No data is transmitted.
Requires scipy and statsmodels installed locally.
"""
import json
import numpy as np
from scipy.stats import chi2_contingency, fisher_exact
from statsmodels.stats.contingency_tables import Table2x2

COUNTS = {payload}
ALPHA = {float(alpha)!r}
a, b, c, d = COUNTS
table = np.array([[a, b], [c, d]], dtype=int)
print("Counts (a,b,c,d):", COUNTS)
print("Pearson chi-square:", chi2_contingency(table, correction=False))
print("Fisher exact (two-sided):", fisher_exact(table, alternative="two-sided"))
if np.all(table.sum(axis=0) > 0) and np.all(table.sum(axis=1) > 0):
    model = Table2x2(table, shift_zeros=False)
    print("Odds ratio:", float(model.oddsratio))
    print(f"{{100*(1-ALPHA):.1f}}% OR CI:", tuple(float(x) for x in model.oddsratio_confint(alpha=ALPHA)))
else:
    print("Association estimates not estimable for a zero-margin table.")
'''


def export_r_script(counts: Sequence[int], *, alpha: float = 0.05, analysis_name: str = "2x2 analysis") -> str:
    """Export standalone base-R calculations; no package installation is required."""
    if len(counts) != 4 or any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in counts):
        raise ValueError("counts must contain four nonnegative integers in (a,b,c,d) order")
    if not 0 < float(alpha) < 1:
        raise ValueError("alpha must be between 0 and 1")
    a, b, c, d = counts
    return f'''# Reproducibility export: {analysis_name.replace(chr(10), ' ').replace(chr(13), ' ')}
# Generated locally by JouriEpi; base R only, no network calls.
# Cell order: exposed/case, exposed/non-case, unexposed/case, unexposed/non-case.
counts <- c(a={a}L, b={b}L, c={c}L, d={d}L)
alpha <- {float(alpha)!r}
tab <- matrix(c(counts["a"], counts["c"], counts["b"], counts["d"]), nrow=2,
              dimnames=list(exposure=c("Exposed", "Unexposed"), outcome=c("Case", "Non-case")))
print(counts)
print(tab)
if (all(rowSums(tab) > 0) && all(colSums(tab) > 0)) {{
  print(chisq.test(tab, correct=FALSE))
  print(fisher.test(tab, alternative="two.sided", conf.level=1-alpha))
  risk_exposed <- counts["a"] / (counts["a"] + counts["b"])
  risk_unexposed <- counts["c"] / (counts["c"] + counts["d"])
  cat("Risk ratio:", risk_exposed / risk_unexposed, "\\n")
}} else {{
  message("Association estimates not estimable for a zero-margin table.")
}}
'''


def export_reproducibility_bundle(counts: Sequence[int], *, alpha: float = 0.05, metadata: Mapping | None = None) -> dict[str, str]:
    """Return Python/R scripts and a small JSON manifest for download."""
    return {"analysis.py": export_python_script(counts, alpha=alpha),
            "analysis.R": export_r_script(counts, alpha=alpha),
            "manifest.json": json.dumps({"format": "jouriepi-reproducibility-v1", "counts": list(counts),
                                         "alpha": alpha, "metadata": dict(metadata or {}),
                                         "scripts": ["analysis.py", "analysis.R"]}, indent=2, sort_keys=True)}
