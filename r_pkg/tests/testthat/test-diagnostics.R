test_that("diagnostic proportions have Wilson score intervals", {
  x <- diagnostic_accuracy(40,10,5,45)
  expect_equal(x$estimates$sensitivity, 40/45)
  expect_equal(length(x$estimates$intervals$sensitivity), 2)
  expect_true(x$estimates$intervals$sensitivity[1] < x$estimates$sensitivity)
  expect_equal(diagnostic_accuracy(40,10,5,45,conf_level=.90)$estimates$intervals$sensitivity,
               diagnostic_accuracy(40,10,5,45,alpha=.10)$estimates$intervals$sensitivity)
})

test_that("diagnostic metrics and log intervals match the Python core contract", {
  x <- diagnostic_accuracy(45, 5, 15, 135)$estimates
  expect_equal(x$sensitivity, .75)
  expect_equal(x$specificity, 135/140)
  expect_equal(x$ppv, .9)
  expect_equal(x$npv, .9)
  expect_equal(x$lr_positive, 21)
  expect_equal(x$lr_negative, .25/(135/140))
  expect_equal(x$diagnostic_odds_ratio, 81)
  expect_equal(x$accuracy, 180/200)
  expect_equal(x$balanced_accuracy, (.75+135/140)/2)
  expect_equal(x$f1, 90/110)
  expect_equal(x$prevalence, 60/200)
  expect_equal(length(x$intervals$lr_positive), 2L)
  expect_equal(length(x$intervals$diagnostic_odds_ratio), 2L)
  expect_equal(x$intervals$sensitivity_wald, c(.6404346824279273,.8595653175720727), tolerance=1e-12)
})

test_that("diagnostic zero denominators are undefined rather than spuriously infinite", {
  x <- diagnostic_accuracy(0, 0, 5, 10)$estimates
  expect_true(is.na(x$ppv))
  expect_true(is.na(x$lr_positive))
  expect_equal(x$lr_negative, 1)
  expect_equal(x$false_positive_rate, 0)
  expect_equal(x$false_negative_rate, 1)
  expect_true(is.null(x$intervals$lr_positive))
  expect_error(diagnostic_accuracy(0, 0, 0, 0))
  expect_error(diagnostic_accuracy(1, 2, 3, 4, alpha=NA_real_))
  expect_error(diagnostic_accuracy(1, NA_real_, 3, 4))
})

test_that("DeLong comparison supports paired and independent samples", {
  y1 <- c(0,1,0,1,0,1); y2 <- c(0,0,1,1,0,1)
  s1 <- c(.1,.9,.3,.8,.2,.7); s2 <- c(.2,.6,.7,.9,.1,.4)
  independent <- compare_roc_delong(s1,s2,y1,paired=FALSE,outcomes2=y2)$estimates
  expect_equal(independent$auc1, 1)
  expect_equal(independent$auc2, 8/9, tolerance=1e-12)
  expect_equal(independent$standard_error, .15713484026367724, tolerance=1e-12)
  expect_equal(independent$p_value, .47950012218695326, tolerance=1e-12)
  expect_equal(independent$covariance, 0)
  expect_error(compare_roc_delong(s1,s2,y1,paired=FALSE), "outcomes2")
  expect_error(decision_curve_analysis(c(".1", ".9"), c(0,1)))
  expect_error(decision_curve_analysis(c(.1,.9), c(0,1), threshold_probabilities=numeric()))
  same <- compare_roc_delong(s1,s1,y1)$estimates
  expect_equal(same$delta_auc, 0)
  expect_equal(same$p_value, 1)
})
