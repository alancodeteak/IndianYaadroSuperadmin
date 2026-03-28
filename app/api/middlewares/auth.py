from __future__ import annotations

from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.exceptions.http_errors import ApiError
from app.api.deps.auth import build_current_user_from_authorization_header


class OptionalAuthMiddleware(BaseHTTPMiddleware):
    """
    Optional auth middleware that tries to resolve a JWT and attaches it to
    `request.state.current_user`. It never rejects requests by default.
    Uses the same decode path as get_current_user (no duplicate decode in Depends).
    """

    async def dispatch(self, request: Request, call_next):
        request.state.current_user = None
        request.state.auth_error = None

        auth_header: Optional[str] = request.headers.get("Authorization")
        if auth_header:
            try:
                request.state.current_user = build_current_user_from_authorization_header(auth_header)
            except ApiError as exc:
                request.state.auth_error = exc.code
                request.state.current_user = None

        return await call_next(request)
