from __future__ import annotations

from datetime import date

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.services.crud import (
    create_certificazione,
    create_fornitore,
    create_ordine,
    delete_certificazione,
    delete_fornitore,
    delete_ordine,
    update_certificazione_field,
    update_fornitore_field,
    update_ordine_field,
)
from app.services.exporter import copy_to_clipboard, export_excel, to_tsv
from app.services.kpi import update_all_kpi
from app.services.query_service import (
    CertificazioniFilters,
    FornitoriFilters,
    OrdiniFilters,
    distinct_ordini_stati,
    distinct_stati_approvazione,
    distinct_tipi_certificazione,
    fornitori_options,
    query_certificazioni,
    query_fornitori,
    query_ordini,
)
from app.db.session import get_session
from app.ui.table_model import DictTableModel


class OptionalDateEdit(QDateEdit):
    MIN_DATE = QDate(1900, 1, 1)

    def __init__(self):
        super().__init__()
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy-MM-dd")
        self.setSpecialValueText("—")
        self.setMinimumDate(self.MIN_DATE)
        self.setDate(self.MIN_DATE)

    def value(self) -> date | None:
        qd = self.date()
        if qd == self.MIN_DATE:
            return None
        return qd.toPyDate()


class ExportMixin:
    columns: list[tuple[str, str]]
    current_rows: list[dict]

    def export_tsv(self):
        tsv = to_tsv(self.current_rows, self.columns)
        copy_to_clipboard(tsv)
        QMessageBox.information(self, "Esporta", f"Copiate {len(self.current_rows)} righe negli appunti.")

    def export_excel(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Esporta Excel", "", "Excel (*.xlsx)")
        if not filepath:
            return
        if not filepath.lower().endswith(".xlsx"):
            filepath += ".xlsx"
        export_excel(self.current_rows, self.columns, filepath)
        QMessageBox.information(self, "Esporta", f"Esportate {len(self.current_rows)} righe in:\n{filepath}")


class FornitoriPage(QWidget, ExportMixin):
    def __init__(self):
        super().__init__()
        self.current_rows: list[dict] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Cerca ragione sociale / UID...")
        self.cmb_stato = QComboBox()
        self.chk_scadute = QCheckBox("Solo fornitori con certificazioni scadute")
        self.dt_scadenza_entro = OptionalDateEdit()

        self.btn_refresh = QPushButton("Aggiorna")
        self.btn_kpi = QPushButton("Calcola KPI puntualità")
        self.btn_add = QPushButton("Nuovo")
        self.btn_delete = QPushButton("Elimina")
        self.btn_copy = QPushButton("Copia (TSV)")
        self.btn_export = QPushButton("Esporta Excel")

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Ricerca:"))
        filter_row.addWidget(self.search, 1)
        filter_row.addWidget(QLabel("Stato approvazione:"))
        filter_row.addWidget(self.cmb_stato)
        filter_row.addWidget(self.chk_scadute)
        filter_row.addWidget(QLabel("Scadenza entro:"))
        filter_row.addWidget(self.dt_scadenza_entro)

        action_row = QHBoxLayout()
        action_row.addWidget(self.btn_add)
        action_row.addWidget(self.btn_delete)
        action_row.addWidget(self.btn_kpi)
        action_row.addWidget(self.btn_copy)
        action_row.addWidget(self.btn_export)
        action_row.addStretch(1)
        action_row.addWidget(self.btn_refresh)

        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        layout = QVBoxLayout(self)
        layout.addLayout(filter_row)
        layout.addLayout(action_row)
        layout.addWidget(self.table, 1)

        self._row_ids: list[int] = []
        self.columns = [
            ("external_uid", "UID"),
            ("ragione_sociale", "Ragione Sociale"),
            ("tipo", "Tipo"),
            ("ambito_fornitura", "Ambito"),
            ("stato_approvazione", "Stato Approv."),
            ("puntualita_consegne_pct", "Puntualità %"),
            ("kpi_last_update", "KPI aggiornato"),
            ("note", "Note"),
            ("ultimo_sync", "Ultimo Sync"),
        ]
        self.model = DictTableModel([], self.columns, on_cell_edited=self._on_cell_edited)
        self.table.setModel(self.model)

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_add.clicked.connect(self.add_record)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_kpi.clicked.connect(self.compute_kpi)
        self.search.textChanged.connect(self.refresh)
        self.cmb_stato.currentIndexChanged.connect(self.refresh)
        self.chk_scadute.toggled.connect(self.refresh)
        self.dt_scadenza_entro.dateChanged.connect(self.refresh)
        self.btn_copy.clicked.connect(self.export_tsv)
        self.btn_export.clicked.connect(self.export_excel)

        self.refresh()

    def _current_filters(self) -> FornitoriFilters:
        stato = self.cmb_stato.currentData()
        return FornitoriFilters(
            text=self.search.text(),
            stato_approvazione=stato,
            only_expired=self.chk_scadute.isChecked(),
            scadenza_entro=self.dt_scadenza_entro.value(),
        )

    def _populate_filters(self):
        selected = self.cmb_stato.currentData()
        self.cmb_stato.blockSignals(True)
        self.cmb_stato.clear()
        self.cmb_stato.addItem("Tutti", None)
        for stato in distinct_stati_approvazione():
            self.cmb_stato.addItem(stato, stato)
        idx = self.cmb_stato.findData(selected)
        self.cmb_stato.setCurrentIndex(0 if idx < 0 else idx)
        self.cmb_stato.blockSignals(False)

    def refresh(self):
        self._populate_filters()
        items = query_fornitori(self._current_filters())
        self._row_ids = [f.id for f in items]
        rows = []
        for f in items:
            rows.append(
                {
                    "external_uid": f.external_uid,
                    "ragione_sociale": f.ragione_sociale,
                    "tipo": f.tipo,
                    "ambito_fornitura": f.ambito_fornitura,
                    "stato_approvazione": f.stato_approvazione,
                    "puntualita_consegne_pct": None if f.puntualita_consegne_pct is None else round(f.puntualita_consegne_pct, 2),
                    "kpi_last_update": f.kpi_last_update,
                    "note": f.note,
                    "ultimo_sync": f.ultimo_sync,
                }
            )
        self.current_rows = rows
        self.model.set_rows(rows)

    def _on_cell_edited(self, row: int, field: str, value: str) -> bool:
        try:
            update_fornitore_field(self._row_ids[row], field, value)
            return True
        except Exception as ex:
            QMessageBox.warning(self, "Modifica non valida", str(ex))
            return False

    def add_record(self):
        create_fornitore()
        self.refresh()

    def delete_selected(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return
        delete_fornitore(self._row_ids[idx.row()])
        self.refresh()

    def compute_kpi(self):
        with get_session() as s:
            updated, nulls = update_all_kpi(s)
        QMessageBox.information(self, "KPI", f"KPI aggiornato per {updated} fornitori. (KPI non calcolabile per {nulls}).")
        self.refresh()


class OrdiniPage(QWidget, ExportMixin):
    def __init__(self):
        super().__init__()
        self.current_rows: list[dict] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Cerca numero / fornitore UID / stato...")
        self.cmb_fornitore = QComboBox()
        self.cmb_stato = QComboBox()
        self.dt_da = OptionalDateEdit()
        self.dt_a = OptionalDateEdit()

        self.btn_refresh = QPushButton("Aggiorna")
        self.btn_add = QPushButton("Nuovo")
        self.btn_delete = QPushButton("Elimina")
        self.btn_copy = QPushButton("Copia (TSV)")
        self.btn_export = QPushButton("Esporta Excel")

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Ricerca:"))
        filter_row.addWidget(self.search, 1)
        filter_row.addWidget(QLabel("Fornitore:"))
        filter_row.addWidget(self.cmb_fornitore)
        filter_row.addWidget(QLabel("Stato:"))
        filter_row.addWidget(self.cmb_stato)
        filter_row.addWidget(QLabel("Data da:"))
        filter_row.addWidget(self.dt_da)
        filter_row.addWidget(QLabel("a:"))
        filter_row.addWidget(self.dt_a)

        action_row = QHBoxLayout()
        action_row.addWidget(self.btn_add)
        action_row.addWidget(self.btn_delete)
        action_row.addWidget(self.btn_copy)
        action_row.addWidget(self.btn_export)
        action_row.addStretch(1)
        action_row.addWidget(self.btn_refresh)

        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.addLayout(filter_row)
        layout.addLayout(action_row)
        layout.addWidget(self.table, 1)

        self._row_ids = []
        self.columns = [
            ("external_uid", "UID"),
            ("numero", "Numero"),
            ("data", "Data"),
            ("fornitore_external_uid", "Fornitore UID"),
            ("importo_totale_eur", "Importo Tot EUR"),
            ("imp_tot_da_evadere_eur", "Da evadere EUR"),
            ("imp_tot_evaso_eur", "Evaso EUR"),
            ("data_richiesta", "Data richiesta"),
            ("data_conferma", "Data conferma"),
            ("data_effettiva", "Data effettiva"),
            ("stato", "Stato"),
            ("imputazione", "Imputazione"),
            ("ultimo_sync", "Ultimo Sync"),
        ]
        self.model = DictTableModel([], self.columns, on_cell_edited=self._on_cell_edited)
        self.table.setModel(self.model)

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_add.clicked.connect(self.add_record)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.search.textChanged.connect(self.refresh)
        self.cmb_fornitore.currentIndexChanged.connect(self.refresh)
        self.cmb_stato.currentIndexChanged.connect(self.refresh)
        self.dt_da.dateChanged.connect(self.refresh)
        self.dt_a.dateChanged.connect(self.refresh)
        self.btn_copy.clicked.connect(self.export_tsv)
        self.btn_export.clicked.connect(self.export_excel)
        self.refresh()

    def _populate_filters(self):
        selected_f = self.cmb_fornitore.currentData()
        selected_s = self.cmb_stato.currentData()

        self.cmb_fornitore.blockSignals(True)
        self.cmb_fornitore.clear()
        self.cmb_fornitore.addItem("Tutti", None)
        for uid, name in fornitori_options():
            self.cmb_fornitore.addItem(f"{name} ({uid})", uid)
        idx = self.cmb_fornitore.findData(selected_f)
        self.cmb_fornitore.setCurrentIndex(0 if idx < 0 else idx)
        self.cmb_fornitore.blockSignals(False)

        self.cmb_stato.blockSignals(True)
        self.cmb_stato.clear()
        self.cmb_stato.addItem("Tutti", None)
        for stato in distinct_ordini_stati():
            self.cmb_stato.addItem(stato, stato)
        idx = self.cmb_stato.findData(selected_s)
        self.cmb_stato.setCurrentIndex(0 if idx < 0 else idx)
        self.cmb_stato.blockSignals(False)

    def _current_filters(self) -> OrdiniFilters:
        return OrdiniFilters(
            text=self.search.text(),
            fornitore_external_uid=self.cmb_fornitore.currentData(),
            stato=self.cmb_stato.currentData(),
            data_da=self.dt_da.value(),
            data_a=self.dt_a.value(),
        )

    def refresh(self):
        self._populate_filters()
        items = query_ordini(self._current_filters())
        self._row_ids = [o.id for o in items]
        rows = []
        for o in items:
            rows.append(
                {
                    "external_uid": o.external_uid,
                    "numero": o.numero,
                    "data": o.data,
                    "fornitore_external_uid": o.fornitore_external_uid,
                    "importo_totale_eur": o.importo_totale_eur,
                    "imp_tot_da_evadere_eur": o.imp_tot_da_evadere_eur,
                    "imp_tot_evaso_eur": o.imp_tot_evaso_eur,
                    "data_richiesta": o.data_richiesta,
                    "data_conferma": o.data_conferma,
                    "data_effettiva": o.data_effettiva,
                    "stato": o.stato,
                    "imputazione": o.imputazione,
                    "ultimo_sync": o.ultimo_sync,
                }
            )
        self.current_rows = rows
        self.model.set_rows(rows)

    def _on_cell_edited(self, row: int, field: str, value: str) -> bool:
        try:
            update_ordine_field(self._row_ids[row], field, value)
            return True
        except Exception as ex:
            QMessageBox.warning(self, "Modifica non valida", str(ex))
            return False

    def add_record(self):
        create_ordine()
        self.refresh()

    def delete_selected(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return
        delete_ordine(self._row_ids[idx.row()])
        self.refresh()


class CertificazioniPage(QWidget, ExportMixin):
    def __init__(self):
        super().__init__()
        self.current_rows: list[dict] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Cerca tipo / fornitore UID / certificazione UID...")
        self.cmb_fornitore = QComboBox()
        self.cmb_tipo = QComboBox()
        self.dt_da = OptionalDateEdit()
        self.dt_a = OptionalDateEdit()

        self.btn_refresh = QPushButton("Aggiorna")
        self.btn_add = QPushButton("Nuovo")
        self.btn_delete = QPushButton("Elimina")
        self.btn_copy = QPushButton("Copia (TSV)")
        self.btn_export = QPushButton("Esporta Excel")

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Ricerca:"))
        filter_row.addWidget(self.search, 1)
        filter_row.addWidget(QLabel("Fornitore:"))
        filter_row.addWidget(self.cmb_fornitore)
        filter_row.addWidget(QLabel("Tipo:"))
        filter_row.addWidget(self.cmb_tipo)
        filter_row.addWidget(QLabel("Scadenza da:"))
        filter_row.addWidget(self.dt_da)
        filter_row.addWidget(QLabel("a:"))
        filter_row.addWidget(self.dt_a)

        action_row = QHBoxLayout()
        action_row.addWidget(self.btn_add)
        action_row.addWidget(self.btn_delete)
        action_row.addWidget(self.btn_copy)
        action_row.addWidget(self.btn_export)
        action_row.addStretch(1)
        action_row.addWidget(self.btn_refresh)

        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.addLayout(filter_row)
        layout.addLayout(action_row)
        layout.addWidget(self.table, 1)

        self._row_ids = []
        self.columns = [
            ("external_uid", "UID"),
            ("fornitore_external_uid", "Fornitore UID"),
            ("tipo_certificazione", "Tipo"),
            ("certificazioni_altro_dettaglio", "Dettaglio"),
            ("data_scadenza", "Scadenza"),
            ("codice_certificazione", "Codice"),
            ("ultimo_sync", "Ultimo Sync"),
        ]
        self.model = DictTableModel([], self.columns, on_cell_edited=self._on_cell_edited)
        self.table.setModel(self.model)

        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_add.clicked.connect(self.add_record)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.search.textChanged.connect(self.refresh)
        self.cmb_fornitore.currentIndexChanged.connect(self.refresh)
        self.cmb_tipo.currentIndexChanged.connect(self.refresh)
        self.dt_da.dateChanged.connect(self.refresh)
        self.dt_a.dateChanged.connect(self.refresh)
        self.btn_copy.clicked.connect(self.export_tsv)
        self.btn_export.clicked.connect(self.export_excel)
        self.refresh()

    def _populate_filters(self):
        selected_f = self.cmb_fornitore.currentData()
        selected_t = self.cmb_tipo.currentData()

        self.cmb_fornitore.blockSignals(True)
        self.cmb_fornitore.clear()
        self.cmb_fornitore.addItem("Tutti", None)
        for uid, name in fornitori_options():
            self.cmb_fornitore.addItem(f"{name} ({uid})", uid)
        idx = self.cmb_fornitore.findData(selected_f)
        self.cmb_fornitore.setCurrentIndex(0 if idx < 0 else idx)
        self.cmb_fornitore.blockSignals(False)

        self.cmb_tipo.blockSignals(True)
        self.cmb_tipo.clear()
        self.cmb_tipo.addItem("Tutti", None)
        for tipo in distinct_tipi_certificazione():
            self.cmb_tipo.addItem(tipo, tipo)
        idx = self.cmb_tipo.findData(selected_t)
        self.cmb_tipo.setCurrentIndex(0 if idx < 0 else idx)
        self.cmb_tipo.blockSignals(False)

    def _current_filters(self) -> CertificazioniFilters:
        return CertificazioniFilters(
            text=self.search.text(),
            fornitore_external_uid=self.cmb_fornitore.currentData(),
            tipo_certificazione=self.cmb_tipo.currentData(),
            scadenza_da=self.dt_da.value(),
            scadenza_a=self.dt_a.value(),
        )

    def refresh(self):
        self._populate_filters()
        items = query_certificazioni(self._current_filters())
        self._row_ids = [c.id for c in items]
        rows = []
        for c in items:
            rows.append(
                {
                    "external_uid": c.external_uid,
                    "fornitore_external_uid": c.fornitore_external_uid,
                    "tipo_certificazione": c.tipo_certificazione,
                    "certificazioni_altro_dettaglio": c.certificazioni_altro_dettaglio,
                    "data_scadenza": c.data_scadenza,
                    "codice_certificazione": c.codice_certificazione,
                    "ultimo_sync": c.ultimo_sync,
                }
            )
        self.current_rows = rows
        self.model.set_rows(rows)

    def _on_cell_edited(self, row: int, field: str, value: str) -> bool:
        try:
            update_certificazione_field(self._row_ids[row], field, value)
            return True
        except Exception as ex:
            QMessageBox.warning(self, "Modifica non valida", str(ex))
            return False

    def add_record(self):
        create_certificazione()
        self.refresh()

    def delete_selected(self):
        idx = self.table.currentIndex()
        if not idx.isValid():
            return
        delete_certificazione(self._row_ids[idx.row()])
        self.refresh()
