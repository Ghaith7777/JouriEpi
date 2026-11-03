"""Reproducible contrast checks for the UI's authored light/dark palettes."""

from __future__ import annotations

import re
from pathlib import Path


APP_SOURCE = Path(__file__).resolve().parents[1] / "ui" / "app.py"
COMPONENT_SOURCE = Path(__file__).resolve().parents[1] / "ui" / "components.py"
STYLE_SOURCE = Path(__file__).resolve().parents[1] / "ui" / "assets" / "style.css"


def _luminance(hex_color: str) -> float:
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground: str, background: str) -> float:
    light, dark = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _palettes() -> dict[str, dict[str, str]]:
    source = STYLE_SOURCE.read_text(encoding="utf-8")
    app = APP_SOURCE.read_text(encoding="utf-8")
    light = dict(re.findall(r"(--epi-[\w-]+):\s*(#[0-9a-fA-F]{6})", source.split("/* Streamlit shell", maxsplit=1)[0]))
    dark_block = re.search(r":root\{([^}]+)\}", app)
    dark = dict(re.findall(r"(--epi-[\w-]+):\s*(#[0-9a-fA-F]{6})", dark_block.group(1))) if dark_block else {}
    return {"light": light, "dark": dark}


def test_authored_text_and_status_pairs_meet_wcag_aa_contrast_threshold():
    pairs = (
        ("--epi-text", "--epi-bg"),
        ("--epi-text", "--epi-card"),
        ("--epi-muted", "--epi-bg"),
        ("--epi-muted", "--epi-card"),
        ("--epi-accent", "--epi-card"),
        ("--epi-green", "--epi-green-bg"),
        ("--epi-amber", "--epi-amber-bg"),
        ("--epi-red", "--epi-red-bg"),
    )
    for theme, palette in _palettes().items():
        for foreground, background in pairs:
            ratio = contrast_ratio(palette[foreground], palette[background])
            assert ratio >= 4.5, f"{theme} {foreground} on {background}: {ratio:.2f}:1"


def test_focus_indicator_contrasts_with_both_page_and_card_surfaces():
    for theme, palette in _palettes().items():
        for surface in ("--epi-bg", "--epi-card"):
            ratio = contrast_ratio(palette["--epi-focus"], palette[surface])
            assert ratio >= 3.0, f"{theme} focus on {surface}: {ratio:.2f}:1"


def test_ui_keeps_keyboard_focus_and_non_color_chart_alternatives():
    source = APP_SOURCE.read_text(encoding="utf-8")
    components = COMPONENT_SOURCE.read_text(encoding="utf-8")
    styles = STYLE_SOURCE.read_text(encoding="utf-8")
    assert source.count("<style>") == 1
    assert ":focus-visible" in styles
    assert "Text alternative: RR" in source
    assert "Expected-count text alternative:" in source
    assert "role=\"img\" aria-label=" in components
    assert "chip-warn" in styles and "chip-good" in styles
    assert 'header[data-testid="stHeader"]' in styles
    assert ".stDeployButton" in styles and "footer" in styles


def test_dark_mode_uses_high_contrast_surfaces_and_controls():
    source = APP_SOURCE.read_text(encoding="utf-8")
    assert "background:#111827!important;color:#f8fafc!important;border-color:#475569!important" in source
    assert "[data-testid=\"stFileUploaderDropzone\"]" in source
    assert "[data-testid=\"stSegmentedControl\"] button[aria-pressed=\"true\"]" in source
