from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_desktop_entry_point_targets_native_qt_application():
    source = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'jouriepi-app = "ui_qt.main:main"' in source
    assert "streamlit" not in source.split("[project.optional-dependencies]")[0]


def test_desktop_runtime_has_no_browser_server_or_webview_launcher():
    source = (ROOT / "run_desktop.py").read_text(encoding="utf-8").lower()
    assert "from ui_qt.main import main" in source
    for forbidden in ("streamlit", "msedge", "webview", "localhost", "urlopen", "subprocess"):
        assert forbidden not in source


def test_native_build_uses_onedir_windowed_pyside6_and_expected_icon():
    build = (ROOT / "build_windows.ps1").read_text(encoding="utf-8")
    assert '"--onedir"' in build
    assert '"--windowed"' in build
    assert "PySide6" in build
    assert '"ui_qt\\main.py"' in build
    assert '"ui_qt\\assets\\app_icon.ico"' in build
    assert '"logo_32.png"' in build
    assert '"logo_header.png"' in build
    assert not (ROOT / "ui_qt" / "assets" / "icon.ico").exists()


def test_native_qt_styles_include_high_contrast_tooltips_and_both_themes():
    dark = (ROOT / "ui_qt" / "styles" / "dark.qss").read_text(encoding="utf-8")
    light = (ROOT / "ui_qt" / "styles" / "light.qss").read_text(encoding="utf-8")
    assert "QToolTip" in dark and "#18181b" in dark and "#e4e4e7" in dark
    assert "QToolTip" in light and "#ffffff" in light and "#0f172a" in light


def test_general_labels_are_transparent_in_source_and_embedded_themes():
    from ui_qt.embedded_styles import DARK_STYLESHEET, LIGHT_STYLESHEET

    for theme_file, embedded in (
        ("dark.qss", DARK_STYLESHEET),
        ("light.qss", LIGHT_STYLESHEET),
    ):
        source = (ROOT / "ui_qt" / "styles" / theme_file).read_text(encoding="utf-8")
        assert "QLabel { background: transparent; background-color: transparent; }" in source
        assert embedded == source


def test_sidebar_restore_button_is_persistent_and_native():
    source = (ROOT / "ui_qt" / "components" / "sidebar.py").read_text(encoding="utf-8")
    assert 'self.toggle_button = QToolButton()' in source
    assert 'self.toggle_button.clicked.connect(self.toggle)' in source
    assert 'self.toggle_button.setText("▶" if self._collapsed else "◀")' in source



def test_splash_screen_has_high_dpi_branding_and_exact_copyright():
    source = (ROOT / "ui_qt" / "main.py").read_text(encoding="utf-8")
    assert "def build_splash_pixmap() -> QPixmap:" in source
    assert "logical_width, logical_height = 500, 320" in source
    assert 'QColor("#09090b")' in source
    assert 'QColor("#27272a")' in source
    assert '"Clinical Epidemiology & Diagnostic Workstation"' in source
    assert "v1.0.0 " + chr(0x00b7) + " Golden Master" in source
    assert chr(0x00a9) + " 2026 Ghaith Baccari. All rights reserved." in source
    assert "logo.setDevicePixelRatio(dpr)" in source
    assert "Qt.WA_TranslucentBackground" in source
    assert "1800 - splash_visible_timer.elapsed()" in source
