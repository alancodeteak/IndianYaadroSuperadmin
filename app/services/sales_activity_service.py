from __future__ import annotations

from typing import Any

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.repositories.sales_activity_repository import SalesActivityRepository


class SalesActivityService:
    def __init__(self, repository: SalesActivityRepository):
        self.repository = repository

    def get_overview(self, *, days: int) -> dict[str, Any]:
        if days < 7 or days > 90:
            raise ApiError(code=ErrorCode.VALIDATION_ERROR, message="days must be 7-90", status_code=400)
        return self.repository.get_overview(days=days)

    def get_monthly(self, *, months: int) -> list[dict[str, Any]]:
        if months < 3 or months > 12:
            raise ApiError(code=ErrorCode.VALIDATION_ERROR, message="months must be 3-12", status_code=400)
        return self.repository.get_monthly(months=months)

    def get_top_shops(self, *, limit: int) -> list[dict[str, Any]]:
        if limit < 1 or limit > 100:
            raise ApiError(code=ErrorCode.VALIDATION_ERROR, message="limit must be 1-100", status_code=400)
        return self.repository.get_top_shops_last_3_months(limit=limit)

    def get_forecast(self, *, months_back: int) -> dict[str, Any]:
        result = self.repository.forecast_next_month_signups(months_back=months_back)
        return {
            "next_month": result.next_month,
            "predicted_signups": result.predicted_signups,
            "low": result.low,
            "high": result.high,
            "method": result.method,
        }

