test_that("canonical epi names and compatibility aliases are direct aliases", {
  pairs <- list(
    c("epi_2x2", "analyze_2x2", "jouri_2x2"),
    c("epi_stratified", "stratified_analysis", "jouri_stratified"),
    c("epi_interaction", "additive_interaction", "jouri_interaction"),
    c("epi_diagnostic", "diagnostic_accuracy", "jouri_diagnostic"),
    c("epi_roc_compare", "compare_roc_delong", "jouri_roc_compare"),
    c("epi_evalue", "evalue", "jouri_evalue"),
    c("epi_rt", "estimate_rt", "jouri_rt"),
    c("epi_fagan", "fagan_post_test_probability", "jouri_fagan"),
    c("epi_mcnemar", "paired_mcnemar", "jouri_mcnemar"),
    c("epi_dca", "decision_curve_analysis", "jouri_dca"),
    c("epi_curve", "epicurve", "jouri_curve"),
    c("epi_clean_linelist", "clean_linelist", "jouri_clean_linelist")
  )
  for (group in pairs) {
    canonical <- getExportedValue("jouriepi", group[1])
    expect_identical(getExportedValue("jouriepi", group[2]), canonical)
    expect_identical(getExportedValue("jouriepi", group[3]), canonical)
  }
})

test_that("legacy and canonical 2x2 calls return identical structured results", {
  counts <- c(20, 80, 10, 90)
  expect_identical(analyze_2x2(counts), epi_2x2(counts))
  expect_identical(jouri_2x2(counts = counts), epi_2x2(counts = counts))
})

test_that("canonical and legacy exports all exist in the namespace", {
  expected <- c(
    "epi_2x2", "analyze_2x2", "jouri_2x2",
    "epi_stratified", "stratified_analysis", "jouri_stratified",
    "epi_interaction", "additive_interaction", "jouri_interaction",
    "epi_diagnostic", "diagnostic_accuracy", "jouri_diagnostic",
    "epi_roc_compare", "compare_roc_delong", "jouri_roc_compare",
    "epi_evalue", "evalue", "jouri_evalue",
    "epi_rt", "estimate_rt", "jouri_rt",
    "epi_fagan", "fagan_post_test_probability", "jouri_fagan",
    "epi_mcnemar", "paired_mcnemar", "jouri_mcnemar",
    "epi_dca", "decision_curve_analysis", "jouri_dca"
  )
  expect_true(all(expected %in% getNamespaceExports("jouriepi")))
})
