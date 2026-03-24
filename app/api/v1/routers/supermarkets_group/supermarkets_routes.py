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
    name: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    shop_id: str | None = Query(default=None),
    phone: str | None = Query(default=None),
    current_user: CurrentUser = Depends(require_authenticated),
    service: ShopOwnerService = Depends(get_shop_owner_service),
) -> dict:
    if current_user.role not in {Role.SUPERADMIN, Role.PORTAL_USER}:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    payload = service.list_supermarkets(
        page=page,
        limit=limit,
        name=name,
        user_id=user_id,
        shop_id=shop_id,
        phone=phone,
    )
    return {"data": payload["data"], "meta": payload["meta"]}


@router.get("/{user_id}")
async def get_supermarket_detail(
    user_id: int,
    current_user: CurrentUser = Depends(require_authenticated),
    service: ShopOwnerService = Depends(get_shop_owner_service),
) -> dict:
    if current_user.role not in {Role.SUPERADMIN, Role.PORTAL_USER}:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Not enough permissions",
            status_code=403,
        )
    payload = service.get_supermarket_detail(user_id=user_id, role=current_user.role)
    return {"data": payload, "meta": None}
