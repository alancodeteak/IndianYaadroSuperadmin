from __future__ import annotations

from datetime import date
from typing import Any

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.repositories.daily_activity_repository import DailyActivityRepository


class DailyActivityService:
    def __init__(self, repository: DailyActivityRepository):
        self.repository = repository

    def get_overview(self, *, target_date: date) -> dict[str, Any]:
        return self.repository.get_overview(target_date=target_date)

    def list_shops(
        self,
        *,
        target_date: date,
        page: int,
        limit: int,
        search: str | None = None,
        sort: str = "revenue_desc",
    ) -> tuple[list[dict[str, Any]], int]:
        allowed_sort = {"revenue_desc", "orders_desc", "name_asc"}
        if sort not in allowed_sort:
            raise ApiError(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"sort must be one of: {', '.join(sorted(allowed_sort))}",
                status_code=400,
            )
        if page < 1:
            raise ApiError(code=ErrorCode.VALIDATION_ERROR, message="page must be >= 1", status_code=400)
        if limit < 1 or limit > 200:
            raise ApiError(code=ErrorCode.VALIDATION_ERROR, message="limit must be 1-200", status_code=400)
        return self.repository.list_shops(
            target_date=target_date,
            page=page,
            limit=limit,
            search=search,
            sort=sort,
        )

    def get_trends(self, *, days: int) -> list[dict[str, Any]]:
        if days < 1 or days > 90:
            raise ApiError(code=ErrorCode.VALIDATION_ERROR, message="days must be 1-90", status_code=400)
        return self.repository.get_trends(days=days)

