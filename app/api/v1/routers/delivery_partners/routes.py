from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, get_delivery_partner_service, require_authenticated
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.domain.enums.roles import Role
from app.services.delivery_partner_service import DeliveryPartnerService

router = APIRouter(prefix="/delivery-partners", tags=["delivery-partners"])

@router.get("/")
async def list_delivery_partners(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    name: str | None = Query(default=None),
    shop_id: str | None = Query(default=None),
    phone: str | None = Query(default=None),
    current_user: CurrentUser = Depends(require_authenticated),
    service: DeliveryPartnerService = Depends(get_delivery_partner_service),
) -> dict:
    if current_user.role != Role.SUPERADMIN:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    payload = service.list_delivery_partners(page=page, limit=limit, name=name, shop_id=shop_id, phone=phone)
    return {"data": payload["data"], "meta": payload["meta"]}
