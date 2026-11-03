# jouriepi

**Deterministic Clinical Epidemiology and Biostatistics Engine**

jouriepi is a headless, offline-first R package for clinical epidemiology and
biostatistics. Its public functions accept ordinary R vectors, matrices, and
data frames and return structured jouriepi_analysis S3 objects. It does not
start Shiny, a browser, a GUI, a server, or a network connection.

The package imports only the recommended stats package. testthat and roxygen2
are suggested development tools.

## Included methods

- 2x2 risk ratio, odds ratio, risk difference, Katz/Woolf/Wald intervals,
  Fisher exact and Pearson chi-square tests, and explicitly requested
  Haldane-Anscombe odds-ratio correction.
- Mantel-Haenszel pooled odds and risk ratios, Robins-Breslow-Greenland
  log-variance, Breslow-Day and Tarone homogeneity tests, and Simpson reversal
  diagnostics, stratum-specific intervals and separately labelled
  Haldane-Anscombe sensitivity estimates.
- Additive interaction on the validated Python core's four-group logistic
  odds-ratio scale, or direct RERI/AP/SI calculations from supplied risk ratios
  and an optional covariance matrix.
- Diagnostic sensitivity, specificity, predictive values, likelihood ratios,
  diagnostic odds ratio, accuracy/F1 measures, Wilson and Wald proportion
  intervals, and log-scale likelihood-ratio/diagnostic-odds intervals.
- VanderWeele-Ding E-values with explicit odds-ratio conversion choices.
- Daily/ISO-week epidemic curves and Cori-style Gamma-Poisson instantaneous
  reproduction-number estimates.
- Paired McNemar, Fagan post-test probability, decision-curve analysis,
  paired or independent DeLong ROC comparison, and line-list data-health review.
- Console printing, summaries, data-frame conversion, and LaTeX booktabs export.

## Quick start

From the repository root:

\`\`\`sh
R CMD INSTALL r_pkg
\`\`\`

\`\`\`r
library(jouriepi)

# Rows: exposed then unexposed. Columns: cases then non-cases.
x <- epi_2x2(c(20, 80, 10, 90))
print(x)
summary(x)
as.data.frame(x)
to_latex(x, caption = "Exposure and outcome association")

# Matrix input is also supported.
epi_2x2(counts = matrix(c(20, 80, 10, 90), nrow = 2, byrow = TRUE))

# Stratified analysis.
s <- epi_stratified(list(
  age_group_1 = c(10, 20, 30, 40),
  age_group_2 = c(20, 30, 40, 50)
))
s$estimates$mantel_haenszel_odds_ratio
s$estimates$breslow_day_p_value

# Risk-ratio-scale additive interaction.
epi_interaction(
  rr11 = 4, rr10 = 2, rr01 = 2,
  cov_matrix = diag(c(0.04, 0.02, 0.02))
)

# Diagnostic accuracy.
epi_diagnostic(tp = 40, fp = 10, fn = 5, tn = 45)

# E-value from a risk ratio and its confidence interval.
epi_evalue(estimate = 2, confidence_interval = c(1.2, 3))

# Independent ROC cohorts must provide outcomes2.
epi_roc_compare(
  scores1 = c(.1, .9, .3, .8, .2, .7),
  scores2 = c(.2, .6, .7, .9, .1, .4),
  outcomes = c(0, 1, 0, 1, 0, 1),
  paired = FALSE,
  outcomes2 = c(0, 0, 1, 1, 0, 1)
)
\`\`\`

## Canonical names and compatibility aliases

All analytical entry points use the `epi_*` prefix as their canonical API.
Existing function names remain fully supported, and each canonical function
also has a `jouri_*` alias. These are direct function aliases (not wrappers),
so their arguments, return values and behavior remain identical. For example,
`analyze_2x2(...)`, `jouri_2x2(...)` and `epi_2x2(...)` call the same function.
The low-level `e_value()` helper and `to_latex()` formatter remain available.
## Validation

Run the test suite and package checks from the repository root:

\`\`\`sh
Rscript -e "roxygen2::roxygenise('r_pkg')"
R CMD INSTALL r_pkg
Rscript -e "library(jouriepi); testthat::test_dir('r_pkg/tests/testthat')"
R CMD build r_pkg
R CMD check jouriepi_1.0.0.tar.gz --no-manual
\`\`\`

The parity tests include numeric reference values from the Python core for the
2x2, E-value, stratified, and additive-interaction benchmarks. The R package
check also validates installation, namespace loading, documentation, examples,
and the testthat runner.
