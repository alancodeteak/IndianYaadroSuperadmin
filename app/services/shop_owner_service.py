from __future__ import annotations

from math import ceil
from typing import Any

from sqlalchemy.orm import Session

from app.api.exceptions.error_codes import ErrorCode
from app.domain.exceptions import NotFoundError, PermissionDeniedError
from app.api.v1.schemas.shop_owner import (
    SupermarketCreateRequest,
    SupermarketListFilters,
    SupermarketUpdateRequest,
)
from app.domain.enums.roles import Role
from app.domain.repositories.shop_owner_repository import AbstractShopOwnerRepository
from app.infrastructure.db.transaction import session_commit_scope
from app.services.validation import (
    validate_days_range,
    validate_limit,
    validate_page_and_limit,
    validate_positive_id,
)


class ShopOwnerService:
    def __init__(self, repository: AbstractShopOwnerRepository, session: Session):
        self.repository = repository
        self._session = session

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
        sort: str = "created_desc",
    ) -> dict[str, Any]:
        validate_page_and_limit(page, limit, max_limit=100)

        filters = SupermarketListFilters(
            name=name, user_id=user_id, shop_id=shop_id, phone=phone, email=email
        )
        rows, total = self.repository.list_supermarkets(
            page=page, limit=limit, filters=filters, sort=sort
        )
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
        validate_positive_id(user_id, field_name="user_id")

        detail = self.repository.get_supermarket_detail_by_user_id(user_id=user_id)
        if detail is None:
            raise NotFoundError("Supermarket not found", code=ErrorCode.RESOURCE_NOT_FOUND)

        if role == Role.PORTAL_USER:
            detail["delivery_partners"] = []
            detail["daily_order_stats"] = None
        elif role == Role.SUPERADMIN:
            # Superadmin receives full detail including daily order metrics.
            pass
        else:
            raise PermissionDeniedError("Not enough permissions")

        return detail

    def get_shop_activity(self, user_id: int, role: Role, days: int) -> dict[str, Any]:
        if role not in {Role.SUPERADMIN, Role.PORTAL_USER}:
            raise PermissionDeniedError("Not enough permissions")
        validate_positive_id(user_id, field_name="user_id")
        validate_days_range(days)

        payload = self.repository.get_shop_activity_by_user_id(user_id=user_id, days=days)
        if payload is None:
            raise NotFoundError("Supermarket not found", code=ErrorCode.RESOURCE_NOT_FOUND)
        return payload

    def get_reports_overview(self, role: Role, days: int) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise PermissionDeniedError("Not enough permissions")
        validate_days_range(days)
        return self.repository.get_reports_overview(days=days)

    def get_reports_shops(self, role: Role, days: int, limit: int) -> list[dict[str, Any]]:
        if role != Role.SUPERADMIN:
            raise PermissionDeniedError("Not enough permissions")
        validate_days_range(days)
        validate_limit(limit, max_limit=100)
        return self.repository.get_reports_shops(days=days, limit=limit)

    def get_reports_funnel(self, role: Role, days: int) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise PermissionDeniedError("Not enough permissions")
        validate_days_range(days)
        return self.repository.get_reports_funnel(days=days)

    def get_reports_finance(self, role: Role, days: int) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise PermissionDeniedError("Not enough permissions")
        validate_days_range(days)
        return self.repository.get_reports_finance(days=days)

    def create_supermarket(self, payload: SupermarketCreateRequest, role: Role) -> dict[str, Any]:
        if role not in {Role.PORTAL_USER, Role.SUPERADMIN}:
            raise PermissionDeniedError("Not enough permissions")
        # Portal users cannot set blocked/suspended at create time: repository always inserts ACTIVE.
        # Admin-only PATCH can change status / block flags.

        with session_commit_scope(self._session):
            self.repository.create_supermarket(payload)
        return self.get_supermarket_detail(user_id=payload.user_id, role=role)

    def update_supermarket(
        self, user_id: int, payload: SupermarketUpdateRequest, role: Role
    ) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise PermissionDeniedError("Not enough permissions")
        validate_positive_id(user_id, field_name="user_id")

        with session_commit_scope(self._session):
            self.repository.update_supermarket(user_id=user_id, payload=payload)
        return self.get_supermarket_detail(user_id=user_id, role=role)

    def delete_supermarket(self, user_id: int, role: Role) -> dict[str, Any]:
        if role != Role.SUPERADMIN:
            raise PermissionDeniedError("Not enough permissions")
        validate_positive_id(user_id, field_name="user_id")

        with session_commit_scope(self._session):
            self.repository.soft_delete_supermarket(user_id=user_id)
        return {"deleted": True, "user_id": user_id}

