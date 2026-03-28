"""
Domain-level errors raised by services.

They carry no HTTP semantics; `register_exception_handlers` maps them to JSON
responses matching the existing ApiError contract.
"""

from __future__ import annotations

from app.api.exceptions.error_codes import ErrorCode


class DomainError(Exception):
    """Base for domain/service failures (not HTTP)."""

    def __init__(self, message: str, *, code: str, status_code: int = 400) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(DomainError):
    def __init__(self, message: str, *, code: str = ErrorCode.RESOURCE_NOT_FOUND) -> None:
        super().__init__(message, code=code, status_code=404)
