from app.db.session import init_db, get_session
from pathlib import Path
from app.services.importer import import_fornitori_csv, import_ordini_csv, import_certificazioni_csv

def main():
    data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / "app.db"
    init_db(f"sqlite:///{db_path}")

    with get_session() as s:
        print(import_fornitori_csv(s, r"/mnt/data/fornitori_import.csv"))
        print(import_ordini_csv(s, r"/mnt/data/ordini_import.csv"))
        print(import_certificazioni_csv(s, r"/mnt/data/certificazioni_import.csv"))

if __name__ == "__main__":
    main()
