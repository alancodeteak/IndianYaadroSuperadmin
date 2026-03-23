from __future__ import annotations

import traceback
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status

from app.api.exceptions.error_codes import ErrorCode
from app.api.exceptions.http_errors import ApiError


def _error_payload(
    code: str, message: str, details: Optional[Any], request_id: Optional[str]
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if request_id:
        payload["error"]["request_id"] = request_id
    if details is not None:
        payload["error"]["details"] = details
    return payload


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.code, exc.message, exc.details, request_id=request_id),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # Map raw HTTPException into the standardized contract.
    code = ErrorCode.http_status_code(exc.status_code)
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            code=code, message=str(exc.detail), details=None, request_id=request_id
        ),
    )


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=_error_payload(
            code=ErrorCode.REQUEST_VALIDATION_ERROR,
            message="Invalid request",
            details={"errors": exc.errors()},
            request_id=request_id,
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Avoid leaking internals by default.
    details: Optional[Any] = None
    request_id = getattr(request.state, "request_id", None)
    if request.url.path.startswith("/_debug/"):
        details = {"trace": traceback.format_exc()}

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            details=details,
            request_id=request_id,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

