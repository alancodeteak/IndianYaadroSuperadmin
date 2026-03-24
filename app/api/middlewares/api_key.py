from __future__ import annotations

from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class OptionalApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Skeleton API-key middleware.

    For now it only attaches the header value to `request.state.api_key`.
    Later use cases can validate it and reject requests.
    """

    async def dispatch(self, request: Request, call_next):
        request.state.api_key = _get_api_key(request)
        return await call_next(request)


def _get_api_key(request: Request) -> Optional[str]:
    # Keep header name compatible with typical API-key usage.
    return request.headers.get("x-api-key") or request.headers.get("X-API-KEY")

