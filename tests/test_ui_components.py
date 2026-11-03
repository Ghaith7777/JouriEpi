import pytest

from ui.components import (expected_counts_grid, forest_plot_svg, forest_plot_png_bytes,
                           power_curve_svg, fagan_nomogram_svg, decision_curve_svg,
                           figure_export_payloads)
from core.engine_2x2 import Table2x2, analyze_2x2
from core.decision_curve import analyze_decision_curve


def test_expected_counts_grid_has_two_by_two_and_marks_low_cells():
    grid = expected_counts_grid(((4.2, 6.8), (7.1, 3.9)))
    assert "Case (D+)" in grid
    assert "Non-case (D−)" in grid
    assert "expected-low" in grid
    assert "4.20 · low" in grid
    assert "3.90 · low" in grid


def test_forest_plot_separates_log_ratios_and_linear_risk_difference():
    result = analyze_2x2(Table2x2(25, 15, 7, 30))
    plot = forest_plot_svg(result, "95%")
    assert "log scale (null = 1)" in plot
    assert "linear scale (null = 0)" in plot
    assert "logarithmic scale with null line at one" in plot
    assert "linear scale with null line at zero" in plot
    assert "<svg" in plot


def test_power_curve_is_self_contained_svg():
    plot = power_curve_svg(lambda n: min(0.99, n / 100), 80, 0.8)
    assert "<svg" in plot
    assert "Approximate power increases" in plot


def test_forest_plot_png_is_rendered_locally():
    result = analyze_2x2(Table2x2(25, 15, 7, 30))
    png = forest_plot_png_bytes(result)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png) > 5000


def test_fagan_nomogram_and_decision_curve_are_standalone_svg_figures():
    fagan = fagan_nomogram_svg(0.2, 10.0, 0.1, 0.7142857, 0.0243902)
    dca = decision_curve_svg(analyze_decision_curve([0.9, 0.7, 0.2, 0.1], [1, 0, 1, 0], [0.25, 0.5, 0.75]))
    assert 'aria-label="Fagan nomogram' in fagan
    assert "LR+" in fagan and "LR−" in fagan
    assert 'aria-label="Decision curve analysis' in dca
    assert "Treat all" in dca and "Model" in dca and "None" in dca


def test_figure_export_payloads_produce_valid_svg_300dpi_png_and_vector_pdf():
    result = analyze_2x2(Table2x2(25, 15, 7, 30))
    svg, png, pdf = figure_export_payloads(forest_plot_svg(result, "95%"))
    assert svg.startswith(b"<svg") and svg.count(b"<svg") >= 3
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert pdf.startswith(b"%PDF-")
    from io import BytesIO
    from PIL import Image
    image = Image.open(BytesIO(png))
    assert image.info["dpi"][0] == pytest.approx(300, abs=1)

