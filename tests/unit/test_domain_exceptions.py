"""Domain errors carry codes and optional details for the global handler."""

from app.api.exceptions.error_codes import ErrorCode
from app.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    DomainValidationError,
    NotFoundError,
    PermissionDeniedError,
)


def test_not_found_defaults() -> None:
    e = NotFoundError("missing")
    assert e.status_code == 404
    assert e.code == ErrorCode.RESOURCE_NOT_FOUND


def test_conflict() -> None:
    e = ConflictError("dup", details={"field": "email"})
    assert e.status_code == 409
    assert e.details == {"field": "email"}


def test_permission_denied() -> None:
    e = PermissionDeniedError("nope")
    assert e.status_code == 403


def test_domain_validation() -> None:
    e = DomainValidationError("bad")
    assert e.status_code == 400


def test_business_rule() -> None:
    e = BusinessRuleViolationError("rule", status_code=422)
    assert e.status_code == 422
