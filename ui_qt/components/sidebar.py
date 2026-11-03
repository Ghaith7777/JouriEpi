from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtWidgets import QFrame, QSizePolicy, QToolButton, QVBoxLayout


class Sidebar(QFrame):
    workspace_selected = Signal(str)
    collapsed_changed = Signal(bool)

    ITEMS = (
        ("association", "2×2 Association"),
        ("stratified", "Stratified & Simpson's check"),
        ("diagnostics", "Diagnostic accuracy & ROC"),
        ("paired", "Paired 2×2 / McNemar"),
        ("interaction", "Additive interaction"),
        ("outbreak", "Line list & outbreak curve"),
        ("reports", "Publication & exports"),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setMinimumWidth(258)
        self.setMaximumWidth(258)
        self._collapsed = False
        self._width_animation = None
        self._buttons: dict[str, QToolButton] = {}
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(8, 8, 8, 8)
        self.layout_box.setSpacing(6)
        self.toggle_button = QToolButton()
        self.toggle_button.setObjectName("SidebarToggle")
        self.toggle_button.setText("◀")
        self.toggle_button.setToolTip("Collapse navigation")
        self.toggle_button.setAccessibleName("Collapse or expand navigation sidebar")
        self.toggle_button.clicked.connect(self.toggle)
        self.layout_box.addWidget(self.toggle_button, alignment=Qt.AlignRight)
        for key, title in self.ITEMS:
            button = QToolButton()
            button.setObjectName("SidebarItem")
            button.setText(title)
            button.setToolButtonStyle(Qt.ToolButtonTextOnly)
            button.setMinimumHeight(44)
            button.setMaximumHeight(44)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, name=key: self._select_workspace(name))
            self.layout_box.addWidget(button)
            self._buttons[key] = button
        self.layout_box.addStretch(1)

    def _select_workspace(self, key: str):
        self.set_active(key)
        self.workspace_selected.emit(key)

    def set_active(self, key: str):
        for name, button in self._buttons.items():
            button.setChecked(name == key)

    @property
    def is_collapsed(self) -> bool:
        return self._collapsed

    def toggle(self):
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool):
        self._collapsed = bool(collapsed)
        # 76 px preserves the chevron hit target and the sidebar's inner margins.
        target_width = 76 if self._collapsed else 258
        start_width = self.width()
        if self._width_animation is not None:
            self._width_animation.stop()
        self.setMinimumWidth(58)
        self.setMaximumWidth(start_width)
        self._width_animation = QPropertyAnimation(self, b"maximumWidth", self)
        self._width_animation.setDuration(180)
        self._width_animation.setStartValue(start_width)
        self._width_animation.setEndValue(target_width)
        self._width_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._width_animation.finished.connect(lambda width=target_width: self.setMinimumWidth(width))
        self._width_animation.start()
        self.toggle_button.setText("▶" if self._collapsed else "◀")
        self.toggle_button.setToolTip("Expand navigation" if self._collapsed else "Collapse navigation")
        for key, button in self._buttons.items():
            title = dict(self.ITEMS)[key]
            button.setText(title if not self._collapsed else title[:1])
            button.setToolButtonStyle(Qt.ToolButtonTextOnly)
            button.setMinimumWidth(0)
            button.setMaximumWidth(44 if self._collapsed else 16777215)
            button.setToolTip(title)
        self.collapsed_changed.emit(self._collapsed)

    def set_language(self, language: str, translate):
        for key, button in self._buttons.items():
            button.setToolTip(translate(f"nav_{key}"))
            if not self._collapsed:
                button.setText(translate(f"nav_{key}"))
