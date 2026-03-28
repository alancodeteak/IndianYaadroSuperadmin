from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import CurrentUser, require_roles
from app.api.deps.services import get_daily_activity_service
from app.domain.enums.roles import Role
from app.services.daily_activity_service import DailyActivityService


router = APIRouter(prefix="/api/v1/admin/daily-activity", tags=["daily-activity"])


@router.get("/overview", response_model=dict[str, Any])
async def get_daily_activity_overview(
    target_date: date = Query(default_factory=date.today),
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: DailyActivityService = Depends(get_daily_activity_service),
) -> dict[str, Any]:
    del current_user
    return {"data": service.get_overview(target_date=target_date), "meta": None}


@router.get("/shops", response_model=dict[str, Any])
async def list_daily_activity_shops(
    target_date: date = Query(default_factory=date.today),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
    search: str | None = None,
    sort: str = Query(default="revenue_desc"),
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: DailyActivityService = Depends(get_daily_activity_service),
) -> dict[str, Any]:
    del current_user
    items, total = service.list_shops(
        target_date=target_date,
        page=page,
        limit=limit,
        search=search,
        sort=sort,
    )
    total_pages = max(1, (total + limit - 1) // limit) if total else 1
    return {
        "data": items,
        "meta": {"page": page, "limit": limit, "total": total, "total_pages": total_pages},
    }


@router.get("/trends", response_model=dict[str, Any])
async def get_daily_activity_trends(
    days: int = Query(default=7, ge=1, le=90),
    current_user: CurrentUser = Depends(require_roles(Role.SUPERADMIN)),
    service: DailyActivityService = Depends(get_daily_activity_service),
) -> dict[str, Any]:
    del current_user
    return {"data": service.get_trends(days=days), "meta": {"days": days}}
