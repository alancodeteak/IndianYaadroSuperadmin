from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, Header
from jose import JWTError, jwt
from starlette import status

from app.domain.enums.roles import Role
from app.api.exceptions.http_errors import ApiError


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    role: Role


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        # Skeleton default; production should require env var.
        secret = "change-me"
    return secret


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise ApiError(
            code="UNAUTHENTICATED",
            message="Missing Authorization header",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ApiError(
            code="UNAUTHENTICATED",
            message="Invalid Authorization header format",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return parts[1]


async def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> CurrentUser:
    token = _extract_bearer_token(authorization)

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError as e:
        raise ApiError(
            code="UNAUTHENTICATED",
            message="Invalid or expired token",
            details={"reason": str(e)},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
    role_raw = payload.get("role") or payload.get("roles")

    if not user_id or not role_raw:
        raise ApiError(
            code="UNAUTHENTICATED",
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
            code="UNAUTHORIZED",
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
                code="UNAUTHORIZED",
                message="Not enough permissions",
                details={"required": [r.value for r in allowed_roles], "actual": current_user.role.value},
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return _checker

