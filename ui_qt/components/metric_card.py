from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout


class MetricCard(QFrame):
    """Compact, accessible estimate card with optional CI and p-value."""

    def __init__(self, title: str, value: str, detail: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("MetricTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setFixedHeight(40)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        self.value_label.setWordWrap(True)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setMinimumHeight(48)
        self.value_label.setContentsMargins(8, 8, 8, 8)
        self.value_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding)
        self.detail_label = QLabel(detail)
        self.detail_label.setObjectName("MetricDetail")
        self.detail_label.setWordWrap(True)
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.detail_label)

    def set_metric(self, title: str, value: str, detail: str = "") -> None:
        self.title_label.setText(title)
        self.value_label.setText(value)
        self.detail_label.setText(detail)
