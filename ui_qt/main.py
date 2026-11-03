from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root is importable when this file is executed directly
# (``python ui_qt/main.py``) and when PyInstaller runs the bundled entry point.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys, "_MEIPASS") and sys._MEIPASS not in sys.path:
    sys.path.insert(0, sys._MEIPASS)

from PySide6.QtCore import QEasingCurve, QElapsedTimer, QPropertyAnimation, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
                               QMessageBox, QSplashScreen, QStackedWidget,
                               QVBoxLayout, QWidget)

ROOT = Path(__file__).resolve().parent


def get_resource_path(relative_path: str) -> str:
    """Resolve a bundled UI asset in source and PyInstaller onedir builds."""
    base = Path(getattr(sys, "_MEIPASS", ROOT.parent))
    candidate = base / "ui_qt" / relative_path
    if candidate.exists():
        return str(candidate)
    return str(ROOT / relative_path)


def build_splash_pixmap() -> QPixmap:
    """Render the high-DPI, rounded JouriEpi startup card."""
    logical_width, logical_height = 500, 320
    screen = QGuiApplication.primaryScreen()
    dpr = max(1.0, screen.devicePixelRatio()) if screen is not None else 1.0
    pixmap = QPixmap(round(logical_width * dpr), round(logical_height * dpr))
    pixmap.setDevicePixelRatio(dpr)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    painter.setPen(QPen(QColor("#27272a"), 1))
    painter.setBrush(QColor("#09090b"))
    painter.drawRoundedRect(0.5, 0.5, logical_width - 1, logical_height - 1, 12, 12)

    logo = QPixmap(get_resource_path("assets/logo_256.png"))
    if not logo.isNull():
        logo = logo.scaled(
            round(80 * dpr), round(80 * dpr),
            Qt.KeepAspectRatio, Qt.SmoothTransformation,
        )
        logo.setDevicePixelRatio(dpr)
        painter.drawPixmap((logical_width - 80) // 2, 34, logo)

    painter.setPen(QColor("#ffffff"))
    title_font = QFont("Segoe UI")
    title_font.setPixelSize(24)
    title_font.setBold(True)
    painter.setFont(title_font)
    painter.drawText(20, 128, logical_width - 40, 34,
                     Qt.AlignHCenter | Qt.AlignVCenter, "JouriEpi")

    painter.setPen(QColor("#38bdf8"))
    subtitle_font = QFont("Segoe UI")
    subtitle_font.setPixelSize(12)
    painter.setFont(subtitle_font)
    painter.drawText(16, 166, logical_width - 32, 22,
                     Qt.AlignHCenter | Qt.AlignVCenter,
                     "Clinical Epidemiology & Diagnostic Workstation")

    painter.setPen(QColor("#a1a1aa"))
    metadata_font = QFont("Segoe UI")
    metadata_font.setPixelSize(11)
    painter.setFont(metadata_font)
    painter.drawText(20, 201, logical_width - 40, 20,
                     Qt.AlignHCenter | Qt.AlignVCenter, "v1.0.0 · Golden Master")

    painter.setPen(QColor("#71717a"))
    painter.setFont(QFont("Segoe UI", 11))
    painter.drawText(20, 245, logical_width - 40, 20,
                     Qt.AlignHCenter | Qt.AlignVCenter,
                     "Initializing mathematical engines...")
    painter.drawText(16, logical_height - 34, logical_width - 32, 18,
                     Qt.AlignHCenter | Qt.AlignVCenter,
                     "© 2026 Ghaith Baccari. All rights reserved.")
    painter.end()
    return pixmap


class JouriEpiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize the native application shell and all workspaces synchronously.
        from ui_qt.components.sidebar import Sidebar
        from ui_qt.components.top_menubar import TopMenuBar
        from ui_qt.localization import normalize_language, retranslate_widget_tree, text as localized_text
        self._normalize_language = normalize_language
        self._retranslate_widget_tree = retranslate_widget_tree
        self._localized_text = localized_text
        self.language = "en"
        self.theme_name = "light"
        self.last_result = None
        self.setWindowTitle(self.tr("title"))
        self.setMinimumSize(960, 600)
        self.resize(1100, 680)
        self.setWindowIcon(QApplication.instance().windowIcon())

        shell = QWidget()
        shell.setObjectName("AppShell")
        outer = QVBoxLayout(shell)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        top = QWidget()
        top.setObjectName("TopBar")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(20, 10, 20, 10)
        self.brand_icon = QLabel()
        self.brand_icon.setObjectName("BrandIcon")
        self.brand_icon.setFixedSize(32, 32)
        self.brand_icon.setAlignment(Qt.AlignCenter)
        # Use the high-resolution source and render at the screen's physical
        # pixel density. A 32 px source is undersampled on 125%/150% displays.
        brand_pixmap = QPixmap(get_resource_path("assets/logo_header.png"))
        if not brand_pixmap.isNull():
            screen = QGuiApplication.primaryScreen()
            dpr = max(1.0, screen.devicePixelRatio()) if screen is not None else 1.0
            target_size = 28
            brand_pixmap = brand_pixmap.scaled(
                round(target_size * dpr), round(target_size * dpr),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            brand_pixmap.setDevicePixelRatio(dpr)
            self.brand_icon.setPixmap(brand_pixmap)
        self.brand = QLabel("JouriEpi Clinical Workstation")
        self.brand.setObjectName("BrandTitle")
        self.privacy = QLabel(self.tr("offline_notice"))
        self.privacy.setObjectName("PrivacyNotice")
        top_layout.addWidget(self.brand_icon)
        top_layout.addWidget(self.brand)
        top_layout.addStretch(1)
        top_layout.addWidget(self.privacy)
        outer.addWidget(top)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.sidebar = Sidebar()
        self.stack = QStackedWidget()
        self.stack.setObjectName("WorkspaceStack")
        self.views = {}
        self._workspaces_loaded = False
        self._loading_page = QLabel("Preparing clinical workspaces…")
        self._loading_page.setAlignment(Qt.AlignCenter)
        self.stack.addWidget(self._loading_page)
        self.sidebar.workspace_selected.connect(self.open_workspace)
        body.addWidget(self.sidebar)
        body.addWidget(self.stack, 1)
        outer.addLayout(body, 1)
        self.setCentralWidget(shell)
        self.statusBar().showMessage(self.tr("offline_notice"))

        self.menus = TopMenuBar(
            self, self.set_language, self.set_theme, self.open_workspace,
            self.new_session, self.close, self.show_about,
        )
        self.set_theme("light")
        self.set_language("en")
        self.load_workspaces()

    def center_on_primary_screen(self):
        """Center the outer native window and account for OS frame margins."""
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        handle = self.windowHandle()
        margins = handle.frameMargins() if handle is not None else None
        left = margins.left() if margins is not None else 0
        right = margins.right() if margins is not None else 0
        top = margins.top() if margins is not None else 0
        bottom = margins.bottom() if margins is not None else 0

        # Keep the standard client size on normal displays. On compact work
        # areas, reserve 24 px around the native frame where the minimum size
        # permits it (the OS frame is not part of QWidget.minimumSize()).
        width = min(1100, max(960, available.width() - 48 - left - right))
        height = min(680, max(600, available.height() - 48 - top - bottom))
        self.resize(width, height)
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    def load_workspaces(self):
        if self._workspaces_loaded:
            return
        # Workspace imports and construction are deliberately synchronous.
        from ui_qt.views.view_association_2x2 import AssociationView
        from ui_qt.views.view_stratified import StratifiedView
        from ui_qt.views.view_diagnostics import DiagnosticsView
        from ui_qt.views.view_paired import PairedView
        from ui_qt.views.view_interaction import InteractionView
        from ui_qt.views.view_outbreak import OutbreakView
        from ui_qt.views.view_reports import ReportsView
        self.views = {
            "association": AssociationView(), "stratified": StratifiedView(),
            "diagnostics": DiagnosticsView(), "paired": PairedView(),
            "interaction": InteractionView(), "outbreak": OutbreakView(),
            "reports": ReportsView(),
        }
        self.stack.removeWidget(self._loading_page)
        self._loading_page.deleteLater()
        for view in self.views.values():
            self.stack.addWidget(view)
            if hasattr(view, "result_ready"):
                view.result_ready.connect(self._receive_result)
        self._workspaces_loaded = True
        self.set_language(self.language)
        self.open_workspace("association")

    def tr(self, key: str) -> str:
        return self._localized_text(key, self.language)

    def open_workspace(self, key: str):
        if not self._workspaces_loaded:
            self.load_workspaces()
        view = self.views.get(key)
        if view is not None:
            self.stack.setCurrentWidget(view)
            self.sidebar.set_active(key)
            self.statusBar().showMessage(self.tr("offline_notice"), 3500)

    def _receive_result(self, result):
        self.last_result = result
        self.views["reports"].set_analysis_result(result)

    def new_session(self):
        self.last_result = None
        for view in self.views.values():
            if hasattr(view, "reset_inputs"):
                view.reset_inputs()
            if hasattr(view, "clear_result"):
                view.clear_result()
        self.views["reports"].result = None
        self.views["reports"].preview.clear()
        self.open_workspace("association")
        self.statusBar().showMessage(self.tr("new_session"), 3500)

    def generate_report_preview(self):
        reports = self.views.get("reports")
        if reports is not None:
            reports.refresh_preview()

    def set_language(self, language: str):
        self.language = self._normalize_language(language)
        app = QApplication.instance()
        direction = Qt.LayoutDirection.RightToLeft if self.language == "ar" else Qt.LayoutDirection.LeftToRight
        app.setLayoutDirection(direction)
        self.setLayoutDirection(direction)
        self.setWindowTitle(self.tr("title"))
        self.privacy.setText(self.tr("offline_notice"))
        self.sidebar.set_language(self.language, self.tr)
        for view in self.views.values():
            self._retranslate_widget_tree(view, self.language)
        self.menus.rebuild(self.language)
        self.statusBar().showMessage(self.tr("offline_notice"))

    def set_theme(self, theme: str):
        self.theme_name = "light" if theme == "light" else "dark"
        style_path = ROOT / "styles" / f"{self.theme_name}.qss"
        if style_path.is_file():
            stylesheet = style_path.read_text(encoding="utf-8")
        else:
            # PyInstaller's exact onedir command does not collect loose QSS files.
            from ui_qt.embedded_styles import DARK_STYLESHEET, LIGHT_STYLESHEET
            stylesheet = LIGHT_STYLESHEET if self.theme_name == "light" else DARK_STYLESHEET
        check_icon = Path(get_resource_path("assets/check_white.svg")).as_posix()
        stylesheet = stylesheet.replace("__CHECK_ICON__", check_icon)
        self.setStyleSheet(stylesheet)

    def show_about(self):
        QMessageBox.about(
            self, self.tr("about"),
            "Software: JouriEpi Clinical Workstation v1.0.0\n\n"
            "Creator & Lead Architect: Ghaith Baccari\n\n"
            "Deterministic Offline-First Clinical Epidemiology & Biostatistics Engine.\n\n"
            "© 2026 Ghaith Baccari. All rights reserved.\n\n"
            "GitHub: https://github.com/Ghaith7777\n"
            "Zenodo DOI: 10.5281/zenodo.23914379\n"
            "https://doi.org/10.5281/zenodo.23914379\n\n"
            "Native Qt 6 interface · Offline-first · Zero telemetry.",
        )


def main() -> int:
    """Start the native Qt workstation; no server or browser is launched."""
    app = QApplication(sys.argv)
    application_icon = QIcon(get_resource_path("assets/app_icon.ico"))
    if not application_icon.isNull():
        app.setWindowIcon(application_icon)
    app.setApplicationName("JouriEpi Clinical Workstation")
    app.setApplicationDisplayName("JouriEpi Clinical Workstation")
    app.setOrganizationName("JouriEpi")
    app.setFont(QFont("Segoe UI", 10))
    try:
        splash_pixmap = build_splash_pixmap()
        splash = QSplashScreen(
            splash_pixmap,
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint,
        )
        splash.setAttribute(Qt.WA_TranslucentBackground, True)
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            splash.move(
                available.x() + (available.width() - splash.width()) // 2,
                available.y() + (available.height() - splash.height()) // 2,
            )
        splash.show()
        splash.raise_()
        splash.activateWindow()
        app.processEvents()
        splash_visible_timer = QElapsedTimer()
        splash_visible_timer.start()
        window = JouriEpiWindow()
        window.show()
        window.center_on_primary_screen()
        app.processEvents()

        def handoff_to_main_window():
            fade = QPropertyAnimation(splash, b"windowOpacity", splash)
            fade.setDuration(240)
            fade.setStartValue(1.0)
            fade.setEndValue(0.0)
            fade.setEasingCurve(QEasingCurve.OutCubic)
            fade.finished.connect(lambda: splash.finish(window))
            splash._fade_animation = fade
            fade.start()

        # Keep the splash visible for at least 1.8 seconds and until the main
        # window has been shown and had an event-loop layout pass.
        remaining_ms = max(0, 1800 - splash_visible_timer.elapsed())
        QTimer.singleShot(remaining_ms, handoff_to_main_window)
    except Exception:
        import traceback

        if "splash" in locals() and splash is not None:
            splash.close()
        err = traceback.format_exc()
        try:
            (Path.cwd() / "startup_crash.log").write_text(err, encoding="utf-8")
        except OSError:
            pass
        QMessageBox.critical(
            None,
            "Fatal Startup Error",
            f"Failed to initialize the main window:\n\n{err}",
        )
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
