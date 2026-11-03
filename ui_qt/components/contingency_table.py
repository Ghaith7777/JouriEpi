from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QAbstractSpinBox, QHeaderView, QSpinBox,
                               QTableWidget)


class ContingencyTable(QTableWidget):
    """Editable 2×2 table in the core convention: a,b,c,d."""

    def __init__(self, parent=None):
        super().__init__(2, 2, parent)
        self.setObjectName("ContingencyTable")
        self.setHorizontalHeaderLabels(["Cases / disease +", "Non-cases / disease −"])
        self.setVerticalHeaderLabels(["Exposed", "Unexposed"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setMinimumHeight(130)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.spins = []
        for row in range(2):
            for column in range(2):
                spin = QSpinBox(self)
                spin.setRange(0, 10_000_000)
                spin.setValue(0)
                spin.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
                spin.setAlignment(Qt.AlignCenter)
                spin.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
                self.setCellWidget(row, column, spin)
                self.spins.append(spin)
        self.set_values((12, 18, 5, 25))

    def set_values(self, values):
        if len(values) != 4:
            raise ValueError("Exactly four cell counts are required in a,b,c,d order.")
        for spin, value in zip(self.spins, values):
            spin.setValue(int(value))

    def values(self) -> tuple[int, int, int, int]:
        return tuple(spin.value() for spin in self.spins)
