## Resubmission

This is a resubmission of `jouriepi` (version 1.0.0) addressing the mandatory
review feedback from CRAN reviewer Uwe Ligges.

The requested changes have been applied:

* Changed `License` in `DESCRIPTION` to exactly `AGPL (>= 3)` and removed the
  package-level two-line template `r_pkg/LICENSE`. The repository-root
  `LICENSE` containing the complete AGPL-3 text is unchanged.
* Added the requested DOI tags to all four literature citations in the
  `Description` field: Haldane (1956), VanderWeele and Ding (2017), Vickers and
  Elkin (2006), and Cori et al. (2013). Continuation lines use four-space
  indentation.

## Test environments
* Windows 11 x64 (build 26100), R 4.5.1 ucrt
* Pandoc 3.13
* MiKTeX 25.12 (pdflatex)

The full test suite previously passed with 203 passes, 0 failures, 0 warnings,
and 0 skips. Results for this resubmission are recorded below after rebuilding
and checking the source package.

## R CMD check results
`R CMD build r_pkg` completed successfully and produced
`jouriepi_1.0.0.tar.gz`. The manual-enabled `R CMD check --as-cran`
completed with **0 errors, 0 warnings, and 2 notes**. All 203 testthat
expectations passed (0 failures, 0 warnings, 0 skips), and the PDF reference
manual was generated successfully.

The remaining notes are:

* The local environment could not verify the current time because its external
  time-server check was unavailable.
* HTML manual validation and math rendering were skipped because HTML Tidy
  (`tidy`) and the optional `V8` package are not installed locally.

The first `--as-cran` attempt could not retrieve CRAN's `Meta/archive.rds`
because the CRAN endpoint timed out. The completed check was therefore run
with `_R_CHECK_CRAN_INCOMING_REMOTE_=false` to avoid that unavailable remote
incoming check; local incoming feasibility and all other package checks
completed successfully. No package-check errors or warnings were reported.

## Downstream dependencies
There are currently no downstream dependencies as this is a new package.
