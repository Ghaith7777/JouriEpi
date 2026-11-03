# Phase 2 statistical validation record

## Scope and status

This record distinguishes mathematical checks performed locally from external
reference validation. The implementation is in `core/stratification.py`; the
focused regression tests are in `tests/test_stratification.py`. Table cells are
`(a,b,c,d)`: exposed cases, exposed non-cases, unexposed cases, unexposed
non-cases. No continuity correction is applied.

**Independent R validation is pending.** On 2026-10-24, a live check of
`Rscript` availability returned `Rscript unavailable`; therefore neither
`epiR` nor `stats::mantelhaen.test` was run in this environment. No output is
represented as an R result. The Python tests below are internal regression
checks, not independent reference evidence. Before publication, run the
reference scripts in an authorized R environment with `epiR` installed and
archive the R version, package version, exact commands, and complete output.

## Formula and edge-case checks

The following checks are encoded in `tests/test_stratification.py`:

| Method/behavior | Dataset or expected property | Validation type |
|---|---|---|
| Mantel–Haenszel odds ratio | Strata `(12,8,6,14)` and `(20,10,10,20)`; compare with the direct weighted-sum formula | Hand calculation in Python test |
| Mantel–Haenszel risk ratio | Same two strata; compare with the direct weighted-sum formula | Hand calculation in Python test |
| Simpson's paradox flag | Strata `(80,20,9,1)` and `(1,9,20,80)`; crude OR above 1, both stratum ORs below 1 | Constructed regression case |
| Confounding flag | Strata `(20,30,10,40)` and `(5,45,20,80)`; absolute relative crude-vs-MH OR difference is at least 10% | Constructed regression case |
| Breslow–Day and Tarone | Two non-degenerate strata; statistics nonnegative, p-values within `[0,1]`, Tarone statistic no greater than uncorrected statistic | Internal invariants |
| One degree of freedom | Verify chi-square survival value against `math.erfc(sqrt(statistic / 2))` | Same-function identity, not an independent implementation |
| Zero cells | Undefined/infinite ratios are explicit; no implicit continuity correction | Regression cases |
| Line-list categories | Exactly two exposure and outcome categories; selected exposed/case values must exist; null/NaN rejected | Input validation cases |

## Independent R reference protocol (not executed here)

After installing the `epiR` package in a separate R environment, use the
following as a reproducible comparison protocol. Confirm argument orientation
against the installed package's help before interpreting outputs: EpiTable
input is exposed row first and case column first, whereas R functions may use
different table dimension conventions.

```r
packageVersion("epiR")
R.version.string

# Build each 2x2 table in the project's orientation:
# rows: exposed, unexposed; columns: case, non-case.
tab1 <- matrix(c(12, 8, 6, 14), nrow = 2, byrow = TRUE,
               dimnames = list(exposure = c("exposed", "unexposed"),
                               outcome = c("case", "noncase")))
tab2 <- matrix(c(20, 10, 10, 20), nrow = 2, byrow = TRUE,
               dimnames = list(exposure = c("exposed", "unexposed"),
                               outcome = c("case", "noncase")))

# Confirm installed epiR syntax with ?epi.2by2; record MH OR/RR and CIs.
# For a 2 x 2 x K array, check dimensions/order carefully before using:
# stats::mantelhaen.test(array_2x2xK, correct = FALSE)
mantel_array <- array(c(12, 6, 8, 14, 20, 10, 10, 20),
                      dim = c(2, 2, 2),
                      dimnames = list(exposure = c("exposed", "unexposed"),
                                      outcome = c("case", "noncase"),
                                      stratum = c("young", "older")))
stats::mantelhaen.test(mantel_array, correct = FALSE)
```

The above R snippet is a **protocol only**, not a completed comparison. Before
using it as a reference fixture, verify that the array's linear storage order
represents the intended cells; record the verified cells next to the output.
`stats::mantelhaen.test` estimates a common odds ratio and performs a
conditional test of conditional independence; it is not a drop-in reference
for every Breslow–Day/Tarone implementation detail. Obtain a separately
documented Breslow–Day result from a suitable validated R package if that
specific statistic is to be independently claimed.

## Limitations requiring review

- Breslow–Day uses a pure-Python fixed-margin noncentral hypergeometric
  calculation and a common-OR score-equation solve. It has not been compared
  against an independent numerical implementation in this environment.
- The confounding flag uses a 10% relative difference between the crude and
  Mantel–Haenszel odds ratios. This is a heuristic, not a causal conclusion;
  the percentage is undefined for zero, infinite, or unavailable crude ORs.
- Simpson's paradox is flagged only when every defined stratum OR is strictly
  on the opposite side of 1 from the crude OR. It does not establish causality.
- `None` denotes an undefined estimate; positive infinity is retained where a
  ratio diverges due to a zero denominator and positive numerator.
- No legacy EpiTable parity is claimed. No legacy executable was run.
