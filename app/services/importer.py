from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import pandas as pd

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Fornitore, Ordine, Certificazione
from app.services.parsing import parse_date, parse_datetime, parse_float

@dataclass
class ImportResult:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0

def import_fornitori_csv(session: Session, csv_path: str) -> ImportResult:
    df = pd.read_csv(csv_path)
    res = ImportResult()
    for _, r in df.iterrows():
        try:
            uid = str(r.get("external_uid", "")).strip()
            if not uid:
                res.skipped += 1
                continue

            obj = session.scalar(select(Fornitore).where(Fornitore.external_uid == uid))
            created = obj is None
            if created:
                obj = Fornitore(external_uid=uid)

            obj.ragione_sociale = _to_nullable_str(r.get("ragione_sociale"))
            obj.tipo = _to_nullable_str(r.get("tipo"))
            obj.ambito_fornitura = _to_nullable_str(r.get("ambito_fornitura"))
            obj.stato_approvazione = _to_nullable_str(r.get("stato_approvazione"))
            obj.puntualita_consegne_pct = parse_float(r.get("puntualita_consegne_pct"))
            obj.kpi_last_update = parse_datetime(r.get("kpi_last_update"))
            obj.note = _to_nullable_str(r.get("note"))
            obj.ultimo_sync = parse_datetime(r.get("ultimo_sync"))

            session.add(obj)
            if created:
                res.inserted += 1
            else:
                res.updated += 1
        except Exception:
            res.errors += 1
    session.commit()
    return res

def import_ordini_csv(session: Session, csv_path: str) -> ImportResult:
    df = pd.read_csv(csv_path)
    res = ImportResult()
    for _, r in df.iterrows():
        try:
            uid = str(r.get("external_uid", "")).strip()
            if not uid:
                res.skipped += 1
                continue

            fornitore_uid = str(r.get("fornitore_external_uid", "")).strip()
            if not fornitore_uid:
                res.skipped += 1
                continue

            # FK: il fornitore deve esistere
            f = session.scalar(select(Fornitore).where(Fornitore.external_uid == fornitore_uid))
            if f is None:
                # se ti serve: creare placeholder automatico
                f = Fornitore(external_uid=fornitore_uid)
                session.add(f)

            obj = session.scalar(select(Ordine).where(Ordine.external_uid == uid))
            created = obj is None
            if created:
                obj = Ordine(external_uid=uid, fornitore_external_uid=fornitore_uid)

            obj.numero = _to_nullable_str(r.get("numero"))
            obj.data = parse_date(r.get("data"))
            obj.fornitore_external_uid = fornitore_uid

            obj.operatore_codice = _to_nullable_str(r.get("operatore_codice"))
            obj.operatore_nome = _to_nullable_str(r.get("operatore_nome"))

            obj.importo_totale_eur = parse_float(r.get("importo_totale_eur"))
            obj.imp_tot_da_evadere_eur = parse_float(r.get("imp_tot_da_evadere_eur"))
            obj.imp_tot_evaso_eur = parse_float(r.get("imp_tot_evaso_eur"))
            obj.valuta_usd = parse_float(r.get("valuta_usd"))
            obj.valuta_gbp = parse_float(r.get("valuta_gbp"))

            obj.data_richiesta = parse_date(r.get("data_richiesta"))
            obj.data_conferma = parse_date(r.get("data_conferma"))
            obj.data_effettiva = parse_date(r.get("data_effettiva"))

            obj.tipo_imputazione = _to_nullable_str(r.get("tipo_imputazione"))
            obj.imputazione = _to_nullable_str(r.get("imputazione"))
            obj.stato = _to_nullable_str(r.get("stato"))
            obj.conferma = _to_nullable_str(r.get("conferma"))
            obj.note = _to_nullable_str(r.get("note"))

            obj.ultimo_sync = parse_datetime(r.get("ultimo_sync"))
            obj.name = _to_nullable_str(r.get("name"))

            session.add(obj)
            if created:
                res.inserted += 1
            else:
                res.updated += 1
        except Exception:
            res.errors += 1
    session.commit()
    return res

def import_certificazioni_csv(session: Session, csv_path: str) -> ImportResult:
    df = pd.read_csv(csv_path)
    res = ImportResult()
    for _, r in df.iterrows():
        try:
            uid = str(r.get("external_uid", "")).strip()
            if not uid:
                res.skipped += 1
                continue

            fornitore_uid = str(r.get("fornitore_external_uid", "")).strip()
            if not fornitore_uid:
                res.skipped += 1
                continue

            f = session.scalar(select(Fornitore).where(Fornitore.external_uid == fornitore_uid))
            if f is None:
                f = Fornitore(external_uid=fornitore_uid)
                session.add(f)

            obj = session.scalar(select(Certificazione).where(Certificazione.external_uid == uid))
            created = obj is None
            if created:
                obj = Certificazione(external_uid=uid, fornitore_external_uid=fornitore_uid)

            obj.fornitore_external_uid = fornitore_uid
            obj.tipo_certificazione = _to_nullable_str(r.get("tipo_certificazione"))
            obj.certificazioni_altro_dettaglio = _to_nullable_str(r.get("certificazioni_altro_dettaglio"))
            obj.data_scadenza = parse_date(r.get("data_scadenza"))
            obj.codice_certificazione = _to_nullable_str(r.get("codice_certificazione"))
            obj.ultimo_sync = parse_datetime(r.get("ultimo_sync"))

            session.add(obj)
            if created:
                res.inserted += 1
            else:
                res.updated += 1
        except Exception:
            res.errors += 1
    session.commit()
    return res

def _to_nullable_str(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return None
    return s
