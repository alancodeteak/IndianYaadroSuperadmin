from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.exceptions.handlers import (
    api_error_handler,
    http_exception_handler,
    request_validation_error_handler,
    unhandled_exception_handler,
)
from app.api.exceptions.http_errors import ApiError
from app.api.router import get_api_router
from app.api.middlewares.request_id import RequestIDMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title="Yadro Superadmin API",
        version="0.1.0",
    )

    app.add_middleware(RequestIDMiddleware)

    # Request/response contracts (standard error envelope)
    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)  # fallback

    # API wiring
    app.include_router(get_api_router())

    return app


app = create_app()

