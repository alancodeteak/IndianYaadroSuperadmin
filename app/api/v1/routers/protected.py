from fastapi import APIRouter

from app.api.v1.routers.supermarkets_group import supermarkets_router


def get_protected_router() -> APIRouter:
    router = APIRouter()
    router.include_router(supermarkets_router)
    return router

