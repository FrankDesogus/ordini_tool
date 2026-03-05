from __future__ import annotations

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from app.ui.import_dialog import ImportDialog
from app.ui.pages import CertificazioniPage, FornitoriPage, OrdiniPage
from app.ui.report_dialog import ScaduteReportDialog


class MainWindow(QMainWindow):
    def __init__(self, db_path: str):
        super().__init__()
        self.setWindowTitle("Ordini Tool")
        self.db_path = db_path

        self.tabs = QTabWidget()
        self.fornitori_page = FornitoriPage()
        self.ordini_page = OrdiniPage()
        self.cert_page = CertificazioniPage()

        self.tabs.addTab(self.fornitori_page, "Fornitori")
        self.tabs.addTab(self.ordini_page, "Ordini")
        self.tabs.addTab(self.cert_page, "Certificazioni")

        self.setCentralWidget(self.tabs)

        self._build_menu()
        self.statusBar().showMessage(f"DB aperto: {self.db_path}")

    def _build_menu(self):
        m_file = self.menuBar().addMenu("File")
        m_report = self.menuBar().addMenu("Report")

        act_import = QAction("Importa CSV", self)
        act_import.triggered.connect(self.open_import)

        act_refresh = QAction("Ricarica tabelle", self)
        act_refresh.triggered.connect(self.refresh_all)

        act_about = QAction("Info", self)
        act_about.triggered.connect(self.about)

        act_report_scadute = QAction("Fornitori con certificazioni scadute", self)
        act_report_scadute.triggered.connect(self.open_report_scadute)

        m_file.addAction(act_import)
        m_file.addAction(act_refresh)
        m_file.addSeparator()
        m_file.addAction(act_about)

        m_report.addAction(act_report_scadute)

    def open_import(self):
        dlg = ImportDialog(self)
        dlg.exec()
        self.refresh_all()

    def refresh_all(self):
        self.fornitori_page.refresh()
        self.ordini_page.refresh()
        self.cert_page.refresh()
        self.statusBar().showMessage(f"DB aperto: {self.db_path}")

    def open_report_scadute(self):
        dlg = ScaduteReportDialog(self)
        dlg.exec()

    def about(self):
        QMessageBox.information(self, "Info", "Ordini Tool\nPyQt6 + SQLite + SQLAlchemy\nImport CSV + KPI puntualità fornitori")
