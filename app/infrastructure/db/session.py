import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Import models so metadata is fully registered when used by migration/tools.
from app.infrastructure.db.models import Base  # noqa: F401


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite+pysqlite:///./superadmin.db")


engine = create_engine(_database_url(), future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

