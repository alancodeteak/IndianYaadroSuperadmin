from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class NoopRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Placeholder for rate limiting middleware.

    The current skeleton focuses on wiring + contracts; concrete limits and
    persistence (Redis/in-memory) come later.
    """

    async def dispatch(self, request: Request, call_next):
        return await call_next(request)

