---
title: 'Modern EpiTable: An Offline Python Framework for Epidemiological 2×2 Analysis and Bias Auditing'
tags:
  - epidemiology
  - contingency tables
  - exact tests
  - sensitivity analysis
  - reproducible research
  - Python
authors:
  - name: 'AUTHOR NAME REQUIRED'
    affiliation: 'AFFILIATION REQUIRED'
    orcid: 'ORCID OPTIONAL'
date: '2026-10-24'
repository: 'REPOSITORY URL REQUIRED BEFORE SUBMISSION'
license: 'LICENSE MUST BE CONFIRMED BEFORE SUBMISSION'
---

# Summary

Modern EpiTable is a local-first Python application for epidemiological 2×2
contingency-table analysis, line-list aggregation, study-planning approximations,
and transparent reporting. It is informed by a forensic review of supplied Epi
Info 6.04 EpiTable help and distribution files, but it does not claim exact
numerical parity with the legacy executable. The implementation makes its cell
orientation explicit: (a) is exposed cases, (b) exposed non-cases, (c)
unexposed cases, and (d) unexposed non-cases. It reports undefined estimates
explicitly and never silently adds a continuity correction.

The core package uses Python's standard library for its primary 2×2 engine,
E-values, stratified analysis, and report formatting. CSV/Excel ingestion and the
Streamlit interface use optional dependencies. Boschloo's unconditional exact
test is implemented as an optional SciPy integration and cannot run unless a
compatible SciPy is installed. All application analysis is designed to run
locally without network requests.

# Statement of need

Researchers and analysts often need to turn clinical line-list data into
auditable contingency tables, understand what their sampling design permits
them to estimate, and carry method-labelled results into a report. A result
screen alone can hide the table orientation, reference categories, sparse-cell
behavior, method choice, and limitations. Modern EpiTable emphasizes explicit
exposure/outcome categories, source-file fingerprints, stale-result
invalidation, transparent formula/method labels, optional sensitivity analysis,
and publication outputs that do not invent unobserved study details.

The application is a modern reference implementation, not a validated clone of
EpiTable 6.04. The supplied legacy help is evidence for documented concepts;
exact algorithm parity remains unverified until the same matrices can be run in
an isolated compatible DOS environment and their outputs captured.

# Software design

The `core/` package separates validated statistical functions from presentation
and file-ingestion code. `core/engine_2x2.py` defines the count contract and
common association measures; `core/causal_sensitivity.py` calculates E-values;
`core/stratification.py` calculates stratum-specific and Mantel–Haenszel
estimates, a Breslow–Day/Tarone homogeneity audit, and heuristic confounding and
Simpson's-paradox flags; `core/exact_advanced.py` wraps SciPy's Boschloo test
behind a version check; and `core/strobe_export.py` builds a results narrative,
Markdown/LaTeX comparison tables, and a provenance-labelled JSON payload. The
Streamlit UI remains a thin interaction and reporting layer. Statistical
calculations do not require the UI and the base project dependency list remains
empty.

# Functionality

- Risk, odds, risk-difference, attributable-fraction, and Fisher/Pearson/Yates
  results for 2×2 tables, with explicit interval method names.
- Optional Haldane–Anscombe sensitivity output, kept separate from uncorrected
  primary estimates.
- E-values for unmeasured-confounding sensitivity analysis with explicit odds
  ratio conversion choices.
- Stratified Mantel–Haenszel summaries, a Breslow–Day/Tarone calculation, and
  automated flags that are labelled as heuristics rather than causal findings.
- Optional Boschloo one-sided and two-sided p-values through compatible SciPy.
- Local CSV/Excel preview, explicit binary category mapping, content
  fingerprinting, missing-value blocking, and four-cell handoff to analysis.
- A Streamlit interface for analysis, line-list aggregation, sample-size/power
  approximations, and publication-oriented STROBE-style text/table exports.
- TXT, CSV, PNG, Markdown, LaTeX, and JSON export paths, depending on the view.

# Example

With counts `(25, 15, 7, 30)`, the exposed risk is (25/(25+15)=0.625), the
unexposed risk is (7/(7+30)\approx0.189), and the odds ratio is
((25\times30)/(15\times7)\approx7.14). These are descriptive measures; their
interpretation depends on study design, data quality, and substantive
assumptions. Run `python -m pytest` for the project tests and `streamlit run
ui/app.py` for the local UI.

# Verification and limitations

The repository includes tests for formula-level properties, sparse/zero-cell
behavior, line-list validation, user-interface workflows, and report formatting.
The independent R reference protocol is documented in
`docs/PHASE2_STATISTICAL_VALIDATION.md`; it has **not** been executed in the
current environment because `Rscript` is unavailable. SciPy was also unavailable
at the time of the phase audit, so Boschloo's numerical integration tests are
conditional and its runtime results remain unverified here. The current
test-suite count must be taken from the recorded final test run, not copied from
historical reports.

The UI's clipboard control uses the browser Clipboard API when available and a
`document.execCommand('copy')` fallback otherwise. Permissions, insecure
contexts, embedded-component restrictions, or browser policy may block either
path; a visible fallback message and downloadable files remain available. UI
tests do not certify that a real browser saved a file or accepted a clipboard
write. Authored color contrast checks are not a complete accessibility audit.
No network-isolation penetration test or legacy executable run is claimed.

The confounding percentage threshold is a heuristic; Simpson's-paradox flags
describe reversal patterns rather than causal mechanisms. Breslow–Day/Tarone
calculations need independent comparison against trusted R output before being
described as independently validated. The STROBE-style paragraph is a drafting
aid, not a STROBE compliance checker; authors must supply missing study details.

# Availability and metadata requiring completion

Before public submission, the maintainer must fill in the author/affiliation,
confirm the license, provide the repository URL, and archive the exact source
revision and environment used for the final test run. These values are left as
explicit placeholders rather than fabricated. No publication, package release,
or independent peer review is claimed.

# Acknowledgements and references

The project draws on concepts in the supplied Epi Info 6.04 help files and
modern statistical literature. Relevant references include:

- VanderWeele TJ, Ding P. Sensitivity Analysis in Observational Research:
  Introducing the E-Value. *Annals of Internal Medicine*. 2017;167(4):268–274.
  <https://doi.org/10.7326/M16-2607>
- Clopper CJ, Pearson ES. The use of confidence or fiducial limits illustrated
  in the case of the binomial. *Biometrika*. 1934;26(4):404–413.
  <https://doi.org/10.1093/biomet/26.4.404>
- Woolf B. On estimating the relation between blood group and disease.
  *Annals of Human Genetics*. 1955;19(4):251–253.
  <https://doi.org/10.1111/j.1469-1809.1955.tb01348.x>
- Katz D, Baptista J, Azen SP, Pike MC. Obtaining confidence intervals for the
  risk ratio in cohort studies. *Biometrics*. 1978;34(3):469–474.
  <https://doi.org/10.2307/2530610>
