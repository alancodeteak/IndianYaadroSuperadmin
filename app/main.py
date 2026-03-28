import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.exceptions.handlers import (
    register_exception_handlers,
)
from app.api.middlewares.api_key import OptionalApiKeyMiddleware
from app.api.middlewares.auth import OptionalAuthMiddleware
from app.api.middlewares.cors_config import apply_cors
from app.api.middlewares.logging_middleware import LoggingMiddleware
from app.api.middlewares.rate_limit import RateLimitMiddleware
from app.api.middlewares.request_id import RequestIDMiddleware
from app.api.middlewares.security_headers import SecurityHeadersMiddleware
from app.api.router import get_api_router
from app.api.core.config import get_settings
from app.api.core.logger import configure_logging
from app.infrastructure.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger = logging.getLogger("app.startup")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(
            "startup readiness: database OK",
            extra={"fail_fast_on_db_error": settings.FAIL_FAST_ON_DB_ERROR},
        )
    except Exception as exc:
        logger.error(
            "startup readiness: database FAILED",
            extra={"error_type": type(exc).__name__, "fail_fast": settings.FAIL_FAST_ON_DB_ERROR},
        )
        if settings.FAIL_FAST_ON_DB_ERROR:
            raise
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    apply_cors(app, settings)
    allowed_hosts = [h.strip() for h in settings.ALLOWED_HOSTS.split(",") if h.strip()]
    if allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    if settings.FORCE_HTTPS_REDIRECT:
        app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(OptionalAuthMiddleware)
    app.add_middleware(OptionalApiKeyMiddleware)
    app.add_middleware(RateLimitMiddleware)
    if settings.ENABLE_RESPONSE_GZIP:
        app.add_middleware(GZipMiddleware, minimum_size=int(settings.GZIP_MINIMUM_SIZE))

    register_exception_handlers(app)
    app.include_router(get_api_router())

    return app


app = create_app()
