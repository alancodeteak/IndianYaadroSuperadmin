"""
Domain-level errors raised by services.

Mapped to HTTP JSON by ``register_exception_handlers`` (same contract as ApiError).
Import as ``DomainValidationError`` if you need to disambiguate from Pydantic's
``ValidationError``.
"""

from __future__ import annotations

from typing import Any

from app.api.exceptions.error_codes import ErrorCode


class DomainError(Exception):
    """Base for domain/service failures (not HTTP)."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.RESOURCE_NOT_FOUND,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=404, details=details)


class ConflictError(DomainError):
    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.CONFLICT,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=409, details=details)


class DomainValidationError(DomainError):
    """Business validation failed (distinct from request body / Pydantic validation)."""

    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.VALIDATION_ERROR,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=400, details=details)


# Alias for callers who prefer the shorter name (avoid clashing with pydantic.ValidationError).
ValidationError = DomainValidationError


class PermissionDeniedError(DomainError):
    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.UNAUTHORIZED,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=403, details=details)


class BusinessRuleViolationError(DomainError):
    """Invariant or workflow rule broken (e.g. invalid state transition)."""

    def __init__(
        self,
        message: str,
        *,
        code: str = ErrorCode.VALIDATION_ERROR,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=status_code, details=details)
