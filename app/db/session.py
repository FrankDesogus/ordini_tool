from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from app.db.models import Base

_ENGINE = None
_SessionFactory = None

def init_db(db_url: str) -> None:
    global _ENGINE, _SessionFactory
    _ENGINE = create_engine(db_url, future=True)
    Base.metadata.create_all(_ENGINE)
    _SessionFactory = scoped_session(sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, future=True))

def get_session():
    if _SessionFactory is None:
        raise RuntimeError("DB not initialized. Call init_db() first.")
    return _SessionFactory()
