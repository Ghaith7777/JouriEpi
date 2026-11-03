## Initial submission

This is the initial CRAN submission of `jouriepi` (version 1.0.0).

## Test environments

* Windows 11 x64 (build 26100)
* R 4.5.1 (ucrt), x86_64-w64-mingw32
* testthat 3.3.2
* Pandoc 3.13
* MiKTeX 25.12 (`pdflatex`)

The package test suite completed with 203 passes, 0 failures, 0 warnings and
0 skips.

## R CMD check results

`R CMD build r_pkg` completed successfully. The full manual-enabled command
`R CMD check --as-cran jouriepi_1.0.0.tar.gz` completed with **0 errors,
0 warnings and 3 NOTEs**. The PDF reference manual was generated successfully
(`checking PDF version of manual ... OK`, 109 seconds).

The package installed successfully, loaded and unloaded cleanly, passed R-code
analysis, passed all Rd syntax/metadata/usage checks, ran all examples, and
passed all 203 testthat expectations.

The remaining NOTEs are: (1) standard CRAN incoming feasibility note for a new
submission; (2) inability to verify the current time in this environment; and
(3) HTML manual validation/math rendering skipped because HTML Tidy (`tidy`)
and the optional `V8` package are unavailable. Pandoc was detected and used.

There were no errors or warnings. Review the remaining notes before submission;
HTML manual validation can be completed by installing HTML Tidy and `V8`.
