"""
Shared business-rule validation for services (pagination bounds, ranges).

Routers should validate request shape; services use these helpers for limits that
must hold regardless of caller.
"""

from __future__ import annotations

from functools import lru_cache

from app.api.core.constants import MAX_PAGE_SIZE
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError


@lru_cache(maxsize=1)
def _default_page_cap() -> int:
    """Stable cap aligned with MAX_PAGE_SIZE (test-friendly)."""
    return MAX_PAGE_SIZE


def validate_page_and_limit(page: int, limit: int, *, max_limit: int | None = None) -> None:
    """page >= 1, limit in [1, max_limit]."""
    cap = max_limit if max_limit is not None else _default_page_cap()
    if page < 1:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="page must be >= 1",
            status_code=400,
        )
    if limit < 1 or limit > cap:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"limit must be between 1 and {cap}",
            status_code=400,
        )


def validate_page_and_limit_daily(page: int, limit: int, *, max_limit: int = 200) -> None:
    validate_page_and_limit(page, limit, max_limit=max_limit)


def validate_page_and_limit_invoice(page: int, limit: int, *, max_limit: int = 200) -> None:
    validate_page_and_limit(page, limit, max_limit=max_limit)


def validate_days_range(days: int, *, min_d: int = 1, max_d: int = 90) -> None:
    if days < min_d or days > max_d:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"days must be between {min_d} and {max_d}",
            status_code=400,
        )


def validate_sales_overview_days(days: int) -> None:
    validate_days_range(days, min_d=7, max_d=90)


def validate_months_range(months: int, *, min_m: int = 3, max_m: int = 12) -> None:
    if months < min_m or months > max_m:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"months must be between {min_m} and {max_m}",
            status_code=400,
        )


def validate_forecast_months_back(months_back: int) -> None:
    """Aligned with SalesActivityRepository.forecast_next_month_signups clamp (3–12)."""
    if months_back < 3 or months_back > 12:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="months_back must be between 3 and 12",
            status_code=400,
        )


def validate_limit(limit: int, *, max_limit: int | None = None) -> None:
    cap = max_limit if max_limit is not None else _default_page_cap()
    if limit < 1 or limit > cap:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"limit must be between 1 and {cap}",
            status_code=400,
        )


def validate_positive_id(value: int, *, field_name: str = "id") -> None:
    if value <= 0:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"{field_name} must be > 0",
            status_code=400,
        )


def validate_non_empty_str(value: str, *, field_name: str) -> str:
    stripped = (value or "").strip()
    if not stripped:
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"{field_name} cannot be empty",
            status_code=400,
        )
    return stripped
