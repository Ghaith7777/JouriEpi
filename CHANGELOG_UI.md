# UI redesign changelog

## Clinical research interface

- Replaced the single long page with persistent sidebar navigation for **2×2 Analysis**, **Line list → 2×2**, and **Sample size & power**.
- Added a calm teal-and-neutral design system, responsive cards, visible keyboard focus, and a session-only/offline indicator. Fonts are system-provided; no external assets or requests are used.
- Added presentation-only helpers for number, p-value, confidence-interval, and percentage formatting. Statistical calculations remain in `core/` unchanged.
- Reorganized 2×2 input around exposed/unexposed rows, case/non-case columns, editable integer cells, computed totals, design-specific measure availability, confidence-level feedback, and Haldane–Anscombe sensitivity notes.
- Replaced raw JSON with metric cards, a formatted measure table, offline SVG forest plot, test table, expected-count audit, plain-language descriptive summary, and text/CSV/SVG downloads.
- Added line-list row/column/missing-value preview, column mapping, explicit category selection, guarded aggregation, a visible 2×2 result, and a handoff action to the analysis view.
- Added explicit empty states, validation feedback, sample-size cards, achieved power, an offline SVG power curve, and an assumptions statement.
- Charts shown inline are self-contained SVG. The downloadable forest plot is a local PNG rendered with Pillow, which is already present in the Streamlit environment; no new runtime dependency was added.
- Added formatting and default-example regression tests. The existing calculation modules are untouched.

## Known UI limitations

- The forest plot is provided inline as SVG and as a PNG download. The chart renderer uses Pillow primitives rather than a dedicated plotting library to avoid adding a dependency.
- The default Streamlit theme is light. CSS variables include a system dark-mode palette, but the exact dark appearance depends on the browser/Streamlit theme wrapper and should be visually checked on the target desktop.
- The report-ready text is available in a native Streamlit code block with its copy control, plus a separate plain-text download.

## Integration audit follow-up

- The forest-plot export is PNG (not SVG); inline plots remain self-contained SVG. Both render locally without a plotting dependency.
- Uploads are fingerprinted from their content, not just their filename. Replacing a file with different content clears stale aggregate results and category picks, including when the filename is unchanged. Category selections are reconciled when their available values change.
- The specified example was checked against the unchanged calculation API: RR 3.303571 (Katz 95% CI 1.625924–6.712234), OR 7.142857 (Woolf 95% CI 2.518641–20.257119), RD 0.435811 (Wald 95% CI 0.239763–0.631858), Pearson χ² 15.030933, and Fisher probability-ordered two-sided p = 0.000170354. Display formatting correctly yields RR 3.30 [1.63–6.71], OR 7.14 [2.52–20.26], RD 0.436 [0.240–0.632], χ² 15.03 and p < 0.001. Statistical code was not changed.
- Light is the configured Streamlit theme. CSS defines a dark preference palette, but complete dark-theme widget contrast and WCAG AA compliance have not been confirmed by a visual contrast audit. This remains a verification limitation rather than a claim of certified compliance.
- There is no prior commit in this workspace and no genuine pre-redesign screenshot was found; only current-state screenshots can be produced without an external historical copy.

## Integrated interaction and accessibility follow-up

- Added Streamlit `AppTest` workflows for real CSV and Excel uploads, preview/mapping/category selection, aggregation, exact four-cell handoff, automatic analysis, missing values, non-binary categories, duplicate CSV headers, same-filename content replacement, mapping/category reconciliation, and navigation/state retention.
- Fixed stale line-list aggregates: the aggregate result records its source fingerprint, column mapping and reference categories. Any change invalidates the displayed result until **Aggregate** is run again. A successful handoff now calculates and displays the analysis for the exact handed-off counts instead of leaving a blank analysis state.
- Fixed count-input loss when leaving the analysis section by mirroring count values outside transient widget state. Analysis design, alpha, Haldane–Anscombe toggle, line-list design, and power planning selections are also mirrored for navigation.
- Removed raw exception diagnostics from the visible interface. Known validation messages remain actionable; unexpected file-read/render errors now show a safe recovery message.
- Corrected report text: risk-difference intervals use three decimals and the Pearson p-value label is no longer duplicated. The missing-value instructions now accurately state that the source file must be corrected; the UI does not offer a row-filtering tool.
- Replaced the fixed focus outline with theme-aware focus colors and made data tables horizontally scrollable on narrow screens. Added reproducible WCAG contrast calculations for authored palette pairs in `tests/test_ui_accessibility.py` and documented measured ratios/scope in `docs/UI_ACCESSIBILITY_AUDIT.md`.
- Accessibility scope remains limited: contrast values are calculated from the CSS hex pairs, and a real browser was inspected under dark system preference; this is not a complete WCAG conformance audit of every Streamlit-native widget, browser zoom level, screen reader, or operating system theme setting.
- Added an AppTest regression check for the calculated report text and the presence/filename extensions of the TXT, CSV, and PNG download controls. The PNG bytes are separately checked by the component test; AppTest's mock download URLs do not by themselves prove a browser successfully saved each file.

## Publication & statistical audit follow-up (2026-10-24)

- Added a fourth **Publication & STROBE** section with a cautious results narrative, Markdown and LaTeX comparison tables, a collapsed **Technical JSON Payload**, and TXT/Markdown/LaTeX/JSON download paths. Narrative fields not present in the analysis (setting, dates, eligibility, ethics, funding, etc.) are explicitly left for authors to supply.
- Added browser clipboard copying through `navigator.clipboard.writeText` with a `document.execCommand('copy')` fallback and visible permission/error messaging. This is an implemented browser path, not proof of successful clipboard write/readback in every browser.
- Added `core/strobe_export.py` and tests for narrative, table and JSON provenance output. Non-finite estimates are serialized as explicit strings rather than non-standard JSON numeric values.
- Added optional `core/exact_advanced.py` integration with version-checked `scipy.stats.boschloo_exact`; SciPy remains an optional extra to preserve the dependency-free base install and local/offline application behavior. SciPy 1.18.1 was installed in the audit user's Python environment and the Boschloo calculation was exercised in both the automated UI test and the running app; users without SciPy receive an actionable dependency message.
- Added `docs/PHASE2_STATISTICAL_VALIDATION.md` with a documented R reference protocol and limitations. `Rscript` is unavailable in the audit environment, so no `epiR` or `stats::mantelhaen.test` result is claimed. The independent comparison remains an explicit follow-up.
- Added root-level `paper.md` as a JOSS/SoftwareX-style draft. Author, affiliation, repository URL, and license are explicit submission placeholders; no public release or peer review is claimed.

## Advanced-method UI integration (2026-10-24)

- Added an **Advanced analyses** navigation section integrating the existing E-value engine, stratified Mantel–Haenszel analysis, Breslow–Day/Tarone heterogeneity checks, Simpson's-paradox direction flag, and Boschloo's unconditional exact test.
- E-value UI supports RR input or explicit OR conversion, optional confidence intervals, baseline-risk entry when selected, and a stale-input warning until recalculated.
- Stratification UI accepts labeled CSV rows of four counts, validates labels/counts, shows stratum-specific and pooled estimates, and displays the implemented heuristic flags and heterogeneity tests without silently correcting cells.
- Boschloo UI uses the current main 2×2 counts, displays greater/less/two-sided p-values and SciPy version, and reports an actionable missing-dependency error if the optional extra is unavailable.
- Added an integrated Streamlit AppTest covering all three panels; updated README navigation and statistical limitations.
