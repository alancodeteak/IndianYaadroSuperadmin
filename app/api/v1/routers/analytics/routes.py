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
async def analytics_root() -> dict:
    return {"data": {"message": "Analytics API router ready"}, "meta": None}


@router.get("/shops/{user_id}/activity")
async def get_shop_activity(
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
async def get_delivery_partner_activity(
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
