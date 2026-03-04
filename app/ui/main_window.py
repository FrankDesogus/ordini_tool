from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PyQt6.QtGui import QAction

from app.ui.pages import FornitoriPage, OrdiniPage, CertificazioniPage
from app.ui.import_dialog import ImportDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ordini Tool")

        self.tabs = QTabWidget()
        self.fornitori_page = FornitoriPage()
        self.ordini_page = OrdiniPage()
        self.cert_page = CertificazioniPage()

        self.tabs.addTab(self.fornitori_page, "Fornitori")
        self.tabs.addTab(self.ordini_page, "Ordini")
        self.tabs.addTab(self.cert_page, "Certificazioni")

        self.setCentralWidget(self.tabs)

        self._build_menu()

    def _build_menu(self):
        m_file = self.menuBar().addMenu("File")

        act_import = QAction("Importa CSV", self)
        act_import.triggered.connect(self.open_import)

        act_refresh = QAction("Ricarica tabelle", self)
        act_refresh.triggered.connect(self.refresh_all)

        act_about = QAction("Info", self)
        act_about.triggered.connect(self.about)

        m_file.addAction(act_import)
        m_file.addAction(act_refresh)
        m_file.addSeparator()
        m_file.addAction(act_about)

    def open_import(self):
        dlg = ImportDialog(self)
        dlg.exec()
        self.refresh_all()

    def refresh_all(self):
        self.fornitori_page.refresh()
        self.ordini_page.refresh()
        self.cert_page.refresh()

    def about(self):
        QMessageBox.information(self, "Info", "Ordini Tool\nPyQt6 + SQLite + SQLAlchemy\nImport CSV + KPI puntualità fornitori")
