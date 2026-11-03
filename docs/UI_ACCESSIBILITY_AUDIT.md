# UI accessibility and contrast audit

## Reproduce the palette calculations

From the project root run:

```powershell
py -3.13 -m pytest tests/test_ui_accessibility.py -q
```

The test parses the authored `--epi-*` CSS variables from the single inline style block and computes WCAG relative luminance and contrast ratios. Normal text pairs use the WCAG AA threshold of 4.5:1; the focus outline is checked against the page and card surfaces at 3:1 as a non-text visual indicator. The results below were calculated from the CSS values with the same formula.

| Pair | Light | Dark | Threshold |
|---|---:|---:|---:|
| Main text / page background | 13.67:1 | 14.83:1 | 4.5:1 |
| Main text / card | 14.55:1 | 13.31:1 | 4.5:1 |
| Muted text / page background | 5.67:1 | 9.46:1 | 4.5:1 |
| Muted text / card | 6.04:1 | 8.49:1 | 4.5:1 |
| Accent / card | 5.47:1 | 10.56:1 | 4.5:1 |
| Success text / success background | 6.49:1 | 9.52:1 | 4.5:1 |
| Warning text / warning background | 6.37:1 | 8.19:1 | 4.5:1 |
| Error text / error background | 6.80:1 | 7.50:1 | 4.5:1 |
| Focus indicator / page background | 5.14:1 | 11.77:1 | 3:1 |
| Focus indicator / card | 5.47:1 | 10.56:1 | 3:1 |

## Scope and findings

- **Themes tested:** the authored light palette and the CSS `prefers-color-scheme: dark` palette. In the inspected local browser, `matchMedia('(prefers-color-scheme: dark)').matches` was true and the computed app/card backgrounds were `rgb(17, 27, 36)` and `rgb(23, 37, 48)` respectively. The configured Streamlit base theme remains light; behavior when users override the Streamlit theme independently of the operating-system preference is not certified.
- **Status communication:** success, warning and error states use explicit text/labels as well as color. Metric cards state whether the interval excludes the null or is not estimable. Expected counts below five are marked `low`, not just colored amber.
- **Keyboard focus:** a visible 3px `:focus-visible` outline is applied to buttons, inputs, comboboxes and radio controls using theme-aware focus colors. Streamlit's own skip-to-content link was present in the inspected browser DOM.
- **Charts:** inline forest and power plots have SVG accessible names and accompanying text alternatives; expected counts have a text alternative. The CSV result table and structured data exports provide non-visual alternatives.
- **Responsive behavior:** metric cards use Streamlit columns and smaller typography/padding at widths below 640px; data frames have horizontal overflow enabled. This CSS inspection and browser DOM inspection are not a comprehensive multi-device layout test.
- **Labels and tooltips:** inputs include meaningful labels and help text; the 2×2 count controls retain descriptive accessible labels despite visually collapsed labels. The sidebar navigation has the accessible label `Navigate`.

## Explicit limitations

These are **contrast-pair measurements**, not a claim of full WCAG 2.2 AA compliance. This audit does not certify every Streamlit-generated control/state color, focus visibility under every browser/OS combination, screen-reader reading order, 200% zoom/reflow, motion preferences, or real-user assistive-technology behavior. The PNG uses dark ink on white for report readability; inline SVG colors are theme-aware. The app makes no external font/CDN/telemetry requests by design; local browser network inspection should be repeated if the app's dependency or rendering architecture changes.
