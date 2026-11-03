## Initial submission

This is the initial CRAN submission of `jouriepi` (version 1.0.0).

## Test environments

* Windows 11 x64 (build 26100)
* R 4.5.1 (2025-06-13 ucrt), x86_64-w64-mingw32
* testthat 3.3.2
* Pandoc 3.13
* TinyTeX / TeX Live 2026

## R CMD check results

Command:

```powershell
$R = "C:\Program Files\R\R-4.5.1\bin\R.exe"
$env:PATH = "$env:APPDATA\TinyTeX\TinyTeX\bin\windows;$env:LOCALAPPDATA\Pandoc;$env:PATH"
$env:LC_ALL = "C"
$env:LANG = "C"
$env:_R_CHECK_CRAN_INCOMING_REMOTE_ = "false"
& $R CMD build r_pkg
& $R CMD check --as-cran jouriepi_1.0.0.tar.gz
```

Result: **0 errors, 0 warnings, 3 notes**.

* The incoming-feasibility note identifies the maintainer and the license
  expression (`AGPL (>= 3) + file LICENSE`); the package LICENSE file supplies
  the required year and copyright holder.
* The future-file-timestamp check could not verify the current time in this
  environment.
* HTML-manual validation was skipped because HTML Tidy (`tidy`) and optional
  math rendering package `V8` are not installed. Pandoc and PDF manual checks
  both ran successfully.

Remote CRAN incoming checks were disabled for this local run because remote
feasibility/time checks are not reliable in this environment. Repeat with
network incoming checks enabled before submission.

The package installed and loaded successfully. R syntax, namespace, dependency,
S3, code-problem, Rd documentation, examples, tests and PDF manual generation
passed. The PDF manual was generated successfully (14 pages). The testthat suite
reported **203 passes, 0 failures, 0 warnings and 0 skips**. The generated PDF
reference manual contains **15 pages**.
