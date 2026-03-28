from __future__ import annotations

from math import ceil
from typing import Any

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.delivery_partner import DeliveryPartnerListFilters
from app.domain.repositories.delivery_partner_repository import AbstractDeliveryPartnerRepository
from app.services.validation import (
    validate_days_range,
    validate_limit,
    validate_page_and_limit,
    validate_non_empty_str,
)


class DeliveryPartnerService:
    def __init__(self, repository: AbstractDeliveryPartnerRepository):
        self.repository = repository

    def list_delivery_partners(
        self,
        page: int,
        limit: int,
        *,
        name: str | None = None,
        delivery_partner_id: str | None = None,
        shop_id: str | None = None,
        shop_name: str | None = None,
        phone: str | None = None,
        current_status: str | None = None,
        online_status: str | None = None,
        include_deleted: bool = True,
    ) -> dict[str, Any]:
        validate_page_and_limit(page, limit, max_limit=100)

        filters = DeliveryPartnerListFilters(
            name=name,
            delivery_partner_id=delivery_partner_id,
            shop_id=shop_id,
            shop_name=shop_name,
            phone=phone,
            current_status=current_status,
            online_status=online_status,
            include_deleted=bool(include_deleted),
        )
        rows, total = self.repository.list_delivery_partners(page=page, limit=limit, filters=filters)
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

    def get_delivery_partner_detail(self, delivery_partner_id: str) -> dict[str, Any]:
        did = validate_non_empty_str(delivery_partner_id, field_name="delivery_partner_id")
        detail = self.repository.get_delivery_partner_detail(
            delivery_partner_id=did
        )
        if detail is None:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return detail

    def get_delivery_partner_activity(self, delivery_partner_id: str, days: int) -> dict[str, Any]:
        did = validate_non_empty_str(delivery_partner_id, field_name="delivery_partner_id")
        validate_days_range(days)
        detail = self.repository.get_delivery_partner_activity(
            delivery_partner_id=did,
            days=days,
        )
        if detail is None:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return detail

    def get_reports_delivery_partners(self, days: int, limit: int) -> list[dict[str, Any]]:
        validate_days_range(days)
        validate_limit(limit, max_limit=100)
        return self.repository.get_reports_delivery_partners(days=days, limit=limit)

    def set_delivery_partner_blocked(self, delivery_partner_id: str, *, blocked: bool) -> dict[str, Any]:
        did = validate_non_empty_str(delivery_partner_id, field_name="delivery_partner_id")
        ok = self.repository.set_delivery_partner_blocked(
            did,
            blocked=bool(blocked),
        )
        if not ok:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return {"delivery_partner_id": did, "is_blocked": bool(blocked)}

    def delete_delivery_partner(self, delivery_partner_id: str) -> dict[str, Any]:
        did = validate_non_empty_str(delivery_partner_id, field_name="delivery_partner_id")
        ok = self.repository.soft_delete_delivery_partner(did)
        if not ok:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return {"delivery_partner_id": did, "deleted": True}

    def restore_delivery_partner(self, delivery_partner_id: str) -> dict[str, Any]:
        did = validate_non_empty_str(delivery_partner_id, field_name="delivery_partner_id")
        ok = self.repository.restore_delivery_partner(did)
        if not ok:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return {"delivery_partner_id": did, "restored": True}

