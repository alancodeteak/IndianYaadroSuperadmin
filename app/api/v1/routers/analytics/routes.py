from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    CurrentUser,
    get_delivery_partner_service,
    get_shop_owner_service,
    require_authenticated,
)
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.domain.enums.roles import Role
from app.services.delivery_partner_service import DeliveryPartnerService
from app.services.shop_owner_service import ShopOwnerService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/")
def analytics_root() -> dict:
    return {"data": {"message": "Analytics API router ready"}, "meta": None}


@router.get("/shops/{user_id}/activity")
def get_shop_activity(
    user_id: int,
    days: int = Query(default=7, ge=1, le=90),
    current_user: CurrentUser = Depends(require_authenticated),
    service: ShopOwnerService = Depends(get_shop_owner_service),
) -> dict:
    if current_user.role not in {Role.SUPERADMIN, Role.PORTAL_USER}:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    payload = service.get_shop_activity(user_id=user_id, role=current_user.role, days=days)
    return {"data": payload, "meta": None}


@router.get("/delivery-partners/{delivery_partner_id}/activity")
def get_delivery_partner_activity(
    delivery_partner_id: str,
    days: int = Query(default=7, ge=1, le=90),
    current_user: CurrentUser = Depends(require_authenticated),
    service: DeliveryPartnerService = Depends(get_delivery_partner_service),
) -> dict:
    if current_user.role != Role.SUPERADMIN:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    payload = service.get_delivery_partner_activity(delivery_partner_id=delivery_partner_id, days=days)
    return {"data": payload, "meta": None}


@router.get("/reports/overview")
def reports_overview(
    days: int = Query(default=30, ge=1, le=90),
    current_user: CurrentUser = Depends(require_authenticated),
    shop_service: ShopOwnerService = Depends(get_shop_owner_service),
) -> dict:
    payload = shop_service.get_reports_overview(role=current_user.role, days=days)
    return {"data": payload, "meta": {"days": days}}


@router.get("/reports/shops")
def reports_shops(
    days: int = Query(default=30, ge=1, le=90),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: CurrentUser = Depends(require_authenticated),
    shop_service: ShopOwnerService = Depends(get_shop_owner_service),
) -> dict:
    payload = shop_service.get_reports_shops(role=current_user.role, days=days, limit=limit)
    return {"data": payload, "meta": {"days": days, "limit": limit}}


@router.get("/reports/delivery-partners")
def reports_delivery_partners(
    days: int = Query(default=30, ge=1, le=90),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: CurrentUser = Depends(require_authenticated),
    partner_service: DeliveryPartnerService = Depends(get_delivery_partner_service),
) -> dict:
    if current_user.role != Role.SUPERADMIN:
        raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
    payload = partner_service.get_reports_delivery_partners(days=days, limit=limit)
    return {"data": payload, "meta": {"days": days, "limit": limit}}


@router.get("/reports/funnel")
def reports_funnel(
    days: int = Query(default=30, ge=1, le=90),
    current_user: CurrentUser = Depends(require_authenticated),
    shop_service: ShopOwnerService = Depends(get_shop_owner_service),
) -> dict:
    payload = shop_service.get_reports_funnel(role=current_user.role, days=days)
    return {"data": payload, "meta": {"days": days}}


@router.get("/reports/finance")
def reports_finance(
    days: int = Query(default=30, ge=1, le=90),
    current_user: CurrentUser = Depends(require_authenticated),
    shop_service: ShopOwnerService = Depends(get_shop_owner_service),
) -> dict:
    payload = shop_service.get_reports_finance(role=current_user.role, days=days)
    return {"data": payload, "meta": {"days": days}}
