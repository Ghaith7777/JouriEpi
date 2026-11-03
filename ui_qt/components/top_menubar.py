from PySide6.QtGui import QAction, QActionGroup


class TopMenuBar:
    """Build the native menu bar and expose language/theme signals as callbacks."""

    def __init__(self, window, on_language, on_theme, on_workspace, on_new, on_exit, on_about):
        bar = window.menuBar()
        self.menus = {}
        self.language_actions = {}
        self.theme_actions = {}
        self._window = window
        self._on_language = on_language
        self._on_theme = on_theme
        self._on_workspace = on_workspace
        self._on_new = on_new
        self._on_exit = on_exit
        self._on_about = on_about
        self.rebuild("en")

    def rebuild(self, language: str):
        bar = self._window.menuBar()
        bar.clear()
        tr = self._window.tr
        menu_specs = [("file", "file"), ("analysis", "analysis"), ("diagnostics", "diagnostics"),
                      ("reports", "reports"), ("language", "language"), ("theme", "theme"), ("help", "help")]
        self.menus = {}
        for key, title_key in menu_specs:
            menu = bar.addMenu(tr(title_key))
            menu.setToolTipsVisible(True)
            menu.setToolTip(tr(f"menu_{key}_help"))
            self.menus[key] = menu
        file_menu = self.menus["file"]
        new_action = file_menu.addAction(tr("new_session"))
        new_action.triggered.connect(self._on_new)
        exit_action = file_menu.addAction(tr("exit"))
        exit_action.triggered.connect(self._on_exit)
        for key, title in (("association", "nav_analysis"), ("stratified", "nav_stratified"),
                           ("diagnostics", "nav_dta"), ("paired", "nav_paired"),
                           ("interaction", "nav_interaction"), ("outbreak", "nav_line_list"),
                           ("reports", "nav_publication")):
            action = self.menus["analysis"].addAction(tr(title))
            action.triggered.connect(lambda checked=False, name=key: self._on_workspace(name))
        diagnostics_menu = self.menus["diagnostics"]
        for key, label in (("diagnostics", "Diagnostic accuracy & ROC"),
                           ("paired", "Paired 2×2 / McNemar")):
            action = diagnostics_menu.addAction(label)
            action.triggered.connect(lambda checked=False, name=key: self._on_workspace(name))
        reports_menu = self.menus["reports"]
        publication_action = reports_menu.addAction("Publication exports")
        publication_action.triggered.connect(lambda: self._on_workspace("reports"))
        generate_action = reports_menu.addAction("Generate / refresh report preview")
        generate_action.triggered.connect(lambda: self._on_workspace("reports"))
        generate_action.triggered.connect(lambda checked=False: self._window.generate_report_preview())
        self.language_actions = {}
        lang_group = QActionGroup(self._window)
        lang_group.setExclusive(True)
        from ui_qt.localization import languages
        LANGUAGES = languages()
        for code, label in LANGUAGES.items():
            action = QAction(label, self._window, checkable=True)
            action.setChecked(code == language)
            action.triggered.connect(lambda checked=False, value=code: self._on_language(value))
            lang_group.addAction(action)
            self.menus["language"].addAction(action)
            self.language_actions[code] = action
        self.theme_actions = {}
        theme_group = QActionGroup(self._window)
        theme_group.setExclusive(True)
        for code, label in (("dark", tr("dark_theme")), ("light", tr("light_theme"))):
            action = QAction(label, self._window, checkable=True)
            action.setChecked(code == self._window.theme_name)
            action.triggered.connect(lambda checked=False, value=code: self._on_theme(value))
            theme_group.addAction(action)
            self.menus["theme"].addAction(action)
            self.theme_actions[code] = action
        self.menus["help"].addAction(tr("about")).triggered.connect(self._on_about)
