from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import CurrentUser, require_roles
from app.api.deps.services import get_sales_activity_service
from app.domain.enums.roles import Role
from app.services.sales_activity_service import SalesActivityService


router = APIRouter(prefix="/api/v1/admin/sales-activity", tags=["sales-activity"])


@router.get("/overview", response_model=dict[str, Any])
async def sales_activity_overview(
    days: int = Query(default=30, ge=7, le=90),
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: SalesActivityService = Depends(get_sales_activity_service),
) -> dict[str, Any]:
    del current_user
    return {"data": service.get_overview(days=days), "meta": {"days": days}}


@router.get("/monthly", response_model=dict[str, Any])
async def sales_activity_monthly(
    months: int = Query(default=6, ge=3, le=12),
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: SalesActivityService = Depends(get_sales_activity_service),
) -> dict[str, Any]:
    del current_user
    return {"data": service.get_monthly(months=months), "meta": {"months": months}}


@router.get("/top-shops", response_model=dict[str, Any])
async def sales_activity_top_shops(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: SalesActivityService = Depends(get_sales_activity_service),
) -> dict[str, Any]:
    del current_user
    return {"data": service.get_top_shops(limit=limit), "meta": {"limit": limit}}


@router.get("/forecast", response_model=dict[str, Any])
async def sales_activity_forecast(
    months_back: int = Query(default=6, ge=3, le=12),
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: SalesActivityService = Depends(get_sales_activity_service),
) -> dict[str, Any]:
    del current_user
    return {"data": service.get_forecast(months_back=months_back), "meta": {"months_back": months_back}}

