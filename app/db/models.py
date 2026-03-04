from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Date, DateTime, Float, ForeignKey, UniqueConstraint, Text
from datetime import datetime, date

class Base(DeclarativeBase):
    pass

class Fornitore(Base):
    __tablename__ = "fornitori"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    external_uid: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    ragione_sociale: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    tipo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ambito_fornitura: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stato_approvazione: Mapped[str | None] = mapped_column(String(80), nullable=True)

    punctualita_consegne_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    kpi_last_update: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    ultimo_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    ordini = relationship("Ordine", back_populates="fornitore", cascade="all, delete-orphan")
    certificazioni = relationship("Certificazione", back_populates="fornitore", cascade="all, delete-orphan")

class Ordine(Base):
    __tablename__ = "ordini"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    external_uid: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    numero: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    data: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    fornitore_external_uid: Mapped[str] = mapped_column(String(64), ForeignKey("fornitori.external_uid"), nullable=False, index=True)

    operatore_codice: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operatore_nome: Mapped[str | None] = mapped_column(String(255), nullable=True)

    importo_totale_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    imp_tot_da_evadere_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    imp_tot_evaso_eur: Mapped[float | None] = mapped_column(Float, nullable=True)

    valuta_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    valuta_gbp: Mapped[float | None] = mapped_column(Float, nullable=True)

    data_richiesta: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_conferma: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_effettiva: Mapped[date | None] = mapped_column(Date, nullable=True)

    tipo_imputazione: Mapped[str | None] = mapped_column(String(80), nullable=True)
    imputazione: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stato: Mapped[str | None] = mapped_column(String(80), nullable=True)
    conferma: Mapped[str | None] = mapped_column(String(80), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    ultimo_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    fornitore = relationship("Fornitore", back_populates="ordini")

class Certificazione(Base):
    __tablename__ = "certificazioni"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    external_uid: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    fornitore_external_uid: Mapped[str] = mapped_column(String(64), ForeignKey("fornitori.external_uid"), nullable=False, index=True)

    tipo_certificazione: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    certificazioni_altro_dettaglio: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_scadenza: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    codice_certificazione: Mapped[str | None] = mapped_column(String(120), nullable=True)

    ultimo_sync: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    fornitore = relationship("Fornitore", back_populates="certificazioni")
