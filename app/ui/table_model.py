from __future__ import annotations

from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex

class DictTableModel(QAbstractTableModel):
    def __init__(self, rows: list[dict], columns: list[tuple[str, str]], on_cell_edited=None):
        super().__init__()
        self._rows = rows
        self._columns = columns  # [(key, header)]
        self._on_cell_edited = on_cell_edited

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
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole, Qt.ItemDataRole.EditRole):
            return None
        key = self._columns[index.column()][0]
        value = self._rows[index.row()].get(key)
        if value is None:
            return ""
        return str(value)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        key = self._columns[index.column()][0]
        row_data = self._rows[index.row()]
        new_value = "" if value is None else str(value)
        old_value = "" if row_data.get(key) is None else str(row_data.get(key))
        if new_value == old_value:
            return True

        if self._on_cell_edited is not None:
            ok = self._on_cell_edited(index.row(), key, new_value)
            if not ok:
                return False

        row_data[key] = new_value
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        return True
