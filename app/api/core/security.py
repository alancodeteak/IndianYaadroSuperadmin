from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from starlette import status

from app.api.core.config import get_settings
from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError


def generate_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expire_minutes)
    payload = {
        "sub": subject,
        "role": role,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
    except JWTError:
        raise ApiError(
            code=ErrorCode.UNAUTHENTICATED,
            message="Invalid token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

