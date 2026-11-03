---
title: 'JouriEpi: A Dual-Engine Clinical Workstation and CRAN-Compliant R Library for Epidemiological Analysis'
tags:
  - epidemiology
  - biostatistics
  - clinical research
  - R
  - Python
  - decision curve analysis
authors:
  - name: Ghaith Baccari
    orcid: ""
    affiliation: 1
affiliations:
  - name: Faculté de Médecine de Sfax, Université de Sfax
    index: 1
date: 03 November 2026
archive_doi: "10.5281/zenodo.23914379"
bibliography: paper.bib
---

# Summary

JouriEpi is an offline-first software project for epidemiological and clinical research. It combines a native desktop workstation, implemented in Python and Qt, with a separately installable R package. The desktop application gives clinicians and researchers a graphical environment for common epidemiological calculations, diagnostic test evaluation, line-list exploration, and report generation. The R package provides a scriptable interface for reproducible analyses in R workflows. Both engines are designed to perform analysis locally, without requiring a hosted service or transmitting study data to an application telemetry endpoint.

The software brings together methods that are often used at different stages of a clinical epidemiology workflow: 2×2 association measures, stratified summaries, diagnostic accuracy, receiver operating characteristic (ROC) analysis, decision curve analysis, sensitivity analysis for unmeasured confounding, and outbreak line-list summaries. It provides explicit method names and exposes undefined or non-estimable results instead of silently changing input cells or substituting an undocumented calculation. Outputs include structured results, plots, Word and LaTeX reports, and reproducibility scripts. JouriEpi is research software and does not provide clinical recommendations, establish causality, or replace statistical review and clinical validation.

# Statement of need

Clinical epidemiology teams often combine data preparation, statistical calculations, interpretation, and reporting across several tools. This can create friction between users who need an accessible graphical workflow and analysts who need transparent, scriptable calculations. It can also complicate governance when study data cannot be transferred to external services. JouriEpi addresses this workflow problem by pairing a locally executed desktop interface with a reusable R library, while keeping calculations in inspectable statistical code.

The intended users include clinical researchers, epidemiologists, public-health practitioners, and biostatisticians working with observational studies, diagnostic evaluations, and outbreak line lists. A clinician can use the workstation to inspect a contingency table and export a report; an analyst can use the R package and retain analysis steps in a version-controlled script. The two interfaces do not imply that every feature is implemented identically in both languages: known scope differences are documented, and parity should be judged from shared numerical fixtures and method-specific tests rather than assumed.

A local-first design is useful where data governance requires processing on an institutionally controlled computer. It does not itself guarantee confidentiality: operating-system access controls, backups, encryption, network policy, and institutional review remain the responsibility of the deploying organization. The application is designed without application telemetry or a required remote analysis service; this architectural property is not presented as a substitute for an independent security assessment.

# State of the field

Epi Info has historically combined data-entry forms, database construction, epidemiological analysis, mapping, and visualization for public-health practice. The US Centers for Disease Control and Prevention announced that product development and technical assistance would end after September 2025, while noting that existing desktop versions could remain operational [@epiinfoCDC]. JouriEpi does not attempt to reproduce Epi Info's broad surveillance and form-design environment. Instead, it concentrates on a narrower set of clinical epidemiology calculations and report workflows in a native workstation paired with a scriptable R interface.

OpenEpi provides web-based epidemiological and statistical calculators intended for public-health applications [@sullivan2009]. Its calculator-oriented delivery is useful for focused analyses, but differs from JouriEpi's integrated desktop workflow and reusable local R package. Users handling restricted data should still assess the data flow and deployment model of any web-based tool before entering study information.

The R package epiR provides a broad collection of functions for epidemiological and surveillance data, including measures of disease frequency, stratified associations, confidence intervals, and sample-size calculations [@stevenson2026]. It is an established and substantial alternative for users comfortable with R. JouriEpi should not be understood as replacing epiR or claiming methodological superiority. Its contribution is the combination of a native graphical workstation, a companion R package with a smaller documented scope, local report generation, and an explicit interface for common clinical analysis tasks. Contributing relevant methods upstream to established projects remains preferable where the requirements align; the paired desktop-and-library workflow and its local reporting integration are the reasons for maintaining this complementary project.

# Software design

## Mathematical and architectural design

The desktop application separates presentation from statistical computation. A Qt-based interface collects inputs and displays results, while a Python core performs calculations and returns structured outputs. The R package is maintained as a separate package under r_pkg/, with base R and stats as its runtime dependencies. This separation allows the graphical application to evolve without embedding statistical logic in widgets, and allows R users to call supported methods without launching a desktop session.

For a 2×2 table, cells are ordered as exposed cases, exposed non-cases, unexposed cases, and unexposed non-cases, denoted by (a,b,c,d). The odds ratio is calculated as ad/bc, while cohort risk ratios compare a/(a+b) with c/(c+d). The software reports the risk difference alongside these measures where the sampling design identifies risks. Confidence intervals use named procedures, including Woolf, Katz, and Wald methods [@woolf1955; @katz1978]. The interface distinguishes uncorrected estimates from an optional Haldane–Anscombe sensitivity estimate; the correction is not silently applied to the primary result. Fisher exact and chi-square procedures are exposed as distinct tests.

For stratified tables, the software calculates stratum-specific estimates and Mantel–Haenszel summaries, with Breslow–Day/Tarone diagnostics for homogeneity [@mantel1959; @breslow1980]. Diagnostic workflows include sensitivity, specificity, predictive values, likelihood ratios, diagnostic odds ratios, ROC areas, and DeLong comparisons [@delong1988]. Decision curve analysis reports net benefit over selected threshold probabilities and compares model strategies with treat-all and treat-none approaches [@vickers2006]. E-values are provided as sensitivity measures for unmeasured confounding, with explicit choices when converting odds ratios [@vanderweele2017]. Line-list utilities support cleaning, data-health summaries, epidemic curves, and a sliding-window reproduction-number estimate based on the Cori framework [@cori2013].

The design favors transparent method selection over automatic correction. Undefined estimates, zero-cell behavior, sampling-design limitations, and assumptions are surfaced to users. This makes some outputs less convenient than a single automatically adjusted number, but preserves the distinction between observed data and sensitivity analyses. The R package intentionally has a smaller feature set than the Python engine; unsupported advanced procedures are not silently replaced by approximate alternatives.

## Software validation

The release verification record reports 314 passing automated Python tests and 203 passing R testthat tests. The Python suite exercises statistical calculations, input validation, reporting, and Qt application behavior. R tests cover the functions implemented in the package, including shared numerical reference cases. The source package was also checked with R CMD check --no-manual, which completed with Status: OK and zero errors or warnings. The --no-manual option means that PDF manual generation was not tested because a LaTeX toolchain was not part of that check.

These tests provide repeatable evidence for the behaviors they exercise; they do not demonstrate clinical validity, complete cross-language parity, or independent statistical peer review. In particular, advanced stratified methods in the Python engine have not all received independent reference validation in R. Users should verify the selected estimand, study design, assumptions, and analysis plan before interpreting results.

# Research impact statement

No independent institutional adoption or external publication using JouriEpi is claimed at this release stage. The near-term research contribution is a reproducible, inspectable implementation with automated test suites in both languages, documented numerical conventions, and distributable source and desktop artifacts. These materials allow reviewers and prospective users to examine calculations and rerun supported tests rather than relying on screenshots or untraceable calculator output. Evidence of external use, integration, and research publications should be added as it becomes available; the existence of tests and a release archive should not be mistaken for demonstrated community adoption.

# AI usage disclosure

Generative AI tools were used to assist with software development tasks, documentation editing, metadata preparation, and drafting and revising this software paper. The author remains responsible for the software and manuscript. Numerical claims in this paper are tied to the project's recorded automated test results and package-check output; AI-generated descriptions and edits require maintainer review against source code, test fixtures, and the cited literature before submission. AI assistance is not presented as independent validation.

# Acknowledgements

The author acknowledges the maintainers and contributors of Python, R, Qt/PySide6, pandas, SciPy, and the other open-source libraries used by JouriEpi. The statistical methods are attributed to the publications cited below. No external financial support is identified in this manuscript; funding and institutional acknowledgements should be updated if applicable.

# Availability

JouriEpi is available from the public source repository at https://github.com/Ghaith7777/JouriEpi and is archived at [https://doi.org/10.5281/zenodo.23914379](https://doi.org/10.5281/zenodo.23914379). The project is distributed under the GNU Affero General Public License, version 3 (AGPL-3.0). The repository contains the native Python/Qt workstation, the jouriepi R package, automated tests, build scripts, and documentation. The Windows installer and portable archive are generated from the source tree; the R package source is provided separately. Users should consult the README for installation instructions and documented feature limitations.

# References
