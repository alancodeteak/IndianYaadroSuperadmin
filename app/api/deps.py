from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session
from starlette import status

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.core.security import decode_token
from app.domain.enums.roles import Role
from app.infrastructure.db.session import get_db_session
from app.repositories.order_repository import OrderRepository
from app.services.order_service import OrderService


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    role: Role


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise ApiError(
            code=ErrorCode.UNAUTHENTICATED,
            message="Missing Authorization header",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ApiError(
            code=ErrorCode.UNAUTHENTICATED,
            message="Invalid Authorization header format",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return parts[1]


async def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> CurrentUser:
    token = _extract_bearer_token(authorization)

    payload: dict[str, Any] = decode_token(token)

    user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
    role_raw = payload.get("role") or payload.get("roles")

    if not user_id or not role_raw:
        raise ApiError(
            code=ErrorCode.UNAUTHENTICATED,
            message="Token missing required claims",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # role_raw can be "SUPERADMIN" or list of roles; normalize.
    if isinstance(role_raw, list):
        role_candidate = role_raw[0] if role_raw else None
    else:
        role_candidate = role_raw

    try:
        role = Role.from_str(str(role_candidate))
    except ValueError:
        raise ApiError(
            code=ErrorCode.UNAUTHORIZED,
            message="Token has unsupported role",
            details={"role": role_candidate},
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return CurrentUser(user_id=str(user_id), role=role)


def require_roles(*allowed_roles: Role):
    """
    Dependency helper for role-based authorization.
    """

    async def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise ApiError(
                code=ErrorCode.UNAUTHORIZED,
                message="Not enough permissions",
                details={"required": [r.value for r in allowed_roles], "actual": current_user.role.value},
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return _checker


async def require_authenticated(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Explicit dependency alias for routes that need authentication
    without role-specific authorization.
    """

    return current_user


def get_order_repository(db: Session = Depends(get_db_session)) -> OrderRepository:
    return OrderRepository(db=db)


def get_order_service(repo: OrderRepository = Depends(get_order_repository)) -> OrderService:
    return OrderService(repository=repo)

