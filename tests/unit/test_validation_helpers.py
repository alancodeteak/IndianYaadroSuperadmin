"""Centralized pagination / range validation."""

import pytest

from app.api.exceptions.http_errors import ApiError
from app.services.validation import validate_days_range, validate_page_and_limit


def test_validate_page_and_limit_rejects_bad_page() -> None:
    with pytest.raises(ApiError) as ei:
        validate_page_and_limit(0, 10)
    assert "page" in str(ei.value.message).lower() or "page" in ei.value.message


def test_validate_days_range() -> None:
    validate_days_range(30, min_d=1, max_d=90)
    with pytest.raises(ApiError):
        validate_days_range(100, min_d=1, max_d=90)
