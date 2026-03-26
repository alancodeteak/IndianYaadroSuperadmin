from __future__ import annotations

from math import ceil
from typing import Any

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.v1.schemas.delivery_partner import DeliveryPartnerListFilters
from app.domain.repositories.delivery_partner_repository import AbstractDeliveryPartnerRepository


class DeliveryPartnerService:
    def __init__(self, repository: AbstractDeliveryPartnerRepository):
        self.repository = repository

    def list_delivery_partners(
        self,
        page: int,
        limit: int,
        *,
        name: str | None = None,
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

        filters = DeliveryPartnerListFilters(name=name, shop_id=shop_id, phone=phone)
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
        if not delivery_partner_id or delivery_partner_id.strip() == "":
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message="delivery_partner_id cannot be empty",
                status_code=400,
            )
        detail = self.repository.get_delivery_partner_detail(
            delivery_partner_id=delivery_partner_id.strip()
        )
        if detail is None:
            raise ApiError(
                code=ErrorCode.RESOURCE_NOT_FOUND,
                message="Delivery partner not found",
                status_code=404,
            )
        return detail

