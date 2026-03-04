from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Fornitore, Ordine

def compute_punctualita_for_fornitore(session: Session, fornitore_uid: str) -> float | None:
    orders = session.scalars(
        select(Ordine).where(Ordine.fornitore_external_uid == fornitore_uid)
    ).all()

    valutabili = 0
    puntuali = 0

    for o in orders:
        if o.data_effettiva is None:
            continue
        # riferimento: conferma se c'è, altrimenti richiesta
        ref = o.data_conferma or o.data_richiesta
        if ref is None:
            continue
        valutabili += 1
        if o.data_effettiva <= ref:
            puntuali += 1

    if valutabili == 0:
        return None
    return (puntuali / valutabili) * 100.0

def update_all_kpi(session: Session) -> tuple[int, int]:
    fornitori = session.scalars(select(Fornitore)).all()
    updated = 0
    nulls = 0
    now = datetime.utcnow()
    for f in fornitori:
        kpi = compute_punctualita_for_fornitore(session, f.external_uid)
        f.puntualita_consegne_pct = kpi
        f.kpi_last_update = now
        updated += 1
        if kpi is None:
            nulls += 1
    session.commit()
    return updated, nulls
