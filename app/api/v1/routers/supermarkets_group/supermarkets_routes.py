from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, get_shop_owner_service, require_authenticated
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.domain.enums.roles import Role
from app.services.shop_owner_service import ShopOwnerService

router = APIRouter(prefix="/supermarkets", tags=["supermarkets"])


@router.get("/")
async def list_supermarkets(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_authenticated),
    service: ShopOwnerService = Depends(get_shop_owner_service),
) -> dict:
    if current_user.role not in {Role.SUPERADMIN, Role.PORTAL_USER}:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    payload = service.list_supermarkets(page=page, limit=limit)
    return {"data": payload["data"], "meta": payload["meta"]}
