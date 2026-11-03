# JouriEpi v1.0.0 — Release Notes

**Release date:** 2026-11-03  
**License:** GNU Affero General Public License v3.0 (AGPL-3.0)
**Status:** Windows build and executable startup smoke test verified; this metadata update does not create a new binary build or release tag.

## Overview

JouriEpi v1.0.0 combines a native, offline-first PySide6 clinical epidemiology workstation with a scriptable Python analysis core and the `jouriepi` base-R package. The desktop application is intended for local workflows and does not require a hosted analysis service. The R package is built on base R and `stats` at runtime. The software is a research and analytical aid; it is not a certified medical device and does not replace clinical, statistical, privacy, or institutional review.

## Main capabilities

- 2×2 association analysis: odds ratio, risk ratio, risk difference, attributable fractions, Wald/Woolf/Katz intervals, Pearson and Yates chi-square tests, and Fisher exact inference.
- Explicit sparse-data behavior, including an optional Haldane–Anscombe sensitivity estimate kept separate from uncorrected primary estimates.
- Stratified analysis with Mantel–Haenszel summaries and Breslow–Day/Tarone homogeneity diagnostics.
- Diagnostic test accuracy, ROC/AUC analysis, paired and independent DeLong comparisons, Fagan post-test probability calculations, and Vickers-style decision curve analysis.
- E-value sensitivity analysis with explicit odds-ratio conversion choices.
- Line-list cleaning, data-health summaries, selected-case outbreak curves, and Cori-style sliding-window instantaneous reproduction-number estimation.
- Native Qt workspaces, local data import, Word/LaTeX reports, plot exports, and Python/R reproducibility scripts.
- `jouriepi` R package functions, S3 result methods, Rd documentation, deterministic examples, and `testthat` coverage.

## Audit fixes included

- Outbreak curves now count only the explicitly selected case/status category; date, status, ID, and category selection changes recalculate the view. The reproducibility R script applies the same case filter.
- Word and LaTeX report p-values below 0.001 display as `< 0.001`, avoiding misleading `0.0000` output.
- Word dossiers embed a 300-DPI association forest plot when the required estimates and intervals are available; the Qt association view offers PNG and PDF plot export.
- R package copyright attribution was aligned with the package maintainer metadata, and examples were added for `epi_clean_linelist`, `epi_curve`, `epi_dca`, `epi_mcnemar`, and `epi_fagan`.
- Removed obsolete installer helper scripts that referenced the legacy `JouriEpiServer.exe` and restricted the Inno Setup installer to x64 architecture.

## Verification evidence

- Python: **314 tests passed** using Python 3.13.5 (`py -3.13 -m pytest tests/ -ra`).
- R: **203 tests passed** in the package's `testthat` suite in the recorded package verification.
- R package: `R CMD build r_pkg` succeeded; `R CMD check --no-manual jouriepi_1.0.0.tar.gz` completed with **Status: OK** (zero errors and zero warnings).
- The R check omitted manual PDF generation; it is not a claim that a manual-enabled CRAN check passed.
- Windows clean build: `powershell -ExecutionPolicy Bypass -File .\build_windows.ps1 -Clean` completed successfully on 2026-11-03 with PyInstaller 6.22.3 and Inno Setup 6.
- Native executable smoke test: the rebuilt `JouriEpi.exe` initialized and exposed the `JouriEpi Clinical Workstation` main window. The first close request did not exit within 15 seconds; a subsequent close request completed gracefully within 20 seconds. An exit code was not captured.
- Installer Authenticode status: **NotSigned**. Sign the installer before broad public distribution.

## Distribution formats

The Windows build script produces:

- `dist/installer/JouriEpi_Setup_v1.0.exe` — Inno Setup installer.
- `dist/JouriEpi_v1.0_Portable.zip` — complete portable onedir application folder.
- `dist/JouriEpi/JouriEpi.exe` — native application executable within its required bundled runtime folder.
- `jouriepi_1.0.0.tar.gz` — R source package tarball.

### Verified Windows release artifacts (2026-11-03)

Sizes are exact file sizes in bytes. SHA-256 values were recomputed from the completed clean-build artifacts.

| Artifact | Size (bytes) | SHA-256 |
|---|---:|---|
| `dist/installer/JouriEpi_Setup_v1.0.exe` | 96,769,124 | `c27e7f6223ba11e5ae36030d694d2707c277e728c16f898f4f861490c511ff91` |
| `dist/JouriEpi_v1.0_Portable.zip` | 142,716,860 | `82ca71ef02ec8406fc0ff3a839f9b0450087a3fcf47e67c4cfe407f951ab7be6` |
| `dist/JouriEpi/JouriEpi.exe` | 20,883,939 | `08c124a26099545a36ba2dff454073b97868ab4947218bf561337c240042322e` |

The portable archive must be extracted as a whole; distributing only the executable is unsupported. Windows code signing, clean-machine installation/uninstallation, and target-machine clinical workflow validation should be completed before broad deployment.

## Known scope and limitations

- Statistical outputs depend on correct input coding, study design, missingness handling, and method assumptions. Users should verify methods against the analysis plan and relevant literature.
- Heuristic confounding/Simpson's-paradox flags are descriptive diagnostics, not causal conclusions.
- E-values do not establish causality or rule out selection, measurement, or other biases.
- The R check was run with `--no-manual`; manual PDF generation requires a LaTeX toolchain.
- A passing automated suite does not constitute independent clinical validation, regulatory clearance, or a complete security certification.

## Citation

Please cite the software using the repository's `CITATION.cff` and archive DOI [10.5281/zenodo.23914379](https://doi.org/10.5281/zenodo.23914379). The project is distributed under the GNU Affero General Public License v3.0 (AGPL-3.0); see the complete root `LICENSE` file.
