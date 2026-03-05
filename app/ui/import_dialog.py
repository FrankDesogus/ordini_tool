from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit, QMessageBox
from app.db.session import get_session
from app.services.importer import import_fornitori_csv, import_ordini_csv, import_certificazioni_csv

class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import file (CSV/Excel)")

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.btn_forn = QPushButton("Importa Fornitori")
        self.btn_ord = QPushButton("Importa Ordini")
        self.btn_cert = QPushButton("Importa Certificazioni")
        self.btn_close = QPushButton("Chiudi")

        btns = QHBoxLayout()
        btns.addWidget(self.btn_forn)
        btns.addWidget(self.btn_ord)
        btns.addWidget(self.btn_cert)

        layout = QVBoxLayout(self)
        layout.addLayout(btns)
        layout.addWidget(QLabel("Log import:"))
        layout.addWidget(self.log, 1)
        layout.addWidget(self.btn_close)

        self.btn_close.clicked.connect(self.accept)
        self.btn_forn.clicked.connect(lambda: self._run("fornitori"))
        self.btn_ord.clicked.connect(lambda: self._run("ordini"))
        self.btn_cert.clicked.connect(lambda: self._run("certificazioni"))

    def _pick_file(self) -> str | None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleziona file", "", "File supportati (*.csv *.xlsx *.xls)")
        return path or None

    def _run(self, kind: str) -> None:
        path = self._pick_file()
        if not path:
            return
        with get_session() as s:
            if kind == "fornitori":
                res = import_fornitori_csv(s, path)
            elif kind == "ordini":
                res = import_ordini_csv(s, path)
            else:
                res = import_certificazioni_csv(s, path)

        msg = f"[{kind}] {path}\n  inserted={res.inserted} updated={res.updated} skipped={res.skipped} errors={res.errors}\n"
        self.log.append(msg)
        if res.errors:
            QMessageBox.warning(self, "Import", f"Import completato con {res.errors} errori. Vedi log.")
        else:
            QMessageBox.information(self, "Import", "Import completato.")
