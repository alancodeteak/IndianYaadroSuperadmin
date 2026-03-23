from fastapi import APIRouter

from app.api.v1.routers import get_protected_router, get_public_router


def get_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(get_public_router())
    router.include_router(get_protected_router())
    return router

