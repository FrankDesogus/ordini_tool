from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QTableView, QVBoxLayout

from app.services.exporter import copy_to_clipboard, export_excel, to_tsv
from app.services.query_service import report_fornitori_certificazioni_scadute
from app.ui.pages import OptionalDateEdit
from app.ui.table_model import DictTableModel


class ScaduteReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Report - Fornitori con certificazioni scadute")
        self.resize(950, 600)

        self.columns = [
            ("fornitore_uid", "Fornitore UID"),
            ("ragione_sociale", "Ragione Sociale"),
            ("tipo_certificazione", "Tipo Certificazione"),
            ("data_scadenza", "Data Scadenza"),
            ("dettaglio", "Dettaglio"),
        ]
        self.current_rows: list[dict] = []

        self.dt_ref = OptionalDateEdit()
        self.dt_ref.setDate(self.dt_ref.date().currentDate())
        self.btn_refresh = QPushButton("Aggiorna")
        self.btn_copy = QPushButton("Copia (TSV)")
        self.btn_export = QPushButton("Esporta Excel")

        top = QHBoxLayout()
        top.addWidget(QLabel("Scadute entro:"))
        top.addWidget(self.dt_ref)
        top.addWidget(self.btn_refresh)
        top.addStretch(1)
        top.addWidget(self.btn_copy)
        top.addWidget(self.btn_export)

        self.table = QTableView()
        self.model = DictTableModel([], self.columns, on_cell_edited=None)
        self.table.setModel(self.model)

        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addWidget(self.table, 1)

        self.btn_refresh.clicked.connect(self.refresh)
        self.dt_ref.dateChanged.connect(self.refresh)
        self.btn_copy.clicked.connect(self.export_tsv)
        self.btn_export.clicked.connect(self.export_xlsx)

        self.refresh()

    def refresh(self):
        ref_date = self.dt_ref.value() or date.today()
        self.current_rows = report_fornitori_certificazioni_scadute(ref_date)
        self.model.set_rows(self.current_rows)

    def export_tsv(self):
        copy_to_clipboard(to_tsv(self.current_rows, self.columns))

    def export_xlsx(self):
        from PyQt6.QtWidgets import QFileDialog

        filepath, _ = QFileDialog.getSaveFileName(self, "Esporta Excel", "", "Excel (*.xlsx)")
        if not filepath:
            return
        if not filepath.lower().endswith(".xlsx"):
            filepath += ".xlsx"
        export_excel(self.current_rows, self.columns, filepath)
