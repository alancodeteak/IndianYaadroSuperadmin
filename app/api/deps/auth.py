from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from fastapi import Depends, Header, Request
from starlette import status

from app.api.core.security import decode_token
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError
from app.api.deps.session import get_session_service
from app.domain.enums.roles import Role


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


def build_current_user_from_authorization_header(authorization: str) -> CurrentUser:
    """
    Single JWT decode + validation path used by OptionalAuthMiddleware and get_current_user.
    """
    token = _extract_bearer_token(authorization)

    payload: dict[str, Any] = decode_token(token)
    session_service = get_session_service()
    jti = payload.get("jti")
    if jti and session_service.is_revoked(str(jti)):
        raise ApiError(
            code=ErrorCode.AUTH_SESSION_EXPIRED,
            message="Session expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
    role_raw = payload.get("role") or payload.get("roles")

    if not user_id or not role_raw:
        raise ApiError(
            code=ErrorCode.UNAUTHENTICATED,
            message="Token missing required claims",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

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


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> CurrentUser:
    """
    Reuses request.state.current_user when OptionalAuthMiddleware already decoded the same request.
    Avoids a second JWT decode on the hot path.
    """
    if authorization:
        cached = getattr(request.state, "current_user", None)
        if cached is not None:
            return cached
    if not authorization:
        raise ApiError(
            code=ErrorCode.UNAUTHENTICATED,
            message="Missing Authorization header",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return build_current_user_from_authorization_header(authorization)


def require_roles(*allowed_roles: Role):
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
    return current_user
