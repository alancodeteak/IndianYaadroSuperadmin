from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Session, sessionmaker

from app.api.core.config import get_settings
# Import models so metadata is fully registered when used by migration/tools.
from app.infrastructure.db.models import Base  # noqa: F401
from app.infrastructure.db.models.enums import ShopPaymentStatus, ShopStatus, SubscriptionStatus


def _database_url() -> str:
    return get_settings().DATABASE_URL


def _use_enum_values(enum_type: SAEnum) -> None:
    # Patch SQLAlchemy Enum to persist Enum.value (lowercase) instead of Enum.name (uppercase).
    # This is a runtime-only change; it does not change DB schema or model definitions.
    enum_type.values_callable = lambda enum_cls: [e.value for e in enum_cls]  # type: ignore[assignment]
    enum_type.enums = [e.value for e in enum_type.enum_class]  # type: ignore[attr-defined]


def _configure_enum_storage() -> None:
    # ShopOwner.status
    t = Base.metadata.tables.get("shop_owners")
    if t is not None and isinstance(t.c.status.type, SAEnum):
        _use_enum_values(t.c.status.type)
    if t is not None and isinstance(t.c.payment_status.type, SAEnum):
        _use_enum_values(t.c.payment_status.type)

    # Subscription.status
    ts = Base.metadata.tables.get("subscriptions")
    if ts is not None and isinstance(ts.c.status.type, SAEnum):
        _use_enum_values(ts.c.status.type)


_configure_enum_storage()


def _engine_args() -> dict:
    settings = get_settings()
    url = _database_url()
    common = {
        "future": True,
        "pool_pre_ping": True,
        "pool_recycle": int(settings.DB_POOL_RECYCLE_SECONDS),
    }
    if url.startswith("sqlite"):
        # SQLite: use NullPool semantics via connect_args; avoid multi-threaded pool assumptions.
        return {
            **common,
            "connect_args": {"check_same_thread": False},
        }
    return {
        **common,
        "pool_size": int(settings.DB_POOL_SIZE),
        "max_overflow": int(settings.DB_MAX_OVERFLOW),
    }


engine = create_engine(_database_url(), **_engine_args())
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
