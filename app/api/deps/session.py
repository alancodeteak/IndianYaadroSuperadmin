from functools import lru_cache

from app.services.session_service import SessionService


@lru_cache
def get_session_service() -> SessionService:
    return SessionService()

