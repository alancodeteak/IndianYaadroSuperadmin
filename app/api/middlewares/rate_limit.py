from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions.error_codes import ErrorCode
from app.api.core.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Lightweight in-memory fixed-window limiter.
    Suitable for single-process environments and local/dev usage.
    """

    _hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if not settings.ENABLE_RATE_LIMIT:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        now = time.time()
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        limit = settings.RATE_LIMIT_REQUESTS
        bucket = self._hits[key]

        while bucket and bucket[0] <= now - window:
            bucket.popleft()

        if len(bucket) >= limit:
            request_id = getattr(request.state, "request_id", None)
            payload = {
                "error": {
                    "code": ErrorCode.RATE_LIMITED,
                    "message": "Too many requests",
                    "details": {"limit": limit, "window_seconds": window},
                }
            }
            if request_id:
                payload["error"]["request_id"] = request_id
            return JSONResponse(
                status_code=429,
                content=payload,
            )

        bucket.append(now)
        return await call_next(request)

