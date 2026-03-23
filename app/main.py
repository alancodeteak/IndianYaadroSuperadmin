from fastapi import FastAPI
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.exceptions.handlers import (
    register_exception_handlers,
)
from app.api.middlewares.api_key import OptionalApiKeyMiddleware
from app.api.middlewares.auth import OptionalAuthMiddleware
from app.api.middlewares.cors_config import apply_cors
from app.api.middlewares.logging_middleware import LoggingMiddleware
from app.api.middlewares.metrics_middleware import MetricsMiddleware
from app.api.middlewares.rate_limit import RateLimitMiddleware
from app.api.middlewares.request_id import RequestIDMiddleware
from app.api.middlewares.security_headers import SecurityHeadersMiddleware
from app.api.router import get_api_router
from app.api.core.config import get_settings
from app.api.core.logger import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
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
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(OptionalAuthMiddleware)
    app.add_middleware(OptionalApiKeyMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Request/response contracts (standard error envelope)
    register_exception_handlers(app)

    # API wiring
    app.include_router(get_api_router())

    return app


app = create_app()

