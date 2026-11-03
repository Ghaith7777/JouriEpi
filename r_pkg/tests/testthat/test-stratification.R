test_that("stratified analysis reports MH, RBG and homogeneity results", {
  x <- stratified_analysis(list(one=c(10,20,30,40), two=c(20,30,40,50)))
  expect_true(is.finite(x$estimates$mantel_haenszel_odds_ratio))
  expect_true(length(x$estimates$mantel_haenszel_odds_ratio_ci) == 2)
  expect_true(is.finite(x$estimates$breslow_day_p_value))
})

test_that("stratum-specific intervals and Haldane-Anscombe sensitivity are returned", {
  x <- stratified_analysis(list(A=c(4,6,0,10), B=c(3,7,2,8)))$estimates$strata[[1]]
  expect_true(is.infinite(x$odds_ratio))
  expect_equal(x$odds_ratio_haldane_anscombe, (4.5*10.5)/(6.5*.5))
  expect_null(x$odds_ratio_ci)
  expect_null(x$risk_ratio_ci)
})

test_that("Simpson flag requires a true directional reversal", {
  x <- stratified_analysis(list(A=c(10,10,5,10), B=c(20,10,10,10)))$estimates
  expect_false(x$simpsons_paradox_detected)
  paradox <- stratified_analysis(list(high=c(80,20,9,1), low=c(1,9,20,80)))$estimates
  expect_gt(paradox$crude_odds_ratio, 1)
  expect_true(all(vapply(paradox$strata, function(s) s$odds_ratio < 1, logical(1))))
  expect_true(paradox$simpsons_paradox_detected)
  duplicate_names <- list(c(1,1,1,1), c(2,2,2,2))
  names(duplicate_names) <- c("A","A")
  expect_error(stratified_analysis(duplicate_names), "unique")
})
