from fastapi import APIRouter

from app.api.v1.routers.analytics import router as analytics_router
from app.api.v1.routers.daily_activity.routes import router as daily_activity_router
from app.api.v1.routers.delivery_partners import router as delivery_partners_router
from app.api.v1.routers.sales_activity.routes import router as sales_activity_router
from app.api.v1.routers.invoices.routes import portal_router as portal_invoices_router
from app.api.v1.routers.invoices.routes import router as invoices_router
from app.api.v1.routers.supermarkets_group import supermarkets_router
from app.api.v1.routers.uploads import router as uploads_router


def get_protected_router() -> APIRouter:
    router = APIRouter()
    router.include_router(supermarkets_router)
    router.include_router(analytics_router)
    router.include_router(daily_activity_router)
    router.include_router(sales_activity_router)
    router.include_router(delivery_partners_router)
    router.include_router(invoices_router)
    router.include_router(portal_invoices_router)
    router.include_router(uploads_router)
    return router

