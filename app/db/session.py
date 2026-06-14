from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def _get_engine() -> Engine:
    return create_engine(
        get_settings().database_url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True,
    )


@lru_cache
def _get_session_local() -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())


def get_db() -> Generator[Session, None, None]:
    db = _get_session_local()()
    try:
        yield db
    finally:
        db.close()
