from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()


def _is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def _create_engine() -> Engine:
    database_url = settings.database_url
    connect_args = {"check_same_thread": False} if _is_sqlite_url(database_url) else {}

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        pool_pre_ping=not _is_sqlite_url(database_url),
    )

    if _is_sqlite_url(database_url):

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
