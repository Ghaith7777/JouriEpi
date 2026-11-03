#' JouriEpi Clinical Epidemiology and Biostatistics
#'
#' Deterministic, offline-first statistical methods for clinical epidemiology
#' and biostatistics. The package uses base R and the recommended \pkg{stats}
#' package and has no graphical, browser, or network side effects.
#'
#' @name jouriepi
#' @aliases jouriepi e_value to_latex
#' @usage
#' e_value(estimate, confidence_interval = NULL)
#' to_latex(x, ..., standalone = FALSE)
#' @param estimate Positive risk-ratio estimate or odds ratio when scale is OR.
#' @param confidence_interval Optional ordered confidence limits on the input
#'   scale.
#' @param x A jouriepi result object.
#' @param ... Additional result-method arguments, including optional caption,
#'   label and digits formatting controls.
#' @param standalone Logical; if TRUE, generates a full standalone document ready for direct PDF compilation. Defaults to FALSE.
#' @return Statistical functions return a \code{jouriepi_analysis} S3 object;
#'   \code{clean_linelist} returns cleaned data and a data-health summary.
#' @details
#'   \strong{2x2 association.} For exposed cases/non-cases \eqn{a,b} and
#'   unexposed cases/non-cases \eqn{c,d}, risks are \eqn{R_1=a/(a+b)} and
#'   \eqn{R_0=c/(c+d)}; the risk ratio is \eqn{R_1/R_0}, odds ratio is
#'   \eqn{ad/(bc)}, and risk difference is \eqn{R_1-R_0}. Katz, Woolf and
#'   Wald intervals are large-sample approximations. Fisher tests condition on
#'   fixed margins and use the probability-ordering two-sided definition. Zero
#'   denominators are returned as undefined rather than silently corrected.
#'   Haldane-Anscombe correction is an explicitly requested, separately labelled
#'   OR sensitivity estimate. Risk and attributable fractions require cohort
#'   sampling for population interpretation and are not identified by
#'   case-control sampling alone.
#'
#'   \strong{Stratification.} The Mantel-Haenszel OR is
#'   \eqn{\sum_i a_i d_i/n_i \,/\, \sum_i b_i c_i/n_i}; the pooled RR is
#'   \eqn{\sum_i a_i(c_i+d_i)/n_i \,/\, \sum_i c_i(a_i+b_i)/n_i}.
#'   The Robins-Breslow-Greenland log-variance gives an approximate log-scale
#'   interval. Breslow-Day and Tarone tests assess homogeneity of stratum ORs
#'   under fixed margins and may be unreliable with sparse tables. Simpson's
#'   paradox is flagged when every stratum-specific OR lies on the opposite
#'   side of one from the crude OR; an outside-range diagnostic is reported
#'   separately.
#'
#'   \strong{Additive interaction.} Four-group counts are ordered 00, 10, 01,
#'   11. The count-based implementation estimates saturated logistic ORs and
#'   computes OR-scale RERI = OR11 - OR10 - OR01 + 1, AP = RERI/OR11, and
#'   SI = (OR11 - 1)/((OR10 - 1) + (OR01 - 1)). Delta-method Wald intervals use
#'   the covariance of log-OR contrasts. These OR-scale quantities are not
#'   risk-ratio-scale causal interaction measures when outcomes are common.
#'   Alternatively, direct RR inputs may be supplied with a positive
#'   semidefinite covariance matrix.
#'
#'   \strong{Diagnostics and sensitivity.} Wilson score and clipped Wald
#'   intervals are provided for sensitivity, specificity, PPV and NPV;
#'   likelihood-ratio and diagnostic-odds-ratio intervals use log-Wald
#'   approximations and are unavailable at zero-cell boundaries. DeLong AUC
#'   comparisons use placement-value covariance for paired subjects, or sum
#'   independent variances when a second outcome vector is supplied. E-values
#'   implement \eqn{RR + \sqrt{RR(RR-1)}} after orienting RR to be at least
#'   one. OR inputs require an explicit square-root approximation or baseline
#'   risk conversion. E-values quantify a sensitivity threshold and do not
#'   establish causality or eliminate other bias.
#'
#'   \strong{Outbreak analysis.} The Cori estimator discretizes a Gamma serial
#'   interval over day bins \eqn{(k-1,k]} and calculates infectiousness as the
#'   weighted sum of prior incidence. For each sliding window, the posterior
#'   is Gamma with shape equal to prior shape plus incident cases and rate equal
#'   to prior rate plus infectiousness. Results depend on the serial-interval
#'   distribution, window and prior; they are not a substitute for checking
#'   reporting delays, imported cases or changing transmission conditions.
#'
#'   Statistical functions return a \code{jouriepi_analysis} object containing
#'   \code{analysis}, \code{estimates} and \code{inputs}. Print, summary and
#'   data-frame methods preserve the structured estimates; \code{to_latex}
#'   exports a compact booktabs table. All calculations are local and headless.
#' @examples
#' tab <- analyze_2x2(20, 80, 10, 90)
#' tab$estimates$risk_ratio
#' strat <- stratified_analysis(list(
#'   younger = c(12, 8, 6, 14), older = c(20, 10, 10, 20)
#' ))
#' strat$estimates$mantel_haenszel_odds_ratio
#' diagnostic_accuracy(tp = 45, fp = 5, fn = 15, tn = 135)
#' additive_interaction(matrix(c(20, 80, 40, 60, 30, 70, 60, 40),
#'   nrow = 4, byrow = TRUE))
#' evalue(estimate = 2, confidence_interval = c(1.2, 3))
#' scores <- c(.1, .9, .3, .8, .2, .7)
#' compare_roc_delong(scores, scores, c(0, 1, 0, 1, 0, 1))
#' dates <- seq(as.Date("2026-01-01"), by = "day", length.out = 8)
#' cases <- data.frame(date = rep(dates, times = c(1, 2, 3, 4, 3, 2, 2, 1)))
#' estimate_rt(cases, "date", window = 3)
#' @seealso \code{stats::fisher.test}, \code{stats::chisq.test},
#'   \code{stats::qgamma}
#' @keywords epidemiology
#' @export e_value
#' @export to_latex
#' @importFrom stats aggregate cov pgamma pnorm qgamma qnorm quantile var
NULL
