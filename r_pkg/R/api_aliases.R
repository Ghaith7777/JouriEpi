#' Canonical 2x2 association analysis
#'
#' Accepts four scalar cells, a four-element vector, a named \code{counts}
#' vector, or a 2x2 matrix/data frame. Rows are exposed and unexposed;
#' columns are cases and non-cases. Returns risk, odds and difference
#' estimates, confidence intervals and exact/asymptotic tests.
#' @name epi_2x2
#' @usage epi_2x2(a = NULL, b = NULL, c = NULL, d = NULL,
#'   conf_level = 0.95, counts = NULL, alpha = NULL,
#'   haldane_anscombe = FALSE)
#' @param a,b,c,d Scalar cell counts in exposed-case, exposed-noncase,
#'   unexposed-case, unexposed-noncase order.
#' @param counts Alternative vector or 2x2 matrix/data-frame input.
#' @param conf_level Confidence interval coverage, default 0.95.
#' @param alpha Legacy significance level; when supplied it overrides
#'   \code{conf_level}.
#' @param haldane_anscombe Whether to include a separately labelled
#'   Haldane-Anscombe odds-ratio sensitivity estimate.
#' @return A \code{jouriepi_analysis} object with estimates, inputs and methods.
#' @examples
#' fit <- epi_2x2(a = 20, b = 80, c = 10, d = 90,
#'   haldane_anscombe = TRUE)
#' fit$estimates$risk_ratio
#' fit$estimates$odds_ratio_haldane_anscombe
#' @export
NULL

#' @rdname epi_2x2
#' @export
analyze_2x2 <- epi_2x2
#' @rdname epi_2x2
#' @export
jouri_2x2 <- epi_2x2

#' Canonical Mantel-Haenszel stratified analysis
#'
#' Calculates pooled Mantel-Haenszel odds and risk ratios, RBG variance,
#' Breslow-Day/Tarone homogeneity tests, stratum-specific intervals and
#' Simpson reversal diagnostics.
#' @name epi_stratified
#' @usage epi_stratified(strata, conf_level = 0.95)
#' @param strata Non-empty list of four-cell tables in a,b,c,d order. Labels,
#'   when supplied, must be unique and non-empty.
#' @param conf_level Confidence interval coverage.
#' @return A \code{jouriepi_analysis} object containing stratum and pooled results.
#' @examples
#' fit <- epi_stratified(list(
#'   younger = c(12, 8, 6, 14), older = c(20, 10, 10, 20)
#' ))
#' fit$estimates$mantel_haenszel_odds_ratio
#' @export
NULL
#' @rdname epi_stratified
#' @export
stratified_analysis <- epi_stratified
#' @rdname epi_stratified
#' @export
jouri_stratified <- epi_stratified

#' Canonical additive interaction analysis
#'
#' Estimates RERI, attributable proportion and synergy index either from
#' four-group case/non-case counts (00, 10, 01, 11) on the implemented
#' saturated-logistic odds-ratio scale, or directly from three risk ratios.
#' Optional covariance supports delta-method intervals for direct RR inputs.
#' @name epi_interaction
#' @usage epi_interaction(counts = NULL, alpha = 0.05, rr11 = NULL,
#'   rr10 = NULL, rr01 = NULL, cov_matrix = NULL, conf_level = NULL)
#' @param counts 4x2 matrix of positive integer cases/non-cases by group.
#' @param alpha Significance level for count-based analysis.
#' @param rr11,rr10,rr01 Joint and single-exposure risk ratios.
#' @param cov_matrix Optional positive-semidefinite covariance matrix ordered
#'   rr11, rr10, rr01.
#' @param conf_level Confidence interval coverage for direct RR analysis.
#' @return A \code{jouriepi_analysis} object containing RERI, AP and SI.
#' @examples
#' epi_interaction(rr11 = 4, rr10 = 2, rr01 = 2,
#'   cov_matrix = diag(c(0.04, 0.02, 0.02)))
#' @export
NULL
#' @rdname epi_interaction
#' @export
additive_interaction <- epi_interaction
#' @rdname epi_interaction
#' @export
jouri_interaction <- epi_interaction

#' Canonical diagnostic accuracy analysis
#'
#' Computes sensitivity, specificity, predictive values, likelihood ratios,
#' diagnostic odds ratio and related measures. Wilson score intervals are
#' supplied for proportions; log-Wald intervals are used for LR and DOR.
#' @name epi_diagnostic
#' @usage epi_diagnostic(tp, fp, fn, tn, alpha = 0.05, conf_level = NULL)
#' @param tp,fp,fn,tn True-positive, false-positive, false-negative and
#'   true-negative counts.
#' @param alpha Significance level.
#' @param conf_level Optional confidence coverage; overrides alpha when set.
#' @return A \code{jouriepi_analysis} object with diagnostic metrics and intervals.
#' @examples
#' fit <- epi_diagnostic(tp = 45, fp = 5, fn = 15, tn = 135)
#' fit$estimates$sensitivity
#' @export
NULL
#' @rdname epi_diagnostic
#' @export
diagnostic_accuracy <- epi_diagnostic
#' @rdname epi_diagnostic
#' @export
jouri_diagnostic <- epi_diagnostic

#' Canonical DeLong ROC comparison
#'
#' Compares two AUCs using placement-value variance. Set \code{paired = FALSE}
#' and provide \code{outcomes2} for independent cohorts.
#' @name epi_roc_compare
#' @usage epi_roc_compare(scores1, scores2, outcomes, paired = TRUE,
#'   alpha = 0.05, outcomes2 = NULL)
#' @param scores1,scores2 Numeric diagnostic scores for the two models.
#' @param outcomes Binary outcomes for the first model (and paired subjects).
#' @param paired Whether scores are paired by subject.
#' @param alpha Significance level for the AUC difference interval.
#' @param outcomes2 Binary outcomes for the independent second cohort.
#' @return A \code{jouriepi_analysis} object with AUCs, difference, interval and test.
#' @examples
#' scores <- c(0.1, 0.9, 0.3, 0.8, 0.2, 0.7)
#' epi_roc_compare(scores, scores, c(0, 1, 0, 1, 0, 1))
#' @export
NULL
#' @rdname epi_roc_compare
#' @export
compare_roc_delong <- epi_roc_compare
#' @rdname epi_roc_compare
#' @export
jouri_roc_compare <- epi_roc_compare

#' Canonical VanderWeele-Ding E-value analysis
#'
#' Calculates the minimum unmeasured-confounding association strength needed
#' to explain away an effect estimate, after explicitly converting OR inputs
#' to the risk-ratio scale using a selected method.
#' @name epi_evalue
#' @usage epi_evalue(estimate, confidence_interval = NULL,
#'   scale = c("RR", "OR"), or_method = NULL, baseline_risk = NULL)
#' @param estimate Positive effect estimate on the selected scale.
#' @param confidence_interval Optional ordered confidence limits on the input scale.
#' @param scale Either risk ratio or odds ratio.
#' @param or_method Required OR conversion: \code{sqrt_approximation} or
#'   \code{baseline_risk}.
#' @param baseline_risk Unexposed baseline risk required by baseline-risk conversion.
#' @return A \code{jouriepi_analysis} object with point and confidence-limit E-values.
#' @examples
#' epi_evalue(estimate = 2, confidence_interval = c(1.2, 3))
#' @export
NULL
#' @rdname epi_evalue
#' @export
evalue <- epi_evalue
#' @rdname epi_evalue
#' @export
jouri_evalue <- epi_evalue

#' Canonical Cori reproduction-number estimation
#'
#' Estimates instantaneous reproduction numbers with a discretized Gamma
#' serial interval and a Gamma-Poisson sliding-window posterior.
#' @name epi_rt
#' @usage epi_rt(df, date_col, window = 7, mean_si = 4.7, std_si = 2.9,
#'   prior_shape = 1, prior_rate = 0.2, credible_level = 0.95)
#' @param df Data frame containing one observation per case.
#' @param date_col Name of the date column.
#' @param window Positive integer sliding-window width in days.
#' @param mean_si,std_si Mean and standard deviation of the Gamma serial interval.
#' @param prior_shape,prior_rate Gamma prior shape and rate.
#' @param credible_level Posterior credible interval coverage.
#' @return A \code{jouriepi_analysis} object with Rt estimates and posterior parameters.
#' @examples
#' dates <- seq(as.Date("2026-01-01"), by = "day", length.out = 8)
#' cases <- data.frame(date = rep(dates, times = c(1, 2, 3, 4, 3, 2, 2, 1)))
#' epi_rt(cases, "date", window = 3)
#' @export
NULL
#' @rdname epi_rt
#' @export
estimate_rt <- epi_rt
#' @rdname epi_rt
#' @export
jouri_rt <- epi_rt

#' Canonical Fagan post-test probability calculation
#'
#' Multiplies pre-test odds by a nonnegative likelihood ratio using a
#' log-odds calculation for numerical stability.
#' @name epi_fagan
#' @usage epi_fagan(pretest_probability, likelihood_ratio)
#' @param pretest_probability Pre-test probability strictly between zero and one.
#' @param likelihood_ratio Nonnegative likelihood ratio.
#' @return A numeric post-test probability.
#' @examples
#' epi_fagan(pretest_probability = 0.20, likelihood_ratio = 5)
#' epi_fagan(pretest_probability = 0.20, likelihood_ratio = 0)
#' @export
NULL
#' @rdname epi_fagan
#' @export
fagan_post_test_probability <- epi_fagan
#' @rdname epi_fagan
#' @export
jouri_fagan <- epi_fagan

#' Canonical paired McNemar analysis
#'
#' Computes continuity-corrected McNemar and exact conditional binomial tests
#' from paired binary outcomes.
#' @name epi_mcnemar
#' @usage epi_mcnemar(a, b, c, d, alpha = 0.05)
#' @param a,b,c,d Paired 2x2 table cells in row-major order.
#' @param alpha Significance level for the exact confidence calculation.
#' @return A \code{jouriepi_analysis} object with asymptotic and exact p-values.
#' @examples
#' fit <- epi_mcnemar(a = 20, b = 8, c = 3, d = 19)
#' fit$estimates$exact_p_value
#' @export
NULL
#' @rdname epi_mcnemar
#' @export
paired_mcnemar <- epi_mcnemar
#' @rdname epi_mcnemar
#' @export
jouri_mcnemar <- epi_mcnemar

#' Canonical decision-curve analysis
#'
#' Calculates model, treat-all and treat-none net benefit over specified
#' probability thresholds.
#' @name epi_dca
#' @usage epi_dca(predicted_probabilities, outcomes,
#'   threshold_probabilities = seq(0.01, 0.99, 0.01))
#' @param predicted_probabilities Numeric predicted risks in [0,1].
#' @param outcomes Complete binary reference outcomes.
#' @param threshold_probabilities Non-empty vector of thresholds in (0,1).
#' @return A \code{jouriepi_analysis} object containing net-benefit curves.
#' @examples
#' probabilities <- c(0.05, 0.15, 0.35, 0.65, 0.85, 0.95)
#' outcomes <- c(0, 0, 0, 1, 1, 1)
#' fit <- epi_dca(probabilities, outcomes, c(0.2, 0.5, 0.8))
#' head(fit$estimates$points)
#' @export
NULL
#' @rdname epi_dca
#' @export
decision_curve_analysis <- epi_dca
#' @rdname epi_dca
#' @export
jouri_dca <- epi_dca

#' Canonical epidemic curve aggregation
#'
#' Counts line-list observations by day or ISO week.
#' @name epi_curve
#' @usage epi_curve(df, date_col, interval = c("day", "iso_week"))
#' @param df Data frame with one row per observation/case.
#' @param date_col Name of the date column.
#' @param interval Daily or ISO-week aggregation.
#' @return A data frame of dates/weeks and case counts.
#' @examples
#' cases <- data.frame(onset = as.Date(c("2026-01-01", "2026-01-01", "2026-01-03")))
#' epi_curve(cases, "onset")
#' @export
NULL
#' @rdname epi_curve
#' @export
epicurve <- epi_curve
#' @rdname epi_curve
#' @export
jouri_curve <- epi_curve

#' Canonical line-list data-health review
#'
#' Normalizes selected date and categorical columns, removes exact duplicate
#' rows, identifies repeated identifiers and summarizes missingness/outliers.
#' @name epi_clean_linelist
#' @usage epi_clean_linelist(df, date_cols = character(),
#'   categorical_cols = character(), id_col = NULL)
#' @param df Non-empty line-list data frame.
#' @param date_cols Columns to parse as dates.
#' @param categorical_cols Character columns to trim and normalize.
#' @param id_col Optional identifier column used to flag repeated IDs.
#' @return A list containing cleaned data and a \code{jouriepi_data_health} summary.
#' @examples
#' line_list <- data.frame(
#'   id = c("P01", "P02", "P03"),
#'   onset = c("2026-01-01", "2026-01-02", "2026-01-02"),
#'   status = c("case", "control", "case "),
#'   stringsAsFactors = FALSE
#' )
#' cleaned <- epi_clean_linelist(line_list, date_cols = "onset",
#'   categorical_cols = "status", id_col = "id")
#' cleaned$data$status
#' @export
NULL
#' @rdname epi_clean_linelist
#' @export
clean_linelist <- epi_clean_linelist
#' @rdname epi_clean_linelist
#' @export
jouri_clean_linelist <- epi_clean_linelist
