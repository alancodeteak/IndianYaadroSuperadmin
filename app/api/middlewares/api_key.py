from __future__ import annotations

from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions.error_codes import ErrorCode
from app.api.core.config import get_settings


ADMIN_KEY_PATHS = (
    "/dashboard/api/cache/rebuild",
    "/dashboard/api/cache/stats",
)
METRICS_KEY_PATHS = (
    "/dashboard/api/socket-stats",
    "/dashboard/api/metrics/sockets/detailed",
)


class OptionalApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Skeleton API-key middleware.

    For now it only attaches the header value to `request.state.api_key`.
    Later use cases can validate it and reject requests.
    """

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        request.state.api_key = _get_api_key(request)
        path = request.url.path
        request_id = getattr(request.state, "request_id", None)

        if path.startswith(ADMIN_KEY_PATHS):
            if not settings.ENABLE_ADMIN_API_KEY_PROTECTION:
                return await call_next(request)
            expected = settings.ADMIN_API_KEY
            if not expected:
                return JSONResponse(
                    status_code=500,
                    content=_error_payload(
                        code=ErrorCode.API_KEY_NOT_CONFIGURED,
                        message="Admin API key protection is enabled but key is not configured",
                        request_id=request_id,
                    ),
                )
            if request.state.api_key != expected:
                return JSONResponse(
                    status_code=401,
                    content=_error_payload(
                        code=ErrorCode.INVALID_ADMIN_API_KEY,
                        message="Invalid admin API key",
                        request_id=request_id,
                    ),
                )

        if path.startswith(METRICS_KEY_PATHS):
            if not settings.ENABLE_METRICS_API_KEY_PROTECTION:
                return await call_next(request)
            expected = settings.METRICS_API_KEY
            if not expected:
                return JSONResponse(
                    status_code=500,
                    content=_error_payload(
                        code=ErrorCode.API_KEY_NOT_CONFIGURED,
                        message="Metrics API key protection is enabled but key is not configured",
                        request_id=request_id,
                    ),
                )
            if request.state.api_key != expected:
                return JSONResponse(
                    status_code=401,
                    content=_error_payload(
                        code=ErrorCode.INVALID_METRICS_API_KEY,
                        message="Invalid metrics API key",
                        request_id=request_id,
                    ),
                )

        return await call_next(request)


def _get_api_key(request: Request) -> Optional[str]:
    # Keep header name compatible with typical API-key usage.
    return request.headers.get("x-api-key") or request.headers.get("X-API-KEY")


def _error_payload(code: str, message: str, request_id: Optional[str]) -> dict[str, dict[str, str]]:
    payload: dict[str, dict[str, str]] = {"error": {"code": code, "message": message}}
    if request_id:
        payload["error"]["request_id"] = request_id
    return payload

