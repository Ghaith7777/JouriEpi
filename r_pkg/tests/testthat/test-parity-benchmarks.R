test_that("Python core benchmark tables agree to 1e-4", {
  x <- analyze_2x2(c(647,2,622,27))$estimates
  expect_equal(x$odds_ratio, 14.042604501607718, tolerance=1e-12)
  expect_equal(x$risk_ratio, 1.040192926045016, tolerance=1e-12)
  expect_equal(x$risk_difference, 0.03852080123266566, tolerance=1e-12)
  expect_equal(x$fisher_two_sided_p, 1.2806738280483774e-06, tolerance=1e-12)
  ev <- evalue(x$risk_ratio, x$risk_ratio_katz_ci)$estimates
  expect_equal(ev$e_value, 1.2446639444047731, tolerance=1e-12)
  expect_equal(ev$confidence_limit_e_value, 1.1767368732924848, tolerance=1e-12)
  stratified <- stratified_analysis(list(A=c(10,20,30,40), B=c(20,30,40,50)))$estimates
  expect_equal(stratified$mantel_haenszel_odds_ratio, 0.7647058823529411, tolerance=1e-12)
  expect_equal(stratified$breslow_day_p_value, 0.7004699665801429, tolerance=1e-12)
  expect_equal(stratified$tarone_corrected_p_value, 0.7004702805198855, tolerance=1e-12)
  expect_equal(stratified$mantel_haenszel_odds_ratio_log_variance, 0.07918552036199095, tolerance=1e-12)
})

test_that("stratified MH, RBG and Breslow-Day outputs match executed Python core", {
  x <- stratified_analysis(list(A=c(12,8,6,14), B=c(20,10,10,20)))$estimates
  expect_equal(x$mantel_haenszel_odds_ratio, 3.7906976744186047, tolerance=1e-12)
  expect_equal(x$mantel_haenszel_risk_ratio, 2, tolerance=1e-12)
  expect_equal(x$mantel_haenszel_odds_ratio_log_variance, .17935177853898016, tolerance=1e-12)
  expect_equal(x$mantel_haenszel_odds_ratio_ci, c(1.6528588560032424,8.693657541690559), tolerance=1e-10)
  expect_equal(x$breslow_day_statistic, .0238905423737922, tolerance=1e-12)
  expect_equal(x$breslow_day_tarone_statistic, .02388954397230461, tolerance=1e-12)
  expect_equal(x$breslow_day_p_value, .8771637461730721, tolerance=1e-12)
  expect_equal(x$tarone_corrected_p_value, .8771662925293053, tolerance=1e-12)
})

test_that("four-group additive interaction matches executed Python core", {
  x <- additive_interaction(matrix(c(20,80,40,60,30,70,60,40), nrow=4, byrow=TRUE))$estimates
  expect_equal(x$odds_ratio_10, 2.6666666666666665, tolerance=1e-12)
  expect_equal(x$odds_ratio_01, 1.7142857142857142, tolerance=1e-12)
  expect_equal(x$odds_ratio_11, 6, tolerance=1e-12)
  expect_equal(unname(x$reri), 2.6190476190476195, tolerance=1e-12)
  expect_equal(unname(x$attributable_proportion), .43650793650793657, tolerance=1e-12)
  expect_equal(unname(x$synergy_index), 2.1, tolerance=1e-12)
  expect_equal(x$reri_ci, c(-.22125749546458584,5.459352733559825), tolerance=1e-4)
})

test_that("VanderWeele-Ding E-values match executed Python core", {
  x <- evalue(2, c(1.2,3))$estimates
  expect_equal(x$e_value, 3.414213562373095, tolerance=1e-12)
  expect_equal(x$confidence_limit_e_value, 1.6898979485566354, tolerance=1e-12)
  expect_equal(x$risk_ratio_confidence_interval, c(1.2,3))
  expect_false(x$confidence_interval_includes_null)
  expect_equal(x$conversion_method, "none (risk ratio input)")
  expect_equal(evalue(1, c(.8,1.2))$estimates$confidence_limit_e_value, 1)
})

test_that("Cori Rt estimates and serial-interval weights match executed Python core", {
  dates <- seq(as.Date("2026-01-01"), by="day", length.out=12)
  daily_cases <- c(1,2,3,5,4,6,7,5,4,3,2,1)
  frame <- data.frame(date=rep(dates, times=daily_cases))
  x <- estimate_rt(frame, "date", window=7)
  expect_equal(x$estimates$infectiousness[1], 5.896293, tolerance=1e-6)
  expect_equal(x$estimates$rt_mean[1], 4.756989, tolerance=1e-6)
  expect_equal(x$estimates$rt_lower[1], 3.185830, tolerance=1e-6)
  expect_equal(x$estimates$rt_upper[1], 6.638099, tolerance=1e-6)
  expect_equal(x$inputs$serial_interval_weights[1:5],
    c(.03803275578083408,.12208713319129166,.16154078257486754,.16054168634055585,.13864861550785967),
    tolerance=1e-12)
})
