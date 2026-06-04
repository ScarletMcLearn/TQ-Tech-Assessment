from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _sqlite_connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _ensure_sqlite_directory(database_url: str) -> None:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite"):
        return
    if not url.database or url.database == ":memory:":
        return
    Path(url.database).parent.mkdir(parents=True, exist_ok=True)


settings = get_settings()
_ensure_sqlite_directory(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args=_sqlite_connect_args(settings.database_url),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from app import models  # noqa: F401

    _ensure_sqlite_directory(get_settings().database_url)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
