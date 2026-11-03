test_that("2x2 estimates preserve exposed-first orientation and exact tests", {
  x <- analyze_2x2(c(20, 80, 10, 90))
  canonical <- epi_2x2(c(20, 80, 10, 90))
  expect_identical(analyze_2x2, epi_2x2)
  expect_identical(x, canonical)
  expect_equal(x$estimates$risk_ratio, 2)
  expect_equal(x$estimates$risk_difference, 0.1)
  expect_true(is.finite(x$estimates$fisher_two_sided_p))
  expect_true(is.finite(x$estimates$pearson_p))
  expect_error(analyze_2x2(c(0, 0, 1, 2)))
  expect_equal(analyze_2x2(matrix(c(20,80,10,90),2,byrow=TRUE))$estimates$risk_ratio, 2)
  expect_equal(analyze_2x2(20, 80, 10, 90)$estimates$risk_ratio, 2)
  expect_equal(analyze_2x2(counts=c(20, 80, 10, 90))$estimates$risk_ratio, 2)
  expect_equal(analyze_2x2(counts=matrix(c(20, 80, 10, 90), 2, byrow=TRUE))$estimates$risk_ratio, 2)
  expect_equal(analyze_2x2(counts=data.frame(x=c(20,10), y=c(80,90)))$estimates$risk_ratio, 2)
  expect_error(analyze_2x2(20, 80, 10), "requires all four")
  expect_error(analyze_2x2(counts=c(20, 80, -1, 90)), "nonnegative integer")
  expect_error(analyze_2x2(counts=c(20, 80, NA_real_, 90)), "nonnegative integer")
  expect_error(analyze_2x2(counts=c(20, 80, Inf, 90)), "nonnegative integer")
  expect_error(analyze_2x2(counts=matrix(1:6,nrow=2)), "2x2")
  expect_equal(analyze_2x2(c(20,80,10,90),conf_level=.90)$estimates$risk_ratio_katz_ci,
               analyze_2x2(c(20,80,10,90),alpha=.10)$estimates$risk_ratio_katz_ci)
  expect_true(is.finite(analyze_2x2(c(0,10,2,8), haldane_anscombe=TRUE)$estimates$odds_ratio_haldane_anscombe))
})

test_that("E-values support risk ratios and explicit odds-ratio conversions", {
  x <- evalue(2, c(1.2, 3))
  expect_equal(x$estimates$e_value, 2 + sqrt(2))
  expect_equal(evalue(4, scale="OR", or_method="sqrt_approximation")$estimates$risk_ratio_estimate, 2)
  expect_equal(evalue(2, scale="OR", or_method="baseline_risk", baseline_risk=.2)$estimates$risk_ratio_estimate, 2/1.2)
  expect_error(evalue(2, scale="OR"))
  expect_error(e_value("2"))
  expect_error(e_value(2, c("1", "3")))
})

test_that("2x2 output includes Python-core directional Fisher and Yates results", {
  x <- analyze_2x2(c(25, 15, 10, 30))$estimates
  expect_equal(x$pearson_chi2, 80/7, tolerance=1e-12)
  expect_equal(x$yates_chi2, 9.955555555555556, tolerance=1e-12)
  expect_equal(x$fisher_less_p, stats::fisher.test(matrix(c(25,15,10,30),2,byrow=TRUE), alternative="less")$p.value)
  expect_equal(x$fisher_greater_p, stats::fisher.test(matrix(c(25,15,10,30),2,byrow=TRUE), alternative="greater")$p.value)
  expect_equal(x$attributable_fraction_exposed_katz_ci,
               1 - 1/x$risk_ratio_katz_ci, tolerance=1e-12)
})

test_that("zero-risk and zero-cross-product ratios remain explicitly undefined", {
  x <- analyze_2x2(c(5, 5, 0, 10))$estimates
  expect_true(is.na(x$risk_ratio))
  expect_true(is.na(x$odds_ratio))
  expect_equal(x$population_attributable_fraction, 1)
  expect_true(is.na(analyze_2x2(c(0, 10, 0, 20))$estimates$pearson_p))
})
