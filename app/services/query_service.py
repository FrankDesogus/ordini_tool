from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import Select, exists, func, or_, select

from app.db.models import Certificazione, Fornitore, Ordine
from app.db.session import get_session


@dataclass(slots=True)
class FornitoriFilters:
    text: str = ""
    stato_approvazione: str | None = None
    only_expired: bool = False
    scadenza_entro: date | None = None


@dataclass(slots=True)
class OrdiniFilters:
    text: str = ""
    fornitore_external_uid: str | None = None
    stato: str | None = None
    data_da: date | None = None
    data_a: date | None = None


@dataclass(slots=True)
class CertificazioniFilters:
    text: str = ""
    fornitore_external_uid: str | None = None
    tipo_certificazione: str | None = None
    scadenza_da: date | None = None
    scadenza_a: date | None = None


def _contains_ci(column, text: str):
    return func.lower(column).like(f"%{text.lower()}%")


def query_fornitori(filters: FornitoriFilters) -> list[Fornitore]:
    with get_session() as s:
        stmt: Select = select(Fornitore)

        q = filters.text.strip()
        if q:
            stmt = stmt.where(
                or_(
                    _contains_ci(Fornitore.ragione_sociale, q),
                    _contains_ci(Fornitore.external_uid, q),
                )
            )

        if filters.stato_approvazione:
            stmt = stmt.where(Fornitore.stato_approvazione == filters.stato_approvazione)

        cutoff: date | None = None
        if filters.only_expired:
            cutoff = filters.scadenza_entro or date.today()
        elif filters.scadenza_entro:
            cutoff = filters.scadenza_entro

        if cutoff:
            cert_exists = exists(
                select(1).where(
                    Certificazione.fornitore_external_uid == Fornitore.external_uid,
                    Certificazione.data_scadenza.is_not(None),
                    Certificazione.data_scadenza <= cutoff,
                )
            )
            stmt = stmt.where(cert_exists)

        stmt = stmt.order_by(Fornitore.ragione_sociale.asc(), Fornitore.external_uid.asc())
        return s.scalars(stmt).all()


def query_ordini(filters: OrdiniFilters) -> list[Ordine]:
    with get_session() as s:
        stmt: Select = select(Ordine)

        q = filters.text.strip()
        if q:
            stmt = stmt.where(
                or_(
                    _contains_ci(Ordine.numero, q),
                    _contains_ci(Ordine.stato, q),
                    _contains_ci(Ordine.fornitore_external_uid, q),
                    _contains_ci(Ordine.external_uid, q),
                )
            )

        if filters.fornitore_external_uid:
            stmt = stmt.where(Ordine.fornitore_external_uid == filters.fornitore_external_uid)
        if filters.stato:
            stmt = stmt.where(Ordine.stato == filters.stato)
        if filters.data_da:
            stmt = stmt.where(Ordine.data >= filters.data_da)
        if filters.data_a:
            stmt = stmt.where(Ordine.data <= filters.data_a)

        stmt = stmt.order_by(Ordine.data.desc(), Ordine.id.desc())
        return s.scalars(stmt).all()


def query_certificazioni(filters: CertificazioniFilters) -> list[Certificazione]:
    with get_session() as s:
        stmt: Select = select(Certificazione)

        q = filters.text.strip()
        if q:
            stmt = stmt.where(
                or_(
                    _contains_ci(Certificazione.tipo_certificazione, q),
                    _contains_ci(Certificazione.fornitore_external_uid, q),
                    _contains_ci(Certificazione.external_uid, q),
                )
            )

        if filters.fornitore_external_uid:
            stmt = stmt.where(Certificazione.fornitore_external_uid == filters.fornitore_external_uid)
        if filters.tipo_certificazione:
            stmt = stmt.where(Certificazione.tipo_certificazione == filters.tipo_certificazione)
        if filters.scadenza_da:
            stmt = stmt.where(Certificazione.data_scadenza >= filters.scadenza_da)
        if filters.scadenza_a:
            stmt = stmt.where(Certificazione.data_scadenza <= filters.scadenza_a)

        stmt = stmt.order_by(Certificazione.data_scadenza.asc(), Certificazione.id.desc())
        return s.scalars(stmt).all()


def report_fornitori_certificazioni_scadute(as_of: date) -> list[dict]:
    with get_session() as s:
        stmt = (
            select(
                Fornitore.external_uid,
                Fornitore.ragione_sociale,
                Certificazione.tipo_certificazione,
                Certificazione.data_scadenza,
                Certificazione.certificazioni_altro_dettaglio,
            )
            .join(Certificazione, Certificazione.fornitore_external_uid == Fornitore.external_uid)
            .where(Certificazione.data_scadenza.is_not(None), Certificazione.data_scadenza <= as_of)
            .order_by(Fornitore.ragione_sociale.asc(), Certificazione.data_scadenza.asc())
        )
        rows = s.execute(stmt).all()
        return [
            {
                "fornitore_uid": item[0],
                "ragione_sociale": item[1],
                "tipo_certificazione": item[2],
                "data_scadenza": item[3],
                "dettaglio": item[4],
            }
            for item in rows
        ]


def distinct_stati_approvazione() -> list[str]:
    with get_session() as s:
        stmt = select(Fornitore.stato_approvazione).where(Fornitore.stato_approvazione.is_not(None)).distinct().order_by(Fornitore.stato_approvazione.asc())
        return [v for v in s.scalars(stmt).all() if v]


def distinct_ordini_stati() -> list[str]:
    with get_session() as s:
        stmt = select(Ordine.stato).where(Ordine.stato.is_not(None)).distinct().order_by(Ordine.stato.asc())
        return [v for v in s.scalars(stmt).all() if v]


def distinct_tipi_certificazione() -> list[str]:
    with get_session() as s:
        stmt = (
            select(Certificazione.tipo_certificazione)
            .where(Certificazione.tipo_certificazione.is_not(None))
            .distinct()
            .order_by(Certificazione.tipo_certificazione.asc())
        )
        return [v for v in s.scalars(stmt).all() if v]


def fornitori_options() -> list[tuple[str, str]]:
    with get_session() as s:
        stmt = select(Fornitore.external_uid, Fornitore.ragione_sociale).order_by(Fornitore.ragione_sociale.asc(), Fornitore.external_uid.asc())
        return [(uid, name or uid) for uid, name in s.execute(stmt).all()]
