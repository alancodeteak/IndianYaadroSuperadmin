from __future__ import annotations

from typing import Any

from app.repositories.sales_activity_repository import SalesActivityRepository
from app.services.validation import (
    validate_forecast_months_back,
    validate_limit,
    validate_months_range,
    validate_sales_overview_days,
)


class SalesActivityService:
    def __init__(self, repository: SalesActivityRepository):
        self.repository = repository

    def get_overview(self, *, days: int) -> dict[str, Any]:
        validate_sales_overview_days(days)
        return self.repository.get_overview(days=days)

    def get_monthly(self, *, months: int) -> list[dict[str, Any]]:
        validate_months_range(months)
        return self.repository.get_monthly(months=months)

    def get_top_shops(self, *, limit: int) -> list[dict[str, Any]]:
        validate_limit(limit, max_limit=100)
        return self.repository.get_top_shops_last_3_months(limit=limit)

    def get_forecast(self, *, months_back: int) -> dict[str, Any]:
        validate_forecast_months_back(months_back)
        result = self.repository.forecast_next_month_signups(months_back=months_back)
        return {
            "next_month": result.next_month,
            "predicted_signups": result.predicted_signups,
            "low": result.low,
            "high": result.high,
            "method": result.method,
        }

