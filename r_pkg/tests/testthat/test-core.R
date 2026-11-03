test_that("2x2 estimates use exposed then unexposed row orientation", {
  result <- analyze_2x2(c(20, 80, 10, 90))
  expect_equal(result$estimates$risk_ratio, 2, tolerance = 1e-8)
  expect_equal(result$estimates$risk_difference, 0.1, tolerance = 1e-8)
  expect_s3_class(result, "jouriepi_result")
  expect_s3_class(result, "jouriepi_analysis")
  expect_true(nrow(as.data.frame(result)) > 0)
  expect_s3_class(summary(result), "summary.jouriepi_result")
  expect_true(is.data.frame(as.data.frame(summary(result))))
  expect_match(to_latex(result), "\\\\begin\\{table\\}")
  expect_match(to_latex(summary(result)), "\\\\begin\\{table\\}")
  expect_false(grepl("\\\\documentclass", to_latex(result)))
  standalone <- to_latex(result, standalone = TRUE)
  expect_match(standalone, "\\\\documentclass\\{article\\}")
  expect_match(standalone, "\\\\usepackage\\{booktabs\\}")
  expect_match(standalone, "\\\\begin\\{document\\}")
  expect_match(standalone, "\\\\end\\{document\\}")
  expect_match(to_latex(summary(result), standalone = TRUE), "\\\\documentclass")
  expect_error(to_latex(result, standalone = NA), "standalone must be TRUE or FALSE")
})

test_that("LaTeX and console output apply fixed precision to scalars and vectors", {
  result <- epi_2x2(22, 23, 66, 77)
  latex <- to_latex(result, digits = 3, standalone = TRUE)
  expect_match(latex, "\\\\documentclass\\{article\\}")
  expect_true(grepl("risk\\_ratio\\_katz\\_ci & 0.748 to 1.499", latex, fixed = TRUE))
  expect_true(grepl("expected\\_counts & 21.064, 66.936, 23.936, 76.064", latex, fixed = TRUE))
  table_text <- sub("(?s).*\\\\begin\\{tabular\\}\\{lr\\}(.*?)\\\\end\\{tabular\\}.*", "\\1", latex, perl = TRUE)
  numeric_tokens <- regmatches(table_text, gregexpr("(?<![A-Za-z])[-+]?[0-9]+\\.[0-9]+", table_text, perl = TRUE))[[1]]
  expect_true(all(nchar(sub("^.*\\.", "", numeric_tokens)) <= 3L))

  interval_result <- .new_result("precision_test", list(
    katz_ci = c(-0.3360071, 0.3329064),
    expected_counts = matrix(c(12.345678, 7.654321), nrow = 1),
    fisher_p = 0.00001,
    ordinary_p = 0.04204,
    estimate = 1.23456
  ))
  formatted <- as.data.frame(interval_result)
  expect_equal(formatted$estimate[formatted$measure == "katz_ci"], "-0.3360 to 0.3329")
  expect_equal(formatted$estimate[formatted$measure == "expected_counts"], "12.3457, 7.6543")
  expect_equal(formatted$estimate[formatted$measure == "fisher_p"], "< 0.001")
  expect_equal(formatted$estimate[formatted$measure == "ordinary_p"], "0.0420")
  expect_equal(formatted$estimate[formatted$measure == "estimate"], "1.2346")
  interval_latex <- to_latex(interval_result, digits = 3)
  expect_true(grepl("fisher\\_p & < 0.001", interval_latex, fixed = TRUE))
  expect_true(grepl("ordinary\\_p & 0.042", interval_latex, fixed = TRUE))

  printed <- capture.output(print(result))
  summary_printed <- capture.output(print(summary(result)))
  expect_false(any(grepl("[0-9]\\.[0-9]{5,}", printed)))
  expect_false(any(grepl("[0-9]\\.[0-9]{5,}", summary_printed)))
})

test_that("Fagan calculation is Bayesian odds multiplication", {
  expect_equal(fagan_post_test_probability(0.2, 4), 0.5, tolerance = 1e-10)
  expect_equal(fagan_post_test_probability(.2, 1e300), 1, tolerance=1e-12)
})

test_that("line-list cleaning removes exact duplicates and flags repeated IDs", {
  frame <- data.frame(id=c("a","b","b","c","c"), date=c("2026-01-01","2026-01-02","2026-01-03","2026-01-04","2026-01-04"), site=c(" X ","Y","Y ","Z","Z"), age=c(20,21,22,23,23))
  cleaned <- clean_linelist(frame, "date", "site", "id")
  expect_equal(nrow(cleaned$data), 4)
  expect_equal(cleaned$health$exact_duplicate_rows_removed, 1)
  expect_equal(cleaned$health$duplicate_id_rows, 2)
  expect_equal(cleaned$data$site[1], "X")
})

test_that("epicurve and Cori estimator return finite nonnegative incidence and Rt", {
  frame <- data.frame(date=rep(seq(as.Date("2026-01-01"), by="day", length.out=20), each=2))
  curve <- epicurve(frame, "date")
  expect_equal(sum(curve$cases), nrow(frame))
  rt <- estimate_rt(frame, "date", window=7)
  expect_equal(nrow(rt$estimates), 14)
  expect_true(all(rt$estimates$rt_lower <= rt$estimates$rt_upper))
  expect_true(all(rt$estimates$posterior_shape > 0))
  expect_true(all(rt$estimates$posterior_rate > 0))
  expect_true(is.data.frame(as.data.frame(rt)))
})

test_that("Cori estimator supports a single-day window", {
  frame <- data.frame(date=as.Date(c("2026-01-01","2026-01-01","2026-01-02")))
  x <- estimate_rt(frame, "date", window=1)
  expect_equal(nrow(x$estimates), 2L)
  expect_equal(x$estimates$cases_in_window, c(2,1))
  expect_error(estimate_rt(frame, "date", window=3))
})

test_that("diagnostic and paired analyses return S3 result objects", {
  dta <- diagnostic_accuracy(40, 10, 5, 45)
  expect_equal(dta$estimates$sensitivity, 40/45)
  paired <- paired_mcnemar(40, 4, 10, 46)
  expect_true(is.finite(paired$estimates$p_value))
})
