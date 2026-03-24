from __future__ import annotations

from math import ceil
from typing import Any

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.shop_owner import SupermarketListFilters
from app.domain.enums.roles import Role
from app.domain.repositories.shop_owner_repository import AbstractShopOwnerRepository


class ShopOwnerService:
    def __init__(self, repository: AbstractShopOwnerRepository):
        self.repository = repository

    def list_supermarkets(
        self,
        page: int,
        limit: int,
        *,
        name: str | None = None,
        user_id: int | None = None,
        shop_id: str | None = None,
        phone: str | None = None,
    ) -> dict[str, Any]:
        if page < 1:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="page must be >= 1",
                status_code=400,
            )
        if limit < 1 or limit > 100:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="limit must be between 1 and 100",
                status_code=400,
            )

        filters = SupermarketListFilters(name=name, user_id=user_id, shop_id=shop_id, phone=phone)
        rows, total = self.repository.list_supermarkets(page=page, limit=limit, filters=filters)
        total_pages = ceil(total / limit) if total > 0 else 1
        return {
            "data": rows,
            "meta": {
                "currentPage": page,
                "limit": limit,
                "total": total,
                "totalPages": total_pages,
            },
        }

    def get_supermarket_detail(self, user_id: int, role: Role) -> dict[str, Any]:
        if user_id <= 0:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="user_id must be > 0",
                status_code=400,
            )

        detail = self.repository.get_supermarket_detail_by_user_id(user_id=user_id)
        if detail is None:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Supermarket not found",
                status_code=404,
            )

        if role == Role.PORTAL_USER:
            detail["delivery_partners"] = []
            detail["daily_order_stats"] = None
        elif role == Role.SUPERADMIN:
            # Superadmin receives full detail including daily order metrics.
            pass
        else:
            raise ApiError(
                code=ErrorCode.UNAUTHORIZED,
                message="Not enough permissions",
                status_code=403,
            )

        return detail

