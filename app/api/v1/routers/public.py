from fastapi import APIRouter

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.health import router as health_router


def get_public_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(auth_router)
    return router

