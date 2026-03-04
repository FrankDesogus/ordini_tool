from __future__ import annotations

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.db.session import init_db

APP_NAME = "Ordini Tool"

def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # DB in ./data/app.db
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / "app.db"

    init_db(f"sqlite:///{db_path}")

    w = MainWindow()
    w.resize(1200, 750)
    w.show()

    sys.exit(app.exec())
