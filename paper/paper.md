---
title: 'JouriEpi: An Offline-First Desktop Workstation and Dual-Core R Library for Clinical Epidemiology and Diagnostic Decision Analytics'
tags:
  - epidemiology
  - biostatistics
  - clinical decision support
  - diagnostic test accuracy
  - R
  - Python
  - reproducible research
  - offline-first
authors:
  - name: Ghaith Baccari
    affiliation: 1
affiliations:
  - name: Faculty of Medicine of Sfax, University of Sfax, Tunisia
    index: 1
date: 2026-11-03
bibliography: paper.bib
---

# Summary

JouriEpi is an offline-first software ecosystem for clinical epidemiology and diagnostic decision analytics. It combines a native PySide6 desktop workstation, backed by a Python statistical engine, with `jouriepi`, a scriptable base-R package. The desktop application is intended to make common analyses and reporting workflows accessible through a point-and-click interface, while the R package provides a reproducible programming interface for analysts who prefer script-based workflows. Both engines operate locally and are designed not to require cloud services or telemetry for analysis.

The software covers 2×2 association analysis, stratified comparisons, diagnostic accuracy, clinical decision analysis, sensitivity analysis for unmeasured confounding, and epidemiological line-list workflows. It exposes method labels, assumptions, and undefined estimates rather than silently changing the input data or applying continuity corrections. The project also generates Word and LaTeX reports and reproducibility scripts. The R package uses base R and the recommended `stats` package for its runtime statistical dependencies.

# Statement of need

Clinical epidemiology frequently involves sensitive patient-level data. Moving line lists or clinical datasets to third-party cloud services can create governance, confidentiality, jurisdiction, and institutional approval concerns. An offline-first architecture allows analysis to take place on a locally controlled workstation without requiring a remote analysis service. JouriEpi is designed around local processing and no application telemetry; this is an architectural design objective, not a substitute for an institution's security assessment, operating-system controls, or network-isolation verification.

A second need is the workflow gap between clinicians and quantitative researchers. Clinicians may need accessible, point-and-click calculations and readable reports without writing code. Biostatisticians and epidemiologists, in contrast, need scriptable methods, inspectable assumptions, reusable functions, and outputs that can be incorporated into reproducible R, LaTeX, or Word workflows. Pairing a native graphical workstation with an R package offers these complementary entry points while keeping statistical methods available outside the GUI.

Finally, clinical software should make methodological choices visible. Sparse 2×2 tables require careful handling: the optional Haldane–Anscombe adjustment is presented as a separate sensitivity estimate rather than silently replacing uncorrected estimates. Outbreak curves must distinguish cases from controls through an explicit selected case category. E-values are presented as sensitivity measures for unmeasured confounding, with odds-ratio conversion choices made explicit rather than treated as universally interchangeable. These design decisions aim to reduce avoidable analytical ambiguity; they do not guarantee that every study-specific source of bias has been addressed.

# Core mathematical and statistical features

## Association and stratification

For a 2×2 table with exposed cases, exposed non-cases, unexposed cases, and unexposed non-cases denoted by (a,b,c,d), respectively, JouriEpi reports common association measures including the odds ratio, risk ratio, risk difference, and attributable fractions when identified by the sampling design and available margins. Confidence intervals include Wald risk-difference, Woolf odds-ratio, and Katz risk-ratio procedures [@woolf1955; @katz1978]. Fisher exact inference and Pearson and continuity-corrected chi-square tests are available. Sparse-data handling is explicit, and the optional Haldane–Anscombe estimate is kept distinct from the primary uncorrected result.

For stratified 2×2 data, the software reports stratum-specific and Mantel–Haenszel summaries and provides Breslow–Day and Tarone-adjusted homogeneity diagnostics. These methods can help assess whether a pooled association conceals heterogeneity or differs from crude estimates, including patterns often discussed in relation to Simpson's paradox. Diagnostic flags are descriptive aids and should not be interpreted as proof of confounding or a causal mechanism [@mantel1959; @breslow1980].

## Diagnostic accuracy and clinical utility

The diagnostic-analysis workflows include sensitivity, specificity, predictive values, likelihood ratios, and diagnostic odds ratios. ROC areas can be compared using DeLong's method for paired predictions evaluated on the same subjects or independent cohorts, as appropriate to the data structure [@delong1988]. Fagan calculations translate pre-test probability and likelihood ratios into post-test probability using Bayesian odds updating. Decision curve analysis evaluates net benefit across user-specified threshold probabilities and compares a model with treat-all and treat-none strategies [@vickers2006].

E-values provide a sensitivity-analysis summary for the minimum strength of association that an unmeasured confounder would need to have with exposure and outcome, conditional on the framework's assumptions, to explain an observed association [@vanderweele2017]. For odds ratios, JouriEpi requires the user to select a conversion approach; the resulting sensitivity estimate should not be mistaken for a direct risk-ratio estimate in all settings.

## Line lists and outbreak dynamics

Line-list utilities support cleaning, data-health summaries, explicit category selection, and daily or weekly epidemic curves. The outbreak-curve workflow filters records to the user-selected case value before counting onset dates, preventing control records from being included merely because they have a valid date. The Python API also includes a discretized serial-interval approach and sliding-window Poisson-Gamma estimation of the instantaneous reproduction number (R_t), following the framework described by Cori and colleagues [@cori2013]. Estimates depend on the serial-interval assumptions, observation window, and completeness and timeliness of the input line list.

# Software architecture and numerical verification

The native desktop application is implemented with PySide6 and delegates calculations to a Python core separated from the presentation layer. It supports local data ingestion, interactive analysis workspaces, Word and LaTeX reporting, plot exports, and reproducibility-script generation. The R package is distributed from `r_pkg/` as `jouriepi`; its runtime imports base R and `stats` and does not require a web framework, cloud service, or compiled extension. The R package's test and documentation tooling is used during development and checking, not as a runtime dependency.

At the release-preparation verification point, the Python test suite completed with **309 passed**. The R package test suite had previously completed with **203 passed**, and the rebuilt source package completed `R CMD check --no-manual` with **Status: OK**, including its examples and `testthat` tests. The R check was performed without manual PDF generation; it should not be represented as a manual-enabled check. Test success is evidence of the exercised test cases, not proof of clinical validity, independent statistical peer review, or suitability for a regulated medical-device use.

# Acknowledgements

The author acknowledges the open-source maintainers of Python, R, PySide6, pandas, SciPy, python-docx, and the other libraries used in the software. The statistical methods are based on the literature cited below. Users and reviewers who identify reproducibility issues, numerical discrepancies, accessibility barriers, or documentation improvements are encouraged to report them through the project's issue tracker once the repository URL is established.

# Availability

The source distribution includes the native Python/PySide6 workstation, the `jouriepi` R package in `r_pkg/`, automated tests, and the documentation in this paper directory. The R source package is built as `jouriepi_1.0.0.tar.gz`; Windows builds produce an Inno Setup installer and a portable onedir archive. The software is licensed under the MIT License. The reserved Zenodo DOI for this release is [10.5281/zenodo.23914379](https://doi.org/10.5281/zenodo.23914379). The public repository URL should be added here once the maintainer publishes the source repository. The release metadata files `CITATION.cff` and `.zenodo.json` are provided to support archival and citation.

# References
