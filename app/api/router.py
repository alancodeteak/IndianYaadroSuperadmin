from fastapi import APIRouter

from app.api.v1.routers.health import router as health_router


def get_api_router() -> APIRouter:
    router = APIRouter()

    router.include_router(health_router)

    # Future: include routers per feature:
    # router.include_router(auth_router, prefix="/auth", tags=["auth"])
    return router

