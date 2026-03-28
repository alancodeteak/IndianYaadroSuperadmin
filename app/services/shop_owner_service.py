from __future__ import annotations

from math import ceil
from typing import Any

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.shop_owner import (
    SupermarketCreateRequest,
    SupermarketListFilters,
    SupermarketUpdateRequest,
)
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
        email: str | None = None,
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

        filters = SupermarketListFilters(
            name=name, user_id=user_id, shop_id=shop_id, phone=phone, email=email
        )
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

    def get_shop_id_for_portal_email(self, email: str) -> str | None:
        return self.repository.get_shop_id_by_email(email)

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

    def get_shop_activity(self, user_id: int, role: Role, days: int) -> dict[str, Any]:
        if role not in {Role.SUPERADMIN, Role.PORTAL_USER}:
            raise ApiError(
                code=ErrorCode.UNAUTHORIZED,
                message="Not enough permissions",
                status_code=403,
            )
        if user_id <= 0:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="user_id must be > 0",
                status_code=400,
            )
        if days < 1 or days > 90:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="days must be between 1 and 90",
                status_code=400,
            )

        payload = self.repository.get_shop_activity_by_user_id(user_id=user_id, days=days)
        if payload is None:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Supermarket not found",
                status_code=404,
            )
        return payload

    def get_reports_overview(self, role: Role, days: int) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
        if days < 1 or days > 90:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="days must be between 1 and 90",
                status_code=400,
            )
        return self.repository.get_reports_overview(days=days)

    def get_reports_shops(self, role: Role, days: int, limit: int) -> list[dict[str, Any]]:
        if role != Role.SUPERADMIN:
            raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
        if days < 1 or days > 90:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="days must be between 1 and 90",
                status_code=400,
            )
        if limit < 1 or limit > 100:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="limit must be between 1 and 100",
                status_code=400,
            )
        return self.repository.get_reports_shops(days=days, limit=limit)

    def get_reports_funnel(self, role: Role, days: int) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
        if days < 1 or days > 90:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="days must be between 1 and 90",
                status_code=400,
            )
        return self.repository.get_reports_funnel(days=days)

    def get_reports_finance(self, role: Role, days: int) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise ApiError(code=ErrorCode.UNAUTHORIZED, message="Not enough permissions", status_code=403)
        if days < 1 or days > 90:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="days must be between 1 and 90",
                status_code=400,
            )
        return self.repository.get_reports_finance(days=days)

    def create_supermarket(self, payload: SupermarketCreateRequest, role: Role) -> dict[str, Any]:
        if role not in {Role.PORTAL_USER, Role.SUPERADMIN}:
            raise ApiError(
                code=ErrorCode.UNAUTHORIZED,
                message="Not enough permissions",
                status_code=403,
            )
        # Portal users cannot set blocked/suspended at create time: repository always inserts ACTIVE.
        # Admin-only PATCH can change status / block flags.

        self.repository.create_supermarket(payload)
        return self.get_supermarket_detail(user_id=payload.user_id, role=role)

    def update_supermarket(
        self, user_id: int, payload: SupermarketUpdateRequest, role: Role
    ) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise ApiError(
                code=ErrorCode.UNAUTHORIZED,
                message="Not enough permissions",
                status_code=403,
            )
        if user_id <= 0:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="user_id must be > 0",
                status_code=400,
            )

        self.repository.update_supermarket(user_id=user_id, payload=payload)
        return self.get_supermarket_detail(user_id=user_id, role=role)

    def delete_supermarket(self, user_id: int, role: Role) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise ApiError(
                code=ErrorCode.UNAUTHORIZED,
                message="Not enough permissions",
                status_code=403,
            )
        if user_id <= 0:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="user_id must be > 0",
                status_code=400,
            )

        self.repository.soft_delete_supermarket(user_id=user_id)
        return {"deleted": True, "user_id": user_id}

