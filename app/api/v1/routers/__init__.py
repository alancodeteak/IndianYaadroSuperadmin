"""Versioned routers."""

from app.api.v1.routers.protected import get_protected_router
from app.api.v1.routers.public import get_public_router

__all__ = ["get_public_router", "get_protected_router"]

