from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QTableView, QAbstractItemView, QMessageBox
from PyQt6.QtCore import Qt

from sqlalchemy import select
from app.db.session import get_session
from app.db.models import Fornitore, Ordine, Certificazione
from app.ui.table_model import DictTableModel
from app.services.kpi import update_all_kpi

class FornitoriPage(QWidget):
    def __init__(self):
        super().__init__()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cerca ragione sociale / UID...")
        self.btn_refresh = QPushButton("Aggiorna")
        self.btn_kpi = QPushButton("Calcola KPI puntualità")

        top = QHBoxLayout()
        top.addWidget(QLabel("Filtro:"))
        top.addWidget(self.search, 1)
        top.addWidget(self.btn_kpi)
        top.addWidget(self.btn_refresh)

        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table, 1)

        self.model = DictTableModel([], [
            ("external_uid", "UID"),
            ("ragione_sociale", "Ragione Sociale"),
            ("tipo", "Tipo"),
            ("ambito_fornitura", "Ambito"),
            ("stato_approvazione", "Stato Approv."),
            ("puntualita_consegne_pct", "Puntualità %"),
            ("kpi_last_update", "KPI aggiornato"),
            ("note", "Note"),
            ("ultimo_sync", "Ultimo Sync"),
        ])
        self.table.setModel(self.model)

        self.btn_refresh.clicked.connect(self.refresh)
        self.search.textChanged.connect(self.refresh)
        self.btn_kpi.clicked.connect(self.compute_kpi)

        self.refresh()

    def refresh(self):
        q = self.search.text().strip().lower()
        with get_session() as s:
            stmt = select(Fornitore)
            items = s.scalars(stmt).all()
            rows = []
            for f in items:
                if q:
                    hay = f"{f.external_uid} {f.ragione_sociale or ''}".lower()
                    if q not in hay:
                        continue
                rows.append({
                    "external_uid": f.external_uid,
                    "ragione_sociale": f.ragione_sociale,
                    "tipo": f.tipo,
                    "ambito_fornitura": f.ambito_fornitura,
                    "stato_approvazione": f.stato_approvazione,
                    "puntualita_consegne_pct": None if f.puntualita_consegne_pct is None else round(f.puntualita_consegne_pct, 2),
                    "kpi_last_update": f.kpi_last_update,
                    "note": f.note,
                    "ultimo_sync": f.ultimo_sync,
                })
        self.model.set_rows(rows)

    def compute_kpi(self):
        with get_session() as s:
            updated, nulls = update_all_kpi(s)
        QMessageBox.information(self, "KPI", f"KPI aggiornato per {updated} fornitori. (KPI non calcolabile per {nulls}).")
        self.refresh()

class OrdiniPage(QWidget):
    def __init__(self):
        super().__init__()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cerca numero / fornitore UID / stato...")
        self.btn_refresh = QPushButton("Aggiorna")

        top = QHBoxLayout()
        top.addWidget(QLabel("Filtro:"))
        top.addWidget(self.search, 1)
        top.addWidget(self.btn_refresh)

        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table, 1)

        self.model = DictTableModel([], [
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
        ])
        self.table.setModel(self.model)

        self.btn_refresh.clicked.connect(self.refresh)
        self.search.textChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        q = self.search.text().strip().lower()
        with get_session() as s:
            items = s.scalars(select(Ordine)).all()
            rows = []
            for o in items:
                if q:
                    hay = f"{o.numero or ''} {o.fornitore_external_uid} {o.stato or ''} {o.external_uid}".lower()
                    if q not in hay:
                        continue
                rows.append({
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
                })
        self.model.set_rows(rows)

class CertificazioniPage(QWidget):
    def __init__(self):
        super().__init__()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Cerca tipo / fornitore UID...")
        self.btn_refresh = QPushButton("Aggiorna")

        top = QHBoxLayout()
        top.addWidget(QLabel("Filtro:"))
        top.addWidget(self.search, 1)
        top.addWidget(self.btn_refresh)

        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.table, 1)

        self.model = DictTableModel([], [
            ("external_uid", "UID"),
            ("fornitore_external_uid", "Fornitore UID"),
            ("tipo_certificazione", "Tipo"),
            ("certificazioni_altro_dettaglio", "Dettaglio"),
            ("data_scadenza", "Scadenza"),
            ("codice_certificazione", "Codice"),
            ("ultimo_sync", "Ultimo Sync"),
        ])
        self.table.setModel(self.model)

        self.btn_refresh.clicked.connect(self.refresh)
        self.search.textChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        q = self.search.text().strip().lower()
        with get_session() as s:
            items = s.scalars(select(Certificazione)).all()
            rows = []
            for c in items:
                if q:
                    hay = f"{c.fornitore_external_uid} {c.tipo_certificazione or ''} {c.external_uid}".lower()
                    if q not in hay:
                        continue
                rows.append({
                    "external_uid": c.external_uid,
                    "fornitore_external_uid": c.fornitore_external_uid,
                    "tipo_certificazione": c.tipo_certificazione,
                    "certificazioni_altro_dettaglio": c.certificazioni_altro_dettaglio,
                    "data_scadenza": c.data_scadenza,
                    "codice_certificazione": c.codice_certificazione,
                    "ultimo_sync": c.ultimo_sync,
                })
        self.model.set_rows(rows)
