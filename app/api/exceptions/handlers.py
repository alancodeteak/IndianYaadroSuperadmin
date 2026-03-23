from __future__ import annotations

import traceback
from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.api.exceptions.http_errors import ApiError


def _error_payload(code: str, message: str, details: Optional[Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }
    # Keep contract stable but omit null details.
    if details is None:
        payload["error"].pop("details", None)
    return payload


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.code, exc.message, exc.details),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # Map raw HTTPException into the standardized contract.
    code = f"HTTP_{exc.status_code}"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(code=code, message=str(exc.detail), details=None),
    )


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=_error_payload(
            code="VALIDATION_ERROR",
            message="Invalid request",
            details={"errors": exc.errors()},
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Avoid leaking internals by default.
    details: Optional[Any] = None
    if request.url.path.startswith("/_debug/"):
        details = {"trace": traceback.format_exc()}

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details=details,
        ),
    )

