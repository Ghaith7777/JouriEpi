"""Reusable, presentation-only Streamlit components."""

from __future__ import annotations

import html
import re
import streamlit as st

from ui.formatting import fmt_ci, fmt_num, fmt_pct, fmt_p


def metric_card(label: str, value: str, detail: str, status: str = "neutral", status_text: str | None = None) -> None:
    """Render a compact accessible metric card."""
    status_label = status_text or {"good": "CI excludes null", "neutral": "CI includes null", "warn": "Not estimable"}.get(status, status)
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value">{html.escape(value)}</div>'
        f'<div class="metric-detail">{html.escape(detail)}</div>'
        f'<div class="metric-status status-{html.escape(status)}"><span aria-hidden="true">●</span> '
        f'{html.escape(status_label)}</div></div>', unsafe_allow_html=True)


def table_2x2(a: int, b: int, c: int, d: int, *, expected=None, editable=False) -> None:
    """Render the epidemiological table convention as a semantic HTML grid."""
    labels = ("Case (D+)", "Non-case (D−)", "Total")
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    cells = [
        '<div class="table-cell table-head"></div>',
        *(f'<div class="table-cell table-head">{x}</div>' for x in labels),
        '<div class="table-cell row-head">Exposed</div>',
        f'<div class="table-cell count-cell">{a:,}</div>', f'<div class="table-cell count-cell">{b:,}</div>', f'<div class="table-cell total-cell">{row1:,}</div>',
        '<div class="table-cell row-head">Unexposed</div>',
        f'<div class="table-cell count-cell">{c:,}</div>', f'<div class="table-cell count-cell">{d:,}</div>', f'<div class="table-cell total-cell">{row2:,}</div>',
        '<div class="table-cell row-head total-row-head">Total</div>',
        f'<div class="table-cell total-cell">{col1:,}</div>', f'<div class="table-cell total-cell">{col2:,}</div>', f'<div class="table-cell grand-total">{a+b+c+d:,}</div>',
    ]
    st.markdown('<div class="contingency-grid">' + ''.join(cells) + '</div>', unsafe_allow_html=True)


def result_table(rows: list[tuple[str, object, object, str, str]], confidence: str) -> None:
    """Display formatted association estimates with methods and interpretation."""
    data = [{"Measure": name, "Estimate": estimate,
             f"{confidence} CI": (fmt_ci(ci, 3) if ci is not None and name == "Risk difference"
                                  else fmt_ci(ci) if ci is not None
                                  else "Not estimable" if method in {"Katz", "Woolf", "Wald", "Katz transform"}
                                  else "—"),
             "Method": method, "Interpretation": hint}
            for name, estimate, ci, method, hint in rows]
    st.dataframe(data, hide_index=True, width="stretch")


def expected_counts_grid(expected) -> str:
    """Return a compact, accessible 2×2 expected-count grid with amber low cells."""
    cells = ['<div class="table-cell table-head"></div>',
             '<div class="table-cell table-head">Case (D+)</div>',
             '<div class="table-cell table-head">Non-case (D−)</div>']
    for label, row in zip(("Exposed", "Unexposed"), expected):
        cells.append(f'<div class="table-cell row-head">{label}</div>')
        for value in row:
            low = value < 5
            klass = "expected-low" if low else "count-cell"
            flag = " · low" if low else ""
            cells.append(f'<div class="table-cell {klass}">{value:.2f}{flag}</div>')
    return '<div class="contingency-grid expected-grid" role="img" aria-label="Expected counts under independence; cells below five are highlighted amber">' + ''.join(cells) + '</div>'


def forest_plot_svg(result: dict, confidence: str) -> str:
    """Build separate ratio (log scale) and risk-difference (linear) SVG panels."""
    import math

    def panel(items, scale, null_value, ticks, aria):
        width, row_h, x0, x1 = 760, 58, 220, 480
        height = 54 + row_h * len(items)
        def position(value):
            if scale == "log":
                low, high = math.log(0.1), math.log(100)
                value = min(100, max(0.1, value))
                return x0 + (math.log(value) - low) / (high - low) * (x1 - x0)
            return x0 + (min(1.0, max(-1.0, value)) + 1) / 2 * (x1 - x0)
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{aria}">',
                 '<style>text{font-family:system-ui,sans-serif;fill:var(--epi-text,#334155);font-size:12px}.axis{stroke:#94a3b8;stroke-width:1}.ci{stroke:var(--epi-accent,#0f766e);stroke-width:3;stroke-linecap:round}.point{fill:var(--epi-accent,#0f766e);stroke:var(--epi-card,#fff);stroke-width:1.5}.null{stroke:#d97706;stroke-width:1.5;stroke-dasharray:4 4}</style>']
        null_x = position(null_value)
        parts.append(f'<line class="null" x1="{null_x:.1f}" x2="{null_x:.1f}" y1="24" y2="{height-23}"/>')
        for idx, (label, estimate, lo, hi) in enumerate(items):
            y = 35 + idx * row_h
            parts.extend([f'<text x="8" y="{y+4}">{label}</text>',
                          f'<line class="ci" x1="{position(lo):.1f}" x2="{position(hi):.1f}" y1="{y}" y2="{y}"/>',
                          f'<circle class="point" cx="{position(estimate):.1f}" cy="{y}" r="5"/>',
                          f'<text x="500" y="{y+4}">{fmt_num(estimate)} ({fmt_num(lo, 2)}–{fmt_num(hi, 2)})</text>'])
        axis_y = height - 20
        parts.append(f'<line class="axis" x1="{x0}" x2="{x1}" y1="{axis_y}" y2="{axis_y}"/>')
        for tick in ticks:
            tx = position(tick)
            parts.append(f'<line class="axis" x1="{tx:.1f}" x2="{tx:.1f}" y1="{axis_y-3}" y2="{axis_y+3}"/><text x="{tx:.1f}" y="{height-4}" text-anchor="middle">{tick:g}</text>')
        parts.append('</svg>')
        return ''.join(parts)

    ratios = []
    for label, estimate, ci in (("Risk ratio", result.get("risk_ratio"), result.get("risk_ratio_katz_ci")),
                                ("Odds ratio", result.get("odds_ratio"), result.get("odds_ratio_woolf_ci"))):
        if estimate is not None and ci is not None and estimate > 0 and ci[0] > 0 and ci[1] > 0:
            ratios.append((label, float(estimate), float(ci[0]), float(ci[1])))
    panels = ['<div class="plot-panel"><b>Risk ratio and odds ratio · log scale (null = 1)</b>']
    if ratios:
        panels.append(panel(ratios, "log", 1, (0.1, 1, 10, 100), "Risk ratio and odds ratio forest plot on a logarithmic scale with null line at one"))
    else:
        panels.append('<p class="muted-note">Ratio intervals are not estimable for this table.</p>')
    panels.append('</div><div class="plot-panel"><b>Risk difference · linear scale (null = 0)</b>')
    rd, rd_ci = result.get("risk_difference"), result.get("risk_difference_wald_ci")
    if rd is not None and rd_ci is not None:
        panels.append(panel([("Risk difference", float(rd), float(rd_ci[0]), float(rd_ci[1]))], "linear", 0, (-1, 0, 1), "Risk difference forest plot on a linear scale with null line at zero"))
    else:
        panels.append('<p class="muted-note">Risk-difference interval is not estimable for this table.</p>')
    panels.append('</div>')
    return ''.join(panels)


def forest_plot_png_bytes(result: dict) -> bytes:
    """Render a report-ready PNG locally with Pillow (already bundled with Streamlit)."""
    from io import BytesIO
    from pathlib import Path
    import math
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (1600, 820), "#ffffff")
    draw = ImageDraw.Draw(image)
    font_candidates = [Path("C:/Windows/Fonts/segoeui.ttf"), Path("C:/Windows/Fonts/arial.ttf")]
    font_path = next((p for p in font_candidates if p.is_file()), None)
    def font(size):
        try:
            return ImageFont.truetype(str(font_path), size) if font_path else ImageFont.load_default(size=size)
        except (OSError, TypeError):
            return ImageFont.load_default()
    title_font, label_font, small_font = font(30), font(22), font(18)
    ink, muted, teal, amber, border = "#172b3a", "#526575", "#0f766e", "#d97706", "#d8e1e7"
    draw.text((64, 36), "JouriEpi | Forest plot", fill=ink, font=title_font)
    draw.text((64, 96), "Risk ratio and odds ratio — logarithmic scale (null = 1)", fill=ink, font=label_font)

    def ratio_x(value):
        value = min(100.0, max(0.1, float(value)))
        return int(450 + (math.log(value) - math.log(0.1)) / (math.log(100) - math.log(0.1)) * 550)
    ratio_rows = [("Risk ratio", result.get("risk_ratio"), result.get("risk_ratio_katz_ci")),
                  ("Odds ratio", result.get("odds_ratio"), result.get("odds_ratio_woolf_ci"))]
    draw.line((ratio_x(1), 135, ratio_x(1), 330), fill=amber, width=3)
    for idx, (label, estimate, ci) in enumerate(ratio_rows):
        y = 170 + idx * 85
        draw.text((64, y-14), label, fill=ink, font=label_font)
        if estimate is None or ci is None or estimate <= 0 or ci[0] <= 0 or ci[1] <= 0:
            draw.text((1050, y-12), "Not estimable", fill=muted, font=small_font)
            continue
        xlo, xhi, xp = ratio_x(ci[0]), ratio_x(ci[1]), ratio_x(estimate)
        draw.line((xlo, y, xhi, y), fill=teal, width=6)
        draw.line((xlo, y-12, xlo, y+12), fill=teal, width=3)
        draw.line((xhi, y-12, xhi, y+12), fill=teal, width=3)
        draw.ellipse((xp-8, y-8, xp+8, y+8), fill=teal, outline="#ffffff", width=2)
        draw.text((1050, y-13), f"{fmt_num(estimate)} ({fmt_num(ci[0], 2)}–{fmt_num(ci[1], 2)})", fill=ink, font=small_font)
    draw.line((450, 335, 1000, 335), fill=border, width=2)
    for tick in (0.1, 1, 10, 100):
        x = ratio_x(tick)
        draw.line((x, 330, x, 342), fill=muted, width=2)
        draw.text((x, 350), f"{tick:g}", fill=muted, font=small_font, anchor="mt")

    draw.text((64, 430), "Risk difference — linear scale (null = 0)", fill=ink, font=label_font)
    x0, x1 = 450, 1000
    def rd_x(value):
        return int(x0 + (min(1.0, max(-1.0, float(value))) + 1) / 2 * (x1-x0))
    draw.line((rd_x(0), 470, rd_x(0), 645), fill=amber, width=3)
    rd, rd_ci = result.get("risk_difference"), result.get("risk_difference_wald_ci")
    draw.text((64, 530), "Risk difference", fill=ink, font=label_font)
    if rd is None or rd_ci is None:
        draw.text((1050, 525), "Not estimable", fill=muted, font=small_font)
    else:
        xlo, xhi, xp = rd_x(rd_ci[0]), rd_x(rd_ci[1]), rd_x(rd)
        draw.line((xlo, 540, xhi, 540), fill=teal, width=6)
        draw.line((xlo, 528, xlo, 552), fill=teal, width=3)
        draw.line((xhi, 528, xhi, 552), fill=teal, width=3)
        draw.ellipse((xp-8, 532, xp+8, 548), fill=teal, outline="#ffffff", width=2)
        draw.text((1050, 525), f"{fmt_num(rd, 3)} ({fmt_num(rd_ci[0], 3)}–{fmt_num(rd_ci[1], 3)})", fill=ink, font=small_font)
    draw.line((x0, 645, x1, 645), fill=border, width=2)
    for tick in (-1, 0, 1):
        x = rd_x(tick)
        draw.line((x, 640, x, 652), fill=muted, width=2)
        draw.text((x, 660), f"{tick:g}", fill=muted, font=small_font, anchor="mt")
    draw.text((64, 760), "Intervals are asymptotic; null values are 1 for ratios and 0 for risk difference.", fill=muted, font=small_font)
    output = BytesIO()
    image.save(output, format="PNG", optimize=True, dpi=(300, 300))
    return output.getvalue()


def stratified_forest_plot_svg(strata, pooled_or, pooled_ci=None) -> str:
    """Render stratum ORs and a pooled Mantel–Haenszel estimate as a forest plot."""
    import math
    import html as _html

    usable = []
    for item in strata:
        estimate, ci = item.odds_ratio, item.odds_ratio_ci
        if estimate is not None and ci is not None and estimate > 0 and ci[0] > 0 and ci[1] > 0 and math.isfinite(estimate):
            usable.append((item.label, estimate, ci[0], ci[1]))
    if pooled_or is not None and pooled_ci is not None and pooled_or > 0 and pooled_ci[0] > 0 and pooled_ci[1] > 0 and math.isfinite(pooled_or):
        usable.append(("Mantel–Haenszel pooled", pooled_or, pooled_ci[0], pooled_ci[1]))
    if not usable:
        return '<p class="muted-note">Odds-ratio confidence intervals are not estimable for the available strata.</p>'
    width, row_h, top, left, right = 860, 42, 28, 250, 570
    height = top + row_h * len(usable) + 46
    lo, hi = math.log(0.1), math.log(100)
    def x(v):
        return left + (math.log(min(100, max(0.1, v))) - lo) / (hi - lo) * (right - left)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Stratum-specific odds ratios and Mantel-Haenszel pooled odds ratio with 95 percent confidence intervals">',
             '<style>text{font-family:system-ui,sans-serif;fill:var(--epi-text,#172b3a);font-size:12px}.ci{stroke:var(--epi-accent,#0f766e);stroke-width:2.5}.pool{stroke:#7c3aed;stroke-width:3}.null{stroke:#d97706;stroke-dasharray:4 4}</style>',
             f'<line class="null" x1="{x(1):.1f}" x2="{x(1):.1f}" y1="14" y2="{height-28}"/>']
    for i, (label, estimate, low, high) in enumerate(usable):
        y = top + i * row_h
        is_pool = label == "Mantel–Haenszel pooled"
        klass = "pool" if is_pool else "ci"
        parts.extend([f'<text x="8" y="{y+4}" font-weight="{"700" if is_pool else "400"}">{_html.escape(str(label)[:32])}</text>',
                      f'<line class="{klass}" x1="{x(low):.1f}" x2="{x(high):.1f}" y1="{y}" y2="{y}"/>'])
        if is_pool:
            xp = x(estimate)
            parts.append(f'<path d="M {xp-7:.1f} {y} L {xp:.1f} {y-6:.1f} L {xp+7:.1f} {y} L {xp:.1f} {y+6:.1f} Z" fill="#7c3aed"/>')
        else:
            parts.append(f'<circle cx="{x(estimate):.1f}" cy="{y}" r="4.5" fill="var(--epi-accent,#0f766e)"/>')
        parts.append(f'<text x="590" y="{y+4}">{fmt_num(estimate)} ({fmt_num(low, 2)}–{fmt_num(high, 2)})</text>')
    axis = height - 26
    parts.append(f'<line x1="{left}" y1="{axis}" x2="{right}" y2="{axis}" stroke="#94a3b8"/>')
    for tick in (0.1, 1, 10, 100):
        parts.append(f'<text x="{x(tick):.1f}" y="{height-7}" text-anchor="middle">{tick:g}</text>')
    parts.append('</svg>')
    return '<div class="plot-panel">' + ''.join(parts) + '</div>'


def roc_plot_svg(points, auc=None, operating_point=None) -> str:
    """Render a dependency-free ROC curve with diagonal and operating point."""
    import html as _html
    width, height, left, top, plotw, ploth = 640, 440, 70, 25, 520, 340
    def xy(fpr, tpr):
        return left + max(0.0, min(1.0, float(fpr))) * plotw, top + (1 - max(0.0, min(1.0, float(tpr)))) * ploth
    coords = " ".join(f"{xy(fpr, tpr)[0]:.1f},{xy(fpr, tpr)[1]:.1f}" for fpr, tpr, *_ in points)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Receiver operating characteristic curve with diagonal reference line">',
             '<style>text{font-family:system-ui,sans-serif;fill:var(--epi-text,#172b3a);font-size:12px}.axis{stroke:#64748b}.ref{stroke:#94a3b8;stroke-dasharray:5 5}.curve{stroke:var(--epi-accent,#0f766e);stroke-width:3;fill:none}</style>',
             f'<line class="ref" x1="{left}" y1="{top+ploth}" x2="{left+plotw}" y2="{top}"/>',
             f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+ploth}"/><line class="axis" x1="{left}" y1="{top+ploth}" x2="{left+plotw}" y2="{top+ploth}"/>']
    if len(points) > 1:
        parts.append(f'<polyline class="curve" points="{coords}"/>')
    if operating_point is not None:
        ox, oy = xy(operating_point[0], operating_point[1])
        parts.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="6" fill="#d97706" stroke="#fff" stroke-width="2"/>')
    for tick in (0, .2, .4, .6, .8, 1):
        x = left + tick * plotw; y = top + (1 - tick) * ploth
        parts.append(f'<text x="{x:.1f}" y="{top+ploth+20}" text-anchor="middle">{tick:.1f}</text><text x="{left-12}" y="{y+4:.1f}" text-anchor="end">{tick:.1f}</text>')
    parts.append(f'<text x="{left+plotw/2}" y="{height-15}" text-anchor="middle">False-positive rate (1 − specificity)</text>')
    parts.append(f'<text transform="translate(18 {top+ploth/2}) rotate(-90)" text-anchor="middle">True-positive rate (sensitivity)</text>')
    if auc is not None:
        parts.append(f'<text x="{left+10}" y="{top+20}">AUC = {_html.escape(f"{auc:.3f}")}</text>')
    parts.append('</svg>')
    return '<div class="plot-panel">' + ''.join(parts) + '</div>'


def dual_roc_plot_svg(result) -> str:
    """Overlay two ROC curves with distinct medical palette colors and operating points."""
    width, height, left, top, plotw, ploth = 760, 480, 82, 34, 610, 350
    def xy(fpr, tpr):
        return left + max(0.0, min(1.0, float(fpr))) * plotw, top + (1 - max(0.0, min(1.0, float(tpr)))) * ploth
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Paired ROC comparison with DeLong test">',
             '<style>text{font-family:system-ui,sans-serif;fill:#172b3a;font-size:13px}.axis{stroke:#64748b}.ref{stroke:#94a3b8;stroke-dasharray:5 5}.roc1{stroke:#0f766e;stroke-width:3;fill:none}.roc2{stroke:#c2415d;stroke-width:3;fill:none;stroke-dasharray:7 4}</style>',
             f'<line class="ref" x1="{left}" y1="{top+ploth}" x2="{left+plotw}" y2="{top}"/>',
             f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+ploth}"/><line class="axis" x1="{left}" y1="{top+ploth}" x2="{left+plotw}" y2="{top+ploth}"/>']
    for idx, (points, klass, color, label, auc, operating) in enumerate((
        (result.roc_points1, "roc1", "#0f766e", "Model 1", result.auc1, result.operating_point1),
        (result.roc_points2, "roc2", "#c2415d", "Model 2", result.auc2, result.operating_point2),
    )):
        coords = " ".join(f"{xy(p[0], p[1])[0]:.1f},{xy(p[0], p[1])[1]:.1f}" for p in points)
        parts.append(f'<polyline class="{klass}" points="{coords}"/>')
        if operating:
            ox, oy = xy(*operating)
            parts.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="6" fill="{color}" stroke="#fff" stroke-width="2"/>')
        parts.append(f'<line class="{klass}" x1="{left+12}" y1="{top+18+idx*22}" x2="{left+38}" y2="{top+18+idx*22}"/><text x="{left+45}" y="{top+22+idx*22}">{label}: AUC {auc:.3f}</text>')
    for tick in (0, .2, .4, .6, .8, 1):
        x = left + tick * plotw; y = top + (1-tick) * ploth
        parts.append(f'<text x="{x:.1f}" y="{top+ploth+22}" text-anchor="middle">{tick:.1f}</text><text x="{left-12}" y="{y+4:.1f}" text-anchor="end">{tick:.1f}</text>')
    parts.append(f'<text x="{left+plotw/2}" y="{height-15}" text-anchor="middle">False-positive rate (1 − specificity)</text>')
    parts.append(f'<text transform="translate(18 {top+ploth/2}) rotate(-90)" text-anchor="middle">True-positive rate (sensitivity)</text>')
    parts.append('</svg>')
    return '<div class="plot-panel">' + ''.join(parts) + '</div>'


def roc_plot_png_bytes(points, auc=None) -> bytes:
    """Create a 300-DPI ROC PNG using only the locally installed Pillow package."""
    from io import BytesIO
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new("RGB", (1600, 1200), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=26)
    small = ImageFont.load_default(size=20)
    left, top, width, height = 180, 120, 1050, 850
    def xy(fpr, tpr):
        return int(left + max(0, min(1, float(fpr))) * width), int(top + (1 - max(0, min(1, float(tpr)))) * height)
    draw.text((left, 35), "JouriEpi | Receiver operating characteristic", fill="#172b3a", font=font)
    draw.line((left, top, left, top+height), fill="#64748b", width=3)
    draw.line((left, top+height, left+width, top+height), fill="#64748b", width=3)
    draw.line((left, top+height, left+width, top), fill="#94a3b8", width=3)
    for tick in range(6):
        v = tick / 5
        x, y = xy(v, v)
        draw.text((x-15, top+height+18), f"{v:.1f}", fill="#526575", font=small)
        draw.text((left-60, y-10), f"{v:.1f}", fill="#526575", font=small)
    coords = [xy(p[0], p[1]) for p in points]
    if len(coords) > 1:
        draw.line(coords, fill="#0f766e", width=6, joint="curve")
    if coords:
        for x, y in coords:
            draw.ellipse((x-4, y-4, x+4, y+4), fill="#0f766e")
    if auc is not None:
        draw.text((left+24, top+20), f"AUC = {auc:.3f}", fill="#172b3a", font=font)
    draw.text((left+width//2-150, top+height+65), "False-positive rate (1 − specificity)", fill="#172b3a", font=font)
    draw.text((30, top+height//2-20), "True-positive rate", fill="#172b3a", font=font)
    output = BytesIO()
    image.save(output, format="PNG", optimize=True, dpi=(300, 300))
    return output.getvalue()


def fagan_nomogram_svg(pretest_probability: float, lr_positive: float | None,
                       lr_negative: float | None, post_positive: float | None,
                       post_negative: float | None) -> str:
    """Render a three-axis Fagan nomogram for positive and negative test results."""
    import math
    width, height, top, bottom = 760, 390, 62, 310
    xs = (120, 380, 640)
    logit = lambda p: math.log(max(0.01, min(0.99, p)) / (1 - max(0.01, min(0.99, p))))
    lo, hi = logit(0.01), logit(0.99)
    def py(p): return bottom - (logit(p) - lo) / (hi - lo) * (bottom - top)
    def ly(lr):
        if lr is None or math.isnan(lr) or lr < 0: return None
        value = -2 if lr == 0 else 3 if math.isinf(lr) else max(-2, min(3, math.log10(lr)))
        return bottom - (value + 2) / 5 * (bottom - top)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Fagan nomogram with pre-test probability, likelihood ratio and post-test probability axes">',
             '<style>text{font-family:system-ui,sans-serif;fill:#172b3a;font-size:12px}.axis{stroke:#64748b;stroke-width:1.5}.positive{stroke:#0f766e;stroke-width:2.5;fill:none}.negative{stroke:#b45309;stroke-width:2.5;fill:none;stroke-dasharray:6 4}</style>']
    for x in xs:
        parts.append(f'<line class="axis" x1="{x}" y1="{top}" x2="{x}" y2="{bottom}"/>')
    parts.extend([f'<text x="{xs[0]}" y="28" text-anchor="middle" font-weight="700">Pre-test probability</text>',
                  f'<text x="{xs[1]}" y="28" text-anchor="middle" font-weight="700">Likelihood ratio</text>',
                  f'<text x="{xs[2]}" y="28" text-anchor="middle" font-weight="700">Post-test probability</text>'])
    for p in (0.01, 0.05, 0.1, 0.2, 0.5, 0.8, 0.9, 0.95, 0.99):
        y = py(p)
        parts.extend([f'<line class="axis" x1="{xs[0]-5}" y1="{y:.1f}" x2="{xs[0]+5}" y2="{y:.1f}"/>',
                      f'<text x="{xs[0]-10}" y="{y+4:.1f}" text-anchor="end">{p:g}</text>',
                      f'<line class="axis" x1="{xs[2]-5}" y1="{y:.1f}" x2="{xs[2]+5}" y2="{y:.1f}"/>',
                      f'<text x="{xs[2]+10}" y="{y+4:.1f}">{p:g}</text>'])
    for lr in (0.01, 0.1, 1, 10, 100, 1000):
        y = ly(lr)
        parts.extend([f'<line class="axis" x1="{xs[1]-5}" y1="{y:.1f}" x2="{xs[1]+5}" y2="{y:.1f}"/>',
                      f'<text x="{xs[1]-10}" y="{y+4:.1f}" text-anchor="end">{lr:g}</text>'])
    ypre = py(pretest_probability)
    parts.append(f'<circle cx="{xs[0]}" cy="{ypre:.1f}" r="5" fill="#334155"/>')
    for lr, post, label, klass in ((lr_positive, post_positive, 'LR+', 'positive'),
                                   (lr_negative, post_negative, 'LR−', 'negative')):
        if lr is None or post is None:
            continue
        yl, yp = ly(lr), py(post)
        parts.append(f'<polyline class="{klass}" points="{xs[0]},{ypre:.1f} {xs[1]},{yl:.1f} {xs[2]},{yp:.1f}"/>')
        parts.append(f'<text x="{xs[1]+12}" y="{yl-6:.1f}">{label} {lr:.3g}</text>')
    parts.append(f'<text x="{width/2}" y="{height-24}" text-anchor="middle">Post-test odds = pre-test odds × likelihood ratio</text>')
    parts.append('</svg>')
    return ''.join(parts)


def decision_curve_svg(result) -> str:
    """Render model/treat-all/treat-none net benefit curves as SVG."""
    width, height, left, top, plotw, ploth = 760, 430, 76, 30, 640, 330
    points = result.points
    if not points:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 120"><text x="20" y="60">No decision-curve thresholds available.</text></svg>'
    min_nb = min(-0.25, *(p.model_net_benefit for p in points), *(p.treat_all_net_benefit for p in points))
    max_nb = max(0.5, *(p.model_net_benefit for p in points), *(p.treat_all_net_benefit for p in points))
    def xy(threshold, value):
        x = left + (threshold - points[0].threshold_probability) / max(1e-12, points[-1].threshold_probability - points[0].threshold_probability) * plotw
        y = top + (max_nb - value) / (max_nb - min_nb) * ploth
        return x, y
    def coords(values):
        return ' '.join(f'{xy(p.threshold_probability, v)[0]:.1f},{xy(p.threshold_probability, v)[1]:.1f}' for p, v in zip(points, values))
    model = [p.model_net_benefit for p in points]
    all_ = [p.treat_all_net_benefit for p in points]
    none = [0.0] * len(points)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="Decision curve analysis net benefit for model, treat all and treat none">',
             '<style>text{font-family:system-ui,sans-serif;fill:#172b3a;font-size:12px}.axis{stroke:#64748b}.model{stroke:#0f766e;stroke-width:3;fill:none}.all{stroke:#b45309;stroke-width:2.5;fill:none;stroke-dasharray:6 4}.none{stroke:#64748b;stroke-width:2;fill:none;stroke-dasharray:3 4}</style>',
             f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+ploth}"/><line class="axis" x1="{left}" y1="{top+ploth}" x2="{left+plotw}" y2="{top+ploth}"/>',
             f'<polyline class="model" points="{coords(model)}"/><polyline class="all" points="{coords(all_)}"/><polyline class="none" points="{coords(none)}"/>']
    for i in range(5):
        t = points[0].threshold_probability + i / 4 * (points[-1].threshold_probability - points[0].threshold_probability)
        x = left + i / 4 * plotw
        parts.append(f'<text x="{x:.1f}" y="{top+ploth+22}" text-anchor="middle">{t:.2f}</text>')
    for i in range(5):
        v = min_nb + i / 4 * (max_nb - min_nb)
        y = top + (max_nb - v) / (max_nb - min_nb) * ploth
        parts.append(f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end">{v:.2f}</text>')
    parts.extend([f'<text x="{left+plotw/2}" y="{height-12}" text-anchor="middle">Threshold probability</text>',
                  f'<text transform="translate(18 {top+ploth/2}) rotate(-90)" text-anchor="middle">Net benefit</text>',
                  f'<line class="model" x1="500" y1="18" x2="524" y2="18"/><text x="530" y="22">Model</text>',
                  f'<line class="all" x1="585" y1="18" x2="609" y2="18"/><text x="615" y="22">Treat all</text>',
                  f'<line class="none" x1="670" y1="18" x2="694" y2="18"/><text x="700" y="22">None</text>', '</svg>'])
    return ''.join(parts)


def figure_export_payloads(svg_markup: str) -> tuple[bytes, bytes, bytes]:
    """Return valid composite SVG, 300-DPI PNG, and vector PDF bytes.

    CairoSVG is bundled as a pinned local dependency; no external service is used.
    Multiple SVG panels in a component are stacked into one valid SVG document.
    """
    from io import BytesIO
    from PIL import Image
    import cairosvg

    matches = re.findall(r'<svg\b[^>]*>.*?</svg>', svg_markup, flags=re.DOTALL | re.IGNORECASE)
    if not matches:
        raise ValueError("figure markup did not contain an SVG element")
    panels = []
    total_height = 0.0
    max_width = 0.0
    for markup in matches:
        view = re.search(r'viewBox=["\']\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)\s*["\']', markup, re.I)
        if view:
            x0, y0, w, h = map(float, view.groups())
        else:
            w = float((re.search(r'width=["\']([\d.]+)', markup, re.I) or [None, "800"])[1])
            h = float((re.search(r'height=["\']([\d.]+)', markup, re.I) or [None, "450"])[1])
            x0 = y0 = 0.0
        inner = re.sub(r'^<svg\b[^>]*>|</svg>\s*$', '', markup.strip(), flags=re.DOTALL | re.I)
        inner = re.sub(r'var\((--[\w-]+),\s*([^)]+)\)', r'\2', inner)
        panels.append((total_height, w, h, x0, y0, inner))
        total_height += h
        max_width = max(max_width, w)
    nested = ''.join(f'<svg x="0" y="{y}" width="{w}" height="{h}" viewBox="{x0} {y0} {w} {h}">{inner}</svg>'
                     for y, w, h, x0, y0, inner in panels)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_width}" height="{total_height}" viewBox="0 0 {max_width} {total_height}">{nested}</svg>'.encode("utf-8")
    pdf = cairosvg.svg2pdf(bytestring=svg)
    png_raw = cairosvg.svg2png(bytestring=svg, output_width=int(max_width * 3))
    image = Image.open(BytesIO(png_raw)).convert("RGB")
    output = BytesIO()
    image.save(output, format="PNG", dpi=(300, 300), optimize=True)
    return svg, output.getvalue(), pdf


def power_curve_svg(power_fn, chosen_n: int, chosen_power: float) -> str:
    """Render a small local SVG power curve with the selected N highlighted."""
    ns = sorted(set(max(4, int(chosen_n * factor)) for factor in (0.35, 0.5, 0.7, 0.85, 1, 1.2, 1.5, 1.8)))
    if len(ns) < 2 or ns[-1] == ns[0]:
        ns = [max(4, chosen_n - 2), max(6, chosen_n + 2)]
    values = []
    for n in ns:
        try:
            values.append((n, max(0.0, min(1.0, float(power_fn(n))))))
        except (ValueError, ArithmeticError):
            continue
    if len(values) < 2:
        return '<p>Power curve is not available for these parameters.</p>'
    w, h, left, top, plotw, ploth = 700, 240, 48, 16, 610, 175
    points = ' '.join(f'{left+(n-min(ns))/(max(ns)-min(ns))*plotw:.1f},{top+(1-p)*ploth:.1f}' for n,p in values)
    chosen_x = left + (chosen_n-min(ns))/(max(ns)-min(ns))*plotw
    chosen_y = top + (1-chosen_power)*ploth
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="Approximate power increases with total sample size">'
            f'<line x1="{left}" y1="{top+ploth}" x2="{left+plotw}" y2="{top+ploth}" stroke="#94a3b8"/>'
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ploth}" stroke="#94a3b8"/>'
            f'<line x1="{left}" y1="{top+ploth*.2:.1f}" x2="{left+plotw}" y2="{top+ploth*.2:.1f}" stroke="#d97706" stroke-dasharray="4 4"/>'
            f'<polyline points="{points}" fill="none" stroke="var(--epi-accent,#0f766e)" stroke-width="3" stroke-linejoin="round"/>'
            f'<line x1="{chosen_x:.1f}" y1="{top}" x2="{chosen_x:.1f}" y2="{top+ploth}" stroke="var(--epi-accent,#0f766e)" stroke-dasharray="3 3"/>'
            f'<circle cx="{chosen_x:.1f}" cy="{chosen_y:.1f}" r="5" fill="var(--epi-accent,#0f766e)"/>'
            f'<text x="{left}" y="{h-8}" font-size="12" fill="#64748b">Smaller N</text><text x="{left+plotw-60}" y="{h-8}" font-size="12" fill="#64748b">Larger N</text>'
            f'<text x="{left+8}" y="{top+12}" font-size="12" fill="#64748b">Power</text></svg>')

