epi_2x2 <- function(a = NULL, b = NULL, c = NULL, d = NULL,
                        conf_level = 0.95, counts = NULL, alpha = NULL,
                        haldane_anscombe = FALSE) {
  # Accept either four scalar cells or one vector/2x2 matrix. The named
  # counts argument remains available for callers using the earlier API.
  scalar_cells_supplied <- !is.null(b) || !is.null(c) || !is.null(d)
  first_input_supplied <- !is.null(a)
  if (!is.null(counts) && (first_input_supplied || scalar_cells_supplied)) {
    stop("supply either counts or a, b, c, d cell arguments, not both", call. = FALSE)
  }
  if (!is.null(counts)) {
    input <- counts
  } else if (!scalar_cells_supplied) {
    if (is.null(a)) stop("supply counts or all four cell counts", call. = FALSE)
    input <- a
  } else {
    if (any(vapply(list(a, b, c, d), is.null, logical(1)))) {
      stop("scalar input requires all four cell counts a, b, c, and d", call. = FALSE)
    }
    input <- c(a, b, c, d)
  }
  if (is.matrix(input) || is.data.frame(input)) {
    if (!identical(dim(input), c(2L, 2L))) stop("counts matrix/data.frame must be 2x2", call. = FALSE)
    input <- as.vector(t(as.matrix(input)))
  } else {
    input <- as.vector(input)
  }
  counts <- .validate_counts(input)
  if (length(haldane_anscombe) != 1L || is.na(haldane_anscombe) || !is.logical(haldane_anscombe))
    stop("haldane_anscombe must be TRUE or FALSE")
  if (!is.null(alpha)) {
    if (length(alpha) != 1L || !is.numeric(alpha) || !is.finite(alpha) || alpha <= 0 || alpha >= 1 || 1-alpha/2 >= 1)
      stop("alpha must be in (0,1)", call. = FALSE)
    conf_level <- 1 - alpha
  }
  if (length(conf_level) != 1L || !is.numeric(conf_level) || !is.finite(conf_level) || conf_level <= 0 || conf_level >= 1 || 1-(1-conf_level)/2 >= 1)
    stop("conf_level must be in (0,1)", call. = FALSE)
  alpha <- 1 - conf_level
  names(counts) <- c("a_exposed_cases", "b_exposed_non_cases", "c_unexposed_cases", "d_unexposed_non_cases")
  a <- unname(counts[1]); b <- unname(counts[2]); c <- unname(counts[3]); d <- unname(counts[4])
  if (a + b == 0 || c + d == 0) stop("each exposure row must have positive total")
  n1 <- a + b; n0 <- c + d; n <- sum(counts)
  p1 <- a / n1; p0 <- c / n0
  # Match the Python core's explicit undefined-ratio convention: a zero
  # denominator is not silently represented as an infinite point estimate.
  rr <- if (p0 > 0) p1 / p0 else NA_real_
  or <- if (b * c > 0) a * d / (b * c) else NA_real_
  rd <- p1 - p0
  z <- qnorm(1 - alpha / 2)
  rr_ci <- if (a > 0 && c > 0 && is.finite(rr) && rr > 0)
    exp(log(rr) + c(-1, 1) * z * sqrt(1/a - 1/n1 + 1/c - 1/n0)) else NULL
  or_ci <- if (all(counts > 0) && is.finite(or))
    exp(log(or) + c(-1, 1) * z * sqrt(sum(1/counts))) else NULL
  ha_or <- ha_ci <- NULL
  if (haldane_anscombe) {
    corrected <- counts + if (any(counts == 0)) 0.5 else 0
    ha_or <- corrected[1] * corrected[4] / (corrected[2] * corrected[3])
    ha_se <- sqrt(sum(1 / corrected))
    ha_ci <- exp(log(ha_or) + c(-1, 1) * z * ha_se)
  }
  rd_se <- sqrt(p1 * (1-p1) / n1 + p0 * (1-p0) / n0)
  rd_ci <- rd + c(-1, 1) * z * rd_se
  tab <- matrix(c(a, b, c, d), nrow = 2, byrow = TRUE)
  fisher <- stats::fisher.test(tab, alternative = "two.sided")
  expected <- outer(rowSums(tab), colSums(tab)) / n
  pearson <- if (all(expected > 0)) suppressWarnings(stats::chisq.test(tab, correct = FALSE)) else NULL
  yates <- if (all(expected > 0)) suppressWarnings(stats::chisq.test(tab, correct = TRUE)) else NULL
  population_risk <- (a + c) / n
  paf <- if (population_risk > 0) (population_risk - p0) / population_risk else NA_real_
  estimates <- list(counts = counts, risk_exposed = p1, risk_unexposed = p0,
    risk_ratio = rr, risk_ratio_katz_ci = rr_ci, odds_ratio = or,
    odds_ratio_woolf_ci = or_ci, odds_ratio_haldane_anscombe = ha_or,
    odds_ratio_haldane_anscombe_woolf_ci = ha_ci,
    risk_difference = rd, risk_difference_wald_ci = rd_ci,
    attributable_fraction_exposed = if (p1 > 0) rd/p1 else NA_real_,
    attributable_fraction_exposed_katz_ci = if (!is.null(rr_ci) && all(rr_ci > 0)) 1 - 1 / rr_ci else NULL,
    population_attributable_fraction = paf,
    fisher_less_p = unname(stats::fisher.test(tab, alternative = "less")$p.value),
    fisher_greater_p = unname(stats::fisher.test(tab, alternative = "greater")$p.value),
    fisher_two_sided_p = unname(fisher$p.value),
    pearson_chi2 = if (is.null(pearson)) NA_real_ else unname(pearson$statistic),
    pearson_p = if (is.null(pearson)) NA_real_ else unname(pearson$p.value),
    yates_chi2 = if (is.null(yates)) NA_real_ else unname(yates$statistic),
    yates_p = if (is.null(yates)) NA_real_ else unname(yates$p.value),
    expected_counts = expected, expected_any_below_5 = any(expected < 5),
    e_value = if (is.finite(rr) && rr > 0) e_value(rr, rr_ci) else NULL,
    methods = list(rr = "Katz log CI", or = "Woolf log CI", rd = "Wald CI",
                   fisher = "Fisher probability-ordering exact test"))
  .new_result("2x2", estimates, list(counts = unname(counts), alpha = alpha))
}
