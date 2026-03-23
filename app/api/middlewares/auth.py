from __future__ import annotations

from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions.http_errors import ApiError
from app.api.deps import CurrentUser, get_current_user


class OptionalAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional auth middleware that tries to resolve a JWT and attaches it to
    `request.state.current_user`. It never rejects requests by default.
    """

    async def dispatch(self, request: Request, call_next):
        request.state.current_user = None
        request.state.auth_error = None

        try:
            # Resolve JWT without using FastAPI Depends (middleware context).
            auth_header: Optional[str] = request.headers.get("Authorization")
            if auth_header:
                request.state.current_user = await get_current_user(
                    authorization=auth_header
                )
        except ApiError as exc:
            # Keep optional behavior while preserving observability.
            request.state.auth_error = exc.code
            request.state.current_user = None

        return await call_next(request)

