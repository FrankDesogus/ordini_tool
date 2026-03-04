from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex

class DictTableModel(QAbstractTableModel):
    def __init__(self, rows: list[dict], columns: list[tuple[str, str]]):
        super().__init__()
        self._rows = rows
        self._columns = columns  # [(key, header)]

    def set_rows(self, rows: list[dict]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._columns[section][1]
        return str(section + 1)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return None
        key = self._columns[index.column()][0]
        value = self._rows[index.row()].get(key)
        if value is None:
            return ""
        return str(value)
