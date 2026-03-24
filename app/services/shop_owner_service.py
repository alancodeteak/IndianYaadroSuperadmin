from __future__ import annotations

from math import ceil
from typing import Any

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.domain.repositories.shop_owner_repository import AbstractShopOwnerRepository


class ShopOwnerService:
    def __init__(self, repository: AbstractShopOwnerRepository):
        self.repository = repository

    def list_supermarkets(self, page: int, limit: int) -> dict[str, Any]:
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

        rows, total = self.repository.list_supermarkets(page=page, limit=limit)
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

