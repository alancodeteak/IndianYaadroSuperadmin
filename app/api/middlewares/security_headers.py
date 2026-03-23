from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds baseline security headers for API responses.
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        path = request.url.path
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if path.startswith("/docs") or path.startswith("/redoc") or path == "/openapi.json":
            # Swagger/ReDoc require script/style loading and inline bootstrap snippets.
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self' https:; img-src 'self' data: https:; style-src 'self' https: 'unsafe-inline'; script-src 'self' https: 'unsafe-inline'; connect-src 'self' https:; frame-ancestors 'none'; base-uri 'none'",
            )
        else:
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
            )
        return response

