from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select

from app.db.models import Fornitore, Ordine, Certificazione
from app.db.session import get_session
from app.services.parsing import parse_date, parse_datetime, parse_float

STRING_FIELDS_FORNITORE = {"external_uid", "ragione_sociale", "tipo", "ambito_fornitura", "stato_approvazione", "note"}
FLOAT_FIELDS_FORNITORE = {"puntualita_consegne_pct"}
DATETIME_FIELDS_FORNITORE = {"kpi_last_update", "ultimo_sync"}

STRING_FIELDS_ORDINE = {
    "external_uid", "numero", "fornitore_external_uid", "operatore_codice", "operatore_nome", "tipo_imputazione",
    "imputazione", "stato", "conferma", "note", "name"
}
FLOAT_FIELDS_ORDINE = {"importo_totale_eur", "imp_tot_da_evadere_eur", "imp_tot_evaso_eur", "valuta_usd", "valuta_gbp"}
DATE_FIELDS_ORDINE = {"data", "data_richiesta", "data_conferma", "data_effettiva"}
DATETIME_FIELDS_ORDINE = {"ultimo_sync"}

STRING_FIELDS_CERT = {
    "external_uid", "fornitore_external_uid", "tipo_certificazione", "certificazioni_altro_dettaglio", "codice_certificazione"
}
DATE_FIELDS_CERT = {"data_scadenza"}
DATETIME_FIELDS_CERT = {"ultimo_sync"}


def create_fornitore() -> None:
    with get_session() as s:
        uid = f"FOR-{uuid4().hex[:8]}"
        while s.scalar(select(Fornitore).where(Fornitore.external_uid == uid)) is not None:
            uid = f"FOR-{uuid4().hex[:8]}"
        s.add(Fornitore(external_uid=uid))
        s.commit()


def create_ordine() -> None:
    with get_session() as s:
        first_fornitore = s.scalar(select(Fornitore).limit(1))
        if first_fornitore is None:
            first_fornitore = Fornitore(external_uid=f"FOR-{uuid4().hex[:8]}")
            s.add(first_fornitore)
            s.flush()

        uid = f"ORD-{uuid4().hex[:8]}"
        while s.scalar(select(Ordine).where(Ordine.external_uid == uid)) is not None:
            uid = f"ORD-{uuid4().hex[:8]}"
        s.add(Ordine(external_uid=uid, fornitore_external_uid=first_fornitore.external_uid))
        s.commit()


def create_certificazione() -> None:
    with get_session() as s:
        first_fornitore = s.scalar(select(Fornitore).limit(1))
        if first_fornitore is None:
            first_fornitore = Fornitore(external_uid=f"FOR-{uuid4().hex[:8]}")
            s.add(first_fornitore)
            s.flush()

        uid = f"CERT-{uuid4().hex[:8]}"
        while s.scalar(select(Certificazione).where(Certificazione.external_uid == uid)) is not None:
            uid = f"CERT-{uuid4().hex[:8]}"
        s.add(Certificazione(external_uid=uid, fornitore_external_uid=first_fornitore.external_uid))
        s.commit()


def delete_fornitore(record_id: int) -> None:
    with get_session() as s:
        obj = s.get(Fornitore, record_id)
        if obj:
            s.delete(obj)
            s.commit()


def delete_ordine(record_id: int) -> None:
    with get_session() as s:
        obj = s.get(Ordine, record_id)
        if obj:
            s.delete(obj)
            s.commit()


def delete_certificazione(record_id: int) -> None:
    with get_session() as s:
        obj = s.get(Certificazione, record_id)
        if obj:
            s.delete(obj)
            s.commit()


def delete_all_data() -> None:
    with get_session() as s:
        s.execute(delete(Certificazione))
        s.execute(delete(Ordine))
        s.execute(delete(Fornitore))
        s.commit()


def update_fornitore_field(record_id: int, field: str, raw_value: str) -> None:
    with get_session() as s:
        obj = s.get(Fornitore, record_id)
        if obj is None:
            return

        if field == "external_uid":
            old_uid = obj.external_uid
            new_uid = _as_nullable_string(raw_value)
            if not new_uid:
                raise ValueError("external_uid non può essere vuoto")
            if new_uid != old_uid and s.scalar(select(Fornitore).where(Fornitore.external_uid == new_uid)):
                raise ValueError("external_uid già esistente")
            obj.external_uid = new_uid
            for ordine in obj.ordini:
                ordine.fornitore_external_uid = new_uid
            for cert in obj.certificazioni:
                cert.fornitore_external_uid = new_uid
        elif field in STRING_FIELDS_FORNITORE:
            setattr(obj, field, _as_nullable_string(raw_value))
        elif field in FLOAT_FIELDS_FORNITORE:
            setattr(obj, field, parse_float(raw_value))
        elif field in DATETIME_FIELDS_FORNITORE:
            setattr(obj, field, parse_datetime(raw_value))
        s.commit()


def update_ordine_field(record_id: int, field: str, raw_value: str) -> None:
    with get_session() as s:
        obj = s.get(Ordine, record_id)
        if obj is None:
            return

        if field == "external_uid":
            v = _as_nullable_string(raw_value)
            if not v:
                raise ValueError("external_uid non può essere vuoto")
            if v != obj.external_uid and s.scalar(select(Ordine).where(Ordine.external_uid == v)):
                raise ValueError("external_uid già esistente")
            obj.external_uid = v
        elif field == "fornitore_external_uid":
            v = _as_nullable_string(raw_value)
            if not v:
                raise ValueError("fornitore_external_uid non può essere vuoto")
            f = s.scalar(select(Fornitore).where(Fornitore.external_uid == v))
            if f is None:
                f = Fornitore(external_uid=v)
                s.add(f)
            obj.fornitore_external_uid = v
        elif field in STRING_FIELDS_ORDINE:
            setattr(obj, field, _as_nullable_string(raw_value))
        elif field in FLOAT_FIELDS_ORDINE:
            setattr(obj, field, parse_float(raw_value))
        elif field in DATE_FIELDS_ORDINE:
            setattr(obj, field, parse_date(raw_value))
        elif field in DATETIME_FIELDS_ORDINE:
            setattr(obj, field, parse_datetime(raw_value))
        s.commit()


def update_certificazione_field(record_id: int, field: str, raw_value: str) -> None:
    with get_session() as s:
        obj = s.get(Certificazione, record_id)
        if obj is None:
            return

        if field == "external_uid":
            v = _as_nullable_string(raw_value)
            if not v:
                raise ValueError("external_uid non può essere vuoto")
            if v != obj.external_uid and s.scalar(select(Certificazione).where(Certificazione.external_uid == v)):
                raise ValueError("external_uid già esistente")
            obj.external_uid = v
        elif field == "fornitore_external_uid":
            v = _as_nullable_string(raw_value)
            if not v:
                raise ValueError("fornitore_external_uid non può essere vuoto")
            f = s.scalar(select(Fornitore).where(Fornitore.external_uid == v))
            if f is None:
                f = Fornitore(external_uid=v)
                s.add(f)
            obj.fornitore_external_uid = v
        elif field in STRING_FIELDS_CERT:
            setattr(obj, field, _as_nullable_string(raw_value))
        elif field in DATE_FIELDS_CERT:
            setattr(obj, field, parse_date(raw_value))
        elif field in DATETIME_FIELDS_CERT:
            setattr(obj, field, parse_datetime(raw_value))
        s.commit()


def _as_nullable_string(v: str | None) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    if s.lower() == "nan":
        return None
    return s
