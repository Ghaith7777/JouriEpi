# Modern EpiTable — Agent Specification

## Mission
Create a reproducible, offline Python implementation of core epidemiological calculations documented in the supplied Epi Info 6.04 / EpiTable distribution. Treat the original executable and help files as evidence; distinguish verified source statements from modern implementation choices. Never claim exact legacy parity until the same matrices have been run in a compatible DOS environment and outputs recorded.

## Source material
- Original installer parts: `C:\Users\Ghaith\Downloads\EPI604\epi604_1.exe`, `epi604_2.exe`, and `epi604_3.exe`.
- Extracted analysis copies are kept in `legacy_payload/` and are excluded from version control.
- Primary files: `EPITABLE.EXE`, `EPITENG.HLP`, `EPITFRA.HLP`, and `EPITABLE.CFG`.
- The English help documents risk in exposed/unexposed groups, relative risk, risk difference, attributable fraction, Fisher's exact test, Yates correction, and several confidence-interval methods.

## Rules
1. Keep all calculation and data processing local; no network calls in the application.
2. Use the epidemiological layout consistently: rows are exposed then unexposed; columns are disease/case then no disease/control. For counts `(a,b,c,d)`, RR is `(a/(a+b))/(c/(c+d))`.
3. Validate nonnegative integer counts and report undefined estimates explicitly. Never silently add a continuity correction to zero cells; offer an explicitly named Haldane–Anscombe option only where applicable.
4. Use typed, documented functions and test regular, sparse, and zero-cell matrices.
5. Do not invent EpiTable-specific algorithms. Cite extracted help file and section in `docs/REVERSE_ENGINEERING_NOTES.md`; label statistical-library behavior as modern implementation where source parity has not been proven.
6. Do not execute legacy binaries on the host. Use read-only extraction and, if available, an isolated DOS emulator for golden-output generation.

## Project structure
`core/` holds calculations and local CSV/Excel/SPSS loading; `ui/app.py` is the optional Streamlit interface; `tests/` holds regression tests and benchmark fixtures; `docs/REVERSE_ENGINEERING_NOTES.md` records evidence and open questions.

## Validation
Run `python -m pytest`. Test all formula paths, invalid input, zero denominators, sparse expected counts, DTA/Fagan/DCA boundary cases, SPSS ingestion, and file ingestion. DCA accepts predicted probabilities on [0,1], not arbitrary ranking scores. `tests/golden_benchmarks.json` must distinguish theoretical expected values from actual legacy outputs. Until legacy outputs are captured, do not call the fixtures legacy goldens.
