# JouriEpi: Clinical Epidemiological & Causal Inference Suite

**License:** GNU Affero General Public License v3.0 (AGPL-3.0). See [LICENSE](LICENSE).

**Air-Gapped, Privacy-Preserving Offline Analytical Engine**

JouriEpi is an offline-first clinical epidemiology workspace and reusable Python package for 2×2 analysis, line-list stratification, diagnostic test accuracy, causal sensitivity analysis, and publication/regulatory-style reporting. Statistical methods are documented and no exact parity with legacy EpiTable 6.04 is claimed.

## What's implemented

- Odds ratio, risk ratio, risk difference, attributable fraction among exposed, and a cohort-style population attributable fraction.
- Woolf odds-ratio, Katz risk-ratio and transformed exposed-attributable-fraction, and Wald risk-difference large-sample confidence intervals where their assumptions are satisfied. A separate binomial-proportion API provides Wilson score and Clopper–Pearson exact intervals. An optional Haldane–Anscombe odds-ratio sensitivity estimate is available only when explicitly requested.
- Pearson chi-square, Yates-corrected chi-square, lower-/upper-tail and probability-ordering two-sided Fisher exact p-values, and expected-cell-count audit.
- Diagnostic test accuracy (DTA): sensitivity, specificity, PPV, NPV, LR+/LR−, diagnostic odds ratio, Wald/Wilson intervals, continuous-score ROC and AUC with DeLong placement-value variance.
- Fagan nomogram calculations using pre-test probability and LR+/LR−, with Bayesian post-test probability derived through odds multiplication.
- Decision curve analysis for predicted risks, comparing model net benefit with treat-all and treat-none strategies over user-selected threshold probabilities.
- Shared local CSV/Excel/SPSS `.sav` loading for paths, raw duplicate-header detection where supported, line-list aggregation with explicit exposure/outcome reference values, and a native PySide6 desktop interface. The former Streamlit shell is retired and is not part of the desktop runtime.
- Transparent cohort, cross-sectional, and case-control sample-size approximations, plus approximate two-proportion power calculation.
- E-values for sensitivity analysis of unmeasured confounding, with protective-estimate and confidence-limit handling and explicit odds-ratio conversion choices.
- Stratified 2×2 analysis directly from pandas DataFrames with stratum-specific OR/RR confidence intervals, Mantel–Haenszel OR/RR, a log-OR interval/variance calculation, Breslow–Day/Tarone homogeneity tests, and an explicit effect-measure-modification flag when the unadjusted Breslow–Day p-value is below 0.05, alongside heuristic confounding/Simpson's-paradox flags. Independent R reference validation is documented but still pending.
- Boschloo unconditional exact p-values (one-sided and two-sided) through SciPy, with an actionable error if SciPy is unavailable in a custom/minimal installation.
- Paired 2×2 McNemar analysis with Edwards continuity correction, exact two-sided binomial inference for discordant pairs, paired odds ratio, and conditional exact odds-ratio limits.
- Dual-ROC DeLong comparison for two models evaluated on the same subjects (paired covariance) or independent cohorts (sum of AUC variances), with a local SVG overlay and operating-point markers.
- Eight-language interface localization: English, Français, Deutsch, العربية (RTL), Español, Русский, 中文, and 日本語. Translation coverage is continuously tested for the shared localization dictionary; some legacy explanatory copy may still require workflow-specific localization review.
- Checksummed compressed `.jepi` workspace files with JSON metadata, DataFrame CSV members, and binary assets; plus standalone Python (`SciPy`/`statsmodels`) and base-R reproducibility script exports.
- Publication & STROBE drafting view with Markdown/LaTeX tables, a narrative, a Word clinical dossier (`.docx`) with software/method provenance and embedded figures, and `audit_certificate.json` with input checksums and calculated metrics.

Analysis and report generation run locally and do not call network services. The UI supports local CSV/Excel/SPSS `.sav` files, vector SVG and PDF figure exports, and 300-DPI PNG exports; CairoSVG and pyreadstat are pinned local dependencies. An integrity certificate is a provenance aid, not proof of FDA 21 CFR Part 11 or GCP compliance.

### E-value sensitivity analysis

`core.causal_sensitivity.e_value(estimate, confidence_interval, scale="RR")` implements the risk-ratio E-value. For odds ratios, choose `scale="OR"` and explicitly select `or_method="sqrt_approximation"` (a rough approximation most defensible for common outcomes) or `or_method="baseline_risk"` with the unexposed baseline risk `baseline_risk=p0`. The methods are not interchangeable and neither is silently selected. The result records conversion metadata and the confidence-limit E-value from the confidence bound nearest the null; a CI crossing RR=1 receives a confidence-limit E-value of 1, while no supplied CI yields `None` for that field. E-values describe the confounding strength needed to explain an association under framework assumptions; they do not establish causality or rule out bias.

Reference: VanderWeele TJ, Ding P. Sensitivity Analysis in Observational Research: Introducing the E-Value. *Annals of Internal Medicine*. 2017;167(4):268-274. https://doi.org/10.7326/M16-2607.

## Install and run

Use Python 3.11 or newer in a virtual environment. Install the native Qt workstation dependencies and test tools:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ui_qt.main
```

After installation, the app can run without network access. The install step itself may need package access unless the wheels are already cached.

### Reusable Python API

Install the core library with `python -m pip install .`; install the workstation extras with `python -m pip install '.[desktop]'`. The distribution is named `jouriepi` (version `1.0.0`) and provides the `jouriepi-app` console command when desktop dependencies are installed.

```python
from jouriepi import (
    analyze_2x2,
    stratified_analysis,
    diagnostic_accuracy,
    paired_mcnemar,
    analyze_decision_curve,
    additive_interaction,
    clean_linelist,
    epicurve,
    estimate_rt,
)

association = analyze_2x2((20, 80, 10, 90))
print(association)
print(association.to_dict())
frame = association.to_dataframe()
latex_table = association.to_latex()

strata = stratified_analysis({
    "Site A": (20, 30, 10, 40),
    "Site B": (15, 25, 8, 32),
})
diagnostic = diagnostic_accuracy(tp=40, fp=10, fn=5, tn=45)
paired = paired_mcnemar(40, 4, 10, 46)
interaction = additive_interaction([(10, 90), (20, 80), (25, 75), (50, 50)])

# Headless field-epidemiology workflows
import pandas as pd
line_list = pd.DataFrame({"case_id": ["A", "B"], "onset_date": ["2026-01-01", "2026-01-02"], "district": ["North", "South"]})
cleaned, health = clean_linelist(line_list, date_cols=["onset_date"],
                                 categorical_cols=["district"], id_col="case_id")
curve = epicurve(cleaned, "onset_date", interval="iso_week")
rt = estimate_rt(cleaned, "onset_date", window=7, mean_si=4.7, std_si=2.9)
```

All analysis wrappers return an `AnalysisResult` with `.to_dict()`, `.to_dataframe()`, `.to_latex()`, `.to_docx()`, `.to_python_script()`, and `.to_r_script()` where that method has a native R implementation. The `jouriepi` namespace is headless: importing it does not import Streamlit or webview, open a browser, launch a window, or make network requests. `clean_linelist` returns the cleaned DataFrame and a structured `DataHealthSummary`; exact duplicate rows are removed, while duplicate IDs and IQR outliers are flagged rather than silently discarded. `estimate_rt` uses a discretized Gamma serial interval and a Poisson-Gamma sliding-window posterior following Cori et al. (2013). Input validation and zero-cell behavior are explicit.

### Native R package

The base-R package source is in `r_pkg/` and exposes `library(jouriepi)` with S3 `print()`, `summary()`, and `as.data.frame()` methods. It uses base R and `stats` only and has no browser, Shiny, popup, or network side effects. Some advanced stratified methods (Robins–Breslow–Greenland variance and Breslow–Day/Tarone tests) and Boschloo unconditional exact inference are not yet implemented in R; the package reports these gaps rather than substituting approximate methods. R numerical parity must be checked with `R CMD check` and shared fixtures on a host with R installed.

### Standalone Windows installer and portable package

On a Windows build machine with Python 3.13, the native Qt dependencies, PyInstaller, and Inno Setup 6, run:

```powershell
.\build_windows.ps1
```

The script creates three deliverables: the native PySide6 `--onedir --windowed` application at `dist/JouriEpi/JouriEpi.exe`, a conventional Windows setup wizard at `dist/installer/JouriEpi_Setup_v1.0.exe`, and an extract-and-run package at `dist/JouriEpi_v1.0_Portable.zip`. Inno Setup 6 is available from https://jrsoftware.org/isinfo.php. The setup wizard installs the complete Qt/Python runtime payload under Program Files, creates a Start Menu shortcut, offers an optional desktop shortcut, and registers an uninstaller. The portable ZIP must be extracted as a whole; do not distribute only the executable. No Streamlit server, localhost listener, Edge process, webview, or browser runtime is launched. Build-time Python and Inno Setup are not required on the target machine.

### Enterprise workspace features

Use the native menu bar to switch all eight interface languages (English, Français, Deutsch, العربية, Español, Русский, 中文, 日本語) and clinical dark/light themes. Arabic switches the complete Qt application to right-to-left layout. The statistical core remains a headless Python package and is never coupled to widgets.

In **Advanced analyses**, enter the matched-pair 2×2 cells to run McNemar's Edwards-corrected asymptotic test and the exact conditional binomial test. The exact paired-OR confidence interval transforms Clopper–Pearson limits for the discordant-cell probability and can have infinite endpoints. In **Diagnostic Test Accuracy**, the dual-ROC panel accepts either one file with two model scores and a shared binary outcome (paired DeLong covariance) or two independent cohort files. It reports AUCs, ΔAUC, standard error, Z and two-sided p-value and exports SVG, 300-DPI PNG, and vector PDF. The **Export Reproducibility Code** section in Publication & STROBE downloads standalone Python and R scripts; review the exported methods, assumptions, and local package versions before using them in a report.

### Native Qt workspaces

The desktop shell is implemented in `ui_qt/` with a native `QMainWindow`, `QMenuBar`, persistent collapsible sidebar, reusable metric cards, editable 2×2 contingency table, and separate workspaces for association, stratified analysis/Simpson's paradox, diagnostic accuracy/ROC/DeLong, paired McNemar analysis, additive interaction (RERI/AP/SI), line-list cleaning/outbreak curves, and publication exports. LaTeX is copied through the native system clipboard; Word dossiers and reproducibility scripts are saved through native file dialogs. Dark and light QSS themes include explicit high-contrast tooltip styling.

The legacy `ui/` directory is retained temporarily as an unshipped historical test fixture; it is excluded from the native desktop build and is not an application entry point. The production dependency set contains PySide6 Essentials, not Streamlit, QtWebEngine, or a browser runtime. The shared `core/` package is unchanged by the Qt migration.

## Count convention

| | Case / disease + | Non-case / disease − |
|---|---:|---:|
| Exposed | a | b |
| Unexposed | c | d |

The risk ratio is `(a/(a+b)) / (c/(c+d))`. Reference categories are explicit during line-list aggregation to prevent silently inverted estimates. Choose the sampling design in the UI: case-control output emphasizes the odds ratio because sampled case/control margins do not identify incidence risks by themselves.

## Evidence and parity

See `docs/REVERSE_ENGINEERING_NOTES.md` for the actual legacy files inspected, SHA-256 hashes, statements extracted from the English/French help, launcher menu/configuration evidence, and traceable published references. `tests/golden_benchmarks.json` follows `tests/golden_benchmarks.schema.json` and contains theoretical reference values with per-value arithmetic provenance; it is explicitly not a set of captured EpiTable outputs. Exact legacy parity remains pending until outputs can be captured in a compatible, isolated DOS emulator.

## Statistical scope and limitations

Confidence-interval method names are explicit in result keys. `proportion_confidence_intervals()` returns Wilson score and Clopper–Pearson exact intervals for a single binomial proportion; this does not imply exact intervals for association measures. The 2×2 association intervals are asymptotic, and exact/mid-p odds-ratio limits remain unimplemented. Stratified Mantel–Haenszel and Breslow–Day/Tarone methods are implemented in `core/stratification.py`, but their independent R reference validation is pending; the 10% confounding threshold and Simpson's-paradox flag are heuristic/direction checks, not causal conclusions. DTA likelihood-ratio and DOR intervals are log-Wald approximations; continuous-score AUC uses a DeLong placement-value variance estimate and normal-approximation CI. The E-value requires the framework's assumptions and cannot prove causality or exclude residual bias; OR conversion is explicit because its assumptions matter. Cohort/cross-sectional wrappers use the same independent two-proportion normal approximation; it requires target power of at least 0.5 and rejects alpha values too small to represent their tail probability in double precision. Complex survey, cluster, survival, and attrition adjustments are outside scope. All results are modern calculations, not claims of exact EpiTable 6.04 parity.

Fisher alternatives are defined relative to the exposed-case cell `a`: `fisher_greater_p` sums fixed-margin tables with a count at least `a`, and `fisher_less_p` sums tables with a count at most `a`. The two-sided value uses probability ordering, not simply twice the smaller tail. Expected-cell-count warnings do not silently switch the displayed test. The optional Haldane–Anscombe estimate applies a 0.5 addition to all four cells only when requested and at least one cell is zero; it never replaces the primary uncorrected estimates.

## Screenshot and interaction verification

Native Qt smoke tests run with `py -3.13 -m pytest tests/test_qt_app.py tests/test_desktop_launcher.py -q` using the offscreen Qt platform plugin. The historical Streamlit interaction fixtures remain test-only during migration and are not shipped or imported by the Qt workstation.
