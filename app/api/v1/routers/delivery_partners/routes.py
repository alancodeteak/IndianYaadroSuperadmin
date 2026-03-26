from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, get_delivery_partner_service, require_authenticated
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.delivery_partner import DeliveryPartnerBlockRequest
from app.domain.enums.roles import Role
from app.services.delivery_partner_service import DeliveryPartnerService

router = APIRouter(prefix="/delivery-partners", tags=["delivery-partners"])


@router.get("/")
async def list_delivery_partners(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    name: str | None = Query(default=None),
    delivery_partner_id: str | None = Query(default=None),
    shop_id: str | None = Query(default=None),
    shop_name: str | None = Query(default=None),
    phone: str | None = Query(default=None),
    current_status: str | None = Query(default=None),
    online_status: str | None = Query(default=None),
    current_user: CurrentUser = Depends(require_authenticated),
    service: DeliveryPartnerService = Depends(get_delivery_partner_service),
) -> dict:
    if current_user.role != Role.SUPERADMIN:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    payload = service.list_delivery_partners(
        page=page,
        limit=limit,
        name=name,
        delivery_partner_id=delivery_partner_id,
        shop_id=shop_id,
        shop_name=shop_name,
        phone=phone,
        current_status=current_status,
        online_status=online_status,
    )
    return {"data": payload["data"], "meta": payload["meta"]}


@router.get("/{delivery_partner_id}")
async def get_delivery_partner_detail(
    delivery_partner_id: str,
    current_user: CurrentUser = Depends(require_authenticated),
    service: DeliveryPartnerService = Depends(get_delivery_partner_service),
) -> dict:
    if current_user.role != Role.SUPERADMIN:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    detail = service.get_delivery_partner_detail(delivery_partner_id=delivery_partner_id)
    return {"data": detail, "meta": None}


@router.patch("/{delivery_partner_id}/block")
async def block_delivery_partner(
    delivery_partner_id: str,
    payload: DeliveryPartnerBlockRequest,
    current_user: CurrentUser = Depends(require_authenticated),
    service: DeliveryPartnerService = Depends(get_delivery_partner_service),
) -> dict:
    if current_user.role != Role.SUPERADMIN:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    result = service.set_delivery_partner_blocked(delivery_partner_id, blocked=payload.blocked)
    return {"data": result, "meta": None}


@router.delete("/{delivery_partner_id}")
async def delete_delivery_partner(
    delivery_partner_id: str,
    current_user: CurrentUser = Depends(require_authenticated),
    service: DeliveryPartnerService = Depends(get_delivery_partner_service),
) -> dict:
    if current_user.role != Role.SUPERADMIN:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    result = service.delete_delivery_partner(delivery_partner_id)
    return {"data": result, "meta": None}
