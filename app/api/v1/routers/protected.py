from fastapi import APIRouter

from app.api.v1.routers.supermarkets_group import supermarkets_router
from app.api.v1.routers.uploads import router as uploads_router


def get_protected_router() -> APIRouter:
    router = APIRouter()
    router.include_router(supermarkets_router)
    router.include_router(uploads_router)
    return router

