from fastapi import APIRouter, Depends

from app.api.deps import require_authenticated
from app.api.v1.routers.analytics import router as analytics_router
from app.api.v1.routers.daily_activity import router as daily_activity_router
from app.api.v1.routers.dashboard import router as dashboard_router
from app.api.v1.routers.delivery_partners import router as delivery_partners_router
from app.api.v1.routers.invoices import router as invoices_router
from app.api.v1.routers.monitorapp import router as monitorapp_router
from app.api.v1.routers.orders import router as orders_router
from app.api.v1.routers.report import router as report_router
from app.api.v1.routers.search import router as search_router
from app.api.v1.routers.supermarkets import router as supermarkets_router
from app.api.v1.routers.supermarkets_add import router as supermarkets_add_router


def get_protected_router() -> APIRouter:
    router = APIRouter()
    protected_dep = [Depends(require_authenticated)]

    router.include_router(dashboard_router, dependencies=protected_dep)
    router.include_router(search_router, dependencies=protected_dep)
    router.include_router(report_router, dependencies=protected_dep)
    router.include_router(delivery_partners_router, dependencies=protected_dep)
    router.include_router(supermarkets_add_router, dependencies=protected_dep)
    router.include_router(supermarkets_router, dependencies=protected_dep)
    router.include_router(analytics_router, dependencies=protected_dep)
    router.include_router(daily_activity_router, dependencies=protected_dep)
    router.include_router(invoices_router, dependencies=protected_dep)
    router.include_router(monitorapp_router, dependencies=protected_dep)
    router.include_router(orders_router, dependencies=protected_dep)
    return router

